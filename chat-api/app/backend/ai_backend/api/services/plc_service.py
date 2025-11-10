# _*_ coding: utf-8 _*_
"""PLC Service for handling PLC operations."""
import logging
from typing import List, Optional

from ai_backend.database.crud.plc_crud import PlcCrud
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PlcService:
    """PLC 서비스를 관리하는 클래스"""
    
    def __init__(self, db: Session):
        if db is None:
            raise ValueError("Database session is required")
        
        self.db = db
        self.plc_crud = PlcCrud(db)
    
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
    ):
        """PLC 생성"""
        try:
            # PLC ID 중복 체크 (삭제된 것 포함)
            existing_plc = self.plc_crud.get_plc_include_deleted(plc_id)
            if existing_plc:
                if existing_plc.is_active:
                    raise HandledException(
                        ResponseCode.USER_ALREADY_EXISTS,  # PLC_ALREADY_EXISTS로 변경 권장
                        msg=f"PLC ID {plc_id}는 이미 사용 중입니다."
                    )
                else:
                    raise HandledException(
                        ResponseCode.USER_ALREADY_EXISTS,
                        msg=f"PLC ID {plc_id}는 삭제된 상태입니다. 복원을 사용하세요."
                    )
            
            plc = self.plc_crud.create_plc(
                plc_id=plc_id,
                plant=plant,
                process=process,
                line=line,
                equipment_group=equipment_group,
                unit=unit,
                plc_name=plc_name,
                create_user=create_user
            )
            return plc
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    # ========== ✨ 일괄 매핑 관련 메서드 ==========
    
    def bulk_map_program_to_plcs(
        self,
        plc_ids: List[str],
        pgm_id: str,
        user: str,
        notes: Optional[str] = None,
        rollback_on_error: bool = False
    ) -> dict:
        """
        복수 PLC에 프로그램 일괄 매핑
        
        Args:
            plc_ids: PLC ID 목록
            pgm_id: 프로그램 ID
            user: 작업자
            notes: 비고
            rollback_on_error: True면 에러 시 전체 롤백, False면 부분 성공
        
        Returns:
            dict: 매핑 결과 (성공/실패 목록)
        """
        try:
            return self.plc_crud.bulk_map_program(
                plc_ids=plc_ids,
                pgm_id=pgm_id,
                user=user,
                notes=notes,
                rollback_on_error=rollback_on_error
            )
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def bulk_unmap_program_from_plcs(
        self,
        plc_ids: List[str],
        user: str,
        notes: Optional[str] = None,
        rollback_on_error: bool = False
    ) -> dict:
        """
        복수 PLC의 프로그램 매핑 일괄 해제
        
        Returns:
            dict: 매핑 해제 결과
        """
        try:
            return self.plc_crud.bulk_unmap_program(
                plc_ids=plc_ids,
                user=user,
                notes=notes,
                rollback_on_error=rollback_on_error
            )
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def bulk_update_program_mapping(
        self,
        plc_ids: List[str],
        new_pgm_id: str,
        user: str,
        notes: Optional[str] = None,
        rollback_on_error: bool = False
    ) -> dict:
        """
        복수 PLC의 프로그램 일괄 변경
        
        Returns:
            dict: 프로그램 변경 결과
        """
        try:
            return self.plc_crud.bulk_update_program(
                plc_ids=plc_ids,
                new_pgm_id=new_pgm_id,
                user=user,
                notes=notes,
                rollback_on_error=rollback_on_error
            )
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_plc(self, plc_id: str, include_deleted: bool = False):
        """PLC 조회"""
        try:
            if include_deleted:
                plc = self.plc_crud.get_plc_include_deleted(plc_id)
            else:
                plc = self.plc_crud.get_plc(plc_id)
            
            if not plc:
                raise HandledException(ResponseCode.USER_NOT_FOUND, msg="PLC를 찾을 수 없습니다.")
            
            return plc
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
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
    ):
        """PLC 목록 조회"""
        try:
            plcs = self.plc_crud.get_plcs(
                skip=skip,
                limit=limit,
                is_active=is_active,
                plant=plant,
                process=process,
                line=line,
                equipment_group=equipment_group,
                unit=unit
            )
            total_count = self.plc_crud.count_plcs(is_active=is_active)
            return plcs, total_count
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
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
    ):
        """PLC 정보 수정"""
        try:
            plc = self.plc_crud.update_plc(
                plc_id=plc_id,
                plant=plant,
                process=process,
                line=line,
                equipment_group=equipment_group,
                unit=unit,
                plc_name=plc_name,
                update_user=update_user
            )
            if not plc:
                raise HandledException(ResponseCode.USER_NOT_FOUND, msg="PLC를 찾을 수 없습니다.")
            
            return plc
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def delete_plc(self, plc_id: str):
        """PLC 삭제 (소프트 삭제)"""
        try:
            success = self.plc_crud.delete_plc(plc_id)
            if not success:
                raise HandledException(ResponseCode.USER_NOT_FOUND, msg="PLC를 찾을 수 없습니다.")
            
            return True
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def restore_plc(self, plc_id: str):
        """PLC 복원"""
        try:
            success = self.plc_crud.restore_plc(plc_id)
            if not success:
                raise HandledException(ResponseCode.USER_NOT_FOUND, msg="PLC를 찾을 수 없습니다.")
            
            return True
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def exists_plc(self, plc_id: str):
        """PLC 존재 여부 확인"""
        try:
            return self.plc_crud.exists_plc(plc_id)
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def search_plcs(self, keyword: str, skip: int = 0, limit: int = 100, is_active: Optional[bool] = True):
        """PLC 검색"""
        try:
            plcs = self.plc_crud.search_plcs(
                keyword=keyword,
                skip=skip,
                limit=limit,
                is_active=is_active
            )
            return plcs
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_plc_count(self):
        """PLC 개수 조회 (활성/비활성/전체)"""
        try:
            active_count = self.plc_crud.count_plcs(is_active=True)
            inactive_count = self.plc_crud.count_plcs(is_active=False)
            total_count = self.plc_crud.count_plcs(is_active=None)
            
            return {
                'active_count': active_count,
                'inactive_count': inactive_count,
                'total_count': total_count
            }
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_hierarchy_values(
        self,
        level: str,
        plant: Optional[str] = None,
        process: Optional[str] = None,
        line: Optional[str] = None,
        equipment_group: Optional[str] = None
    ):
        """계층별 고유 값 조회"""
        try:
            values = self.plc_crud.get_distinct_values(
                field=level,
                plant=plant,
                process=process,
                line=line,
                equipment_group=equipment_group
            )
            return values
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    # ========== ✨ 프로그램 매핑 관련 메서드 ==========
    
    def map_program_to_plc(
        self,
        plc_id: str,
        pgm_id: str,
        user: str,
        notes: Optional[str] = None
    ):
        """PLC에 프로그램 매핑"""
        try:
            plc = self.plc_crud.map_program(
                plc_id=plc_id,
                pgm_id=pgm_id,
                user=user,
                notes=notes
            )
            return plc
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def unmap_program_from_plc(
        self,
        plc_id: str,
        user: str,
        notes: Optional[str] = None
    ):
        """PLC의 프로그램 매핑 해제"""
        try:
            plc = self.plc_crud.unmap_program(
                plc_id=plc_id,
                user=user,
                notes=notes
            )
            return plc
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_plc_mapping_history(
        self,
        plc_id: str,
        skip: int = 0,
        limit: int = 50
    ):
        """PLC의 프로그램 매핑 변경 이력 조회"""
        try:
            histories, total = self.plc_crud.get_mapping_history(
                plc_id=plc_id,
                skip=skip,
                limit=limit
            )
            return histories, total
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_plcs_by_program(
        self,
        pgm_id: str,
        skip: int = 0,
        limit: int = 100
    ):
        """특정 프로그램에 매핑된 PLC 목록 조회"""
        try:
            plcs, total = self.plc_crud.get_plcs_by_program(
                pgm_id=pgm_id,
                skip=skip,
                limit=limit
            )
            return plcs, total
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_unmapped_plcs(
        self,
        skip: int = 0,
        limit: int = 100
    ):
        """프로그램이 매핑되지 않은 PLC 목록 조회"""
        try:
            plcs, total = self.plc_crud.get_unmapped_plcs(
                skip=skip,
                limit=limit
            )
            return plcs, total
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def count_plcs_by_program(self, pgm_id: str) -> int:
        """특정 프로그램에 매핑된 PLC 개수"""
        try:
            return self.plc_crud.count_plcs_by_program(pgm_id)
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    # ========== ✨ 계층 구조 조회 메서드 ==========
    
    def get_plc_hierarchy(
        self,
        is_active: Optional[bool] = True
    ):
        """PLC 계층 구조 조회
        
        Args:
            is_active: 활성 PLC만 조회 (기본값: True)
        
        Returns:
            dict: 계층 구조로 변환된 PLC 데이터
        """
        try:
            # 1. get_plcs() 사용해서 데이터 조회
            plcs, total = self.get_plcs(
                skip=0,
                limit=10000,  # 전체 조회 (계층 구조는 페이징 불가)
                is_active=is_active
            )
            
            logger.info(f"PLC 계층 구조 조회: {len(plcs)}개 PLC 조회 완료 (total: {total})")
            
            # 데이터가 없는 경우도 정상 처리
            if not plcs or len(plcs) == 0:
                logger.info("PLC 데이터가 없어 빈 계층 구조 반환")
                return {"data": []}
            
            # 2. 계층 구조로 변환
            return self._build_hierarchy(plcs)
        
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"PLC 계층 구조 조회 중 오류 발생: {str(e)}", exc_info=True)
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def _build_hierarchy(self, plcs):
        """PLC 리스트를 계층 구조로 변환
        
        Args:
            plcs: PLC 리스트
        
        Returns:
            dict: 계층 구조 데이터
        """
        hierarchy = {}
        
        for plc in plcs:
            # Plant 레벨
            if plc.plant not in hierarchy:
                hierarchy[plc.plant] = {}
            
            # Process 레벨
            if plc.process not in hierarchy[plc.plant]:
                hierarchy[plc.plant][plc.process] = {}
            
            # Line 레벨
            if plc.line not in hierarchy[plc.plant][plc.process]:
                hierarchy[plc.plant][plc.process][plc.line] = {}
            
            # Equipment Group 레벨
            if plc.equipment_group not in hierarchy[plc.plant][plc.process][plc.line]:
                hierarchy[plc.plant][plc.process][plc.line][plc.equipment_group] = {}
            
            # Unit 레벨 (딕셔너리로 변경)
            if plc.unit not in hierarchy[plc.plant][plc.process][plc.line][plc.equipment_group]:
                hierarchy[plc.plant][plc.process][plc.line][plc.equipment_group][plc.unit] = []
            
            # info 추가
            hierarchy[plc.plant][plc.process][plc.line][plc.equipment_group][plc.unit].append({
                "plcId": plc.plc_id,
                "plcNm": plc.plc_name,
                "regDt": plc.create_dt.isoformat() if plc.create_dt else None,
                "regUsr": plc.create_user or "unknown"
            })
        
        # 딕셔너리를 Response 모델로 변환
        return self._convert_to_response(hierarchy)
    
    def _convert_to_response(self, hierarchy):
        """딕셔너리를 PlcHierarchyResponse 형식으로 변환 (TO-BE 구조)
        
        Args:
            hierarchy: 계층 구조 딕셔너리
        
        Returns:
            dict: Response 형식의 데이터
        """
        plants = []
        
        for plant_name, processes_dict in hierarchy.items():
            processes = []
            
            for process_name, lines_dict in processes_dict.items():
                lines = []
                
                for line_name, eq_groups_dict in lines_dict.items():
                    equipment_groups = []
                    
                    for eq_group_name, units_dict in eq_groups_dict.items():
                        units = []
                        for unit_name, info_list in units_dict.items():
                            units.append({
                                "unit": unit_name,
                                "info": info_list  # 리스트 형태로 전달
                            })
                        
                        equipment_groups.append({
                            "eqpGrp": eq_group_name,
                            "unitList": units
                        })
                    
                    lines.append({
                        "line": line_name,
                        "eqpGrpList": equipment_groups
                    })
                
                processes.append({
                    "proc": process_name,
                    "lineList": lines
                })
            
            plants.append({
                "plt": plant_name,
                "procList": processes
            })
        
        return {"data": plants}
