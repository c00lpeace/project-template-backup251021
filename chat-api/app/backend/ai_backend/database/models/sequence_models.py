# _*_ coding: utf-8 _*_
"""Program Sequence models."""

from ai_backend.database.base import Base
from sqlalchemy import Column, Integer, DateTime, CheckConstraint
from sqlalchemy.sql.expression import func

__all__ = [
    "ProgramSequence",
]


class ProgramSequence(Base):
    """프로그램 ID 시퀀스 관리 테이블"""
    __tablename__ = "PROGRAM_SEQUENCE"
    
    id = Column('ID', Integer, primary_key=True, default=1)
    last_number = Column('LAST_NUMBER', Integer, nullable=False, default=0)
    update_dt = Column('UPDATE_DT', DateTime, nullable=True, onupdate=func.now(), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint('ID = 1', name='chk_single_row'),
    )
