# _*_ coding: utf-8 _*_
"""Template CRUD operations"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from ai_backend.database.models.template_models import PgmTemplate
import logging

logger = logging.getLogger(__name__)


class TemplateCrud:
    """PGM Template CRUD operations"""
    def __init__(self, db: Session):
        self.db = db
    
    def bulk_create(self, templates: List[Dict]) -> List[PgmTemplate]:
        """템플릿 일괄 생성
        
        Args:
            db: Database session
            templates: 템플릿 데이터 리스트
            
        Returns:
            생성된 PgmTemplate 객체 리스트
        """
        try:
            db_templates = [PgmTemplate(**data) for data in templates]
            self.db.add_all(db_templates)
            self.db.commit()
            logger.info(f"템플릿 {len(db_templates)}개 생성 완료")
            return db_templates
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 일괄 생성 실패: {e}")
            raise e
    
    
    def get_templates_by_pgm(
        self, 
        pgm_id: str
    ) -> List[PgmTemplate]:
        """프로그램별 템플릿 조회
        
        Args:
            db: Database session
            pgm_id: 프로그램 ID
            
        Returns:
            PgmTemplate 객체 리스트 (정렬됨)
        """
        return self.db.query(PgmTemplate)\
                 .filter(PgmTemplate.pgm_id == pgm_id)\
                 .order_by(
                     PgmTemplate.folder_id,
                     PgmTemplate.sub_folder_name,
                     PgmTemplate.logic_id
                 )\
                 .all()
    
    
    def get_templates_by_document(
        self,
        document_id: str
    ) -> List[PgmTemplate]:
        """문서별 템플릿 조회
        
        Args:
            db: Database session
            document_id: 문서 ID
            
        Returns:
            PgmTemplate 객체 리스트
        """
        return self.db.query(PgmTemplate)\
                 .filter(PgmTemplate.document_id == document_id)\
                 .order_by(
                     PgmTemplate.folder_id,
                     PgmTemplate.sub_folder_name,
                     PgmTemplate.logic_id
                 )\
                 .all()
    
    
    def get_template_by_id(
        self,
        template_id: int
    ) -> Optional[PgmTemplate]:
        """템플릿 ID로 조회
        
        Args:
            db: Database session
            template_id: 템플릿 ID
            
        Returns:
            PgmTemplate 객체 또는 None
        """
        return self.db.query(PgmTemplate)\
                 .filter(PgmTemplate.template_id == template_id)\
                 .first()
    
    
    def delete_by_pgm_id(self, pgm_id: str) -> int:
        """프로그램별 템플릿 삭제
        
        Args:
            db: Database session
            pgm_id: 프로그램 ID
            
        Returns:
            삭제된 행 수
        """
        try:
            deleted = self.db.query(PgmTemplate)\
                        .filter(PgmTemplate.pgm_id == pgm_id)\
                        .delete()
            self.db.commit()
            logger.info(f"프로그램 {pgm_id}의 템플릿 {deleted}개 삭제 완료")
            return deleted
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 삭제 실패: {e}")
            raise e
    
    
    def delete_by_document_id(self, document_id: str) -> int:
        """문서별 템플릿 삭제
        
        Args:
            db: Database session
            document_id: 문서 ID
            
        Returns:
            삭제된 행 수
        """
        try:
            deleted = self.db.query(PgmTemplate)\
                        .filter(PgmTemplate.document_id == document_id)\
                        .delete()
            self.db.commit()
            logger.info(f"문서 {document_id}의 템플릿 {deleted}개 삭제 완료")
            return deleted
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 삭제 실패: {e}")
            raise e
    
    
    def get_template_count_by_pgm(self, pgm_id: str) -> int:
        """프로그램별 템플릿 개수 조회
        
        Args:
            db: Database session
            pgm_id: 프로그램 ID
            
        Returns:
            템플릿 개수
        """
        return self.db.query(func.count(PgmTemplate.template_id))\
                 .filter(PgmTemplate.pgm_id == pgm_id)\
                 .scalar()
    
    
    def get_all_pgm_ids(db: Session) -> List[str]:
        """모든 프로그램 ID 목록 조회
        
        Args:
            db: Database session
            
        Returns:
            프로그램 ID 리스트 (중복 제거)
        """
        result = self.db.query(PgmTemplate.pgm_id)\
                   .distinct()\
                   .order_by(PgmTemplate.pgm_id)\
                   .all()
        return [row[0] for row in result]
    
    
    def search_templates(
        self,
        pgm_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        logic_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PgmTemplate]:
        """템플릿 검색
        
        Args:
            db: Database session
            pgm_id: 프로그램 ID (선택)
            folder_id: 폴더 ID (선택)
            logic_name: 로직명 (부분 검색, 선택)
            skip: 페이징 offset
            limit: 페이징 limit
            
        Returns:
            PgmTemplate 객체 리스트
        """
        query = self.db.query(PgmTemplate)
        
        if pgm_id:
            query = query.filter(PgmTemplate.pgm_id == pgm_id)
        
        if folder_id:
            query = query.filter(PgmTemplate.folder_id == folder_id)
        
        if logic_name:
            query = query.filter(PgmTemplate.logic_name.ilike(f"%{logic_name}%"))
        
        return query.order_by(
                    PgmTemplate.pgm_id,
                    PgmTemplate.folder_id,
                    PgmTemplate.logic_id
                )\
                .offset(skip)\
                .limit(limit)\
                .all()
