# _*_ coding: utf-8 _*_
"""Document Service for handling file uploads and management."""
import logging
from typing import Dict, List
from datetime import datetime
from pathlib import Path

from ai_backend.config.simple_settings import settings
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
from fastapi import UploadFile
from sqlalchemy.orm import Session
from ai_backend.database.crud.program_crud import ProgramCrud

# 공통 모듈 사용
from shared_core import Document
from shared_core import DocumentService as BaseDocumentService
from shared_core import ProcessingJobService

from ai_backend.api.services.template_service import TemplateService

logger = logging.getLogger(__name__)


class DocumentService(BaseDocumentService):
    """문서 관리 서비스 (FastAPI 전용 확장)"""
    
    def __init__(self, db: Session, upload_base_path: str = None):
        # 환경변수에서 업로드 경로 가져오기 (k8s 환경 대응)
        upload_path = upload_base_path or settings.upload_base_path
        super().__init__(db, upload_path)
        self.program_crud = ProgramCrud(db)
        self.template_service = TemplateService(db)

    def upload_document(
        self,
        file: UploadFile,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        document_type: str = 'common',
        metadata: Dict = None  # 참고: 내부적으로 metadata_json으로 변환됨
    ) -> Dict:
        """문서 업로드 (FastAPI UploadFile 전용)"""
        try:
            # 문서 타입 검증
            if document_type not in Document.VALID_DOCUMENT_TYPES:
                raise HandledException(ResponseCode.DOCUMENT_INVALID_FILE_TYPE, 
                                     msg=f"유효하지 않은 문서 타입: {document_type}. 허용된 타입: {', '.join(Document.VALID_DOCUMENT_TYPES)}")
            
            # 파일 정보 추출
            original_filename = file.filename
            file_extension = self._get_file_extension(original_filename)
            
            # 파일 크기 확인 (환경변수에서 설정값 가져오기)
            file_content = file.file.read()
            file_size = len(file_content)
            max_size = settings.upload_max_size
            
            if file_size > max_size:
                max_size_mb = settings.get_upload_max_size_mb()
                raise HandledException(ResponseCode.DOCUMENT_FILE_TOO_LARGE, 
                                     msg=f"파일 크기가 너무 큽니다. (최대 {max_size_mb:.1f}MB)")
            
            # 허용된 파일 타입 확인 (환경변수에서 설정값 가져오기)
            allowed_extensions = settings.get_upload_allowed_types()
            
            if file_extension not in allowed_extensions:
                allowed_types_str = ', '.join(allowed_extensions)
                raise HandledException(ResponseCode.DOCUMENT_INVALID_FILE_TYPE, 
                                     msg=f"지원하지 않는 파일 형식입니다. 허용된 형식: {allowed_types_str}")
            
            # 공통 모듈의 create_document_from_file 사용
            result = self.create_document_from_file(
                file_content=file_content,
                filename=str(original_filename),
                user_id=user_id,
                is_public=is_public,
                permissions=permissions,
                document_type=document_type,
                metadata_json=metadata  # ⭐ metadata_json으로 전달 (**additional_metadata로 받음)
            )
            
            # ⭐ NEW: document_type이 "pgm_template"이면 Excel 파싱
            if document_type == "pgm_template":
                try:
                    # metadata에서 pgm_id 추출
                    metadata = result.get('metadata_json') or {}
                    pgm_id = metadata.get('pgm_id')
                    
                    if not pgm_id:
                        logger.warning(f"pgm_template 업로드 시 metadata에 pgm_id 필요: {result['document_id']}")
                    else:
                        # Excel 파싱 및 PGM_TEMPLATE 테이블 저장
                        # ⭐ file_path 대신 upload_path 사용
                        file_path = result.get('upload_path') or result.get('file_path')
                        if not file_path:
                            logger.error(f"file_path를 찾을 수 없음: result keys = {list(result.keys())}")
                            raise ValueError("file_path를 result에서 찾을 수 없습니다")
                        
                        parse_result = self.template_service.parse_and_save(
                            document_id=result['document_id'],
                            file_path=file_path,
                            pgm_id=pgm_id,
                            user_id=user_id
                        )
                        
                        # 파싱 결과를 metadata_json에 추가 저장
                        metadata['template_parse_result'] = parse_result
                        
                        # ⭐ update_document() 사용하여 metadata 업데이트
                        success = self.document_crud.update_document(
                            result['document_id'],
                            metadata_json=metadata  # ⭐ **kwargs로 전달됨
                        )
                        
                        if success:
                            logger.info(f"문서 metadata 업데이트 성공: {result['document_id']}")
                        else:
                            logger.warning(f"문서를 찾을 수 없음: {result['document_id']}")
                        
                        # 응답에 파싱 결과 포함
                        result['metadata_json'] = metadata
                        result['template_parse_result'] = parse_result
                        
                        logger.info(f"템플릿 파싱 완료: {parse_result}")
                        
                except HandledException:
                    # 템플릿 파싱 실패 시 예외 전파
                    raise
                except Exception as e:
                    logger.error(f"템플릿 파싱 실패: {e}")
                    # 파싱 실패해도 문서는 저장되었으므로 경고만 로그
                    # 원한다면 여기서 예외를 전파할 수도 있음
            
            return result
                
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            raise HandledException(ResponseCode.DOCUMENT_UPLOAD_ERROR, e=e)
    
    def get_document(self, document_id: str, user_id: str) -> Dict:
        """문서 정보 조회 (권한 체크 포함)"""
        try:
            result = super().get_document(document_id, user_id)
            if not result:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            return result
                
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        """사용자의 문서 목록 조회"""
        try:
            return super().get_user_documents(user_id)
                
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def search_documents(self, user_id: str, search_term: str) -> List[Dict]:
        """문서 검색"""
        try:
            return super().search_documents(user_id, search_term)
                
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def download_document(self, document_id: str, user_id: str) -> tuple[bytes, str, str]:
        """문서 다운로드"""
        try:
            return super().download_document(document_id, user_id)
                
        except FileNotFoundError:
            raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="파일이 존재하지 않습니다.")
        except PermissionError:
            raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.DOCUMENT_DOWNLOAD_ERROR, e=e)
    
    def delete_document(self, document_id: str, user_id: str) -> bool:
        """문서 삭제"""
        try:
            return super().delete_document(document_id, user_id)
                
        except PermissionError:
            raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.DOCUMENT_DELETE_ERROR, e=e)
    
    def update_document_processing_status(
        self,
        document_id: str,
        user_id: str,
        status: str,
        **processing_info
    ) -> bool:
        """문서 처리 상태 및 정보 업데이트"""
        try:
            return super().update_document_processing_status(
                document_id, status, user_id, **processing_info
            )
            
        except PermissionError:
            raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_document_processing_stats(self, user_id: str) -> Dict:
        """사용자 문서 처리 통계 조회"""
        try:
            return super().get_document_processing_stats(user_id)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    # 권한 관련 메서드들 (기존 인터페이스 유지)
    def check_document_permission(self, document_id: str, user_id: str, required_permission: str) -> bool:
        """문서 권한 체크"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return document.has_permission(required_permission)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def check_document_permissions(self, document_id: str, user_id: str, required_permissions: List[str], require_all: bool = False) -> bool:
        """문서 여러 권한 체크"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return document.has_permissions(required_permissions, require_all)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def update_document_permissions(self, document_id: str, user_id: str, permissions: List[str]) -> bool:
        """문서 권한 업데이트"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return self.document_crud.update_document_permissions(document_id, permissions)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def add_document_permission(self, document_id: str, user_id: str, permission: str) -> bool:
        """문서에 권한 추가"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return self.document_crud.add_document_permission(document_id, permission)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def remove_document_permission(self, document_id: str, user_id: str, permission: str) -> bool:
        """문서에서 권한 제거"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return self.document_crud.remove_document_permission(document_id, permission)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_documents_with_permission(self, user_id: str, required_permission: str) -> List[Dict]:
        """특정 권한을 가진 문서 목록 조회"""
        try:
            documents = self.document_crud.get_documents_with_permission(user_id, required_permission)
            return [self._document_to_dict(doc) for doc in documents]
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_documents_by_type(self, user_id: str, document_type: str) -> List[Dict]:
        """특정 문서 타입의 사용자 문서 목록 조회"""
        try:
            # 유효한 타입 검증
            if document_type not in Document.VALID_DOCUMENT_TYPES:
                raise HandledException(ResponseCode.DOCUMENT_INVALID_FILE_TYPE, 
                                     msg=f"유효하지 않은 문서 타입: {document_type}. 허용된 타입: {', '.join(Document.VALID_DOCUMENT_TYPES)}")
            
            documents = self.document_crud.get_documents_by_type(user_id, document_type)
            return [self._document_to_dict(doc) for doc in documents]
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def update_document_type(self, document_id: str, user_id: str, document_type: str) -> bool:
        """문서 타입 업데이트"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return self.document_crud.update_document_type(document_id, document_type)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_document_type_stats(self, user_id: str) -> Dict[str, int]:
        """사용자의 문서 타입별 통계 조회"""
        try:
            return self.document_crud.get_document_type_stats(user_id)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_document_processing_jobs(self, document_id: str) -> List[Dict]:
        """문서의 모든 처리 작업 조회"""
        try:
            job_service = ProcessingJobService(self.db)
            return job_service.get_document_jobs(document_id)
            
        except Exception as e:
            logger.error(f"문서 처리 작업 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_processing_job_progress(self, job_id: str) -> Dict:
        """처리 작업의 실시간 진행률 조회"""
        try:
            job_service = ProcessingJobService(self.db)
            from shared_core.crud import ProcessingJobCRUD
            job_crud = ProcessingJobCRUD(self.db)
            
            job = job_crud.get_job(job_id)
            if not job:
                return None
                
            return job_service._job_to_dict(job)
            
        except Exception as e:
            logger.error(f"처리 작업 진행률 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    # ========================================
    # ZIP 파일 관련 메서드
    # ========================================
    
    # Step 1: /upload/zip_document에서 호출
    def upload_zip_document(
        self,
        file: UploadFile,
        pgm_id: str,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        keep_zip_file: bool = True
    ) -> Dict:
        """ZIP 파일 업로드 및 압축 해제 후 각 파일을 DOCUMENTS 테이블에 저장
        
        Args:
            file: ZIP 파일
            pgm_id: 프로그램 ID (필수)
            user_id: 사용자 ID
            is_public: 공개 여부
            permissions: 권한 리스트
            keep_zip_file: True=원본 ZIP 저장, False=저장 안함
        """
        try:
            # 1. 확장자 체크
            if not file.filename.endswith('.zip'):
                raise HandledException(
                    ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                    msg="zip 파일만 업로드 가능합니다"
                )
            
            # 2. PGM_ID 유효성 검증 (soft validation)
            program = self.program_crud.get_program_by_id(pgm_id)
            if not program:
                logger.warning(f"[ZIP Upload] 프로그램 미등록 상태로 업로드 진행: pgm_id={pgm_id}, user_id={user_id}")
                # 검증 실패해도 계속 진행
            
            # 3. ZIP 파일 메모리에서 읽기
            file_content = file.file.read()
            file.file.seek(0)  # 포인터 초기화 (keep_zip_file용)
            
            # 4. 압축 해제 및 파일 저장 (메모리에서 직접 처리)
            result = self._extract_and_save_each_files(
                zip_bytes=file_content,
                pgm_id=pgm_id,
                user_id=user_id,
                is_public=is_public,
                permissions=permissions,
                keep_zip_file=keep_zip_file
            )
            
            # 5. 원본 ZIP 파일 저장 (선택사항)
            zip_file_info = None
            if keep_zip_file:
                file.file.seek(0)  # 포인터 재초기화
                zip_file_info = self._save_original_zip(
                    file=file,
                    pgm_id=pgm_id,
                    user_id=user_id,
                    is_public=is_public,
                    permissions=permissions,
                    extracted_file_count=result['total_files']
                )
            
            # 6. 결과 반환
            response = {
                'zip_file': zip_file_info,
                'extracted_files': result['extracted_files'],
                'summary': {
                    'pgm_id': pgm_id,
                    'total_files': result['total_files'],
                    'success_count': result['success_count'],
                    'failed_count': result['failed_count'],
                    'failed_files': result['failed_files'],
                    'zip_saved': keep_zip_file,
                    'extraction_path': result['extraction_path']
                }
            }
            
            logger.info(f"ZIP 업로드 완료: {file.filename}, PGM_ID={pgm_id}, "
                      f"성공={result['success_count']}, 실패={result['failed_count']}")
            
            return response
            
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"ZIP 파일 업로드 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_UPLOAD_ERROR, e=e)
        
    # Step 2: Zip 파일 압축 해제 및 각 파일 저장
    def _extract_and_save_each_files(
        self,
        zip_bytes: bytes,
        pgm_id: str,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        keep_zip_file: bool = True
    ) -> Dict:
        """ZIP 파일 압축 해제 및 각 파일을 DOCUMENTS 테이블에 저장 (메모리 처리)"""
        import io
        import zipfile
        from pathlib import Path
        
        try:
            # 1. 압축 해제 대상 디렉토리 설정
            extraction_base = Path(self.upload_base_path) / pgm_id
            extraction_base.mkdir(parents=True, exist_ok=True)
            
            extracted_files = []
            failed_files = []
            success_count = 0
            failed_count = 0
            
            # 2. 메모리에서 ZIP 파일 열기
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
                file_list = zip_ref.infolist()
                
                for info in file_list:
                    try:
                        # 디렉토리는 스킵
                        if info.is_dir():
                            continue
                        
                        # 파일 경로 및 이름 추출
                        file_relative_path = info.filename
                        file_name = Path(file_relative_path).name
                        file_key = f"{pgm_id}/{file_relative_path}"
                        
                        # 압축 해제된 파일 경로
                        extracted_file_path = extraction_base / file_relative_path
                        extracted_file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 파일 압축 해제
                        with zip_ref.open(info.filename) as source:
                            file_content = source.read()
                            with open(extracted_file_path, 'wb') as target:
                                target.write(file_content)
                        
                        # 3. DOCUMENTS 테이블에 저장
                        # save_extracted_file_to_db 호출 (새로운 메서드)
                        doc_result = self.save_extracted_file_to_db(
                            file_content=file_content,
                            filename=file_name,
                            pgm_id=pgm_id,
                            user_id=user_id,
                            relative_path=file_relative_path,
                            file_key=file_key,
                            actual_file_path=str(extracted_file_path),  # ⭐ 실제 디스크 경로
                            original_zip_document_id=None,  # 추후 추가 가능
                            is_public=is_public,
                            permissions=permissions,
                            document_type="pgm_ladder"                            
                        )
                        
                        extracted_files.append({
                            'document_id': doc_result['document_id'],
                            'document_name': doc_result['document_name'],
                            'relative_path': doc_result['metadata_json'].get('original_zip_path'),
                            'file_size': doc_result['file_size'],
                            'file_extension': doc_result['file_extension']
                        })
                        
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"파일 저장 실패: {info.filename}, 오류: {str(e)}")
                        failed_files.append({
                            'file_name': info.filename,
                            'error': str(e)
                        })
                        failed_count += 1
            
            return {
                'extracted_files': extracted_files,
                'total_files': len(file_list) - sum(1 for f in file_list if f.is_dir()),
                'success_count': success_count,
                'failed_count': failed_count,
                'failed_files': failed_files,
                'extraction_path': str(extraction_base)
            }
            
        except zipfile.BadZipFile:
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="손상된 ZIP 파일입니다"
            )
        except Exception as e:
            logger.error(f"ZIP 파일 압축 해제 실패: {str(e)}")
            raise
    
    # Step 3: 각 추출 파일을 DOCUMENTS 테이블에 저장
    def save_extracted_file_to_db(
        self,
        file_content: bytes,
        filename: str,
        pgm_id: str,
        user_id: str,
        relative_path: str,
        file_key: str,
        actual_file_path: str,  # ⭐ 실제 디스크 경로
        original_zip_document_id: str = None,
        is_public: bool = False,
        permissions: List[str] = None,
        document_type: str = "pgm_ladder"
    ) -> Dict:
        """ZIP에서 추출한 파일을 DOCUMENTS 테이블에 저장
        
        Args:
            file_content: 파일 바이트 데이터
            filename: 파일명
            pgm_id: 프로그램 ID
            user_id: 사용자 ID
            relative_path: ZIP 내부 경로 (예: "folder/file.txt")
            actual_file_path: 실제 디스크 저장 경로 (예: "/uploads/PGM001/folder/file.txt")
            original_zip_document_id: 원본 ZIP의 document_id (선택)
            is_public: 공개 여부
            permissions: 권한 목록
            
        Returns:
            {
                'document_id': str,
                'file_name': str,
                'file_path': str,
                ...
            }
        """
        try:
            # 1. ZIP 전용 metadata 구성
            metadata = {
                'extracted_from_zip': True,
                'original_zip_path': relative_path,  # ZIP 내부 경로
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            # 원본 ZIP document_id가 있으면 추가
            if original_zip_document_id:
                metadata['original_zip_document_id'] = original_zip_document_id
            
            # 파일 정보 추출
            file_extension = self._get_file_extension(filename)
            file_type = self._get_mime_type(filename)
            file_size = len(file_content)
            file_hash = self._calculate_file_hash(file_content)
            
            # document_id 생성
            document_id = (
                    f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}"
                )

            # 4. document_crud.create_document() 직접 호출
            # Document 레코드 생성
            document = self.document_crud.create_document(
                document_id=document_id,
                document_name=filename,
                user_id=user_id,
                original_filename=filename,
                file_key=file_key,  # 파일 키
                upload_path=actual_file_path,  # ⭐ 실제 디스크 경로
                file_size=file_size,
                file_type=file_type,
                file_extension=file_extension,
                document_type='PGM_LADDER_CSV',
                is_public=is_public,
                permissions=permissions,
                metadata_json=metadata,
                pgm_id=pgm_id
            )
            
            # 5. 결과 반환 (dict 형태로 변환)
            result = {
                'document_id': document.document_id,
                'document_name': document.document_name,
                'upload_path': document.upload_path,
                'file_size': document.file_size,
                'file_extension': document.file_extension,
                'document_type': document.document_type,
                'user_id': document.user_id,
                'is_public': document.is_public,
                'permissions': document.permissions,
                'metadata_json': document.metadata_json,
                'pgm_id': pgm_id,
                'create_dt': document.create_dt.isoformat() if hasattr(document, 'create_dt') else None
            }
            
            # 6. 로깅
            logger.info(f"ZIP 추출 파일 저장 완료: {filename} -> {document_id} (pgm_id={pgm_id}, path={actual_file_path})")
            
            return result
            
        except Exception as e:
            logger.error(f"ZIP 추출 파일 저장 실패: {filename}, 오류: {str(e)}")
            raise
    
    # Strp 4
    def _save_original_zip(
        self,
        file: UploadFile,
        pgm_id: str,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        extracted_file_count: int = 0
    ) -> Dict:
        """원본 ZIP 파일을 /uploads/{pgm_id}/zip/ 폴더에 저장"""
        
        try:
            # 1. zipfiles 폴더 생성 (사용자 구분 없이 중앙 관리)
            zipfiles_dir = Path(self.upload_base_path) / pgm_id / 'zip'
            zipfiles_dir.mkdir(parents=True, exist_ok=True)
            
            # 2. 파일 저장 경로 생성
            if not file.filename:
                raise ValueError("파일명이 없습니다")
            filename = file.filename
            actual_file_path = str(zipfiles_dir / filename)
            
            # 3. 파일 저장
            # file.file.seek(0)
            file_content = file.file.read()
            # file.file.seek(0)
            with open(actual_file_path, 'wb') as f:
                f.write(file_content)
            
            # 파일 정보 추출
            file_extension = self._get_file_extension(filename)
            file_type = self._get_mime_type(filename)
            file_size = len(file_content)
            file_hash = self._calculate_file_hash(file_content)
            file_key = f"{pgm_id}/zipfiles/{filename}"

            # document_id 생성
            document_id = (
                    f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}"
                )
            
            # metadata 구성
            metadata = {
                'is_original_zip': True,
                'extracted_file_count': extracted_file_count,
                'stored_in_zipfiles': True,
                'upload_timestamp': datetime.now().isoformat()
            }
            
            # Document 레코드 생성
            document = self.document_crud.create_document(
                document_id=document_id,
                document_name=filename,
                user_id=user_id,
                original_filename=filename,
                file_key=file_key,  # 파일 키
                upload_path=actual_file_path,
                file_size=file_size,
                file_type=file_type,
                file_extension=file_extension,
                document_type='PGM_LADDER_ZIP',
                is_public=is_public,
                permissions=permissions,
                metadata_json=metadata,
                pgm_id=pgm_id
            )
            
            # 5. 결과 반환 (dict 형태로 변환)
            result = {
                'document_id': document.document_id,
                'document_name': document.document_name,
                'upload_path': document.upload_path,
                'file_size': document.file_size,
                'file_extension': document.file_extension,
                'document_type': document.document_type,
                'user_id': document.user_id,
                'is_public': document.is_public,
                'permissions': document.permissions,
                'metadata_json': document.metadata_json,
                'pgm_id': pgm_id,
                'create_dt': document.create_dt.isoformat() if hasattr(document, 'create_dt') else None
            }
            
            logger.info(f"원본 ZIP 파일 저장 완료: {filename}, document_id={document_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"원본 ZIP 파일 저장 실패: {str(e)}")
            raise