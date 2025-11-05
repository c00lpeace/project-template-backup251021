# _*_ coding: utf-8 _*_
"""Template Service - Excel 파싱 및 템플릿 관리"""
import pandas as pd
from typing import Dict, List
from sqlalchemy.orm import Session
from ai_backend.database.crud.template_crud import TemplateCrud
from ai_backend.database.crud.program_crud import ProgramCrud
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
from ai_backend.types.response.template_response import (
    TemplateTreeResponse, FolderInfo, SubFolderInfo, LogicInfo,
    TemplateListResponse, TemplateListItem, TemplateSummary
)
import logging

logger = logging.getLogger(__name__)


class TemplateService:
    """템플릿 서비스 - Excel 파싱 및 템플릿 관리"""
    
    def __init__(self, db: Session):
        self.db = db
        self.template_crud = TemplateCrud(db)
        self.program_crud = ProgramCrud(db)
    
    def parse_and_save(
        self,
        document_id: str,
        file_path: str,
        pgm_id: str,
        user_id: str
    ) -> Dict:
        """Excel 파일 파싱 및 PGM_TEMPLATE 테이블 저장
        
        Args:
            document_id: 문서 ID
            file_path: Excel 파일 경로
            pgm_id: 프로그램 ID
            user_id: 사용자 ID
            
        Returns:
            파싱 결과 딕셔너리
        """
        logger.info(f"템플릿 파싱 시작: pgm_id={pgm_id}, document_id={document_id}")
        
        # 1. 프로그램 ID 중복 체크
        existing = self.program_crud.get_program_by_id(pgm_id)
        if existing:
            raise HandledException(
                ResponseCode.PROGRAM_ALREADY_EXISTS,
                msg=f"프로그램 ID '{pgm_id}'가 이미 존재합니다"
            )
        
        # 2. Excel 파일 읽기
        try:
            df = pd.read_excel(file_path)
            logger.info(f"Excel 파일 읽기 완료: {len(df)}행")
        except Exception as e:
            logger.error(f"Excel 파일 읽기 실패: {e}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"Excel 파일을 읽을 수 없습니다: {str(e)}"
            )
        
        # 3. 필수 컬럼 검증
        required_columns = [
            'PGM ID', 'Folder ID', 'Folder Name',
            'Sub Folder Name', 'Logic ID', 'Logic Name'
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise HandledException(
                ResponseCode.REQUIRED_FIELD_MISSING,
                msg=f"필수 컬럼이 없습니다: {missing}"
            )
        
        # 4. 데이터 변환
        templates = []
        skipped_rows = 0
        
        for idx, row in df.iterrows():
            # # PGM ID 필터링 (엑셀에 여러 프로그램이 있을 수 있음)
            # row_pgm_id = str(row['PGM ID']).strip()
            # if row_pgm_id != pgm_id:
            #     skipped_rows += 1
            #     continue
            
            # 빈 행 스킵
            if pd.isna(row['Logic ID']) or pd.isna(row['Logic Name']):
                skipped_rows += 1
                continue
            
            templates.append({
                'document_id': document_id,
                'pgm_id': pgm_id,
                'folder_id': str(row['Folder ID']).strip(),
                'folder_name': str(row['Folder Name']).strip(),
                'sub_folder_name': str(row['Sub Folder Name']).strip() if pd.notna(row['Sub Folder Name']) else None,
                'logic_id': str(row['Logic ID']).strip(),
                'logic_name': str(row['Logic Name']).strip(),
                'create_user': user_id
            })
        
        if not templates:
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"엑셀에 {pgm_id}에 해당하는 유효한 데이터가 없습니다"
            )
        
        logger.info(f"데이터 변환 완료: {len(templates)}개 (스킵: {skipped_rows}개)")
        
        # 5. 기존 템플릿 삭제 (덮어쓰기)
        deleted_count = self.template_crud.delete_by_pgm_id(pgm_id)
        logger.info(f"기존 템플릿 삭제: {deleted_count}개")
        
        # 6. Bulk Insert
        created = self.template_crud.bulk_create(templates)
        logger.info(f"새 템플릿 생성: {len(created)}개")
        
        result = {
            'pgm_id': pgm_id,
            'document_id': document_id,
            'total_rows': len(df),
            'skipped_rows': skipped_rows,
            'deleted_count': deleted_count,
            'created_count': len(created)
        }
        
        logger.info(f"템플릿 파싱 완료: {result}")
        return result
    
    def get_template_tree(self, pgm_id: str) -> TemplateTreeResponse:
        """프로그램별 템플릿 트리 구조 조회
        
        Args:
            pgm_id: 프로그램 ID
            
        Returns:
            TemplateTreeResponse
        """
        logger.info(f"템플릿 트리 조회: pgm_id={pgm_id}")
        
        # 1. 템플릿 조회
        templates = self.template_crud.get_templates_by_pgm(pgm_id)
        
        if not templates:
            raise HandledException(
                status_code=404,
                error_code=ResponseCode.NOT_FOUND.code,
                message=f"프로그램 {pgm_id}의 템플릿을 찾을 수 없습니다"
            )
        
        # 2. 계층 구조 변환
        folders = self._build_template_hierarchy(templates)
        
        # 3. 문서 ID 추출 (첫 번째 템플릿에서)
        document_id = templates[0].document_id if templates else None
        
        response = TemplateTreeResponse(
            pgm_id=pgm_id,
            document_id=document_id,
            total_count=len(templates),
            folder_count=len(folders),
            folders=folders
        )
        
        logger.info(f"템플릿 트리 조회 완료: {len(templates)}개, {len(folders)}개 폴더")
        return response
    
    def _build_template_hierarchy(self, templates: List) -> List[FolderInfo]:
        """템플릿을 계층 구조로 변환
        
        Args:
            templates: PgmTemplate 객체 리스트
            
        Returns:
            FolderInfo 리스트
        """
        folder_dict = {}
        
        for t in templates:
            folder_id = t.folder_id
            sub_folder_name = t.sub_folder_name or "기본"
            
            # Folder 생성
            if folder_id not in folder_dict:
                folder_dict[folder_id] = {
                    'folder_id': folder_id,
                    'folder_name': t.folder_name,
                    'sub_folders': {}
                }
            
            # Sub Folder 생성
            if sub_folder_name not in folder_dict[folder_id]['sub_folders']:
                folder_dict[folder_id]['sub_folders'][sub_folder_name] = {
                    'sub_folder_name': sub_folder_name,
                    'logics': []
                }
            
            # Logic 추가
            folder_dict[folder_id]['sub_folders'][sub_folder_name]['logics'].append(
                LogicInfo(
                    logic_id=t.logic_id,
                    logic_name=t.logic_name
                )
            )
        
        # 딕셔너리 → FolderInfo 리스트 변환
        result = []
        for folder_data in folder_dict.values():
            sub_folders = []
            total_logic_count = 0
            
            for sub_folder_data in folder_data['sub_folders'].values():
                logic_count = len(sub_folder_data['logics'])
                total_logic_count += logic_count
                
                sub_folders.append(
                    SubFolderInfo(
                        sub_folder_name=sub_folder_data['sub_folder_name'],
                        logic_count=logic_count,
                        logics=sub_folder_data['logics']
                    )
                )
            
            result.append(
                FolderInfo(
                    folder_id=folder_data['folder_id'],
                    folder_name=folder_data['folder_name'],
                    sub_folder_count=len(sub_folders),
                    total_logic_count=total_logic_count,
                    sub_folders=sub_folders
                )
            )
        
        return result
    
    def get_template_list(
        self,
        pgm_id: str = None,
        folder_id: str = None,
        logic_name: str = None,
        page: int = 1,
        page_size: int = 100
    ) -> TemplateListResponse:
        """템플릿 목록 조회 (검색, 페이징)
        
        Args:
            pgm_id: 프로그램 ID (선택)
            folder_id: 폴더 ID (선택)
            logic_name: 로직명 검색어 (선택)
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지 크기
            
        Returns:
            TemplateListResponse
        """
        skip = (page - 1) * page_size
        
        templates = self.template_crud.search_templates(
            pgm_id=pgm_id,
            folder_id=folder_id,
            logic_name=logic_name,
            skip=skip,
            limit=page_size
        )
        
        # 전체 개수 조회 (필터링 적용)
        if pgm_id:
            total_count = self.template_crud.get_template_count_by_pgm(pgm_id)
        else:
            # 전체 개수 (필터 없을 때)
            from sqlalchemy import func
            from ai_backend.database.models.template_models import PgmTemplate
            total_count = self.db.query(func.count(PgmTemplate.template_id)).scalar()
        
        items = [TemplateListItem.model_validate(t) for t in templates]
        
        return TemplateListResponse(
            total_count=total_count,
            items=items,
            page=page,
            page_size=page_size
        )
    
    def delete_template(self, pgm_id: str) -> Dict:
        """프로그램별 템플릿 삭제
        
        Args:
            pgm_id: 프로그램 ID
            
        Returns:
            삭제 결과 딕셔너리
        """
        logger.info(f"템플릿 삭제 시작: pgm_id={pgm_id}")
        
        deleted_count = self.template_crud.delete_by_pgm_id(pgm_id)
        
        if deleted_count == 0:
            raise HandledException(
                status_code=404,
                error_code=ResponseCode.NOT_FOUND.code,
                message=f"프로그램 {pgm_id}의 템플릿을 찾을 수 없습니다"
            )
        
        logger.info(f"템플릿 삭제 완료: {deleted_count}개")
        
        return {
            'pgm_id': pgm_id,
            'deleted_count': deleted_count
        }
    
    def get_all_template_summary(self) -> List[TemplateSummary]:
        """모든 프로그램의 템플릿 요약 정보 조회
        
        Returns:
            TemplateSummary 리스트
        """
        pgm_ids = self.template_crud.get_all_pgm_ids(self.db)
        
        summaries = []
        for pgm_id in pgm_ids:
            templates = self.template_crud.get_templates_by_pgm(pgm_id)
            if not templates:
                continue
            
            # 폴더 개수 계산
            folder_ids = set(t.folder_id for t in templates)
            
            summaries.append(
                TemplateSummary(
                    pgm_id=pgm_id,
                    template_count=len(templates),
                    folder_count=len(folder_ids),
                    document_id=templates[0].document_id if templates else None,
                    create_dt=templates[0].create_dt if templates else None
                )
            )
        
        return summaries
