# _*_ coding: utf-8 _*_
"""Document Service for handling file uploads and management."""
import logging
from typing import Dict, List, Optional
from datetime import datetime

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
from ai_backend.api.services.program_document_processor import (
    ProgramDocumentProcessorFactory
)

logger = logging.getLogger(__name__)


class DocumentService(BaseDocumentService):
    """
    문서 관리 서비스 (FastAPI 전용 확장)
    
    Phase 2 리팩토링 (2025-11-06):
    - DB 저장 전담으로 단순화
    - 파일 저장 로직 제거 (FileStorageService로 이동)
    - 검증 로직 제거 (FileValidationService로 이동)
    - 환경변수 기반 설정
    - ProgramDocumentProcessorFactory 통합
    """
    
    def __init__(
        self, 
        db: Session, 
        upload_base_path: str = None,
        processor_factory: Optional[ProgramDocumentProcessorFactory] = None
    ):
        """
        Args:
            db: 데이터베이스 세션
            upload_base_path: 업로드 기본 경로
            processor_factory: 문서 타입별 프로세서 팩토리 (선택)
        """
        # 환경변수에서 업로드 경로 가져오기 (k8s 환경 대응)
        upload_path = upload_base_path or settings.upload_base_path
        super().__init__(db, upload_path)
        
        self.program_crud = ProgramCrud(db)
        self.template_service = TemplateService(db)
        
        # 프로세서 팩토리 주입 (없으면 생성)
        if processor_factory is None:
            self.processor_factory = ProgramDocumentProcessorFactory(
                db=db,
                template_service=self.template_service
            )
        else:
            self.processor_factory = processor_factory

    # ========================================
    # 기존 메서드 (호환성 유지)
    # ========================================
    
    def upload_document(
        self,
        file: UploadFile,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        document_type: str = 'common',
        metadata: Dict = None  # 참고: 내부적으로 metadata_json으로 변환됨
    ) -> Dict:
        """
        문서 업로드 (FastAPI UploadFile 전용)
        
        ⚠️ 레거시 메서드: 기존 호환성 유지
        새 코드는 create_ladder_csv_document() 또는 create_template_document() 사용 권장
        """
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
    
    # ========================================
    # 권한 관련 메서드들 (기존 인터페이스 유지)
    # ========================================
    
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
    # Phase 2 신규 메서드 (명확한 이름)
    # ========================================
    
    def create_ladder_csv_document(
        self,
        document_name: str,
        original_filename: str,
        file_key: str,
        upload_path: str,
        file_size: int,
        pgm_id: str,
        user_id: str,
        is_public: bool = False,
        permissions: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Document:
        """
        레더 CSV 문서 레코드 생성
        
        Phase 2 신규 메서드 (2025-11-06)
        - DB INSERT만 수행 (파일 저장은 FileStorageService가 담당)
        - document_type은 환경변수에서 가져옴
        
        Args:
            document_name: 문서명
            original_filename: 원본 파일명
            file_key: 파일 키 (예: "PGM_1/ladder_files/0000_11.csv")
            upload_path: 실제 저장 경로
            file_size: 파일 크기 (bytes)
            pgm_id: 프로그램 ID
            user_id: 사용자 ID
            is_public: 공개 여부
            permissions: 권한 목록
            metadata: 추가 메타데이터
            
        Returns:
            Document: 생성된 문서 레코드
        """
        try:
            # 환경변수에서 document_type 가져오기
            document_type = settings.pgm_ladder_csv_doctype
            
            # 파일 정보 추출
            file_extension = self._get_file_extension(document_name)
            file_type = self._get_mime_type(document_name)
            
            # document_id 생성
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_key.split('/')[-1][:8]}"
            
            # metadata 구성
            metadata_json = metadata or {}
            metadata_json.update({
                'created_by_service': 'DocumentService',
                'creation_method': 'create_ladder_csv_document',
                'upload_timestamp': datetime.now().isoformat()
            })
            
            # Document 레코드 생성
            document = self.document_crud.create_document(
                document_id=document_id,
                document_name=document_name,
                user_id=user_id,
                original_filename=original_filename,
                file_key=file_key,
                upload_path=upload_path,
                file_size=file_size,
                file_type=file_type,
                file_extension=file_extension,
                document_type=document_type,  # 환경변수
                is_public=is_public,
                permissions=permissions,
                metadata_json=metadata_json,
                pgm_id=pgm_id
            )
            
            logger.info(
                f"✅ 레더 CSV 문서 레코드 생성 완료: {document.document_id} "
                f"(pgm_id={pgm_id}, path={upload_path})"
            )
            
            return document
            
        except Exception as e:
            logger.error(f"❌ 레더 CSV 문서 레코드 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_UPLOAD_ERROR, e=e)
    
    def create_template_document(
        self,
        document_name: str,
        original_filename: str,
        file_key: str,
        upload_path: str,
        file_size: int,
        pgm_id: str,
        user_id: str,
        is_public: bool = False,
        permissions: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Document:
        """
        템플릿 문서 레코드 생성 및 자동 프로세서 호출
        
        Phase 2 신규 메서드 (2025-11-06)
        - DB INSERT 수행 (파일 저장은 FileStorageService가 담당)
        - document_type은 환경변수에서 가져옴
        - 자동으로 ProgramTemplateProcessor 호출 (템플릿 파싱)
        
        Args:
            document_name: 문서명
            original_filename: 원본 파일명
            file_key: 파일 키 (예: "PGM_1/template/template.xlsx")
            upload_path: 실제 저장 경로
            file_size: 파일 크기 (bytes)
            pgm_id: 프로그램 ID
            user_id: 사용자 ID
            is_public: 공개 여부
            permissions: 권한 목록
            metadata: 추가 메타데이터
            
        Returns:
            Document: 생성된 문서 레코드 (템플릿 파싱 완료)
        """
        try:
            # 환경변수에서 document_type 가져오기
            document_type = settings.pgm_template_doctype
            
            # 파일 정보 추출
            file_extension = self._get_file_extension(document_name)
            file_type = self._get_mime_type(document_name)
            
            # document_id 생성
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_key.split('/')[-1][:8]}"
            
            # metadata 구성
            metadata_json = metadata or {}
            metadata_json.update({
                'created_by_service': 'DocumentService',
                'creation_method': 'create_template_document',
                'upload_timestamp': datetime.now().isoformat()
            })
            
            # Document 레코드 생성
            document = self.document_crud.create_document(
                document_id=document_id,
                document_name=document_name,
                user_id=user_id,
                original_filename=original_filename,
                file_key=file_key,
                upload_path=upload_path,
                file_size=file_size,
                file_type=file_type,
                file_extension=file_extension,
                document_type=document_type,  # 환경변수
                is_public=is_public,
                permissions=permissions,
                metadata_json=metadata_json,
                pgm_id=pgm_id
            )
            
            logger.info(
                f"✅ 템플릿 문서 레코드 생성 완료: {document.document_id} "
                f"(pgm_id={pgm_id}, path={upload_path})"
            )
            
            # 자동으로 템플릿 프로세서 호출 (파싱 + PGM_TEMPLATE 저장)
            processor = self.processor_factory.get_processor(document_type)
            processor.process(document)
            
            logger.info(
                f"✅ 템플릿 프로세서 호출 완료: {document.document_id}"
            )
            
            return document
            
        except Exception as e:
            logger.error(f"❌ 템플릿 문서 레코드 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_UPLOAD_ERROR, e=e)
    
    def bulk_create_ladder_csv_documents(
        self,
        documents_data: List[Dict]
    ) -> List[Document]:
        """
        레더 CSV 문서 일괄 생성 (성능 최적화)
        
        Phase 2 신규 메서드 (2025-11-06)
        - 여러 레더 CSV 파일을 한 번에 DB INSERT
        - 트랜잭션 커밋 횟수 최소화
        
        Args:
            documents_data: 문서 데이터 리스트
                [
                    {
                        'document_name': str,
                        'original_filename': str,
                        'file_key': str,
                        'upload_path': str,
                        'file_size': int,
                        'pgm_id': str,
                        'user_id': str,
                        'is_public': bool (optional),
                        'permissions': List[str] (optional),
                        'metadata': Dict (optional)
                    },
                    ...
                ]
                
        Returns:
            List[Document]: 생성된 문서 레코드 리스트
        """
        try:
            # 환경변수에서 document_type 가져오기
            document_type = settings.pgm_ladder_csv_doctype
            
            # 문서 레코드 리스트 생성
            documents = []
            
            for data in documents_data:
                # 파일 정보 추출
                document_name = data['document_name']
                file_extension = self._get_file_extension(document_name)
                file_type = self._get_mime_type(document_name)
                
                # document_id 생성
                document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data['file_key'].split('/')[-1][:8]}"
                
                # metadata 구성
                metadata_json = data.get('metadata', {})
                metadata_json.update({
                    'created_by_service': 'DocumentService',
                    'creation_method': 'bulk_create_ladder_csv_documents',
                    'upload_timestamp': datetime.now().isoformat()
                })
                
                # Document 레코드 생성 (개별)
                document = self.document_crud.create_document(
                    document_id=document_id,
                    document_name=document_name,
                    user_id=data['user_id'],
                    original_filename=data['original_filename'],
                    file_key=data['file_key'],
                    upload_path=data['upload_path'],
                    file_size=data['file_size'],
                    file_type=file_type,
                    file_extension=file_extension,
                    document_type=document_type,  # 환경변수
                    is_public=data.get('is_public', False),
                    permissions=data.get('permissions'),
                    metadata_json=metadata_json,
                    pgm_id=data['pgm_id']
                )
                
                documents.append(document)
            
            logger.info(
                f"✅ 레더 CSV 문서 일괄 생성 완료: {len(documents)}개 레코드"
            )
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ 레더 CSV 문서 일괄 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_UPLOAD_ERROR, e=e)
