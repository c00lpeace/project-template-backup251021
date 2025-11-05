# _*_ coding: utf-8 _*_
"""Sequence service."""

from sqlalchemy.orm import Session
from ai_backend.database.crud.sequence_crud import SequenceCrud
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
import logging

logger = logging.getLogger(__name__)


class SequenceService:
    """시퀀스 서비스를 관리하는 클래스"""
    
    def __init__(self, db: Session):
        if db is None:
            raise ValueError("Database session is required")
        self.db = db
        self.sequence_crud = SequenceCrud(db)
    
    def generate_pgm_id(self) -> str:
        """
        새로운 프로그램 ID 생성
        
        트랜잭션 안전성을 보장하며, 동시 요청 시에도 중복 없이 고유한 ID를 생성합니다.
        
        Returns:
            str: 'PGM_1', 'PGM_2', 'PGM_3' 형식의 프로그램 ID
        
        Raises:
            HandledException: ID 생성 실패 시
        """
        try:
            pgm_id = self.sequence_crud.generate_next_pgm_id()
            logger.info(f"✅ 새로운 PGM_ID 생성: {pgm_id}")
            return pgm_id
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"❌ PGM_ID 생성 중 예상치 못한 오류: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_current_number(self) -> int:
        """
        현재 시퀀스 번호 조회
        
        Returns:
            int: 현재 last_number 값
        """
        try:
            current = self.sequence_crud.get_current_number()
            logger.debug(f"현재 시퀀스 번호: {current}")
            return current
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"시퀀스 번호 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_next_pgm_id_preview(self) -> str:
        """
        다음에 생성될 PGM_ID를 미리 확인 (실제 생성은 하지 않음)
        
        주의: 동시성 환경에서는 실제 생성되는 ID와 다를 수 있습니다.
        
        Returns:
            str: 다음 PGM_ID 예상값
        """
        try:
            current = self.sequence_crud.get_current_number()
            next_number = current + 1
            next_pgm_id = f"PGM_{next_number}"
            
            logger.debug(f"다음 PGM_ID 예상: {next_pgm_id}")
            return next_pgm_id
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"다음 PGM_ID 예상 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def initialize_sequence(self) -> bool:
        """
        시퀀스 테이블 초기화 (레코드가 없을 때만)
        
        주로 시스템 초기 설정이나 테스트 환경에서 사용됩니다.
        
        Returns:
            bool: 초기화 성공 여부 (이미 존재하면 False)
        """
        try:
            result = self.sequence_crud.initialize_sequence()
            if result:
                logger.info("✅ PROGRAM_SEQUENCE 초기화 완료")
            else:
                logger.info("ℹ️ PROGRAM_SEQUENCE가 이미 초기화되어 있습니다")
            return result
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"시퀀스 초기화 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def reset_sequence(self, start_number: int = 0) -> bool:
        """
        시퀀스 강제 초기화 (운영 환경에서는 절대 사용 금지!)
        
        ⚠️ 경고: 이 메서드는 기존 프로그램 ID와의 충돌을 일으킬 수 있습니다.
        테스트 환경에서만 사용하세요.
        
        Args:
            start_number: 시작 번호 (기본값: 0)
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            logger.warning(f"⚠️ 시퀀스 강제 초기화 시도: start_number={start_number}")
            result = self.sequence_crud.reset_sequence(start_number)
            
            if result:
                logger.warning(f"⚠️ PROGRAM_SEQUENCE 강제 초기화됨: {start_number}")
            
            return result
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"시퀀스 초기화 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
