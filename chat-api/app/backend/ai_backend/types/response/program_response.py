# _*_ coding: utf-8 _*_
"""Program response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

__all__ = [
    "ProgramResponse",
    "ProgramListResponse",
    "ProgramDeleteResponse",
    "PgmMappingResponse",
    "PgmMappingDetailResponse",
    "PgmMappingListResponse",
    "ValidationResult",
    "SavedFileInfo",
    "ProgramUploadResponse",
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


class ValidationResult(BaseModel):
    """파일 검증 결과"""
    required_files: List[str] = Field(description="템플릿에 명시된 필수 파일")
    zip_files: List[str] = Field(description="ZIP 내부 파일 목록")
    matched_files: List[str] = Field(description="일치하는 파일")
    missing_files: List[str] = Field(description="누락된 파일")
    extra_files: List[str] = Field(description="불필요한 파일")
    validation_passed: bool = Field(description="검증 통과 여부")


class SavedFileInfo(BaseModel):
    """저장된 파일 정보"""
    document_id: str
    document_name: str
    file_type: str
    file_size: int
    upload_path: str


class ProgramUploadResponse(BaseModel):
    """프로그램 업로드 응답"""
    
    # ⭐ 생성된 프로그램 정보
    pgm_id: str = Field(description="서버에서 자동 생성된 프로그램 ID (예: PGM_1, PGM_2)")
    pgm_name: str
    pgm_version: Optional[str]
    description: Optional[str]
    create_user: str
    create_dt: datetime
    
    # 검증 결과
    validation_result: ValidationResult
    
    # 저장된 파일들
    saved_files: Dict = Field(description="저장된 파일 정보")
    
    # 통계
    summary: Dict = Field(
        description="업로드 통계",
        example={
            'total_ladder_files': 10,
            'template_parsed': True,
            'template_row_count': 10
        }
    )
    
    message: str = Field(default="프로그램이 성공적으로 생성되었습니다")
    
    class Config:
        from_attributes = True
