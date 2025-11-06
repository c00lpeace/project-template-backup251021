# _*_ coding: utf-8 _*_
"""
프로그램 문서 타입별 후처리 로직 (Strategy 패턴)

문서 타입에 따라 다른 후처리를 수행:
- 템플릿 파일: 파싱 후 PGM_TEMPLATE 테이블 저장
- 기타 파일: 후처리 없음

Phase 1 작업: 리팩토링 - Strategy 패턴 적용
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict

from sqlalchemy.orm import Session

from ai_backend.config.simple_settings import settings
from shared_core.models import Document


logger = logging.getLogger(__name__)


# ==========================================
# 추상 클래스
# ==========================================

class ProgramDocumentProcessor(ABC):
    """
    문서 타입별 후처리 추상 클래스
    
    Strategy 패턴을 사용하여 문서 타입별로 다른 처리를 수행합니다.
    """
    
    @abstractmethod
    def process(self, document: Document) -> None:
        """
        문서 타입별 후처리
        
        Args:
            document: 문서 레코드 (DOCUMENTS 테이블)
        """
        pass


# ==========================================
# 기본 프로세서 (후처리 없음)
# ==========================================

class DefaultProgramDocumentProcessor(ProgramDocumentProcessor):
    """
    기본 문서 프로세서
    
    후처리가 필요 없는 문서 타입에 사용됩니다.
    """
    
    def process(self, document: Document) -> None:
        """
        후처리 없음
        
        Args:
            document: 문서 레코드
        """
        logger.debug(f"기본 프로세서: 후처리 없음 - {document.document_id}")
        pass


# ==========================================
# 템플릿 프로세서
# ==========================================

class ProgramTemplateProcessor(ProgramDocumentProcessor):
    """
    템플릿 문서 프로세서
    
    템플릿 파일을 파싱하여 PGM_TEMPLATE 테이블에 저장합니다.
    """
    
    def __init__(self, db: Session, template_service):
        """
        Args:
            db: 데이터베이스 세션
            template_service: 템플릿 서비스
        """
        self.db = db
        self.settings = settings
        self.template_service = template_service
    
    def process(self, document: Document) -> None:
        """
        템플릿 파싱 및 PGM_TEMPLATE 테이블 저장
        
        Args:
            document: 템플릿 문서 레코드
        """
        # document_type 확인
        if document.document_type != self.settings.pgm_template_doctype:
            logger.warning(
                f"템플릿 프로세서에 잘못된 문서 타입이 전달되었습니다: "
                f"{document.document_type} (예상: {self.settings.pgm_template_doctype})"
            )
            return
        
        try:
            logger.info(f"템플릿 프로세서 시작: {document.document_id}")
            
            # 파일 경로에서 XLSX 읽기
            file_path = document.upload_path
            
            # 템플릿 파싱
            parsed_data = self.template_service.parse_template_xlsx(file_path)
            
            # PGM_TEMPLATE 테이블 저장
            saved_count = self.template_service.save_template_data(
                document_id=document.document_id,
                pgm_id=document.pgm_id,
                template_data=parsed_data
            )
            
            logger.info(
                f"✅ 템플릿 프로세서 완료: {document.document_id} "
                f"({saved_count}개 행 저장)"
            )
        
        except Exception as e:
            logger.error(f"❌ 템플릿 프로세서 실패: {document.document_id} - {str(e)}")
            # 에러를 다시 발생시켜서 트랜잭션 롤백
            raise


# ==========================================
# 프로세서 팩토리
# ==========================================

class ProgramDocumentProcessorFactory:
    """
    문서 타입별 프로세서 팩토리
    
    문서 타입에 따라 적절한 프로세서를 반환합니다.
    """
    
    def __init__(self, db: Session, template_service):
        """
        Args:
            db: 데이터베이스 세션
            template_service: 템플릿 서비스
        """
        self.db = db
        self.settings = settings
        self.template_service = template_service
        
        # 프로세서 매핑 (환경변수 기반)
        self.processors: Dict[str, ProgramDocumentProcessor] = {
            self.settings.pgm_template_doctype: ProgramTemplateProcessor(
                db=self.db,
                template_service=self.template_service
            ),
            'default': DefaultProgramDocumentProcessor()
        }
    
    def get_processor(self, document_type: str) -> ProgramDocumentProcessor:
        """
        문서 타입에 맞는 프로세서 반환
        
        Args:
            document_type: 문서 타입 (예: "PGM_TEMPLATE_FILE", "PGM_LADDER_CSV")
            
        Returns:
            ProgramDocumentProcessor: 문서 프로세서
        """
        processor = self.processors.get(document_type)
        
        if processor is None:
            logger.debug(f"문서 타입 '{document_type}'에 대한 프로세서 없음. 기본 프로세서 사용.")
            return self.processors['default']
        
        return processor
    
    def register_processor(
        self,
        document_type: str,
        processor: ProgramDocumentProcessor
    ) -> None:
        """
        새로운 프로세서 등록 (확장성)
        
        Args:
            document_type: 문서 타입
            processor: 프로세서 인스턴스
        """
        self.processors[document_type] = processor
        logger.info(f"새 프로세서 등록: {document_type}")
