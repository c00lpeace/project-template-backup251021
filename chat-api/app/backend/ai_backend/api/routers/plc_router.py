# _*_ coding: utf-8 _*_
"""PLC REST API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from ai_backend.core.dependencies import get_plc_service
from ai_backend.api.services.plc_service import PlcService
from ai_backend.types.request.plc_request import (
    CreatePlcRequest,
    UpdatePlcRequest,
    PlcListRequest,
    PlcSearchRequest,
    PlcHierarchyRequest,
    MapProgramRequest,
    UnmapProgramRequest,
    BulkMapProgramRequest,
    BulkUnmapProgramRequest,
    BulkUpdateProgramRequest
)
from ai_backend.types.response.plc_response import (
    PlcResponse,
    PlcCreateResponse,
    PlcUpdateResponse,
    PlcDeleteResponse,
    PlcRestoreResponse,
    PlcListResponse,
    PlcSearchResponse,
    PlcCountResponse,
    PlcExistsResponse,
    PlcHierarchyResponse,
    PlcWithMappingResponse,
    MapProgramResponse,
    UnmapProgramResponse,
    UnmappedPlcsResponse,
    BulkMapProgramResponse,
    BulkUnmapProgramResponse,
    BulkUpdateProgramResponse,
    BulkMappingResultItem
)
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["plc"])


@router.post("/plcs", response_model=PlcCreateResponse, status_code=status.HTTP_201_CREATED)
def create_plc(
    request: CreatePlcRequest,
    plc_service: PlcService = Depends(get_plc_service)
):
    """새로운 PLC를 생성합니다."""
    plc = plc_service.create_plc(
        plc_id=request.plc_id,
        plant=request.plant,
        process=request.process,
        line=request.line,
        equipment_group=request.equipment_group,
        unit=request.unit,
        plc_name=request.plc_name,
        create_user=request.create_user
    )
    
    return PlcCreateResponse(
        plc_id=plc.plc_id,
        plant=plc.plant,
        process=plc.process,
        line=plc.line,
        equipment_group=plc.equipment_group,
        unit=plc.unit,
        plc_name=plc.plc_name
    )


@router.get("/plc/{plc_id}", response_model=PlcResponse)
def get_plc(
    plc_id: str,
    include_deleted: bool = Query(False, description="삭제된 PLC도 포함"),
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC ID로 PLC 정보를 조회합니다."""
    plc = plc_service.get_plc(plc_id, include_deleted=include_deleted)
    return PlcResponse.model_validate(plc)


@router.get("/plcs", response_model=PlcListResponse)
def get_plcs(
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 개수"),
    is_active: Optional[bool] = Query(True, description="활성 상태 필터 (None=전체)"),
    plant: Optional[str] = Query(None, description="Plant 필터"),
    process: Optional[str] = Query(None, description="공정 필터"),
    line: Optional[str] = Query(None, description="Line 필터"),
    equipment_group: Optional[str] = Query(None, description="장비그룹 필터"),
    unit: Optional[str] = Query(None, description="호기 필터"),
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC 목록을 조회합니다."""
    plcs, total = plc_service.get_plcs(
        skip=skip,
        limit=limit,
        is_active=is_active,
        plant=plant,
        process=process,
        line=line,
        equipment_group=equipment_group,
        unit=unit
    )
    
    return PlcListResponse(
        total=total,
        items=[PlcResponse.model_validate(plc) for plc in plcs]
    )


@router.put("/plc/{plc_id}", response_model=PlcUpdateResponse)
def update_plc(
    plc_id: str,
    request: UpdatePlcRequest,
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC 정보를 수정합니다."""
    plc = plc_service.update_plc(
        plc_id=plc_id,
        plant=request.plant,
        process=request.process,
        line=request.line,
        equipment_group=request.equipment_group,
        unit=request.unit,
        plc_name=request.plc_name,
        update_user=request.update_user
    )
    
    return PlcUpdateResponse(
        plc_id=plc.plc_id,
        plant=plc.plant,
        process=plc.process,
        line=plc.line,
        equipment_group=plc.equipment_group,
        unit=plc.unit,
        plc_name=plc.plc_name,
        update_dt=plc.update_dt
    )


@router.delete("/plc/{plc_id}", response_model=PlcDeleteResponse)
def delete_plc(
    plc_id: str,
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC를 삭제합니다 (소프트 삭제: IS_ACTIVE=FALSE)."""
    plc_service.delete_plc(plc_id)
    
    return PlcDeleteResponse(
        plc_id=plc_id,
        message="PLC가 성공적으로 삭제되었습니다."
    )


@router.post("/plc/{plc_id}/restore", response_model=PlcRestoreResponse)
def restore_plc(
    plc_id: str,
    plc_service: PlcService = Depends(get_plc_service)
):
    """삭제된 PLC를 복원합니다 (IS_ACTIVE=TRUE)."""
    plc_service.restore_plc(plc_id)
    
    return PlcRestoreResponse(
        plc_id=plc_id,
        message="PLC가 성공적으로 복원되었습니다."
    )


@router.get("/plcs/search/keyword", response_model=PlcSearchResponse)
def search_plcs(
    keyword: str = Query(..., min_length=1, description="검색 키워드 (PLC_ID, PLC_NAME)"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 개수"),
    is_active: Optional[bool] = Query(True, description="활성 상태 필터"),
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC를 검색합니다 (PLC_ID, PLC_NAME)."""
    plcs = plc_service.search_plcs(
        keyword=keyword,
        skip=skip,
        limit=limit,
        is_active=is_active
    )
    
    return PlcSearchResponse(
        total=len(plcs),
        items=[PlcResponse.model_validate(plc) for plc in plcs]
    )


@router.get("/plcs/count/summary", response_model=PlcCountResponse)
def get_plc_count(
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC 개수를 조회합니다 (활성/비활성/전체)."""
    counts = plc_service.get_plc_count()
    
    return PlcCountResponse(
        active_count=counts['active_count'],
        inactive_count=counts['inactive_count'],
        total_count=counts['total_count']
    )


@router.get("/plc/{plc_id}/exists", response_model=PlcExistsResponse)
def check_plc_exists(
    plc_id: str,
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC 존재 여부를 확인합니다."""
    exists = plc_service.exists_plc(plc_id)
    
    return PlcExistsResponse(
        plc_id=plc_id,
        exists=exists
    )


@router.get("/plcs/hierarchy/values", response_model=PlcHierarchyResponse)
def get_hierarchy_values(
    level: str = Query(..., description="조회할 레벨 (plant, process, line, equipment_group, unit)"),
    plant: Optional[str] = Query(None, description="Plant 필터"),
    process: Optional[str] = Query(None, description="공정 필터"),
    line: Optional[str] = Query(None, description="Line 필터"),
    equipment_group: Optional[str] = Query(None, description="장비그룹 필터"),
    plc_service: PlcService = Depends(get_plc_service)
):
    """계층별 고유 값을 조회합니다 (예: Plant 목록, 공정 목록 등)."""
    valid_levels = ['plant', 'process', 'line', 'equipment_group', 'unit']
    if level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"level은 {valid_levels} 중 하나여야 합니다."
        )
    
    values = plc_service.get_hierarchy_values(
        level=level,
        plant=plant,
        process=process,
        line=line,
        equipment_group=equipment_group
    )
    
    return PlcHierarchyResponse(
        level=level,
        values=values
    )


# ========== ✨ 프로그램 매핑 관련 API ==========

@router.post("/plc/{plc_id}/mapping", response_model=MapProgramResponse)
def map_program_to_plc(
    plc_id: str,
    request: MapProgramRequest,
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC에 프로그램을 매핑합니다."""
    plc = plc_service.map_program_to_plc(
        plc_id=plc_id,
        pgm_id=request.pgm_id,
        user=request.user,
        notes=request.notes
    )
    
    return MapProgramResponse(
        plc_id=plc.plc_id,
        pgm_id=plc.pgm_id,
        pgm_mapping_dt=plc.pgm_mapping_dt,
        pgm_mapping_user=plc.pgm_mapping_user,
        message=f"PLC '{plc_id}'에 프로그램 '{request.pgm_id}'가 성공적으로 매핑되었습니다."
    )


@router.delete("/plc/{plc_id}/mapping", response_model=UnmapProgramResponse)
def unmap_program_from_plc(
    plc_id: str,
    request: UnmapProgramRequest,
    plc_service: PlcService = Depends(get_plc_service)
):
    """PLC의 프로그램 매핑을 해제합니다."""
    plc_service.unmap_program_from_plc(
        plc_id=plc_id,
        user=request.user,
        notes=request.notes
    )
    
    return UnmapProgramResponse(
        plc_id=plc_id,
        message=f"PLC '{plc_id}'의 프로그램 매핑이 성공적으로 해제되었습니다."
    )


@router.get("/plcs/unmapped/list", response_model=UnmappedPlcsResponse)
def get_unmapped_plcs(
    skip: int = Query(0, ge=0, description="건너뜰 개수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 개수"),
    plc_service: PlcService = Depends(get_plc_service)
):
    """프로그램이 매핑되지 않은 PLC 목록을 조회합니다."""
    plcs, total = plc_service.get_unmapped_plcs(
        skip=skip,
        limit=limit
    )
    
    return UnmappedPlcsResponse(
        total=total,
        items=[PlcWithMappingResponse.model_validate(plc) for plc in plcs]
    )


# ========== PLC 계층 구조 트리 조회 API ==========

@router.get("/plcs/tree", response_model=dict)
def get_plc_tree(
    is_active: bool = Query(True, description="활성 PLC만 조회"),
    plc_service: PlcService = Depends(get_plc_service)
):
    """
    PLC 계층 구조를 트리 형태로 조회
    
    - **is_active**: 활성 PLC만 조회 (기본값: True)
    
    **반환 구조:**
    ```json
    {
        "data": [
            {
                "plt": "PLT1",
                "procList": [
                    {
                        "proc": "PLT1-PRC1",
                        "lineList": [
                            {
                                "line": "PLT1-PRC1-LN1",
                                "eqGrpList": [
                                    {
                                        "eqGrp": "PLT1-PRC1-LN1-EQ1",
                                        "unitList": [
                                            {
                                                "unit": "PLT1-PRC1-LN1-EQ1-U1",
                                                "info": [
                                                    {
                                                        "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
                                                        "create_dt": "2023-10-01T10:00:00",
                                                        "user": "admin"
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    ```
    """
    logger.info(f"PLC 계층 구조 조회 요청: is_active={is_active}")
    result = plc_service.get_plc_hierarchy(is_active=is_active)
    return result


# ========== ✨ 일괄 매핑 API ==========

@router.post("/plcs/mapping/bulk", response_model=BulkMapProgramResponse, status_code=status.HTTP_200_OK)
def bulk_map_program(
    request: BulkMapProgramRequest,
    plc_service: PlcService = Depends(get_plc_service)
):
    """
    복수 PLC에 프로그램 일괄 매핑
    
    - **plc_ids**: 매핑할 PLC ID 목록 (최대 100개)
    - **pgm_id**: 매핑할 프로그램 ID
    - **user**: 작업자
    - **notes**: 비고 (선택)
    - **rollback_on_error**: 에러 시 전체 롤백 여부 (기본: False)
      - True: 하나라도 실패하면 전체 롤백
      - False: 성공한 것만 커밋 (부분 성공)
    
    **반환 예시:**
    ```json
    {
        "total": 3,
        "success_count": 2,
        "failure_count": 1,
        "pgm_id": "PGM_1",
        "results": [
            {
                "plc_id": "PLC01",
                "success": true,
                "message": "프로그램 'PGM_1' 매핑 성공",
                "pgm_id": "PGM_1",
                "prev_pgm_id": null
            },
            {
                "plc_id": "PLC02",
                "success": false,
                "message": "PLC 'PLC02'를 찾을 수 없습니다.",
                "pgm_id": null,
                "prev_pgm_id": null
            }
        ],
        "message": "3개 중 2개 성공, 1개 실패",
        "rolled_back": false
    }
    ```
    """
    logger.info(f"일괄 매핑 요청: plc_ids={request.plc_ids}, pgm_id={request.pgm_id}")
    
    result = plc_service.bulk_map_program_to_plcs(
        plc_ids=request.plc_ids,
        pgm_id=request.pgm_id,
        user=request.user,
        notes=request.notes,
        rollback_on_error=request.rollback_on_error
    )
    
    # 결과 변환
    success_count = len(result['success'])
    failure_count = len(result['failed'])
    total = success_count + failure_count
    
    # 결과 항목 변환
    results = []
    for item in result['success']:
        results.append(BulkMappingResultItem(
            plc_id=item['plc_id'],
            success=True,
            message=item['message'],
            pgm_id=item['pgm_id'],
            prev_pgm_id=item['prev_pgm_id']
        ))
    
    for item in result['failed']:
        results.append(BulkMappingResultItem(
            plc_id=item['plc_id'],
            success=False,
            message=item['message'],
            pgm_id=item.get('pgm_id'),
            prev_pgm_id=item.get('prev_pgm_id')
        ))
    
    # 메시지 생성
    if result['rolled_back']:
        message = f"에러 발생으로 인해 전체 롤백되었습니다. (실패: {failure_count}개)"
    elif failure_count == 0:
        message = f"모두 성공적으로 매핑되었습니다. (성공: {success_count}개)"
    else:
        message = f"{total}개 중 {success_count}개 성공, {failure_count}개 실패"
    
    return BulkMapProgramResponse(
        total=total,
        success_count=success_count,
        failure_count=failure_count,
        pgm_id=request.pgm_id,
        results=results,
        message=message,
        rolled_back=result['rolled_back']
    )


@router.delete("/plcs/mapping/bulk", response_model=BulkUnmapProgramResponse, status_code=status.HTTP_200_OK)
def bulk_unmap_program(
    request: BulkUnmapProgramRequest,
    plc_service: PlcService = Depends(get_plc_service)
):
    """
    복수 PLC의 프로그램 매핑 일괄 해제
    
    - **plc_ids**: 매핑 해제할 PLC ID 목록 (최대 100개)
    - **user**: 작업자
    - **notes**: 비고 (선택)
    - **rollback_on_error**: 에러 시 전체 롤백 여부
    """
    logger.info(f"일괄 매핑 해제 요청: plc_ids={request.plc_ids}")
    
    result = plc_service.bulk_unmap_program_from_plcs(
        plc_ids=request.plc_ids,
        user=request.user,
        notes=request.notes,
        rollback_on_error=request.rollback_on_error
    )
    
    # 결과 변환
    success_count = len(result['success'])
    failure_count = len(result['failed'])
    total = success_count + failure_count
    
    results = []
    for item in result['success']:
        results.append(BulkMappingResultItem(
            plc_id=item['plc_id'],
            success=True,
            message=item['message'],
            pgm_id=item['pgm_id'],
            prev_pgm_id=item['prev_pgm_id']
        ))
    
    for item in result['failed']:
        results.append(BulkMappingResultItem(
            plc_id=item['plc_id'],
            success=False,
            message=item['message'],
            pgm_id=item.get('pgm_id'),
            prev_pgm_id=item.get('prev_pgm_id')
        ))
    
    if result['rolled_back']:
        message = f"에러 발생으로 인해 전체 롤백되었습니다. (실패: {failure_count}개)"
    elif failure_count == 0:
        message = f"모두 성공적으로 매핑 해제되었습니다. (성공: {success_count}개)"
    else:
        message = f"{total}개 중 {success_count}개 성공, {failure_count}개 실패"
    
    return BulkUnmapProgramResponse(
        total=total,
        success_count=success_count,
        failure_count=failure_count,
        results=results,
        message=message,
        rolled_back=result['rolled_back']
    )


@router.put("/plcs/mapping/bulk", response_model=BulkUpdateProgramResponse, status_code=status.HTTP_200_OK)
def bulk_update_program(
    request: BulkUpdateProgramRequest,
    plc_service: PlcService = Depends(get_plc_service)
):
    """
    복수 PLC의 프로그램 일괄 변경
    
    - **plc_ids**: 프로그램을 변경할 PLC ID 목록 (최대 100개)
    - **new_pgm_id**: 새로운 프로그램 ID
    - **user**: 작업자
    - **notes**: 비고 (선택)
    - **rollback_on_error**: 에러 시 전체 롤백 여부
    """
    logger.info(f"일괄 프로그램 변경 요청: plc_ids={request.plc_ids}, new_pgm_id={request.new_pgm_id}")
    
    result = plc_service.bulk_update_program_mapping(
        plc_ids=request.plc_ids,
        new_pgm_id=request.new_pgm_id,
        user=request.user,
        notes=request.notes,
        rollback_on_error=request.rollback_on_error
    )
    
    # 결과 변환
    success_count = len(result['success'])
    failure_count = len(result['failed'])
    total = success_count + failure_count
    
    results = []
    for item in result['success']:
        results.append(BulkMappingResultItem(
            plc_id=item['plc_id'],
            success=True,
            message=item['message'],
            pgm_id=item['pgm_id'],
            prev_pgm_id=item['prev_pgm_id']
        ))
    
    for item in result['failed']:
        results.append(BulkMappingResultItem(
            plc_id=item['plc_id'],
            success=False,
            message=item['message'],
            pgm_id=item.get('pgm_id'),
            prev_pgm_id=item.get('prev_pgm_id')
        ))
    
    if result['rolled_back']:
        message = f"에러 발생으로 인해 전체 롤백되었습니다. (실패: {failure_count}개)"
    elif failure_count == 0:
        message = f"모두 성공적으로 프로그램이 변경되었습니다. (성공: {success_count}개)"
    else:
        message = f"{total}개 중 {success_count}개 성공, {failure_count}개 실패"
    
    return BulkUpdateProgramResponse(
        total=total,
        success_count=success_count,
        failure_count=failure_count,
        new_pgm_id=request.new_pgm_id,
        results=results,
        message=message,
        rolled_back=result['rolled_back']
    )
