# _*_ coding: utf-8 _*_
"""Program Upload Service for handling program file upload workflow."""
import logging
import io
import zipfile
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from ai_backend.api.services.sequence_service import SequenceService
from ai_backend.api.services.document_service import DocumentService
from ai_backend.api.services.template_service import TemplateService
from ai_backend.api.services.program_service import ProgramService
from ai_backend.database.crud.program_crud import ProgramCrud
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class ProgramUploadService:
    """
    프로그램 파일 업로드 통합 서비스
    
    워크플로우:
    0. PGM_ID 자동 생성 (서버)
    1. 파일 타입 검증
    2. 파일 검증 (Logic ID vs ZIP 파일 목록)
    3. 불필요한 파일 제거
    4. 파일 저장 (DOCUMENTS 테이블)
    5. 프로그램 생성 (PROGRAMS 테이블)
    """
    
    def __init__(
        self,
        db: Session,
        sequence_service: SequenceService,
        document_service: DocumentService,
        template_service: TemplateService,
        program_service: ProgramService
    ):
        self.db = db
        self.sequence_service = sequence_service
        self.document_service = document_service
        self.template_service = template_service
        self.program_service = program_service
        self.program_crud = ProgramCrud(db)
    
    def upload_and_create_program(
        self,
        pgm_name: str,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        create_user: str,
        pgm_version: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        프로그램 파일 업로드 및 생성 (전체 워크플로우)
        
        Args:
            pgm_name: 프로그램 명칭
            ladder_zip: 레더 CSV 파일들이 압축된 ZIP
            template_xlsx: 필수 파일 목록이 기재된 템플릿 파일
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
                'message': str
            }
        """
        try:
            # 0. PGM_ID 자동 생성 (서버)
            pgm_id = self.sequence_service.generate_pgm_id()
            logger.info(f"[Step 0] PGM_ID 자동 생성: {pgm_id}")
            
            # 1. 파일 타입 검증
            logger.info(f"[Step 1] 파일 타입 검증 시작: pgm_id={pgm_id}")
            self._validate_file_types(ladder_zip, template_xlsx)
            
            # 2. 파일 검증 (Logic ID vs ZIP 파일 목록)
            logger.info(f"[Step 2] 파일 검증 시작: pgm_id={pgm_id}")
            validation_result = self._validate_files(
                ladder_zip, template_xlsx, pgm_id
            )
            
            # 3. 검증 실패 시 에러
            if not validation_result['validation_passed']:
                missing_files_str = ', '.join(validation_result['missing_files'])
                logger.error(f"파일 검증 실패: pgm_id={pgm_id}, 누락 파일={missing_files_str}")
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"필수 파일이 누락되었습니다: {missing_files_str}"
                )
            
            logger.info(f"파일 검증 통과: matched={len(validation_result['matched_files'])}, "
                       f"extra={len(validation_result['extra_files'])}")
            
            # 4. 불필요한 파일 제거 (검증 통과 시)
            logger.info(f"[Step 3] 불필요한 파일 제거: {len(validation_result['extra_files'])}개")
            filtered_zip_bytes = self._filter_unnecessary_files(
                ladder_zip,
                validation_result['matched_files']
            )
            
            # 5. 파일 저장 (DOCUMENTS 테이블 자동 등록)
            logger.info(f"[Step 4] 파일 저장 시작: pgm_id={pgm_id}")
            save_result = self._save_files(
                filtered_zip_bytes,
                template_xlsx,
                pgm_id,
                create_user
            )
            
            # 6. ⭐ 프로그램 생성 (단순화: create_program()만 호출)
            logger.info(f"[Step 5] 프로그램 생성: pgm_id={pgm_id}")
            program = self.program_service.create_program(
                pgm_id=pgm_id,
                pgm_name=pgm_name,
                pgm_version=pgm_version,
                description=description,
                create_user=create_user,
                notes=notes
            )
            
            # 7. 커밋
            self.db.commit()
            logger.info(f"[Success] 프로그램 생성 완료: pgm_id={pgm_id}")
            
            # 8. 결과 반환
            return {
                'program': program,
                'pgm_id': pgm_id,
                'validation_result': validation_result,
                'saved_files': save_result,
                'summary': {
                    'total_ladder_files': len(validation_result['matched_files']),
                    'template_parsed': True,
                    'template_row_count': len(validation_result['required_files'])
                },
                'message': '프로그램이 성공적으로 생성되었습니다'
            }
            
        except HandledException:
            # HandledException은 그대로 전파
            self.db.rollback()
            raise
        except Exception as e:
            # 롤백
            self.db.rollback()
            logger.error(f"프로그램 업로드 실패: {str(e)}", exc_info=True)
            
            # 저장된 파일 삭제 (선택사항)
            if 'save_result' in locals():
                try:
                    self._cleanup_saved_files(save_result)
                except Exception as cleanup_error:
                    logger.error(f"파일 정리 실패: {str(cleanup_error)}")
            
            raise HandledException(
                ResponseCode.UNDEFINED_ERROR,
                msg=f"프로그램 업로드 중 오류 발생: {str(e)}",
                e=e
            )
    
    def _validate_file_types(self, ladder_zip: UploadFile, template_xlsx: UploadFile):
        """파일 타입 검증"""
        if not ladder_zip.filename or not ladder_zip.filename.endswith('.zip'):
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="레더 파일은 .zip 형식이어야 합니다"
            )
        
        if not template_xlsx.filename or not template_xlsx.filename.endswith('.xlsx'):
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="템플릿 파일은 .xlsx 형식이어야 합니다"
            )
    
    def _validate_files(
        self,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        pgm_id: str
    ) -> Dict:
        """
        파일 검증 (Logic ID vs ZIP 파일 목록)
        
        Returns:
            {
                'required_files': List[str],
                'zip_files': List[str],
                'matched_files': List[str],
                'missing_files': List[str],
                'extra_files': List[str],
                'validation_passed': bool
            }
        """
        # 템플릿에서 필수 파일 추출
        required_files = self._extract_required_files_from_template(
            template_xlsx, pgm_id
        )
        
        # ZIP에서 파일 목록 추출
        zip_files = self._extract_file_list_from_zip(ladder_zip)
        
        # 파일 비교
        return self._compare_files(required_files, zip_files)
    
    def _extract_required_files_from_template(
        self,
        template_xlsx: UploadFile,
        pgm_id: str
    ) -> List[str]:
        """
        XLSX 템플릿 파일에서 Logic ID 컬럼을 읽어 필수 CSV 파일 목록 생성
        
        Logic ID 예시: "0000_11", "0001_11", "0002_11"
        변환 결과: ["0000_11.csv", "0001_11.csv", "0002_11.csv"]
        """
        try:
            # 메모리에서 XLSX 읽기
            file_content = template_xlsx.file.read()
            template_xlsx.file.seek(0)  # 포인터 초기화
            
            df = pd.read_excel(io.BytesIO(file_content))
            
            # 필수 컬럼 확인
            if 'Logic ID' not in df.columns:
                raise HandledException(
                    ResponseCode.REQUIRED_FIELD_MISSING,
                    msg="템플릿 파일에 'Logic ID' 컬럼이 없습니다"
                )
            
            # Logic ID에서 필수 파일 목록 생성
            required_files = []
            for logic_id in df['Logic ID']:
                if pd.notna(logic_id):
                    csv_filename = f"{str(logic_id).strip()}.csv"
                    required_files.append(csv_filename)
            
            # 중복 제거
            unique_files = list(set(required_files))
            logger.info(f"템플릿에서 필수 파일 {len(unique_files)}개 추출: {unique_files[:5]}...")
            
            return unique_files
            
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"템플릿 파일 파싱 실패: {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"템플릿 파일 파싱 실패: {str(e)}",
                e=e
            )
    
    def _extract_file_list_from_zip(self, ladder_zip: UploadFile) -> List[str]:
        """
        ZIP 파일 내부의 CSV 파일 목록 추출
        
        주의: 디렉토리는 제외, 파일명만 추출
        """
        try:
            # 메모리에서 ZIP 읽기
            file_content = ladder_zip.file.read()
            ladder_zip.file.seek(0)  # 포인터 초기화
            
            zip_files = []
            with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_ref:
                for info in zip_ref.infolist():
                    # 디렉토리 제외
                    if not info.is_dir():
                        # 파일명만 추출 (경로 제거)
                        filename = Path(info.filename).name
                        zip_files.append(filename)
            
            logger.info(f"ZIP에서 파일 {len(zip_files)}개 추출: {zip_files[:5]}...")
            return zip_files
            
        except zipfile.BadZipFile:
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="손상된 ZIP 파일입니다"
            )
        except Exception as e:
            logger.error(f"ZIP 파일 읽기 실패: {str(e)}")
            raise HandledException(
                ResponseCode.DOCUMENT_UPLOAD_ERROR,
                msg=f"ZIP 파일 읽기 실패: {str(e)}",
                e=e
            )
    
    def _compare_files(
        self,
        required_files: List[str],
        zip_files: List[str]
    ) -> Dict:
        """필수 파일과 ZIP 파일 비교"""
        required_set = set(required_files)
        zip_set = set(zip_files)
        
        matched = required_set & zip_set
        missing = required_set - zip_set
        extra = zip_set - required_set
        
        return {
            'required_files': list(required_set),
            'zip_files': list(zip_set),
            'matched_files': list(matched),
            'missing_files': list(missing),
            'extra_files': list(extra),
            'validation_passed': len(missing) == 0
        }
    
    def _filter_unnecessary_files(
        self,
        ladder_zip: UploadFile,
        keep_files: List[str]
    ) -> bytes:
        """
        ZIP에서 필요한 파일만 남기고 새로운 ZIP 생성
        
        Args:
            ladder_zip: 원본 ZIP 파일
            keep_files: 유지할 파일 목록
            
        Returns:
            bytes: 필터링된 ZIP 파일 바이트
        """
        try:
            # 원본 ZIP 읽기
            original_content = ladder_zip.file.read()
            ladder_zip.file.seek(0)
            
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
            return filtered_buffer.read()
            
        except Exception as e:
            logger.error(f"ZIP 파일 필터링 실패: {str(e)}")
            raise HandledException(
                ResponseCode.DOCUMENT_UPLOAD_ERROR,
                msg=f"ZIP 파일 필터링 실패: {str(e)}",
                e=e
            )
    
    def _save_files(
        self,
        filtered_zip_bytes: bytes,
        template_xlsx: UploadFile,
        pgm_id: str,
        user_id: str
    ) -> Dict:
        """
        검증된 파일들을 지정된 경로에 저장
        
        Returns:
            {
                'ladder_files': Dict,
                'template_file': Dict
            }
        """
        try:
            # 1. 레더 파일 저장 (ZIP 압축 해제)
            # 기존 document_service.upload_zip_document() 재사용
            # UploadFile 객체로 변환
            ladder_upload_file = self._create_upload_file_from_bytes(
                filtered_zip_bytes,
                filename="ladder_files.zip"
            )
            
            ladder_result = self.document_service.upload_zip_document(
                file=ladder_upload_file,
                pgm_id=pgm_id,
                user_id=user_id,
                is_public=False,
                keep_zip_file=True  # 원본 ZIP도 저장
            )
            
            # 2. 템플릿 파일 저장
            # 기존 document_service.upload_document() 재사용
            template_result = self.document_service.upload_document(
                file=template_xlsx,
                user_id=user_id,
                is_public=False,
                document_type='pgm_template',
                metadata={'pgm_id': pgm_id}
            )
            
            return {
                'ladder_files': ladder_result,
                'template_file': template_result
            }
            
        except Exception as e:
            logger.error(f"파일 저장 실패: {str(e)}")
            raise
    
    def _create_upload_file_from_bytes(
        self,
        file_bytes: bytes,
        filename: str
    ) -> UploadFile:
        """바이트 데이터에서 UploadFile 객체 생성"""
        from fastapi import UploadFile as FastAPIUploadFile
        
        file_obj = io.BytesIO(file_bytes)
        
        # UploadFile 객체 생성
        upload_file = FastAPIUploadFile(
            file=file_obj,
            filename=filename
        )
        
        return upload_file
    
    def _cleanup_saved_files(self, save_result: Dict):
        """
        저장된 파일 삭제 (롤백 시)
        
        주의: 실제 구현 시 파일 시스템에서 파일을 삭제해야 함
        """
        try:
            # TODO: 실제 파일 삭제 로직 구현
            # 예: os.remove(file_path)
            logger.warning("파일 정리 로직은 아직 구현되지 않았습니다")
            pass
        except Exception as e:
            logger.error(f"파일 정리 실패: {str(e)}")
