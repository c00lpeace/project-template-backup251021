# _*_ coding: utf-8 _*_
"""Program Master models."""

from ai_backend.database.base import Base
from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql.expression import func

__all__ = [
    "Program",
]


class Program(Base):
    """프로그램 마스터 테이블"""
    __tablename__ = "PROGRAMS"
    
    pgm_id = Column('PGM_ID', String(50), primary_key=True)
    pgm_name = Column('PGM_NAME', String(200), nullable=False)    
    pgm_version = Column('PGM_VERSION', String(20), nullable=True)
    description = Column('DESCRIPTION', String(1000), nullable=True)
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    create_user = Column('CREATE_USER', String(50), nullable=True)
    update_dt = Column('UPDATE_DT', DateTime, nullable=True, onupdate=func.now())
    update_user = Column('UPDATE_USER', String(50), nullable=True)
    notes = Column('NOTES', String(1000), nullable=True)
