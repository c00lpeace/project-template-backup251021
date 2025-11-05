# _*_ coding: utf-8 _*_
"""Program REST API endpoints."""

from fastapi import APIRouter, Depends, Query, File, Form, UploadFile
from ai_backend.core.dependencies import get_program_service, get_plc_service, get_program_upload_service
from ai_backend.api.services.program_service import ProgramService
from ai_backend.api.services.plc_service import PlcService
from ai_backend.api.services.program_upload_service import ProgramUploadService
from ai_backend.types.request.program_request import (
    ProgramCreateRequest,
    ProgramUpdateRequest,
)
from ai_backend.types.response.program_response import (
    ProgramResponse,
    ProgramListResponse,
    ProgramDeleteResponse,
    ProgramUploadResponse,
)
from ai_backend.types.response.plc_response import (
    PlcsByProgramResponse,
    PlcWithMappingResponse,
)
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["programs"])


@router.post("/programs", response_model=ProgramResponse, status_code=201)
def create_program(
    request: ProgramCreateRequest,
    program_service: ProgramService = Depends(get_program_service)
):
    """프로그램을 생성합니다."""
    program = program_service.create_program(
        pgm_id=request.pgm_id,
        pgm_name=request.pgm_name,        
        pgm_version=request.pgm_version,
        description=request.description,
        create_user=request.create_user,
        notes=request.notes
    )
    return ProgramResponse.model_validate(program)


@router.get("/programs/{pgm_id}", response_model=ProgramResponse)
def get_program(
    pgm_id: str,
    program_service: ProgramService = Depends(get_program_service)
):
    """프로그램 ID로 프로그램을 조회합니다."""
    program = program_service.get_program(pgm_id)
    return ProgramResponse.model_validate(program)


@router.get("/programs", response_model=ProgramListResponse)
def get_programs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(50, ge=1, le=100, description="페이지당 개수"),
    search: Optional[str] = Query(None, description="검색어 (ID 또는 명칭)"),
    pgm_version: Optional[str] = Query(None, description="프로그램 버전 필터"),
    program_service: ProgramService = Depends(get_program_service)
):
    """프로그램 목록을 조회합니다."""
    skip = (page - 1) * page_size
    programs, total = program_service.get_programs(
        skip=skip,
        limit=page_size,
        search=search,
        pgm_version=pgm_version
    )
    
    return ProgramListResponse(
        items=[ProgramResponse.model_validate(p) for p in programs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/programs/{pgm_id}", response_model=ProgramResponse)
def update_program(
    pgm_id: str,
    request: ProgramUpdateRequest,
    program_service: ProgramService = Depends(get_program_service)
):
    """프로그램을 수정합니다."""
    program = program_service.update_program(
        pgm_id=pgm_id,
        pgm_name=request.pgm_name,        
        pgm_version=request.pgm_version,
        description=request.description,
        notes=request.notes,
        update_user=request.update_user
    )
    return ProgramResponse.model_validate(program)


@router.delete("/programs/{pgm_id}", response_model=ProgramDeleteResponse)
def delete_program(
    pgm_id: str,
    program_service: ProgramService = Depends(get_program_service)
):
    """프로그램을 삭제합니다."""
    program_service.delete_program(pgm_id)
    
    return ProgramDeleteResponse(
        pgm_id=pgm_id,
        message="프로그램이 성공적으로 삭제되었습니다."
    )


# ========== ✨ 프로그램별 매핑 PLC 조회 API ==========

@router.get("/programs/{pgm_id}/plcs", response_model=PlcsByProgramResponse)
def get_plcs_by_program(
    pgm_id: str,
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(100, ge=1, le=100, description="조회할 개수"),
    plc_service: PlcService = Depends(get_plc_service)
):
    """
    특정 프로그램에 매핑된 PLC 목록을 조회합니다.
    
    이 엔드포인트는 해당 프로그램을 사용하는 모든 PLC를 조회합니다.
    """
    plcs, total = plc_service.get_plcs_by_program(
        pgm_id=pgm_id,
        skip=skip,
        limit=limit
    )
    
    return PlcsByProgramResponse(
        pgm_id=pgm_id,
        total=total,
        items=[PlcWithMappingResponse.model_validate(plc) for plc in plcs]
    )


# ========== ⭐ 프로그램 파일 업로드 API (Phase 2) ==========

@router.post("/programs/upload", response_model=ProgramUploadResponse, status_code=201)
async def upload_program_files(
    pgm_name: str = Form(..., description="프로그램 명칭"),
    create_user: str = Form(..., description="생성자"),
    ladder_zip: UploadFile = File(..., description="레더 CSV 파일들이 압축된 ZIP"),
    template_xlsx: UploadFile = File(..., description="필수 파일 목록이 기재된 템플릿 파일"),
    pgm_version: Optional[str] = Form(None, description="프로그램 버전"),
    description: Optional[str] = Form(None, description="프로그램 설명"),
    notes: Optional[str] = Form(None, description="비고"),
    program_upload_service: ProgramUploadService = Depends(get_program_upload_service)
):
    """
    PLC 프로그램 파일 업로드 및 생성
    
    **PGM_ID는 서버에서 자동 생성** (클라이언트 전달 불필요)
    
    **워크플로우:**
    1. PGM_ID 자동 생성 (예: PGM_1, PGM_2)
    2. 파일 타입 검증 (.zip, .xlsx)
    3. 파일 검증 (템플릿 Logic ID vs ZIP 파일 목록)
    4. 불필요한 파일 제거
    5. 파일 저장 (DOCUMENTS 테이블)
    6. 프로그램 생성 (PROGRAMS 테이블)
    
    **파일 요구사항:**
    - `ladder_zip`: 레더 CSV 파일들이 압축된 ZIP 파일
    - `template_xlsx`: Logic ID 컬럼이 포함된 템플릿 엑셀 파일
    
    **검증 규칙:**
    - 템플릿의 Logic ID와 ZIP 내부 파일명 비교
    - 누락된 파일이 있으면 에러 반환
    - 불필요한 파일은 자동 제거
    """
    result = program_upload_service.upload_and_create_program(
        pgm_name=pgm_name,
        ladder_zip=ladder_zip,
        template_xlsx=template_xlsx,
        create_user=create_user,
        pgm_version=pgm_version,
        description=description,
        notes=notes
    )
    
    return ProgramUploadResponse(
        pgm_id=result['pgm_id'],
        pgm_name=result['program'].pgm_name,
        pgm_version=result['program'].pgm_version,
        description=result['program'].description,
        create_user=result['program'].create_user,
        create_dt=result['program'].create_dt,
        validation_result=result['validation_result'],
        saved_files=result['saved_files'],
        summary=result['summary'],
        message=result['message']
    )
