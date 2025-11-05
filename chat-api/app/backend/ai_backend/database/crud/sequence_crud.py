# _*_ coding: utf-8 _*_
"""Sequence CRUD operations with database"""
import logging
from typing import Optional

from ai_backend.database.models.sequence_models import ProgramSequence
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SequenceCrud:
    """시퀀스 관련 CRUD 작업을 처리하는 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_next_pgm_id(self) -> str:
        """
        다음 프로그램 ID 생성 (트랜잭션 안전)
        
        Returns:
            str: 'PGM_1', 'PGM_2', 'PGM_3' 형식
        """
        try:
            # Row Lock으로 동시성 제어 (SELECT FOR UPDATE)
            sequence = self.db.query(ProgramSequence).with_for_update().filter(
                ProgramSequence.id == 1
            ).first()
            
            if not sequence:
                # 시퀀스 레코드가 없으면 생성
                logger.info("PROGRAM_SEQUENCE 레코드가 없어 초기화합니다.")
                sequence = ProgramSequence(id=1, last_number=0)
                self.db.add(sequence)
                self.db.flush()
            
            # 번호 증가
            sequence.last_number += 1
            self.db.flush()
            
            pgm_id = f"PGM_{sequence.last_number}"
            logger.info(f"새로운 PGM_ID 생성: {pgm_id}")
            
            return pgm_id
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"PGM_ID 생성 실패 (무결성 오류): {str(e)}")
            raise HandledException(ResponseCode.DATABASE_INTEGRITY_ERROR, e=e)
        except Exception as e:
            self.db.rollback()
            logger.error(f"PGM_ID 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_current_number(self) -> int:
        """
        현재 시퀀스 번호 조회
        
        Returns:
            int: 현재 last_number 값 (시퀀스가 없으면 0)
        """
        try:
            sequence = self.db.query(ProgramSequence).filter(
                ProgramSequence.id == 1
            ).first()
            
            if not sequence:
                logger.warning("PROGRAM_SEQUENCE 레코드가 존재하지 않습니다.")
                return 0
            
            return sequence.last_number
            
        except Exception as e:
            logger.error(f"시퀀스 번호 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def reset_sequence(self, start_number: int = 0) -> bool:
        """
        시퀀스 초기화 (주의: 운영 환경에서는 사용 금지!)
        
        Args:
            start_number: 시작 번호 (기본값: 0)
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            sequence = self.db.query(ProgramSequence).filter(
                ProgramSequence.id == 1
            ).first()
            
            if not sequence:
                # 시퀀스가 없으면 생성
                sequence = ProgramSequence(id=1, last_number=start_number)
                self.db.add(sequence)
            else:
                # 기존 시퀀스 초기화
                sequence.last_number = start_number
            
            self.db.commit()
            logger.warning(f"⚠️ PROGRAM_SEQUENCE 초기화됨: {start_number}")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"시퀀스 초기화 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def initialize_sequence(self) -> bool:
        """
        시퀀스 테이블 초기화 (레코드가 없을 때만)
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            # 이미 레코드가 있는지 확인
            existing = self.db.query(ProgramSequence).filter(
                ProgramSequence.id == 1
            ).first()
            
            if existing:
                logger.info("PROGRAM_SEQUENCE 레코드가 이미 존재합니다.")
                return False
            
            # 초기 레코드 생성
            sequence = ProgramSequence(id=1, last_number=0)
            self.db.add(sequence)
            self.db.commit()
            
            logger.info("✅ PROGRAM_SEQUENCE 테이블 초기화 완료")
            return True
            
        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"시퀀스 초기화 중복 시도: {str(e)}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"시퀀스 초기화 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
