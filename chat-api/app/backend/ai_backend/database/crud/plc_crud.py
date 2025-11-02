# _*_ coding: utf-8 _*_
"""PLC CRUD operations with database - 프로그램 매핑 메서드 추가"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from ai_backend.database.models.pgm_mapping_models import (
    PgmMappingAction,
    PgmMappingHistory,
)
from ai_backend.database.models.plc_models import PLCMaster
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PlcCrud:
    """PLC 관련 CRUD 작업을 처리하는 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== 기존 PLC CRUD 메서드들 ==========
    
    def create_plc(
        self,
        plc_id: str,
        plant: str,
        process: str,
        line: str,
        equipment_group: str,
        unit: str,
        plc_name: str,
        create_user: Optional[str] = None
    ) -> PLCMaster:
        """PLC 생성 (IS_ACTIVE=TRUE)"""
        try:
            plc = PLCMaster(
                plc_id=plc_id,
                plant=plant,
                process=process,
                line=line,
                equipment_group=equipment_group,
                unit=unit,
                plc_name=plc_name,
                create_dt=datetime.now(),
                create_user=create_user,
                is_active=True
            )
            self.db.add(plc)
            self.db.commit()
            self.db.refresh(plc)
            return plc
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"PLC 생성 실패 (중복 키): {str(e)}")
            raise HandledException(ResponseCode.DATABASE_INTEGRITY_ERROR, e=e)
        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_plc(self, plc_id: str) -> Optional[PLCMaster]:
        """PLC 조회 (활성 상태만)"""
        try:
            return self.db.query(PLCMaster).filter(
                and_(
                    PLCMaster.plc_id == plc_id,
                    PLCMaster.is_active == True
                )
            ).first()
        except Exception as e:
            logger.error(f"PLC 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_plc_include_deleted(self, plc_id: str) -> Optional[PLCMaster]:
        """PLC 조회 (삭제된 것 포함)"""
        try:
            return self.db.query(PLCMaster).filter(
                PLCMaster.plc_id == plc_id
            ).first()
        except Exception as e:
            logger.error(f"PLC 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_plcs(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = True,
        plant: Optional[str] = None,
        process: Optional[str] = None,
        line: Optional[str] = None,
        equipment_group: Optional[str] = None,
        unit: Optional[str] = None
    ) -> List[PLCMaster]:
        """PLC 목록 조회 (필터링 지원)"""
        try:
            query = self.db.query(PLCMaster)
            
            # 활성 상태 필터
            if is_active is not None:
                query = query.filter(PLCMaster.is_active == is_active)
            
            # 계층 구조 필터
            if plant:
                query = query.filter(PLCMaster.plant == plant)
            if process:
                query = query.filter(PLCMaster.process == process)
            if line:
                query = query.filter(PLCMaster.line == line)
            if equipment_group:
                query = query.filter(PLCMaster.equipment_group == equipment_group)
            if unit:
                query = query.filter(PLCMaster.unit == unit)
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"PLC 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def count_plcs(self, is_active: Optional[bool] = True) -> int:
        """PLC 개수 조회"""
        try:
            query = self.db.query(PLCMaster)
            if is_active is not None:
                query = query.filter(PLCMaster.is_active == is_active)
            return query.count()
        except Exception as e:
            logger.error(f"PLC 개수 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_plc(
        self,
        plc_id: str,
        plant: Optional[str] = None,
        process: Optional[str] = None,
        line: Optional[str] = None,
        equipment_group: Optional[str] = None,
        unit: Optional[str] = None,
        plc_name: Optional[str] = None,
        update_user: Optional[str] = None
    ) -> Optional[PLCMaster]:
        """PLC 정보 수정"""
        try:
            plc = self.get_plc(plc_id)
            if not plc:
                return None
            
            # 변경된 필드만 업데이트
            if plant is not None:
                plc.plant = plant
            if process is not None:
                plc.process = process
            if line is not None:
                plc.line = line
            if equipment_group is not None:
                plc.equipment_group = equipment_group
            if unit is not None:
                plc.unit = unit
            if plc_name is not None:
                plc.plc_name = plc_name
            
            plc.update_dt = datetime.now()
            plc.update_user = update_user
            
            self.db.commit()
            self.db.refresh(plc)
            return plc
        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC 수정 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def delete_plc(self, plc_id: str) -> bool:
        """PLC 삭제 (소프트 삭제: IS_ACTIVE=FALSE)"""
        try:
            plc = self.get_plc(plc_id)
            if not plc:
                return False
            
            plc.is_active = False
            plc.update_dt = datetime.now()
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def restore_plc(self, plc_id: str) -> bool:
        """PLC 복원 (IS_ACTIVE=TRUE)"""
        try:
            plc = self.get_plc_include_deleted(plc_id)
            if not plc:
                return False
            
            plc.is_active = True
            plc.update_dt = datetime.now()
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC 복원 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def exists_plc(self, plc_id: str) -> bool:
        """PLC 존재 여부 확인 (활성 상태만)"""
        try:
            return self.db.query(PLCMaster).filter(
                and_(
                    PLCMaster.plc_id == plc_id,
                    PLCMaster.is_active == True
                )
            ).count() > 0
        except Exception as e:
            logger.error(f"PLC 존재 확인 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def search_plcs(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = True
    ) -> List[PLCMaster]:
        """PLC 검색 (PLC_ID, PLC_NAME)"""
        try:
            query = self.db.query(PLCMaster)
            
            if is_active is not None:
                query = query.filter(PLCMaster.is_active == is_active)
            
            # PLC_ID 또는 PLC_NAME에서 검색
            query = query.filter(
                or_(
                    PLCMaster.plc_id.ilike(f"%{keyword}%"),
                    PLCMaster.plc_name.ilike(f"%{keyword}%")
                )
            )
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"PLC 검색 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_distinct_values(
        self,
        field: str,
        plant: Optional[str] = None,
        process: Optional[str] = None,
        line: Optional[str] = None,
        equipment_group: Optional[str] = None
    ) -> List[str]:
        """계층별 고유 값 조회 (예: Plant 목록, 공정 목록 등)"""
        try:
            query = self.db.query(PLCMaster).filter(PLCMaster.is_active == True)
            
            # 상위 계층 필터
            if plant:
                query = query.filter(PLCMaster.plant == plant)
            if process:
                query = query.filter(PLCMaster.process == process)
            if line:
                query = query.filter(PLCMaster.line == line)
            if equipment_group:
                query = query.filter(PLCMaster.equipment_group == equipment_group)
            
            # 필드별 고유 값 추출
            if field == "plant":
                results = query.distinct(PLCMaster.plant).all()
                return [r.plant for r in results]
            elif field == "process":
                results = query.distinct(PLCMaster.process).all()
                return [r.process for r in results]
            elif field == "line":
                results = query.distinct(PLCMaster.line).all()
                return [r.line for r in results]
            elif field == "equipment_group":
                results = query.distinct(PLCMaster.equipment_group).all()
                return [r.equipment_group for r in results]
            elif field == "unit":
                results = query.distinct(PLCMaster.unit).all()
                return [r.unit for r in results]
            else:
                return []
        except Exception as e:
            logger.error(f"고유 값 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    # ========== ✨ 새로 추가된 프로그램 매핑 메서드들 ==========
    
    def map_program(
        self,
        plc_id: str,
        pgm_id: str,
        user: str,
        notes: Optional[str] = None
    ) -> PLCMaster:
        """
        PLC에 프로그램 매핑
        - PLC_MASTER의 pgm_id 업데이트 (현재 상태)
        - PGM_MAPPING_HISTORY에 이력 기록
        """
        try:
            plc = self.get_plc(plc_id)
            if not plc:
                raise HandledException(
                    ResponseCode.USER_NOT_FOUND, 
                    msg=f"PLC '{plc_id}'를 찾을 수 없습니다."
                )
            
            # 이전 매핑 정보 백업
            prev_pgm_id = plc.pgm_id
            action = PgmMappingAction.CREATE if not prev_pgm_id else PgmMappingAction.UPDATE
            
            # 1. PLC_MASTER 업데이트 (현재 상태)
            plc.pgm_id = pgm_id
            plc.pgm_mapping_dt = datetime.now()
            plc.pgm_mapping_user = user
            # plc.update_dt = datetime.now()
            
            # 2. PGM_MAPPING_HISTORY에 이력 추가
            history = PgmMappingHistory(
                plc_id=plc_id,
                pgm_id=pgm_id,
                action=action.value,
                action_dt=datetime.now(),
                action_user=user,
                prev_pgm_id=prev_pgm_id,
                notes=notes
            )
            self.db.add(history)
            
            self.db.commit()
            self.db.refresh(plc)
            
            logger.info(f"프로그램 매핑 성공: PLC={plc_id}, PGM={pgm_id}, Action={action.value}")
            return plc
            
        except HandledException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 매핑 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def unmap_program(
        self,
        plc_id: str,
        user: str,
        notes: Optional[str] = None
    ) -> PLCMaster:
        """
        PLC의 프로그램 매핑 해제
        - PLC_MASTER의 pgm_id를 NULL로 설정
        - PGM_MAPPING_HISTORY에 DELETE 이력 기록
        """
        try:
            plc = self.get_plc(plc_id)
            if not plc:
                raise HandledException(
                    ResponseCode.USER_NOT_FOUND,
                    msg=f"PLC '{plc_id}'를 찾을 수 없습니다."
                )
            
            if not plc.pgm_id:
                raise HandledException(
                    ResponseCode.INVALID_REQUEST,
                    msg="매핑된 프로그램이 없습니다."
                )
            
            prev_pgm_id = plc.pgm_id
            
            # 1. PLC_MASTER 업데이트
            plc.pgm_id = None
            plc.pgm_mapping_dt = datetime.now()
            plc.pgm_mapping_user = user
            plc.update_dt = datetime.now()
            
            # 2. PGM_MAPPING_HISTORY에 이력 추가
            history = PgmMappingHistory(
                plc_id=plc_id,
                pgm_id=None,
                action=PgmMappingAction.DELETE.value,
                action_dt=datetime.now(),
                action_user=user,
                prev_pgm_id=prev_pgm_id,
                notes=notes
            )
            self.db.add(history)
            
            self.db.commit()
            self.db.refresh(plc)
            
            logger.info(f"프로그램 매핑 해제 성공: PLC={plc_id}, Prev PGM={prev_pgm_id}")
            return plc
            
        except HandledException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 매핑 해제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_mapping_history(
        self,
        plc_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PgmMappingHistory], int]:
        """
        PLC의 프로그램 매핑 변경 이력 조회
        Returns: (이력 목록, 전체 개수)
        """
        try:
            query = self.db.query(PgmMappingHistory).filter(
                PgmMappingHistory.plc_id == plc_id
            )
            
            total = query.count()
            
            histories = query.order_by(
                PgmMappingHistory.action_dt.desc()
            ).offset(skip).limit(limit).all()
            
            return histories, total
            
        except Exception as e:
            logger.error(f"매핑 이력 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_plcs_by_program(
        self,
        pgm_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[PLCMaster], int]:
        """
        특정 프로그램에 매핑된 PLC 목록 조회
        Returns: (PLC 목록, 전체 개수)
        """
        try:
            query = self.db.query(PLCMaster).filter(
                and_(
                    PLCMaster.pgm_id == pgm_id,
                    PLCMaster.is_active == True
                )
            )
            
            total = query.count()
            plcs = query.offset(skip).limit(limit).all()
            
            return plcs, total
            
        except Exception as e:
            logger.error(f"프로그램별 PLC 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def count_plcs_by_program(self, pgm_id: str) -> int:
        """특정 프로그램에 매핑된 PLC 개수"""
        try:
            return self.db.query(PLCMaster).filter(
                and_(
                    PLCMaster.pgm_id == pgm_id,
                    PLCMaster.is_active == True
                )
            ).count()
        except Exception as e:
            logger.error(f"프로그램별 PLC 개수 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_unmapped_plcs(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[PLCMaster], int]:
        """
        프로그램이 매핑되지 않은 PLC 목록 조회
        Returns: (PLC 목록, 전체 개수)
        """
        try:
            query = self.db.query(PLCMaster).filter(
                and_(
                    PLCMaster.pgm_id.is_(None),
                    PLCMaster.is_active == True
                )
            )
            
            total = query.count()
            plcs = query.offset(skip).limit(limit).all()
            
            return plcs, total
            
        except Exception as e:
            logger.error(f"미매핑 PLC 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
