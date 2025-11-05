# 🗄️ Database Schema Reference

> **최종 업데이트:** 2025-11-05 22:00 (수요일 밤 10시) - Phase 2 완료 + PROGRAM_SEQUENCE 테이블 추가!  
> **목적:** 모든 테이블 구조와 관계를 한눈에 파악  
> **⭐ 중요:** 실제 코드 기준으로 작성됨

---

## 📊 테이블 목록

| 테이블명 | 설명 | 모델 파일 | 주요 용도 |
|---------|------|-----------|-----------|
| PLC_MASTER | PLC 마스터 정보 | plc_models.py | PLC 기본 정보 + 현재 매핑 상태 |
| PROGRAMS | 프로그램 마스터 | program_models.py | 프로그램 기본 정보 |
| **PROGRAM_SEQUENCE** ⭐ NEW | 프로그램 ID 시퀀스 | sequence_models.py | PGM_ID 자동 생성 |
| PGM_MAPPING_HISTORY | 매핑 변경 이력 | mapping_models.py | 모든 매핑 변경 감사 추적 |
| DOCUMENTS | 문서 정보 | shared_core/models.py ⭐ | 업로드된 파일 메타데이터 (ZIP 포함) |
| USERS | 사용자 정보 | user_models.py | 사용자 계정 |
| GROUPS | 그룹 정보 | group_models.py | 사용자 그룹 |
| GROUP_USERS | 그룹-사용자 매핑 | group_models.py | N:M 관계 |
| CHAT_HISTORY | 채팅 이력 | chat_models.py | LLM 대화 기록 |
| PGM_TEMPLATE | 프로그램 템플릿 | template_models.py | 프로그램 구조 템플릿 |
| DOCUMENT_CHUNKS | 문서 청크 | shared_core/models.py ⭐ | 문서 분할 데이터 |
| PROCESSING_JOBS | 처리 작업 | shared_core/models.py ⭐ | 문서 처리 작업 추적 |

---

## 1️⃣ PLC_MASTER ⭐ (업데이트됨 - 2025-10-17)

### SQLAlchemy 모델 (실제 코드 확인)
```python
# D:\project-template\chat-api\app\backend\ai_backend\database\models\plc_models.py

class PLCMaster(Base):
    __tablename__ = "PLC_MASTER"
    
    plc_id = Column('PLC_ID', String(50), primary_key=True)
    plant = Column('PLANT', String(100), nullable=False)
    process = Column('PROCESS', String(100), nullable=False)
    line = Column('LINE', String(100), nullable=False)
    equipment_group = Column('EQUIPMENT_GROUP', String(100), nullable=False)
    unit = Column('UNIT', String(100), nullable=False)
    plc_name = Column('PLC_NAME', String(200), nullable=False)
    
    # 프로그램 매핑
    pgm_id = Column('PGM_ID', String(50), nullable=True)
    pgm_mapping_dt = Column('PGM_MAPPING_DT', DateTime, nullable=True)
    pgm_mapping_user = Column('PGM_MAPPING_USER', String(50), nullable=True)
    
    # 메타데이터 ⭐ 실제 코드 확인됨
    is_active = Column('IS_ACTIVE', Boolean, nullable=False, server_default=true())
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    create_user = Column('CREATE_USER', String(50), nullable=True)  # ⭐ 존재!
    update_dt = Column('UPDATE_DT', DateTime, nullable=True)
    update_user = Column('UPDATE_USER', String(50), nullable=True)  # ⭐ 존재!
```

### 컬럼 설명
| 컬럼명 | 타입 | NULL | 설명 | 예시 |
|--------|------|------|------|------|
| PLC_ID | VARCHAR(50) | NOT NULL | PLC 고유 ID (PK) | "M1CFB01000" |
| PLANT | VARCHAR(100) | NOT NULL | Plant (계층 1단계) | "PLT1" |
| PROCESS | VARCHAR(100) | NOT NULL | 공정 (계층 2단계) | "PLT1-PRC1" |
| LINE | VARCHAR(100) | NOT NULL | Line (계층 3단계) | "PLT1-PRC1-LN1" |
| EQUIPMENT_GROUP | VARCHAR(100) | NOT NULL | 장비그룹 (계층 4단계) | "PLT1-PRC1-LN1-EQ1" |
| UNIT | VARCHAR(100) | NOT NULL | 호기 (계층 5단계) | "PLT1-PRC1-LN1-EQ1-U1" |
| PLC_NAME | VARCHAR(200) | NOT NULL | PLC 명칭 | "조립라인1 PLC" |
| PGM_ID | VARCHAR(50) | NULL | 현재 매핑된 프로그램 ID | "PGM00001" |
| PGM_MAPPING_DT | DATETIME | NULL | 마지막 매핑 일시 | 2025-10-17 10:30:00 |
| PGM_MAPPING_USER | VARCHAR(50) | NULL | 마지막 매핑 사용자 | "admin" |
| IS_ACTIVE | BOOLEAN | NOT NULL | 활성 상태 (삭제=FALSE) | TRUE |
| CREATE_DT | DATETIME | NOT NULL | 생성일시 | 2025-10-17 09:00:00 |
| **CREATE_USER** ⭐ | VARCHAR(50) | NULL | **생성자** | **"admin"** |
| UPDATE_DT | DATETIME | NULL | 수정일시 | 2025-10-17 10:30:00 |
| **UPDATE_USER** ⭐ | VARCHAR(50) | NULL | **수정자** | **"admin"** |

### 계층 구조 (Hierarchy) ⭐
```
PLC_MASTER의 5단계 계층:

1. PLANT          (예: "PLT1")
   ↓
2. PROCESS        (예: "PLT1-PRC1")
   ↓
3. LINE           (예: "PLT1-PRC1-LN1")
   ↓
4. EQUIPMENT_GROUP (예: "PLT1-PRC1-LN1-EQ1")
   ↓
5. UNIT           (예: "PLT1-PRC1-LN1-EQ1-U1")
   + PLC_ID       (예: "PLT1-PRC1-LN1-EQ1-U1-PLC01")
   + CREATE_USER  (예: "admin") ← /v1/plcs/tree에서 사용
```

---

## 2️⃣ PROGRAMS

### SQLAlchemy 모델
```python
class Program(Base):
    __tablename__ = "PROGRAMS"
    
    pgm_id = Column('PGM_ID', String(50), primary_key=True)
    pgm_name = Column('PGM_NAME', String(200), nullable=False)
    document_id = Column('DOCUMENT_ID', String(100), nullable=True)
    pgm_version = Column('PGM_VERSION', String(20), nullable=True)
    description = Column('DESCRIPTION', String(1000), nullable=True)
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    create_user = Column('CREATE_USER', String(50), nullable=True)
    update_dt = Column('UPDATE_DT', DateTime, nullable=True, onupdate=func.now())
    update_user = Column('UPDATE_USER', String(50), nullable=True)
    notes = Column('NOTES', String(1000), nullable=True)
```

---

## 3️⃣ PROGRAM_SEQUENCE ⭐ NEW (2025-11-05 Phase 1)

### 테이블 정의
```sql
CREATE TABLE PROGRAM_SEQUENCE (
    ID INT PRIMARY KEY DEFAULT 1,
    LAST_NUMBER INT NOT NULL DEFAULT 0,
    UPDATE_DT DATETIME DEFAULT NOW() ON UPDATE NOW(),
    CONSTRAINT chk_single_row CHECK (ID = 1)
) ENGINE=InnoDB;

-- 초기 데이터
INSERT INTO PROGRAM_SEQUENCE (ID, LAST_NUMBER) VALUES (1, 0);
```

### SQLAlchemy 모델 (sequence_models.py)
```python
from sqlalchemy import Column, Integer, DateTime, CheckConstraint
from sqlalchemy.sql import func
from ai_backend.database.base import Base

class ProgramSequence(Base):
    """프로그램 ID 시퀀스 관리 테이블"""
    __tablename__ = 'PROGRAM_SEQUENCE'
    
    id = Column('ID', Integer, primary_key=True, default=1)
    last_number = Column('LAST_NUMBER', Integer, nullable=False, default=0)
    update_dt = Column('UPDATE_DT', DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint('ID = 1', name='chk_single_row'),
    )
```

### 컬럼 설명
| 컬럼명 | 타입 | NULL | 설명 | 예시 |
|--------|------|------|------|------|
| ID | INT | NOT NULL | 시퀀스 ID (PK, 항상 1) | 1 |
| LAST_NUMBER | INT | NOT NULL | 마지막 생성된 번호 | 0, 1, 2, 3... |
| UPDATE_DT | DATETIME | NULL | 마지막 업데이트 시간 | 2025-11-05 14:30:00 |

### 특징
```
✅ 단일 행 테이블: CHECK 제약 조건으로 ID는 항상 1만 허용
✅ 트랜잭션 안전: Row Lock으로 동시성 제어
✅ 자동 생성: PGM_1, PGM_2, PGM_3 형식으로 ID 생성
✅ 시퀀스 관리: LAST_NUMBER 필드로 다음 번호 추적
```

### 사용 예시
```sql
-- 현재 시퀀스 번호 조회
SELECT LAST_NUMBER FROM PROGRAM_SEQUENCE WHERE ID = 1;
-- 결과: 3 (다음 생성될 ID는 PGM_4)

-- 다음 프로그램 ID 생성 (CRUD/Service에서 자동 처리)
UPDATE PROGRAM_SEQUENCE 
SET LAST_NUMBER = LAST_NUMBER + 1 
WHERE ID = 1;
-- LAST_NUMBER: 3 → 4

-- 생성된 PGM_ID: "PGM_4"
```

### 샘플 데이터
```sql
-- 초기 상태
INSERT INTO PROGRAM_SEQUENCE (ID, LAST_NUMBER) 
VALUES (1, 0);

-- 3개의 프로그램 생성 후
UPDATE PROGRAM_SEQUENCE 
SET LAST_NUMBER = 3 
WHERE ID = 1;

-- 결과
SELECT * FROM PROGRAM_SEQUENCE;
┌────┬─────────────┬─────────────────────┐
│ ID │ LAST_NUMBER │ UPDATE_DT           │
├────┼─────────────┼─────────────────────┤
│ 1  │ 3           │ 2025-11-05 14:30:00 │
└────┴─────────────┴─────────────────────┘
```

### 관련 코드
```python
# ai_backend/database/crud/sequence_crud.py
class SequenceCrud:
    def generate_next_pgm_id(self) -> str:
        """다음 프로그램 ID 생성 (트랜잭션 안전)"""
        # Row Lock으로 동시성 제어
        sequence = self.db.query(ProgramSequence).with_for_update().filter(
            ProgramSequence.id == 1
        ).first()
        
        if not sequence:
            sequence = ProgramSequence(id=1, last_number=0)
            self.db.add(sequence)
            self.db.flush()
        
        # 번호 증가
        sequence.last_number += 1
        self.db.flush()
        
        # PGM_{숫자} 형식으로 반환
        return f"PGM_{sequence.last_number}"
```

### 인덱스
```sql
PRIMARY KEY (ID)
CHECK CONSTRAINT chk_single_row (ID = 1)
```

---

## 4️⃣ PGM_MAPPING_HISTORY

### SQLAlchemy 모델
```python
class PgmMappingHistory(Base):
    __tablename__ = "PGM_MAPPING_HISTORY"
    
    history_id = Column('HISTORY_ID', Integer, primary_key=True, autoincrement=True)
    plc_id = Column('PLC_ID', String(50), nullable=False, index=True)
    pgm_id = Column('PGM_ID', String(50), nullable=True)
    
    action = Column('ACTION', String(20), nullable=False)
    action_dt = Column('ACTION_DT', DateTime, nullable=False, server_default=func.now(), index=True)
    action_user = Column('ACTION_USER', String(50), nullable=True)
    
    prev_pgm_id = Column('PREV_PGM_ID', String(50), nullable=True)
    notes = Column('NOTES', String(500), nullable=True)
```

### 액션 타입
| ACTION | 설명 | 시나리오 |
|--------|------|----------|
| CREATE | 최초 매핑 | PLC에 처음으로 프로그램 매핑 |
| UPDATE | 프로그램 변경 | 기존 프로그램을 다른 프로그램으로 변경 |
| DELETE | 매핑 해제 | PLC에서 프로그램 매핑 제거 |
| RESTORE | 매핑 복원 | 이전에 삭제된 매핑을 다시 복원 |

---

## 5️⃣ DOCUMENTS ⭐ (shared_core, 2025-11-05 업데이트)

### 테이블 정의
```sql
CREATE TABLE DOCUMENTS (
    DOCUMENT_ID VARCHAR(50) PRIMARY KEY,
    
    -- 기본 정보
    DOCUMENT_NAME VARCHAR(255) NOT NULL,        -- 파일명 ⭐
    ORIGINAL_FILENAME VARCHAR(255) NOT NULL,    -- 원본 파일명 ⭐
    
    -- 파일 정보
    FILE_KEY VARCHAR(255) NOT NULL,             -- 파일 키 ⭐
    FILE_SIZE INT NOT NULL,
    FILE_TYPE VARCHAR(100) NOT NULL,            -- MIME 타입 ⭐
    FILE_EXTENSION VARCHAR(10) NOT NULL,
    UPLOAD_PATH VARCHAR(500) NOT NULL,          -- 저장 경로 ⭐
    FILE_HASH VARCHAR(64),                      -- 해시값 (중복 방지)
    
    -- 사용자 정보
    USER_ID VARCHAR(50) NOT NULL,
    IS_PUBLIC BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 문서 타입
    DOCUMENT_TYPE VARCHAR(20) DEFAULT 'common', -- ⭐ 'PGM_LADDER_CSV', 'PGM_LADDER_ZIP' 등
    
    -- 프로그램 연결
    PGM_ID VARCHAR(50),                         -- ⭐ ZIP 업로드 시 사용
    
    -- 처리 상태
    STATUS VARCHAR(20) NOT NULL DEFAULT 'processing',
    TOTAL_PAGES INT DEFAULT 0,
    PROCESSED_PAGES INT DEFAULT 0,
    ERROR_MESSAGE TEXT,
    
    -- 벡터화 정보
    MILVUS_COLLECTION_NAME VARCHAR(255),
    VECTOR_COUNT INT DEFAULT 0,
    
    -- 문서 메타데이터
    LANGUAGE VARCHAR(10),
    AUTHOR VARCHAR(255),
    SUBJECT VARCHAR(500),
    
    -- JSON 필드
    METADATA_JSON JSON,                         -- ⭐ 추가 메타데이터
    PROCESSING_CONFIG JSON,
    PERMISSIONS JSON,                           -- 권한 리스트
    
    -- 시간 정보
    CREATE_DT DATETIME NOT NULL DEFAULT NOW(),
    UPDATED_AT DATETIME,
    PROCESSED_AT DATETIME,
    
    -- 삭제 플래그
    IS_DELETED BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 인덱스
    INDEX idx_user_id (USER_ID),
    INDEX idx_pgm_id (PGM_ID),
    INDEX idx_document_type (DOCUMENT_TYPE),
    INDEX idx_file_hash (FILE_HASH)
);
```

### SQLAlchemy 모델 (shared_core/models.py)
```python
class Document(Base):
    __tablename__ = "DOCUMENTS"
    
    # 기본 정보
    document_id = Column('DOCUMENT_ID', String(50), primary_key=True)
    document_name = Column('DOCUMENT_NAME', String(255), nullable=False)
    original_filename = Column('ORIGINAL_FILENAME', String(255), nullable=False)
    
    # 파일 정보
    file_key = Column('FILE_KEY', String(255), nullable=False)
    file_size = Column('FILE_SIZE', Integer, nullable=False)
    file_type = Column('FILE_TYPE', String(100), nullable=False)
    file_extension = Column('FILE_EXTENSION', String(10), nullable=False)
    upload_path = Column('UPLOAD_PATH', String(500), nullable=False)
    file_hash = Column('FILE_HASH', String(64), nullable=True)
    
    # 사용자 정보
    user_id = Column('USER_ID', String(50), nullable=False)
    is_public = Column('IS_PUBLIC', Boolean, nullable=False, server_default=false())
    
    # 문서 타입
    document_type = Column('DOCUMENT_TYPE', String(20), nullable=True, default='common')
    
    # 프로그램 연결
    pgm_id = Column('PGM_ID', String(50), nullable=True, index=True)
    
    # 처리 상태
    status = Column('STATUS', String(20), nullable=False, server_default='processing')
    total_pages = Column('TOTAL_PAGES', Integer, default=0, nullable=True)
    processed_pages = Column('PROCESSED_PAGES', Integer, default=0, nullable=True)
    error_message = Column('ERROR_MESSAGE', Text, nullable=True)
    
    # 벡터화 정보
    milvus_collection_name = Column('MILVUS_COLLECTION_NAME', String(255), nullable=True)
    vector_count = Column('VECTOR_COUNT', Integer, default=0, nullable=True)
    
    # 문서 메타데이터
    language = Column('LANGUAGE', String(10), nullable=True)
    author = Column('AUTHOR', String(255), nullable=True)
    subject = Column('SUBJECT', String(500), nullable=True)
    
    # JSON 필드
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    processing_config = Column('PROCESSING_CONFIG', JSON, nullable=True)
    permissions = Column('PERMISSIONS', JSON, nullable=True)
    
    # 시간 정보
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    updated_at = Column('UPDATED_AT', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    processed_at = Column('PROCESSED_AT', DateTime, nullable=True)
    
    # 삭제 플래그
    is_deleted = Column('IS_DELETED', Boolean, nullable=False, server_default=false())
```

### 컴럼 설명
| 컴럼명 | 타입 | NULL | 설명 | 예시 |
|--------|------|------|------|------|
| DOCUMENT_ID | VARCHAR(50) | NOT NULL | 문서 ID (PK) | "doc_20251105_143022_a1b2c3d4" |
| DOCUMENT_NAME ⭐ | VARCHAR(255) | NOT NULL | 파일명 | "file.txt" |
| ORIGINAL_FILENAME ⭐ | VARCHAR(255) | NOT NULL | 원본 파일명 | "file.txt" |
| FILE_KEY ⭐ | VARCHAR(255) | NOT NULL | 파일 키 | "PGM001/folder/file.txt" |
| FILE_SIZE | INT | NOT NULL | 파일 크기 (바이트) | 1024 |
| FILE_TYPE ⭐ | VARCHAR(100) | NOT NULL | MIME 타입 | "text/csv" |
| FILE_EXTENSION | VARCHAR(10) | NOT NULL | 확장자 | "csv" |
| UPLOAD_PATH ⭐ | VARCHAR(500) | NOT NULL | 저장 경로 | "/uploads/PGM001/folder/file.txt" |
| FILE_HASH | VARCHAR(64) | NULL | MD5 해시 | "a1b2c3d4e5f6..." |
| USER_ID | VARCHAR(50) | NOT NULL | 사용자 ID | "admin" |
| IS_PUBLIC | BOOLEAN | NOT NULL | 공개 여부 | FALSE |
| DOCUMENT_TYPE ⭐ | VARCHAR(20) | NULL | 문서 타입 | "PGM_LADDER_CSV" |
| PGM_ID ⭐ | VARCHAR(50) | NULL | 프로그램 ID | "PGM001" |
| STATUS | VARCHAR(20) | NOT NULL | 처리 상태 | "completed" |
| METADATA_JSON ⭐ | JSON | NULL | 추가 메타데이터 | {"extracted_from_zip": true} |
| CREATE_DT | DATETIME | NOT NULL | 생성일시 | 2025-11-05 14:30:00 |
| IS_DELETED | BOOLEAN | NOT NULL | 삭제 플래그 | FALSE |

### 유효한 document_type 목록
```python
TYPE_COMMON = 'common'
TYPE_TYPE1 = 'type1'
TYPE_TYPE2 = 'type2'
TYPE_ZIP = 'zip'
TYPE_PGM_TEMPLATE = 'pgm_template'
TYPE_PGM_LADDER_CSV = 'PGM_LADDER_CSV'    # ⭐ ZIP 추출 파일
TYPE_PGM_LADDER_ZIP = 'PGM_LADDER_ZIP'    # ⭐ 원본 ZIP 파일
```

### ZIP 업로드 시 데이터 예시
```sql
-- 원본 ZIP 파일
INSERT INTO DOCUMENTS VALUES (
    'doc_20251105_143022_a1b2c3d4',  -- document_id
    'archive.zip',                    -- document_name
    'archive.zip',                    -- original_filename
    'PGM001/zip/archive.zip',        -- file_key
    1048576,                          -- file_size (1MB)
    'application/zip',                -- file_type
    'zip',                            -- file_extension
    '/uploads/PGM001/zip/archive.zip', -- upload_path
    'a1b2c3d4e5f6...',               -- file_hash
    'admin',                          -- user_id
    FALSE,                            -- is_public
    'PGM_LADDER_ZIP',                -- document_type ⭐
    'PGM001',                        -- pgm_id ⭐
    'completed',                      -- status
    '{"is_original_zip": true}',     -- metadata_json ⭐
    NOW(),                           -- create_dt
    FALSE                            -- is_deleted
);

-- ZIP에서 추출한 파일
INSERT INTO DOCUMENTS VALUES (
    'doc_20251105_143023_b2c3d4e5',
    'file.txt',
    'file.txt',
    'PGM001/folder/file.txt',
    2048,
    'text/plain',
    'txt',
    '/uploads/PGM001/folder/file.txt',
    'b2c3d4e5f6g7...',
    'admin',
    FALSE,
    'PGM_LADDER_CSV',                -- document_type ⭐
    'PGM001',                        -- pgm_id ⭐
    'completed',
    '{"extracted_from_zip": true, "original_zip_path": "folder/file.txt"}', -- metadata_json ⭐
    NOW(),
    FALSE
);
```

### 주요 차이점 (2025-11-05 업데이트)
```
✅ 필드명 표준화: file_name → document_name, file_path → upload_path
✅ 신규 필드: original_filename, file_key, file_type
✅ document_type 고정값: PGM_LADDER_CSV, PGM_LADDER_ZIP
✅ pgm_id 필드로 ZIP 업로드 관리
✅ metadata_json에 ZIP 관련 정보 저장
```

**상세 문서:** `docs/ZIP_UPLOAD_CHANGES_20251105.md` 참조

---

## 6️⃣ PGM_TEMPLATE ⭐ NEW (2025-10-19)

### 테이블 정의
```sql
CREATE TABLE PGM_TEMPLATE (
    TEMPLATE_ID INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 문서 연결 (원본 Excel 파일)
    DOCUMENT_ID VARCHAR(100),
    
    -- 프로그램 참조
    PGM_ID VARCHAR(50) NOT NULL,
    
    -- 폴더 구조 (3단계 계층)
    FOLDER_ID VARCHAR(20) NOT NULL,
    FOLDER_NAME VARCHAR(200) NOT NULL,
    SUB_FOLDER_NAME VARCHAR(200),
    
    -- 로직 정보
    LOGIC_ID VARCHAR(20) NOT NULL,
    LOGIC_NAME VARCHAR(200) NOT NULL,
    
    -- 메타데이터
    CREATE_DT DATETIME NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50),
    
    -- 인덱스
    INDEX idx_document_id (DOCUMENT_ID),
    INDEX idx_pgm_id (PGM_ID),
    INDEX idx_folder_id (FOLDER_ID),
    INDEX idx_logic_id (LOGIC_ID),
    INDEX idx_pgm_folder_logic (PGM_ID, FOLDER_ID, LOGIC_ID)
);
```

### SQLAlchemy 모델
```python
class PgmTemplate(Base):
    __tablename__ = "PGM_TEMPLATE"
    
    template_id = Column('TEMPLATE_ID', Integer, primary_key=True, autoincrement=True)
    document_id = Column('DOCUMENT_ID', String(100), nullable=True)
    pgm_id = Column('PGM_ID', String(50), nullable=False)
    folder_id = Column('FOLDER_ID', String(20), nullable=False)
    folder_name = Column('FOLDER_NAME', String(200), nullable=False)
    sub_folder_name = Column('SUB_FOLDER_NAME', String(200), nullable=True)
    logic_id = Column('LOGIC_ID', String(20), nullable=False)
    logic_name = Column('LOGIC_NAME', String(200), nullable=False)
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    create_user = Column('CREATE_USER', String(50), nullable=True)
```

### 컬럼 설명
| 컬럼명 | 타입 | NULL | 설명 | 예시 |
|--------|------|------|------|------|
| TEMPLATE_ID | INT | NOT NULL | 템플릿 ID (PK, AUTO_INCREMENT) | 1, 2, 3... |
| DOCUMENT_ID | VARCHAR(100) | NULL | 원본 Excel 문서 ID | "doc-uuid-123" |
| PGM_ID | VARCHAR(50) | NOT NULL | 프로그램 ID (FK → PROGRAMS.PGM_ID) | "PGM001" |
| FOLDER_ID | VARCHAR(20) | NOT NULL | 폴더 ID | "0", "20", "40" |
| FOLDER_NAME | VARCHAR(200) | NOT NULL | 폴더 명칭 | "Unit01_Endplate Box Loader" |
| SUB_FOLDER_NAME | VARCHAR(200) | NULL | 서브 폴더 명칭 | "Assy11_Endplate Box Loader" |
| LOGIC_ID | VARCHAR(20) | NOT NULL | 로직 ID | "0000_11", "0001_11" |
| LOGIC_NAME | VARCHAR(200) | NOT NULL | 로직 명칭 | "Mode", "Input", "Interlock" |
| CREATE_DT | DATETIME | NOT NULL | 생성일시 | 2025-10-19 15:00:00 |
| CREATE_USER | VARCHAR(50) | NULL | 생성자 | "admin" |

### 샘플 데이터
```sql
INSERT INTO PGM_TEMPLATE VALUES
(1, 'doc-123', 'PGM001', '0', 'Unit01_Endplate Box Loader', 'Assy11_Endplate Box Loader', 
 '0000_11', 'Mode', '2025-10-19 15:00:00', 'admin'),
(2, 'doc-123', 'PGM001', '0', 'Unit01_Endplate Box Loader', 'Assy11_Endplate Box Loader', 
 '0001_11', 'Input', '2025-10-19 15:00:00', 'admin'),
(3, 'doc-123', 'PGM001', '0', 'Unit01_Endplate Box Loader', 'Assy11_Endplate Box Loader', 
 '0002_11', 'Interlock', '2025-10-19 15:00:00', 'admin');
```

### 계층 구조 (Hierarchy) ⭐
```
PGM_TEMPLATE의 3단계 계층:

1. FOLDER (Folder ID + Folder Name)
   ↓
2. SUB_FOLDER (Sub Folder Name)
   ↓
3. LOGIC (Logic ID + Logic Name)

예시:
PGM001
  └─ Folder: 0 "Unit01_Endplate Box Loader"
      └─ Sub Folder: "Assy11_Endplate Box Loader"
          ├─ Logic: 0000_11 "Mode"
          ├─ Logic: 0001_11 "Input"
          └─ Logic: 0002_11 "Interlock"
```

### 인덱스
```sql
PRIMARY KEY (TEMPLATE_ID)
INDEX idx_document_id (DOCUMENT_ID)
INDEX idx_pgm_id (PGM_ID)
INDEX idx_folder_id (FOLDER_ID)
INDEX idx_logic_id (LOGIC_ID)
INDEX idx_pgm_folder_logic (PGM_ID, FOLDER_ID, LOGIC_ID)
```

---

## 🔗 테이블 관계도

```
USERS ────┐
          │
          ├─── PLC_MASTER (CREATE_USER, UPDATE_USER) ⭐
          │         │
          │         ├─── PROGRAMS (PGM_ID)
          │         │        │
          │         │        └─── PROGRAM_SEQUENCE ⭐ (PGM_ID 자동 생성)
          │         │
          │         └─── PGM_MAPPING_HISTORY (PLC_ID)
          │
          └─── DOCUMENTS ──── PROGRAMS (DOCUMENT_ID)
```

---

## 🎯 데이터 흐름 예시

### ⭐ NEW: PLC 계층 구조 트리 조회 시나리오 (2025-10-17)
```
1. GET /v1/plcs/tree?is_active=true 요청

2. plc_service.get_plc_hierarchy(is_active=true) 호출
   → plc_service.get_plcs(is_active=true) 재사용
   
3. PLC_MASTER 조회
   SELECT * FROM PLC_MASTER
   WHERE IS_ACTIVE = TRUE
   ORDER BY PLANT, PROCESS, LINE, EQUIPMENT_GROUP, UNIT

4. 계층 구조 변환 (_build_hierarchy)
   {
     "PLT1": {
       "PLT1-PRC1": {
         "PLT1-PRC1-LN1": {
           "PLT1-PRC1-LN1-EQ1": [
             {
               "unit": "PLT1-PRC1-LN1-EQ1-U1",
               "plc_id": "...",
               "create_dt": "...",
               "user": "admin"  ← CREATE_USER 사용!
             }
           ]
         }
       }
     }
   }

5. Response 형식으로 변환 (_convert_to_response)
   → data: [Plant[Process[Line[EquipmentGroup[UnitData[]]]]]]
```

### ⭐ NEW: 프로그램 업로드 시나리오 (2025-11-05 Phase 2)
```
1. POST /programs/upload 요청
   - pgm_name, ladder_zip, template_xlsx

2. 0단계: PGM_ID 자동 생성
   → SequenceService.generate_pgm_id()
   → PROGRAM_SEQUENCE 테이블 업데이트
   SELECT * FROM PROGRAM_SEQUENCE WHERE ID = 1 FOR UPDATE;
   UPDATE PROGRAM_SEQUENCE SET LAST_NUMBER = LAST_NUMBER + 1 WHERE ID = 1;
   → 결과: "PGM_1", "PGM_2", "PGM_3" 형식

3. 1-2단계: 파일 검증
   - 템플릿에서 Logic ID 추출 → 필수 파일 목록 생성
   - ZIP에서 파일 목록 추출
   - 비교 → 누락/불필요 파일 확인

4. 3-4단계: 파일 저장
   - DOCUMENTS 테이블 등록 (자동)
   - PGM_TEMPLATE 테이블 파싱/저장 (자동)

5. 5단계: 프로그램 생성
   - PROGRAMS 테이블 등록
   - ⭐ PGM_ID는 0단계에서 생성된 ID 사용

6. 트랜잭션 커밋
   - 모든 단계 성공 → 커밋
   - 실패 시 → 롤백 + 파일 삭제
```

---

## 📝 중요 변경사항

### ⭐ 2025-11-05 Phase 2 완료
```diff
+ PROGRAM_SEQUENCE 테이블 추가
+ PGM_ID 서버 자동 생성 (PGM_1, PGM_2 형식)
+ 시퀀스 기반 ID 생성으로 중복 방지
+ Row Lock으로 동시성 제어
+ PROGRAMS 테이블 단순화 (DOCUMENT_ID 등 외래키 제거)
```

### ⭐ 2025-10-17 PLC_MASTER 테이블 구조 확인
```diff
✅ 실제 코드 확인 결과:
+ CREATE_USER VARCHAR(50)  # 실제 존재 (plc_models.py)
+ UPDATE_USER VARCHAR(50)  # 실제 존재 (plc_models.py)
```

**변경 사유:**
- 실제 코드(plc_models.py)를 확인하여 문서 현행화
- 다른 테이블(PROGRAMS, GROUPS)과의 일관성 확인
- PLC 계층 구조 트리 조회 API에서 user 필드로 활용

**영향:**
- ✅ PLC 생성 시 CREATE_USER 저장 가능
- ✅ PLC 수정 시 UPDATE_USER 저장 가능
- ✅ GET /v1/plcs/tree API의 unit_data.user 필드에 사용
- ✅ 감사 추적(Audit Trail) 기능 강화

---

**이 문서는 실제 코드를 기준으로 작성되었습니다!** 📚  
**파일 위치:** `D:\project-template\chat-api\app\backend\ai_backend\database\models\*`
