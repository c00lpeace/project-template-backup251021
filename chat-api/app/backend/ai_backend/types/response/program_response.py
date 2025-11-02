# _*_ coding: utf-8 _*_
"""Program response models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

__all__ = [
    "ProgramResponse",
    "ProgramListResponse",
    "ProgramDeleteResponse",
    "PgmMappingResponse",
    "PgmMappingDetailResponse",
    "PgmMappingListResponse",
]


class ProgramResponse(BaseModel):
    """프로그램 응답"""
    pgm_id: str
    pgm_name: str
    pgm_version: Optional[str]
    description: Optional[str]
    create_dt: datetime
    create_user: Optional[str]
    update_dt: Optional[datetime]
    update_user: Optional[str]
    notes: Optional[str]
    plc_count: Optional[int] = Field(None, description="매핑된 PLC 개수")
    
    class Config:
        from_attributes = True


class ProgramListResponse(BaseModel):
    """프로그램 목록 응답"""
    items: List[ProgramResponse]
    total: int
    page: int
    page_size: int


class ProgramDeleteResponse(BaseModel):
    """프로그램 삭제 응답"""
    pgm_id: str
    message: str


class PgmMappingResponse(BaseModel):
    """매핑 응답"""
    mapping_id: int
    plc_id: str
    pgm_id: str
    create_dt: datetime
    create_user: Optional[str]
    update_dt: Optional[datetime]
    update_user: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class PgmMappingDetailResponse(BaseModel):
    """매핑 상세 응답 (PLC 및 프로그램 정보 포함)"""
    mapping_id: int
    plc_id: str
    pgm_id: str
    notes: Optional[str]
    create_dt: datetime
    create_user: Optional[str]
    update_dt: Optional[datetime]
    update_user: Optional[str]
    
    # PLC 정보
    plc_name: Optional[str] = None
    plant: Optional[str] = None
    process: Optional[str] = None
    line: Optional[str] = None
    equipment_group: Optional[str] = None
    unit: Optional[str] = None
    
    # 프로그램 정보
    pgm_name: Optional[str] = None
    pgm_version: Optional[str] = None


class PgmMappingListResponse(BaseModel):
    """매핑 목록 응답"""
    items: List[PgmMappingDetailResponse]
    total: int
    page: int
    page_size: int
