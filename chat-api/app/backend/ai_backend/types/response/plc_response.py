# _*_ coding: utf-8 _*_
"""PLC response models."""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class PlcResponse(BaseModel):
    """PLC 응답"""
    model_config = ConfigDict(from_attributes=True)
    
    plc_id: str = Field(..., description="PLC ID")
    plant: str = Field(..., description="Plant")
    process: str = Field(..., description="공정")
    line: str = Field(..., description="Line")
    equipment_group: str = Field(..., description="장비그룹")
    unit: str = Field(..., description="호기")
    plc_name: str = Field(..., description="PLC 명칭")
    is_active: bool = Field(..., description="활성 상태")
    create_dt: datetime = Field(..., description="생성일시")
    create_user: Optional[str] = Field(None, description="생성자")
    update_dt: Optional[datetime] = Field(None, description="수정일시")
    update_user: Optional[str] = Field(None, description="수정자")


class PlcCreateResponse(BaseModel):
    """PLC 생성 응답"""
    plc_id: str = Field(..., description="PLC ID")
    plant: str = Field(..., description="Plant")
    process: str = Field(..., description="공정")
    line: str = Field(..., description="Line")
    equipment_group: str = Field(..., description="장비그룹")
    unit: str = Field(..., description="호기")
    plc_name: str = Field(..., description="PLC 명칭")


class PlcUpdateResponse(BaseModel):
    """PLC 수정 응답"""
    plc_id: str = Field(..., description="PLC ID")
    plant: str = Field(..., description="Plant")
    process: str = Field(..., description="공정")
    line: str = Field(..., description="Line")
    equipment_group: str = Field(..., description="장비그룹")
    unit: str = Field(..., description="호기")
    plc_name: str = Field(..., description="PLC 명칭")
    update_dt: Optional[datetime] = Field(None, description="수정일시")


class PlcDeleteResponse(BaseModel):
    """PLC 삭제 응답"""
    plc_id: str = Field(..., description="삭제된 PLC ID")
    message: str = Field(..., description="메시지")


class PlcRestoreResponse(BaseModel):
    """PLC 복원 응답"""
    plc_id: str = Field(..., description="복원된 PLC ID")
    message: str = Field(..., description="메시지")


class PlcListResponse(BaseModel):
    """PLC 목록 응답"""
    total: int = Field(..., description="전체 개수")
    items: List[PlcResponse] = Field(..., description="PLC 목록")


class PlcSearchResponse(BaseModel):
    """PLC 검색 응답"""
    total: int = Field(..., description="검색 결과 개수")
    items: List[PlcResponse] = Field(..., description="검색 결과")


class PlcCountResponse(BaseModel):
    """PLC 개수 응답"""
    active_count: int = Field(..., description="활성 PLC 개수")
    inactive_count: int = Field(..., description="비활성 PLC 개수")
    total_count: int = Field(..., description="전체 PLC 개수")


class PlcExistsResponse(BaseModel):
    """PLC 존재 여부 응답"""
    plc_id: str = Field(..., description="PLC ID")
    exists: bool = Field(..., description="존재 여부")


class PlcHierarchyResponse(BaseModel):
    """PLC 계층 조회 응답"""
    level: str = Field(..., description="조회한 레벨")
    values: List[str] = Field(..., description="고유 값 목록")


# ========== ✨ 프로그램 매핑 관련 Response ==========

class PlcWithMappingResponse(BaseModel):
    """PLC 매핑 정보 포함 응답"""
    model_config = ConfigDict(from_attributes=True)
    
    plc_id: str = Field(..., description="PLC ID")
    plant: str = Field(..., description="Plant")
    process: str = Field(..., description="공정")
    line: str = Field(..., description="Line")
    equipment_group: str = Field(..., description="장비그룹")
    unit: str = Field(..., description="호기")
    plc_name: str = Field(..., description="PLC 명칭")
    pgm_id: Optional[str] = Field(None, description="매핑된 프로그램 ID")
    pgm_mapping_dt: Optional[datetime] = Field(None, description="매핑 일시")
    pgm_mapping_user: Optional[str] = Field(None, description="매핑 사용자")
    is_active: bool = Field(..., description="활성 상태")
    create_dt: datetime = Field(..., description="생성일시")
    create_user: Optional[str] = Field(None, description="생성자")
    update_dt: Optional[datetime] = Field(None, description="수정일시")
    update_user: Optional[str] = Field(None, description="수정자")


class MapProgramResponse(BaseModel):
    """프로그램 매핑 응답"""
    plc_id: str = Field(..., description="PLC ID")
    pgm_id: str = Field(..., description="프로그램 ID")
    pgm_mapping_dt: datetime = Field(..., description="매핑 일시")
    pgm_mapping_user: str = Field(..., description="매핑 사용자")
    message: str = Field(..., description="메시지")


class UnmapProgramResponse(BaseModel):
    """프로그램 매핑 해제 응답"""
    plc_id: str = Field(..., description="PLC ID")
    message: str = Field(..., description="메시지")


class MappingHistoryItemResponse(BaseModel):
    """매핑 이력 항목"""
    model_config = ConfigDict(from_attributes=True)
    
    history_id: int = Field(..., description="이력 ID")
    plc_id: str = Field(..., description="PLC ID")
    pgm_id: Optional[str] = Field(None, description="프로그램 ID")
    action: str = Field(..., description="작업 타입 (CREATE/UPDATE/DELETE)")
    action_dt: datetime = Field(..., description="작업 일시")
    action_user: str = Field(..., description="작업자")
    prev_pgm_id: Optional[str] = Field(None, description="이전 프로그램 ID")
    notes: Optional[str] = Field(None, description="비고")


class MappingHistoryResponse(BaseModel):
    """매핑 이력 목록 응답"""
    total: int = Field(..., description="전체 개수")
    items: List[MappingHistoryItemResponse] = Field(..., description="이력 목록")


class PlcsByProgramResponse(BaseModel):
    """프로그램별 PLC 목록 응답"""
    pgm_id: str = Field(..., description="프로그램 ID")
    total: int = Field(..., description="전체 PLC 개수")
    items: List[PlcWithMappingResponse] = Field(..., description="PLC 목록")


class UnmappedPlcsResponse(BaseModel):
    """미매핑 PLC 목록 응답"""
    total: int = Field(..., description="전체 미매핑 PLC 개수")
    items: List[PlcWithMappingResponse] = Field(..., description="미매핑 PLC 목록")


# ========== ✨ 일괄 매핑 관련 Response ==========

class BulkMappingResultItem(BaseModel):
    """일괄 매핑 처리 결과 항목"""
    plc_id: str = Field(..., description="PLC ID")
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="처리 결과 메시지")
    pgm_id: Optional[str] = Field(None, description="매핑된 프로그램 ID")
    prev_pgm_id: Optional[str] = Field(None, description="이전 프로그램 ID")


class BulkMappingResponse(BaseModel):
    """일괄 매핑 응답"""
    total: int = Field(..., description="전체 요청 개수")
    success_count: int = Field(..., description="성공 개수")
    failure_count: int = Field(..., description="실패 개수")
    results: List[BulkMappingResultItem] = Field(..., description="개별 처리 결과")
    message: str = Field(..., description="전체 처리 결과 메시지")
    rolled_back: bool = Field(False, description="롤백 여부")


class BulkMapProgramResponse(BulkMappingResponse):
    """일괄 프로그램 매핑 응답"""
    pgm_id: str = Field(..., description="매핑한 프로그램 ID")


class BulkUnmapProgramResponse(BulkMappingResponse):
    """일괄 프로그램 매핑 해제 응답"""
    pass


class BulkUpdateProgramResponse(BulkMappingResponse):
    """일괄 프로그램 변경 응답"""
    new_pgm_id: str = Field(..., description="변경한 프로그램 ID")
