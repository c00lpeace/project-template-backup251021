# _*_ coding: utf-8 _*_
"""Database module with all models imported to register with Base."""

# Base를 먼저 import
from .base import Base, Database
from .models.chat_models import *
from .models.document_models import *
from .models.group_models import *
from .models.pgm_mapping_models import *
from .models.plc_models import *
from .models.program_models import *
from .models.pgm_mapping_models import *
from .models.template_models import *
from .models.sequence_models import *

# 모든 모델을 import하여 Base에 등록
from .models.user_models import *

__all__ = [
    "Base",
    "Database",
    "User",
    "Chat",
    "ChatMessage",
    "Document",
    "Group",
    "GroupMember",
    "PLCMaster",
    "Program",
    "PgmMappingHistory",
    "PgmMappingAction",
    "PgmTemplate",
    "ProgramSequence",
]
