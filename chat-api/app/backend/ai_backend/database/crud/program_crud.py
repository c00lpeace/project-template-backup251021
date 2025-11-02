# _*_ coding: utf-8 _*_
"""Program CRUD operations with database"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from ai_backend.database.models.program_models import Program
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ProgramCrud:
    """프로그램 관련 CRUD 작업을 처리하는 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_program(self, program_data: dict) -> Program:
        """
        프로그램 생성
        Args:
            program_data: 프로그램 생성 데이터
        Returns:
            생성된 프로그램 객체
        """
        try:
            program = Program(**program_data)
            self.db.add(program)
            self.db.commit()
            self.db.refresh(program)
            logger.info(f"프로그램 생성 성공: PGM_ID={program.pgm_id}")
            return program
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"프로그램 생성 실패 (중복 키): {str(e)}")
            raise HandledException(ResponseCode.DATABASE_INTEGRITY_ERROR, e=e)
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_program_by_id(self, pgm_id: str) -> Optional[Program]:
        """
        프로그램 ID로 조회
        Args:
            pgm_id: 프로그램 ID
        Returns:
            프로그램 객체 또는 None
        """
        try:
            if not self.db or not self.db.is_active:
                raise RuntimeError("Database session is not active")
            # return self.db.query(Program).filter(Program.pgm_id == pgm_id).first()
            return self.db.query(Program).filter(Program.pgm_id == pgm_id).first()
        except Exception as e:
            logger.error(f"프로그램 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_programs(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        pgm_version: Optional[str] = None
    ) -> List[Program]:
        """프로그램 목록 조회"""
        try:
            query = self.db.query(Program)
            
            if search:
                query = query.filter(
                    (Program.pgm_id.ilike(f"%{search}%")) |
                    (Program.pgm_name.ilike(f"%{search}%"))
                )
            
            if pgm_version:
                query = query.filter(Program.pgm_version == pgm_version)
            
            return query.order_by(Program.create_dt.desc()).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"프로그램 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def count_programs(
        self,
        search: Optional[str] = None,
        pgm_version: Optional[str] = None
    ) -> int:
        """
        프로그램 총 개수 조회
        Args:
            search: 검색 키워드
            pgm_version: 프로그램 버전 필터
        Returns:
            프로그램 개수
        """
        try:
            query = self.db.query(Program)
            
            if search:
                query = query.filter(
                    or_(
                        Program.pgm_id.ilike(f"%{search}%"),
                        Program.pgm_name.ilike(f"%{search}%")
                    )
                )
            
            if pgm_version:
                query = query.filter(Program.pgm_version == pgm_version)
            
            return query.count()
        except Exception as e:
            logger.error(f"프로그램 개수 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_program(self, pgm_id: str, update_data: dict) -> Optional[Program]:
        """
        프로그램 수정
        Args:
            pgm_id: 프로그램 ID
            update_data: 수정할 데이터
        Returns:
            수정된 프로그램 객체 또는 None
        """
        try:
            program = self.db.query(Program).filter(Program.pgm_id == pgm_id).first()
            
            if not program:
                logger.warning(f"프로그램을 찾을 수 없음: PGM_ID={pgm_id}")
                return None
            
            # 변경된 필드만 업데이트
            for key, value in update_data.items():
                if hasattr(program, key):
                    setattr(program, key, value)
            
            program.update_dt = datetime.now()
            self.db.commit()
            self.db.refresh(program)
            
            logger.info(f"프로그램 수정 성공: PGM_ID={pgm_id}")
            return program
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 수정 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def delete_program(self, pgm_id: str) -> bool:
        """
        프로그램 삭제 (하드 삭제)
        Args:
            pgm_id: 프로그램 ID
        Returns:
            삭제 성공 여부
        """
        try:
            program = self.db.query(Program).filter(Program.pgm_id == pgm_id).first()
            
            if not program:
                logger.warning(f"프로그램을 찾을 수 없음: PGM_ID={pgm_id}")
                return False
            
            self.db.delete(program)
            self.db.commit()
            
            logger.info(f"프로그램 삭제 성공: PGM_ID={pgm_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def exists_program(self, pgm_id: str) -> bool:
        """
        프로그램 존재 여부 확인
        Args:
            pgm_id: 프로그램 ID
        Returns:
            존재 여부
        """
        try:
            return self.db.query(Program).filter(
                Program.pgm_id == pgm_id
            ).count() > 0
        except Exception as e:
            logger.error(f"프로그램 존재 확인 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def search_programs(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Program], int]:
        """
        프로그램 검색 (PGM_ID, PGM_NAME)
        Args:
            keyword: 검색 키워드
            skip: 건너뛸 개수
            limit: 조회할 최대 개수
        Returns:
            (프로그램 목록, 전체 개수)
        """
        try:
            query = self.db.query(Program).filter(
                or_(
                    Program.pgm_id.ilike(f"%{keyword}%"),
                    Program.pgm_name.ilike(f"%{keyword}%")
                )
            )
            
            total = query.count()
            
            programs = query.order_by(
                Program.create_dt.desc()
            ).offset(skip).limit(limit).all()
            
            return programs, total
            
        except Exception as e:
            logger.error(f"프로그램 검색 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_programs_by_version(
        self,
        pgm_version: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Program], int]:
        """
        특정 버전의 프로그램 목록 조회
        Args:
            pgm_version: 프로그램 버전
            skip: 건너뛸 개수
            limit: 조회할 최대 개수
        Returns:
            (프로그램 목록, 전체 개수)
        """
        try:
            query = self.db.query(Program).filter(
                Program.pgm_version == pgm_version
            )
            
            total = query.count()
            
            programs = query.order_by(
                Program.create_dt.desc()
            ).offset(skip).limit(limit).all()
            
            return programs, total
            
        except Exception as e:
            logger.error(f"버전별 프로그램 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
