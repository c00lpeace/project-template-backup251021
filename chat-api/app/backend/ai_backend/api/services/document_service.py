# _*_ coding: utf-8 _*_
"""Document Service for handling file uploads and management."""
import logging
from typing import Dict, List

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

logger = logging.getLogger(__name__)


class DocumentService(BaseDocumentService):
    """문서 관리 서비스 (FastAPI 전용 확장)"""
    
    def __init__(self, db: Session, upload_base_path: str = None):
        # 환경변수에서 업로드 경로 가져오기 (k8s 환경 대응)
        upload_path = upload_base_path or settings.upload_base_path
        super().__init__(db, upload_path)
        self.program_crud = ProgramCrud(db)

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
                filename=original_filename,
                user_id=user_id,
                is_public=is_public,
                permissions=permissions,
                document_type=document_type,
                metadata_json=metadata  # ⭐ metadata_json으로 전달 (**additional_metadata로 받음)
            )
            
            # ⭐ NEW: document_type이 "pgm_template"이면 Excel 파싱
            if document_type == "pgm_template":
                try:
                    from ai_backend.api.services.template_service import TemplateService
                    template_service = TemplateService(self.db)
                    
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
                        
                        parse_result = template_service.parse_and_save(
                            document_id=result['document_id'],
                            file_path=file_path,
                            pgm_id=pgm_id,
                            user_id=user_id
                        )
                        
                        # 파싱 결과를 metadata_json에 추가 저장
                        metadata['template_parse_result'] = parse_result
                        
                        # ⭐ update_document() 사용하여 metadata 업데이트
                        from shared_core.crud import DocumentCRUD
                        doc_crud = DocumentCRUD(self.db)
                        success = doc_crud.update_document(
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
        import zipfile
        from datetime import datetime
        from pathlib import Path
        
        import os
        import tempfile
        
        try:
            # 1. 확장자 체크
            if not file.filename.endswith('.zip'):
                raise HandledException(
                    ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                    msg="zip 파일만 업로드 가능합니다"
                )
            
            # 2. PGM_ID 유효성 검증
            # from ai_backend.database.crud.program_crud import ProgramCrud
            # program = ProgramCrud.get_program_by_id(self.db, pgm_id)
            program = self.program_crud.get_program_by_id(pgm_id)
            if not program:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"존재하지 않는 프로그램 ID입니다: {pgm_id}"
                )
            
            # 3. ZIP 파일 읽기
            file_content = file.file.read()
            file.file.seek(0)  # 포인터 초기화
            
            # 4. 임시로 ZIP 파일 저장 (압축 해제용)
            temp_zip_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                    temp_file.write(file_content)
                    temp_zip_path = temp_file.name
                
                # 5. 압축 해제 및 파일 저장
                result = self._extract_and_save_to_db(
                    zip_path=temp_zip_path,
                    pgm_id=pgm_id,
                    user_id=user_id,
                    is_public=is_public,
                    permissions=permissions
                )
                
                # 6. 원본 ZIP 파일 저장 (선택사항)
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
                
                # 7. 결과 반환
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
                
            finally:
                # 임시 ZIP 파일 삭제
                if temp_zip_path and os.path.exists(temp_zip_path):
                    try:
                        os.unlink(temp_zip_path)
                    except Exception as e:
                        logger.warning(f"임시 ZIP 파일 삭제 실패: {e}")
            
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"ZIP 파일 업로드 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_UPLOAD_ERROR, e=e)
    
    def _extract_and_store_zip(self, zip_path: str, document_id: str, user_id: str) -> Dict:
        """압축 해제 및 저장 (Phase 1 - 기본 기능)
        
        Args:
            zip_path: 원본 ZIP 파일 경로
            document_id: 문서 ID
            user_id: 사용자 ID
            
        Returns:
            {
                'zip_contents': {...},  # 분석 결과
                'extracted_path': 'path/to/extracted',
                'extracted_count': 500,
                'failed_count': 0
            }
        """
        import os
        import zipfile
        from collections import defaultdict
        from datetime import datetime
        from pathlib import Path
        
        try:
            # 1. 해제 대상 디렉토리 생성
            zip_path_obj = Path(zip_path)
            extracted_base = zip_path_obj.parent / f"{zip_path_obj.stem}_extracted"
            extracted_base.mkdir(parents=True, exist_ok=True)
            
            # 2. ZIP 파일 분석 및 해제
            files = []
            file_type_stats = defaultdict(int)
            extracted_count = 0
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for info in zip_ref.infolist():
                    try:
                        path_obj = Path(info.filename)
                        extension = path_obj.suffix.lower() if not info.is_dir() else ''
                        
                        # 파일 정보 저장
                        extracted_file_path = extracted_base / info.filename
                        
                        file_info = {
                            'path': info.filename,
                            'name': path_obj.name,
                            'extension': extension,
                            'size': info.compress_size,
                            'uncompressed_size': info.file_size,
                            'is_directory': info.is_dir(),
                            'modified_date': datetime(*info.date_time).isoformat() if info.date_time else None,
                            'extracted_path': str(extracted_file_path)  # 해제된 파일 경로
                        }
                        
                        files.append(file_info)
                        
                        # 파일 타입 통계
                        if not info.is_dir():
                            if extension:
                                file_type_stats[extension] += 1
                            else:
                                file_type_stats['[no extension]'] += 1
                        
                        # 실제 파일 해제
                        if not info.is_dir():
                            # 디렉토리 생성
                            extracted_file_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # 파일 해제
                            with zip_ref.open(info.filename) as source:
                                with open(extracted_file_path, 'wb') as target:
                                    target.write(source.read())
                            
                            extracted_count += 1
                        else:
                            # 빈 디렉토리 생성
                            extracted_file_path.mkdir(parents=True, exist_ok=True)
                    
                    except Exception as e:
                        logger.warning(f"파일 해제 실패: {info.filename}, 오류: {str(e)}")
                        continue
            
            # 3. 원본 ZIP 파일 보관 (백업 및 원본 다운로드용)
            # 압축 해제 모드에서도 원본 ZIP을 보관하여:
            # - 사용자가 원본 ZIP을 다운로드할 수 있도록 함 (/documents/{id}/download)
            # - 백업 및 복구 시 사용
            logger.info(f"원본 ZIP 파일 보관: {zip_path}")
            
            # 4. 결과 반환
            return {
                'zip_contents': {
                    'files': files,
                    'file_type_stats': dict(file_type_stats)
                },
                'extracted_path': str(extracted_base),
                'extracted_count': extracted_count,
                'failed_count': len(files) - extracted_count
            }
            
        except zipfile.BadZipFile:
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="손상된 zip 파일입니다"
            )
        except Exception as e:
            logger.error(f"zip 파일 해제 실패: {str(e)}")
            raise
    
    def _analyze_zip_file(self, file_path: str) -> Dict:
        """zip 파일 분석하여 내부 파일 목록 추출"""
        import zipfile
        from collections import defaultdict
        from datetime import datetime
        from pathlib import Path
        
        files = []
        file_type_stats = defaultdict(int)
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for info in zip_ref.infolist():
                    path_obj = Path(info.filename)
                    extension = path_obj.suffix.lower() if not info.is_dir() else ''
                    
                    file_info = {
                        'path': info.filename,
                        'name': path_obj.name,
                        'extension': extension,
                        'size': info.compress_size,
                        'uncompressed_size': info.file_size,
                        'is_directory': info.is_dir(),
                        'modified_date': datetime(*info.date_time).isoformat() if info.date_time else None
                    }
                    
                    files.append(file_info)
                    
                    # 파일 타입 통계
                    if not info.is_dir():
                        if extension:
                            file_type_stats[extension] += 1
                        else:
                            file_type_stats['[no extension]'] += 1
            
            return {
                'files': files,
                'file_type_stats': dict(file_type_stats)
            }
            
        except zipfile.BadZipFile:
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="손상된 zip 파일입니다"
            )
        except Exception as e:
            logger.error(f"zip 파일 분석 실패: {str(e)}")
            raise
    
    def search_in_zip(
        self,
        document_id: str,
        user_id: str,
        search_term: str = None,
        extension: str = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict:
        """zip 파일 내부 파일 검색"""
        try:
            # 1. 문서 조회 및 권한 체크
            doc_info = self.get_document(document_id, user_id)
            
            if doc_info.get('document_type') != 'zip':
                raise HandledException(
                    ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                    msg="zip 파일이 아닙니다"
                )
            
            # 2. metadata_json에서 파일 목록 가져오기
            from shared_core.crud import DocumentCRUD
            doc_crud = DocumentCRUD(self.db)
            document = doc_crud.get_document(document_id)
            
            if not document or not document.metadata_json:
                return {
                    'items': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size
                }
            
            files = document.metadata_json.get('files', [])
            
            # 3. 필터링
            filtered_files = files
            
            # 검색어 필터링
            if search_term:
                search_lower = search_term.lower()
                filtered_files = [
                    f for f in filtered_files
                    if search_lower in f['path'].lower() or search_lower in f['name'].lower()
                ]
            
            # 확장자 필터링
            if extension:
                ext_lower = extension.lower()
                if not ext_lower.startswith('.'):
                    ext_lower = '.' + ext_lower
                filtered_files = [
                    f for f in filtered_files
                    if f.get('extension', '').lower() == ext_lower
                ]
            
            # 4. 페이지네이션
            total = len(filtered_files)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_files = filtered_files[start:end]
            
            return {
                'items': paginated_files,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
            
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"zip 내부 파일 검색 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_zip_file_content(
        self,
        document_id: str,
        user_id: str,
        file_path: str
    ) -> tuple[bytes, str]:
        """zip 내부 특정 파일 추출"""
        import zipfile
        from pathlib import Path
        
        try:
            # 1. 문서 조회 및 권한 체크
            doc_info = self.get_document(document_id, user_id)
            
            if doc_info.get('document_type') != 'zip':
                raise HandledException(
                    ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                    msg="zip 파일이 아닙니다"
                )
            
            # 2. storage_type 확인
            from shared_core.crud import DocumentCRUD
            doc_crud = DocumentCRUD(self.db)
            document = doc_crud.get_document(document_id)
            
            storage_type = 'compressed'
            if document.metadata_json:
                storage_type = document.metadata_json.get('storage_type', 'compressed')
            
            # 3. storage_type에 따라 분기
            if storage_type == 'extracted':
                # 압축 해제된 파일에서 직접 읽기
                extracted_path = document.metadata_json.get('extracted_path')
                if not extracted_path:
                    raise HandledException(
                        ResponseCode.DOCUMENT_NOT_FOUND,
                        msg="압축 해제 경로를 찾을 수 없습니다"
                    )
                
                extracted_file_path = Path(extracted_path) / file_path
                if not extracted_file_path.exists():
                    raise HandledException(
                        ResponseCode.DOCUMENT_NOT_FOUND,
                        msg=f"파일이 존재하지 않습니다: {file_path}"
                    )
                
                with open(extracted_file_path, 'rb') as f:
                    file_content = f.read()
                filename = Path(file_path).name
                return file_content, filename
            else:
                # 압축 파일에서 추출 (기존 로직)
                zip_file_path = doc_info['file_path']
                
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    try:
                        file_content = zip_ref.read(file_path)
                        filename = Path(file_path).name
                        return file_content, filename
                    except KeyError:
                        raise HandledException(
                            ResponseCode.DOCUMENT_NOT_FOUND,
                            msg=f"zip 내부에 '{file_path}' 파일이 존재하지 않습니다"
                        )
            
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"zip 파일 추출 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_DOWNLOAD_ERROR, e=e)
    
    # ========================================
    # ⭐ 새로운 ZIP 업로드 메서드들
    # ========================================
    
    def _extract_and_save_to_db(
        self,
        zip_path: str,
        pgm_id: str,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None
    ) -> Dict:
        """ZIP 파일 압축 해제 및 각 파일을 DOCUMENTS 테이블에 저장"""
        import os
        import zipfile
        from pathlib import Path
        from collections import defaultdict
        
        try:
            # 1. 압축 해제 대상 디렉토리 설정
            extraction_base = Path(self.upload_base_path) / user_id / pgm_id
            extraction_base.mkdir(parents=True, exist_ok=True)
            
            extracted_files = []
            failed_files = []
            success_count = 0
            failed_count = 0
            
            # 2. ZIP 파일 열기
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                
                for info in file_list:
                    try:
                        # 디렉토리는 스킵
                        if info.is_dir():
                            continue
                        
                        # 파일 경로 및 이름 추출
                        file_relative_path = info.filename
                        file_name = Path(file_relative_path).name
                        
                        # 압축 해제된 파일 경로
                        extracted_file_path = extraction_base / file_relative_path
                        extracted_file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 파일 압축 해제
                        with zip_ref.open(info.filename) as source:
                            file_content = source.read()
                            with open(extracted_file_path, 'wb') as target:
                                target.write(file_content)
                        
                        # 3. DOCUMENTS 테이블에 저장
                        file_extension = Path(file_name).suffix.lower() or '.unknown'
                        file_size = len(file_content)
                        
                        # create_document_from_file 호출
                        doc_result = self.create_document_from_file(
                            file_content=file_content,
                            filename=file_name,
                            user_id=user_id,
                            is_public=is_public,
                            permissions=permissions,
                            document_type='common',
                            metadata_json={
                                'original_zip_path': file_relative_path,
                                'extracted_from_zip': True
                            },
                            pgm_id=pgm_id
                        )
                        
                        extracted_files.append({
                            'document_id': doc_result['document_id'],
                            'file_name': file_name,
                            'relative_path': file_relative_path,
                            'file_size': file_size,
                            'file_extension': file_extension
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
    
    def _save_original_zip(
        self,
        file: UploadFile,
        pgm_id: str,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        extracted_file_count: int = 0
    ) -> Dict:
        """원본 ZIP 파일을 zipfiles 폴더에 저장"""
        from pathlib import Path
        import os
        from datetime import datetime
        
        try:
            # 1. zipfiles 폴더 생성
            zipfiles_dir = Path(self.upload_base_path) / user_id / 'zipfiles'
            zipfiles_dir.mkdir(parents=True, exist_ok=True)
            
            # 2. 파일 저장 경로 생성
            file_name = file.filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{file_name}"
            zip_file_path = zipfiles_dir / safe_filename
            
            # 3. 파일 저장
            file_content = file.file.read()
            with open(zip_file_path, 'wb') as f:
                f.write(file_content)
            
            # 4. DOCUMENTS 테이블에 저장
            doc_result = self.create_document_from_file(
                file_content=file_content,
                filename=file_name,
                user_id=user_id,
                is_public=is_public,
                permissions=permissions,
                document_type='zip',
                metadata_json={
                    'is_original_zip': True,
                    'extracted_file_count': extracted_file_count,
                    'stored_in_zipfiles': True
                },
                pgm_id=pgm_id
            )
            
            logger.info(f"원본 ZIP 파일 저장 완료: {file_name}, document_id={doc_result['document_id']}")
            
            return doc_result
            
        except Exception as e:
            logger.error(f"원본 ZIP 파일 저장 실패: {str(e)}")
            raise