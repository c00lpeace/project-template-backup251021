# _*_ coding: utf-8 _*_
"""
Program Upload Service for handling program file upload workflow.

Phase 3 리팩토링 (2025-11-06):
- FileValidationService, FileStorageService 통합
- 명확한 변수명 적용 (pgm_ladder_zip_file, pgm_template_file)
- 환경변수 기반 설정
- DocumentService의 새 메서드 사용
- 트랜잭션 경계 명확화
"""
import logging
import io
import zipfile
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ai_backend.config.simple_settings import settings
from ai_backend.api.services.sequence_service import SequenceService
from ai_backend.api.services.file_validation_service import FileValidationService
from ai_backend.api.services.file_storage_service import FileStorageService
from ai_backend.api.services.document_service import DocumentService
from ai_backend.api.services.template_service import TemplateService
from ai_backend.api.services.program_service import ProgramService
from ai_backend.database.crud.program_crud import ProgramCrud
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class ProgramUploadService:
    """
    프로그램 파일 업로드 통합 서비스 (Phase 3 리팩토링)
    
    워크플로우:
    Phase 1: 검증 (DB 트랜잭션 외부)
    Step 1-2: 레더 ZIP 타입/크기 검증
    Step 3:   ZIP 구조 검증 (손상 여부, 파일 목록만)
    Step 4-5: 템플릿 타입/크기 검증
    Step 6:   템플릿 구조 검증 (필수 컬럼, Logic ID 추출)
    Step 7:   매칭 검증 (템플릿 Logic ID vs ZIP 파일 목록)
    Step 8:   매칭된 CSV만 구조 검증 (메모리) ⭐ Phase 1.5 신규
    
    Phase 2: 파일 저장 (DB 트랜잭션 외부)
    Step 9:  레더 ZIP 필터링
    Step 10: 레더 ZIP 저장 및 압축 해제 (FileStorageService)
    Step 11: 템플릿 파일 저장 (FileStorageService)
    
    Phase 3: DB 저장 (트랜잭션 시작)
    Step 12: 레더 CSV 문서 레코드 일괄 생성 (DocumentService)
    Step 13: 템플릿 문서 레코드 생성 + 자동 파싱 (DocumentService)
    Step 14: 프로그램 레코드 생성 (ProgramService)
    Step 15: 커밋
    """
    
    def __init__(
        self,
        db: Session,
        sequence_service: SequenceService,
        file_validation_service: FileValidationService,
        file_storage_service: FileStorageService,
        document_service: DocumentService,
        template_service: TemplateService,
        program_service: ProgramService
    ):
        """
        Args:
            db: 데이터베이스 세션
            sequence_service: PGM_ID 생성 서비스
            file_validation_service: 파일 검증 서비스 (Phase 1 신규)
            file_storage_service: 파일 저장 서비스 (Phase 1 신규)
            document_service: 문서 DB 서비스 (Phase 2 리팩토링)
            template_service: 템플릿 서비스
            program_service: 프로그램 서비스
        """
        self.db = db
        self.settings = settings  # 환경변수 주입
        self.sequence_service = sequence_service
        self.file_validation_service = file_validation_service
        self.file_storage_service = file_storage_service
        self.document_service = document_service
        self.template_service = template_service
        self.program_service = program_service
        self.program_crud = ProgramCrud(db)
    
    def upload_program_with_files(
        self,
        pgm_name: str,
        pgm_ladder_zip_file: UploadFile,  # 명확한 변수명
        pgm_template_file: UploadFile,    # 명확한 변수명
        create_user: str,
        pgm_version: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        프로그램 파일 업로드 및 생성 (전체 워크플로우)
        
        Phase 3 리팩토링 (2025-11-06):
        - 명확한 변수명 사용
        - 새 서비스 통합 (FileValidationService, FileStorageService)
        - DocumentService 새 메서드 사용
        - 트랜잭션 경계 명확화
        
        Args:
            pgm_name: 프로그램 명칭
            pgm_ladder_zip_file: 레더 CSV 파일들이 압축된 ZIP
            pgm_template_file: 필수 파일 목록이 기재된 템플릿 파일
            create_user: 생성자
            pgm_version: 프로그램 버전 (선택)
            description: 프로그램 설명 (선택)
            notes: 비고 (선택)
            
        Returns:
            {
                'program': Program,
                'pgm_id': str,
                'validation_result': Dict,
                'saved_files': Dict,
                'summary': Dict,
                'message': str
            }
        """
        saved_file_paths = []  # 롤백용
        
        try:
            # ======================================
            # Phase 1: 검증 (DB 트랜잭션 외부)
            # ======================================
            
            # 0. PGM_ID 자동 생성
            pgm_id = self.sequence_service.generate_pgm_id()
            logger.info(f"✅ [Step 0] PGM_ID 자동 생성: {pgm_id}")
            
            # 1. 레더 ZIP 파일 타입/크기 검증 (환경변수 기반)
            self.file_validation_service.validate_ladder_zip_file_type(
                pgm_ladder_zip_file
            )
            self.file_validation_service.validate_ladder_zip_file_size(
                pgm_ladder_zip_file
            )
            logger.info(
                f"✅ [Step 1] 레더 ZIP 파일 검증 완료: {pgm_ladder_zip_file.filename}"
            )
            
            # 2. 템플릿 파일 타입/크기 검증 (환경변수 기반)
            self.file_validation_service.validate_template_file_type(
                pgm_template_file
            )
            self.file_validation_service.validate_template_file_size(
                pgm_template_file
            )
            logger.info(
                f"✅ [Step 2] 템플릿 파일 검증 완료: {pgm_template_file.filename}"
            )
            
            # 3. 템플릿 구조 검증 (환경변수 기반 필수 컬럼)
            template_structure = self.file_validation_service.validate_template_file_structure(
                pgm_template_file
            )
            logger.info(
                f"✅ [Step 3] 템플릿 구조 검증 완료: "
                f"{len(template_structure['logic_ids'])}개 Logic ID"
            )
            
            # 4. ZIP 구조 검증
            zip_structure = self.file_validation_service.validate_ladder_zip_structure(
                pgm_ladder_zip_file
            )
            logger.info(
                f"✅ [Step 4] ZIP 구조 검증 완료: "
                f"{len(zip_structure['file_list'])}개 파일"
            )
            
            # 5. 레더 파일 매칭 검증
            validation_result = self.file_validation_service.validate_ladder_files_match(
                required_files=template_structure['logic_ids'],
                actual_files=zip_structure['file_list']
            )
            
            if not validation_result['validation_passed']:
                missing_files_str = ', '.join(validation_result['missing_files'])
                logger.error(
                    f"❌ 파일 검증 실패: pgm_id={pgm_id}, "
                    f"누락 파일={missing_files_str}"
                )
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"필수 레더 파일이 누락되었습니다: {missing_files_str}"
                )
            
            logger.info(
                f"✅ [Step 7] 레더 파일 매칭 검증 완료: "
                f"{len(validation_result['matched_files'])}개 일치"
            )
            
            # 8. 매칭된 레더 CSV 파일 구조 검증 (메모리) - Phase 1.5 신규
            csv_structure_validation_result = self.file_validation_service.validate_matched_ladder_csv_structures_in_memory(
                ladder_zip_file=pgm_ladder_zip_file,
                matched_files=validation_result['matched_files']
            )
            
            logger.info(
                f"✅ [Step 8] 레더 CSV 구조 검증 완료: "
                f"{csv_structure_validation_result['validated_count']}개 파일 통과"
            )
            
            # ======================================
            # Phase 2: 파일 저장 (DB 트랜잭션 외부)
            # ======================================
            
            # 9. 레더 ZIP 필터링 (필요한 파일만)
            filtered_ladder_zip_bytes = self._filter_ladder_zip(
                pgm_ladder_zip_file,
                validation_result['matched_files']
            )
            logger.info(f"✅ [Step 9] 레더 ZIP 필터링 완료")
            
            # 10. 레더 ZIP 저장 및 압축 해제 (환경변수 기반 경로)
            ladder_zip_extract_result = self.file_storage_service.save_and_extract_ladder_zip(
                ladder_zip_bytes=filtered_ladder_zip_bytes,
                pgm_id=pgm_id,
                original_filename=pgm_ladder_zip_file.filename
            )
            
            # 저장된 파일 경로 기록 (롤백용)
            saved_file_paths.extend([
                f['path'] for f in ladder_zip_extract_result['extracted_ladder_files']
            ])
            if ladder_zip_extract_result.get('original_zip'):
                saved_file_paths.append(
                    ladder_zip_extract_result['original_zip']['path']
                )
            
            logger.info(
                f"✅ [Step 10] 레더 파일 저장 완료: "
                f"{len(ladder_zip_extract_result['extracted_ladder_files'])}개"
            )
            
            # 11. 템플릿 파일 저장 (환경변수 기반 경로)
            template_save_result = self.file_storage_service.save_template_file(
                template_file=pgm_template_file,
                pgm_id=pgm_id
            )
            saved_file_paths.append(template_save_result['file_path'])
            
            logger.info(f"✅ [Step 11] 템플릿 파일 저장 완료")
            
            # ======================================
            # Phase 3: DB 저장 (트랜잭션 시작)
            # ======================================
            
            # 12. 레더 CSV 문서 레코드 일괄 생성
            pgm_ladder_csv_documents_data = [
                {
                    'document_name': file_info['filename'],
                    'original_filename': file_info['filename'],
                    'file_key': f"{pgm_id}/{self.settings.pgm_ladder_dir_name}/{file_info['filename']}",
                    'upload_path': str(file_info['path']),
                    'file_size': file_info['size'],
                    'pgm_id': pgm_id,
                    'user_id': create_user,
                    'is_public': False,
                    'metadata': {
                        'file_hash': file_info.get('hash'),
                        'upload_method': 'program_upload',
                        'extracted_from_zip': True
                    }
                }
                for file_info in ladder_zip_extract_result['extracted_ladder_files']
            ]
            
            pgm_ladder_csv_documents = self.document_service.bulk_create_ladder_csv_documents(
                pgm_ladder_csv_documents_data
            )
            
            logger.info(
                f"✅ [Step 12] 레더 CSV 문서 레코드 생성 완료: "
                f"{len(pgm_ladder_csv_documents)}개"
            )
            
            # 13. 템플릿 문서 레코드 생성 (자동으로 템플릿 파싱됨)
            pgm_template_document = self.document_service.create_template_document(
                document_name=template_save_result['filename'],
                original_filename=template_save_result['filename'],
                file_key=f"{pgm_id}/{self.settings.pgm_template_dir_name}/{template_save_result['filename']}",
                upload_path=str(template_save_result['file_path']),
                file_size=template_save_result['size'],
                pgm_id=pgm_id,
                user_id=create_user,
                is_public=False,
                metadata={
                    'file_hash': template_save_result.get('hash'),
                    'upload_method': 'program_upload'
                }
            )
            # ↑ create_template_document() 내부에서 자동으로:
            #    - ProgramTemplateProcessor 호출
            #    - 템플릿 파싱
            #    - PGM_TEMPLATE 테이블 INSERT
            
            logger.info(
                f"✅ [Step 13] 템플릿 문서 레코드 생성 및 파싱 완료: "
                f"{pgm_template_document.document_id}"
            )
            
            # 14. 프로그램 레코드 생성
            program = self.program_service.create_program(
                pgm_id=pgm_id,
                pgm_name=pgm_name,
                pgm_version=pgm_version,
                description=description,
                create_user=create_user,
                notes=notes
            )
            
            logger.info(
                f"✅ [Step 14] 프로그램 레코드 생성 완료: {pgm_id}"
            )
            
            # 15. 커밋
            self.db.commit()
            logger.info(f"🎉 [Success] 프로그램 업로드 완료: {pgm_id}")
            
            # 16. 결과 반환
            return {
                'program': program,
                'pgm_id': pgm_id,
                'validation_result': validation_result,
                'saved_files': {
                    'ladder_csv_documents': [
                        {
                            'document_id': doc.document_id,
                            'document_name': doc.document_name,
                            'upload_path': doc.upload_path
                        }
                        for doc in pgm_ladder_csv_documents
                    ],
                    'template_document': {
                        'document_id': pgm_template_document.document_id,
                        'document_name': pgm_template_document.document_name,
                        'upload_path': pgm_template_document.upload_path
                    }
                },
                'summary': {
                    'total_ladder_files': len(pgm_ladder_csv_documents),
                    'template_parsed': True,
                    'template_row_count': len(template_structure['logic_ids'])
                },
                'message': '프로그램이 성공적으로 생성되었습니다'
            }
            
        except HandledException:
            # HandledException은 그대로 전파
            self.db.rollback()
            
            # 저장된 파일 삭제
            if saved_file_paths:
                self.file_storage_service.delete_files(saved_file_paths)
                logger.info(f"🔄 [Rollback] 저장된 파일 삭제 완료")
            
            raise
            
        except Exception as e:
            # 롤백
            self.db.rollback()
            logger.error(f"❌ [Error] 프로그램 업로드 실패: {str(e)}", exc_info=True)
            
            # 저장된 파일 삭제
            if saved_file_paths:
                try:
                    self.file_storage_service.delete_files(saved_file_paths)
                    logger.info(f"🔄 [Rollback] 저장된 파일 삭제 완료")
                except Exception as cleanup_error:
                    logger.error(f"❌ 파일 정리 실패: {str(cleanup_error)}")
            
            raise HandledException(
                ResponseCode.UNDEFINED_ERROR,
                msg=f"프로그램 업로드 중 오류 발생: {str(e)}",
                e=e
            )
    
    def _filter_ladder_zip(
        self,
        pgm_ladder_zip_file: UploadFile,
        keep_files: List[str]
    ) -> bytes:
        """
        레더 ZIP에서 필요한 파일만 남기고 새로운 ZIP 생성
        
        Args:
            pgm_ladder_zip_file: 원본 레더 ZIP 파일
            keep_files: 유지할 파일 목록 (예: ["0000_11.csv", "0001_11.csv"])
            
        Returns:
            bytes: 필터링된 ZIP 파일 바이트
        """
        try:
            # 원본 ZIP 읽기
            original_content = pgm_ladder_zip_file.file.read()
            pgm_ladder_zip_file.file.seek(0)  # 포인터 복원
            
            # 새로운 ZIP 생성
            filtered_buffer = io.BytesIO()
            
            with zipfile.ZipFile(io.BytesIO(original_content), 'r') as original_zip:
                with zipfile.ZipFile(filtered_buffer, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    for info in original_zip.infolist():
                        if not info.is_dir():
                            filename = Path(info.filename).name
                            if filename in keep_files:
                                # 필요한 파일만 복사
                                new_zip.writestr(info, original_zip.read(info.filename))
            
            filtered_buffer.seek(0)
            filtered_bytes = filtered_buffer.read()
            
            logger.info(
                f"레더 ZIP 필터링 완료: "
                f"{len(keep_files)}개 파일 유지"
            )
            
            return filtered_bytes
            
        except Exception as e:
            logger.error(f"❌ ZIP 파일 필터링 실패: {str(e)}")
            raise HandledException(
                ResponseCode.DOCUMENT_UPLOAD_ERROR,
                msg=f"ZIP 파일 필터링 실패: {str(e)}",
                e=e
            )
