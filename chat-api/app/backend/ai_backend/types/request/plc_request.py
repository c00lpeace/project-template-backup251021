# _*_ coding: utf-8 _*_
"""PLC request models."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CreatePlcRequest(BaseModel):
    """PLC 생성 요청"""
    plc_id: str = Field(..., min_length=1, max_length=50, description="PLC ID (예: M1CFB01000)")
    plant: str = Field(..., min_length=1, max_length=100, description="Plant")
    process: str = Field(..., min_length=1, max_length=100, description="공정")
    line: str = Field(..., min_length=1, max_length=100, description="Line")
    equipment_group: str = Field(..., min_length=1, max_length=100, description="장비그룹")
    unit: str = Field(..., min_length=1, max_length=100, description="호기")
    plc_name: str = Field(..., min_length=1, max_length=200, description="PLC 명칭")
    create_user: Optional[str] = Field(None, max_length=50, description="생성자")
    
    @field_validator('plc_id', 'plant', 'process', 'line', 'equipment_group', 'unit', 'plc_name')
    @classmethod
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('필드는 공백일 수 없습니다.')
        return v.strip()


class UpdatePlcRequest(BaseModel):
    """PLC 수정 요청"""
    plant: Optional[str] = Field(None, min_length=1, max_length=100, description="Plant")
    process: Optional[str] = Field(None, min_length=1, max_length=100, description="공정")
    line: Optional[str] = Field(None, min_length=1, max_length=100, description="Line")
    equipment_group: Optional[str] = Field(None, min_length=1, max_length=100, description="장비그룹")
    unit: Optional[str] = Field(None, min_length=1, max_length=100, description="호기")
    plc_name: Optional[str] = Field(None, min_length=1, max_length=200, description="PLC 명칭")
    update_user: Optional[str] = Field(None, max_length=50, description="수정자")
    
    @field_validator('plant', 'process', 'line', 'equipment_group', 'unit', 'plc_name')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('필드는 공백일 수 없습니다.')
        return v.strip() if v else v


class PlcListRequest(BaseModel):
    """PLC 목록 조회 요청"""
    skip: int = Field(0, ge=0, description="건너뛸 개수")
    limit: int = Field(100, ge=1, le=1000, description="조회할 개수")
    is_active: Optional[bool] = Field(True, description="활성 상태 필터 (None=전체)")
    plant: Optional[str] = Field(None, description="Plant 필터")
    process: Optional[str] = Field(None, description="공정 필터")
    line: Optional[str] = Field(None, description="Line 필터")
    equipment_group: Optional[str] = Field(None, description="장비그룹 필터")
    unit: Optional[str] = Field(None, description="호기 필터")


class PlcSearchRequest(BaseModel):
    """PLC 검색 요청"""
    keyword: str = Field(..., min_length=1, description="검색 키워드 (PLC_ID, PLC_NAME)")
    skip: int = Field(0, ge=0, description="건너뛸 개수")
    limit: int = Field(100, ge=1, le=1000, description="조회할 개수")
    is_active: Optional[bool] = Field(True, description="활성 상태 필터")
    
    @field_validator('keyword')
    @classmethod
    def validate_keyword(cls, v):
        if not v.strip():
            raise ValueError('검색 키워드는 공백일 수 없습니다.')
        return v.strip()


class PlcHierarchyRequest(BaseModel):
    """PLC 계층 조회 요청"""
    level: str = Field(..., description="조회할 레벨 (plant, process, line, equipment_group, unit)")
    plant: Optional[str] = Field(None, description="Plant 필터")
    process: Optional[str] = Field(None, description="공정 필터")
    line: Optional[str] = Field(None, description="Line 필터")
    equipment_group: Optional[str] = Field(None, description="장비그룹 필터")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = ['plant', 'process', 'line', 'equipment_group', 'unit']
        if v not in valid_levels:
            raise ValueError(f'level은 {valid_levels} 중 하나여야 합니다.')
        return v


# ========== ✨ 프로그램 매핑 관련 Request ==========

class MapProgramRequest(BaseModel):
    """프로그램 매핑 요청"""
    pgm_id: str = Field(..., min_length=1, max_length=50, description="프로그램 ID")
    user: str = Field(..., min_length=1, max_length=50, description="작업자")
    notes: Optional[str] = Field(None, max_length=500, description="비고")
    
    @field_validator('pgm_id', 'user')
    @classmethod
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('필드는 공백일 수 없습니다.')
        return v.strip()


class UnmapProgramRequest(BaseModel):
    """프로그램 매핑 해제 요청"""
    user: str = Field(..., min_length=1, max_length=50, description="작업자")
    notes: Optional[str] = Field(None, max_length=500, description="비고")
    
    @field_validator('user')
    @classmethod
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('필드는 공백일 수 없습니다.')
        return v.strip()


# ========== ✨ 일괄 매핑 관련 Request ==========

class BulkMapProgramRequest(BaseModel):
    """복수 PLC에 프로그램 일괄 매핑 요청"""
    plc_ids: list[str] = Field(..., min_length=1, description="PLC ID 목록 (최대 100개)")
    pgm_id: str = Field(..., min_length=1, max_length=50, description="프로그램 ID")
    user: str = Field(..., min_length=1, max_length=50, description="작업자")
    notes: Optional[str] = Field(None, max_length=500, description="비고")
    rollback_on_error: bool = Field(False, description="에러 시 전체 롤백 여부 (기본: 부분 성공)")
    
    @field_validator('plc_ids')
    @classmethod
    def validate_plc_ids(cls, v):
        if not v:
            raise ValueError('PLC ID 목록은 비어있을 수 없습니다.')
        if len(v) > 100:
            raise ValueError('PLC ID는 최대 100개까지 지정할 수 있습니다.')
        # 중복 제거
        unique_ids = list(set(v))
        if len(unique_ids) != len(v):
            raise ValueError('중복된 PLC ID가 포함되어 있습니다.')
        return unique_ids
    
    @field_validator('pgm_id', 'user')
    @classmethod
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('필드는 공백일 수 없습니다.')
        return v.strip()


class BulkUnmapProgramRequest(BaseModel):
    """복수 PLC의 프로그램 매핑 일괄 해제 요청"""
    plc_ids: list[str] = Field(..., min_length=1, description="PLC ID 목록 (최대 100개)")
    user: str = Field(..., min_length=1, max_length=50, description="작업자")
    notes: Optional[str] = Field(None, max_length=500, description="비고")
    rollback_on_error: bool = Field(False, description="에러 시 전체 롤백 여부 (기본: 부분 성공)")
    
    @field_validator('plc_ids')
    @classmethod
    def validate_plc_ids(cls, v):
        if not v:
            raise ValueError('PLC ID 목록은 비어있을 수 없습니다.')
        if len(v) > 100:
            raise ValueError('PLC ID는 최대 100개까지 지정할 수 있습니다.')
        # 중복 제거
        unique_ids = list(set(v))
        if len(unique_ids) != len(v):
            raise ValueError('중복된 PLC ID가 포함되어 있습니다.')
        return unique_ids
    
    @field_validator('user')
    @classmethod
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('필드는 공백일 수 없습니다.')
        return v.strip()


class BulkUpdateProgramRequest(BaseModel):
    """복수 PLC의 프로그램 일괄 변경 요청"""
    plc_ids: list[str] = Field(..., min_length=1, description="PLC ID 목록 (최대 100개)")
    new_pgm_id: str = Field(..., min_length=1, max_length=50, description="새 프로그램 ID")
    user: str = Field(..., min_length=1, max_length=50, description="작업자")
    notes: Optional[str] = Field(None, max_length=500, description="비고")
    rollback_on_error: bool = Field(False, description="에러 시 전체 롤백 여부 (기본: 부분 성공)")
    
    @field_validator('plc_ids')
    @classmethod
    def validate_plc_ids(cls, v):
        if not v:
            raise ValueError('PLC ID 목록은 비어있을 수 없습니다.')
        if len(v) > 100:
            raise ValueError('PLC ID는 최대 100개까지 지정할 수 있습니다.')
        # 중복 제거
        unique_ids = list(set(v))
        if len(unique_ids) != len(v):
            raise ValueError('중복된 PLC ID가 포함되어 있습니다.')
        return unique_ids
    
    @field_validator('new_pgm_id', 'user')
    @classmethod
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('필드는 공백일 수 없습니다.')
        return v.strip()
