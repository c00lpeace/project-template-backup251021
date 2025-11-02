# _*_ coding: utf-8 _*_
"""Program service."""

from sqlalchemy.orm import Session
from ai_backend.database.crud.program_crud import ProgramCrud
from ai_backend.database.models.program_models import Program
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class ProgramService:
    """프로그램 서비스를 관리하는 클래스"""
    
    def __init__(self, db: Session):
        if db is None:
            raise ValueError("Database session is required")
        self.db = db
        self.program_crud = ProgramCrud(db)
    
    def create_program(
        self,
        pgm_id: str,
        pgm_name: str,
        pgm_version: Optional[str] = None,
        description: Optional[str] = None,
        create_user: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Program:
        """프로그램 생성"""
        try:
            # 프로그램 ID 중복 체크
            existing = self.program_crud.get_program_by_id(pgm_id)
            if existing:
                raise HandledException(
                    ResponseCode.PROGRAM_ALREADY_EXISTS,
                    msg=f"프로그램 ID '{pgm_id}'가 이미 존재합니다"
                )

            program_data = {
                'pgm_id': pgm_id,
                'pgm_name': pgm_name,
                'pgm_version': pgm_version,
                'description': description,
                'create_user': create_user,
                'notes': notes
            }

            program = self.program_crud.create_program(program_data)
            logger.info(f"프로그램 생성: {pgm_id}")
            return program
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)

    def get_program(self, pgm_id: str) -> Program:
        """프로그램 조회"""
        try:
            program = self.program_crud.get_program_by_id(pgm_id)
            if not program:
                raise HandledException(
                    ResponseCode.PROGRAM_NOT_FOUND,
                    msg=f"프로그램 ID '{pgm_id}'를 찾을 수 없습니다."
                )
            return program
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)

    def get_programs(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        pgm_version: Optional[str] = None
    ) -> tuple[List[Program], int]:
        """프로그램 목록 조회"""
        try:
            programs = self.program_crud.get_programs(
                skip=skip,
                limit=limit,
                search=search,
                pgm_version=pgm_version
            )
            
            total_count = self.program_crud.count_programs(
                search=search,
                pgm_version=pgm_version
            )
            
            return programs, total_count
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)

    def update_program(
        self,
        pgm_id: str,
        pgm_name: Optional[str] = None,
        pgm_version: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        update_user: Optional[str] = None
    ) -> Program:
        """프로그램 수정"""
        try:
            # 프로그램 존재 여부 확인
            existing = self.program_crud.get_program_by_id(pgm_id)
            if not existing:
                raise HandledException(
                    ResponseCode.PROGRAM_NOT_FOUND,
                    msg=f"프로그램 ID '{pgm_id}'를 찾을 수 없습니다."
                )

            # 업데이트할 데이터를 구성
            update_data = {}
            if pgm_name is not None:
                update_data['pgm_name'] = pgm_name
            if pgm_version is not None:
                update_data['pgm_version'] = pgm_version
            if description is not None:
                update_data['description'] = description
            if notes is not None:
                update_data['notes'] = notes
            if update_user is not None:
                update_data['update_user'] = update_user
            
            program = self.program_crud.update_program(pgm_id, update_data)
            logger.info(f"프로그램 수정: {pgm_id}")
            return program
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)

    def delete_program(self, pgm_id: str) -> bool:
        """프로그램 삭제"""
        try:
            # 프로그램 존재 여부 확인
            existing = self.program_crud.get_program_by_id(pgm_id)
            if not existing:
                raise HandledException(
                    ResponseCode.PROGRAM_NOT_FOUND,
                    msg=f"프로그램 ID '{pgm_id}'를 찾을 수 없습니다."
                )

            success = self.program_crud.delete_program(pgm_id)
            if success:
                logger.info(f"프로그램 삭제: {pgm_id}")
            return success
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
