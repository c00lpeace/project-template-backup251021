# 📋 PLC 프로그램 생성 프로세스 상세 설계

## ✨ 최근 변경사항

### 2025-11-05 21:45 - Phase 2 구현 완료 🎉 (수요일 밤 9시 45분)
- ✅ **program_upload_service.py 구현 완료** - 전체 워크플로우 통합 서비스
- ✅ **POST /programs/upload 엔드포인트 추가** - 파일 업로드 API 구현
- ✅ **파일 검증 로직 구현** - 템플릿 Logic ID vs ZIP 파일 비교
- ✅ **불필요한 파일 자동 제거** - 보안 및 데이터 정합성 강화
- ✅ **트랜잭션 관리 구현** - 롤백 및 파일 정리 포함
- ✅ **정상 작동 확인** - 실제 환경에서 테스트 완료
- ✅ **의존성 주입 완료** - dependencies.py 업데이트
- ✅ **Response 모델 완료** - ValidationResult, ProgramUploadResponse 구현

### 2025-11-05 - Phase 1 구현 완료 (오전)
- ✅ PGM_ID 서버 자동 생성으로 변경 (PGM_1, PGM_2 형식)
- ✅ PROGRAMS 테이블에서 DOCUMENT_ID, LADDER_DOC_ID, TEMPLATE_DOC_ID 컬럼 제거
- ✅ 5단계에서 기존 create_program()만 사용 (별도 업데이트 제거)
- ✅ 시퀀스 테이블 기반 ID 생성 방식 채택
- ✅ sequence_models.py, sequence_crud.py, sequence_service.py 구현
- ✅ PROGRAM_SEQUENCE 테이블 생성 및 마이그레이션

---

## 🎯 개요

**목표**: 사용자가 ZIP(레더 파일)과 XLSX(템플릿 파일)를 업로드하면, 검증 후 프로그램을 생성하는 통합 워크플로우

**설계 원칙**:
- 기존 코드 재사용 최대화 (document_service, template_service, program_service)
- Layered Architecture 준수 (Router → Service → CRUD → Model)
- 트랜잭션 안정성 보장 (원자성)
- 명확한 에러 핸들링

---

## 📐 아키텍처 설계

### 계층 구조
```
program_router.py
    ↓ (POST /programs/upload)
ProgramUploadService (✅ 완료)
    ↓
├─ SequenceService (✅ 완료 - PGM_ID 생성)
├─ DocumentService (ZIP 업로드)
├─ TemplateService (XLSX 파싱)
└─ ProgramService (프로그램 생성)
    ↓
PROGRAM_SEQUENCE, DOCUMENTS, PGM_TEMPLATE, PROGRAMS 테이블
```

### 파일 구조
```
ai_backend/
├── api/
│   ├── routers/
│   │   └── program_router.py         # ✅ 업로드 엔드포인트 추가 완료
│   │
│   └── services/
│       ├── program_upload_service.py  # ✅ 완료 (통합 로직)
│       ├── sequence_service.py        # ✅ 완료 (ID 생성)
│       ├── document_service.py        # ✅ 기존 (ZIP 업로드 재사용)
│       ├── template_service.py        # ✅ 기존 (XLSX 파싱 재사용)
│       └── program_service.py         # ✅ 기존 (프로그램 생성 재사용)
│
├── database/
│   ├── models/
│   │   └── sequence_models.py         # ✅ 완료 (PROGRAM_SEQUENCE 모델)
│   │
│   └── crud/
│       └── sequence_crud.py           # ✅ 완료 (CRUD 로직)
│
└── types/
    ├── request/
    │   └── program_request.py         # ✅ 완료 (ProgramUploadMetadata)
    └── response/
        └── program_response.py        # ✅ 완료 (ValidationResult, ProgramUploadResponse)
```

---

## 🆕 PROGRAM_SEQUENCE 테이블 설계

### 테이블 구조
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

### 모델 정의
```python
# ai_backend/database/models/sequence_models.py

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

### CRUD 메서드
```python
# ai_backend/database/crud/sequence_crud.py

from sqlalchemy.orm import Session
from sqlalchemy import select
from ai_backend.database.models.sequence_models import ProgramSequence

class SequenceCrud:
    """시퀀스 CRUD"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_next_pgm_id(self) -> str:
        """
        다음 프로그램 ID 생성 (트랜잭션 안전)
        
        Returns:
            str: 'PGM_1', 'PGM_2', 'PGM_3' 형식
        """
        # Row Lock으로 동시성 제어
        sequence = self.db.query(ProgramSequence).with_for_update().filter(
            ProgramSequence.id == 1
        ).first()
        
        if not sequence:
            # 시퀀스 레코드가 없으면 생성
            sequence = ProgramSequence(id=1, last_number=0)
            self.db.add(sequence)
            self.db.flush()
        
        # 번호 증가
        sequence.last_number += 1
        self.db.flush()
        
        # PGM_{숫자} 형식으로 반환
        return f"PGM_{sequence.last_number}"
    
    def get_current_number(self) -> int:
        """현재 시퀀스 번호 조회"""
        sequence = self.db.query(ProgramSequence).filter(
            ProgramSequence.id == 1
        ).first()
        
        return sequence.last_number if sequence else 0
```

### SequenceService
```python
# ai_backend/api/services/sequence_service.py

from sqlalchemy.orm import Session
from ai_backend.database.crud.sequence_crud import SequenceCrud

class SequenceService:
    """시퀀스 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sequence_crud = SequenceCrud(db)
    
    def generate_pgm_id(self) -> str:
        """
        새로운 프로그램 ID 생성
        
        Returns:
            str: 'PGM_1', 'PGM_2' 형식
        """
        return self.sequence_crud.generate_next_pgm_id()
    
    def get_current_number(self) -> int:
        """현재 시퀀스 번호 조회"""
        return self.sequence_crud.get_current_number()
```

---

## 🔄 프로세스 플로우

### **0단계: PGM_ID 자동 생성 (서버)**

#### 변경 사항
```diff
- # Before: 클라이언트가 PGM_ID 생성 → 서버가 검증
- pgm_id = request.pgm_id
- existing = program_crud.get_program_by_id(pgm_id)
- if existing:
-     raise HandledException(ResponseCode.PROGRAM_ALREADY_EXISTS)

+ # After: 서버가 자동 생성 (중복 걱정 없음)
+ pgm_id = sequence_service.generate_pgm_id()  # 예: PGM_1, PGM_2
```

#### 장점
```
✅ 데이터 일관성: 서버에서 생성하므로 중복 불가능
✅ 사용자 부담 감소: 클라이언트가 ID 생성 규칙을 몰라도 됨
✅ 보안: ID 생성 로직을 서버에서 통제
✅ 유지보수: ID 규칙 변경 시 서버만 수정
✅ 트랜잭션 안전성: Row Lock으로 동시성 제어
```

---

### **1단계: 파일 업로드**

#### API 엔드포인트
```python
# program_router.py

@router.post("/programs/upload", response_model=ProgramUploadResponse, status_code=201)
async def upload_program_files(
    pgm_name: str = Form(...),                  # 프로그램 명칭
    pgm_version: Optional[str] = Form(None),    # 버전
    description: Optional[str] = Form(None),    # 설명
    create_user: str = Form(...),               # 생성자
    notes: Optional[str] = Form(None),          # 비고
    
    ladder_zip: UploadFile = File(...),         # ZIP 파일 (레더)
    template_xlsx: UploadFile = File(...),      # XLSX 파일 (템플릿)
    
    program_upload_service: ProgramUploadService = Depends(get_program_upload_service)
):
    """
    PLC 프로그램 파일 업로드 및 생성
    
    ⭐ PGM_ID는 서버에서 자동 생성 (클라이언트 전달 불필요)
    
    - ladder_zip: 레더 CSV 파일들이 압축된 ZIP
    - template_xlsx: 필수 파일 목록이 기재된 템플릿 파일
    """
```

#### 변경 사항
```diff
- # Before: pgm_id를 Form 파라미터로 받음
- pgm_id: str = Form(...)

+ # After: pgm_id 파라미터 제거 (서버에서 자동 생성)
+ # 클라이언트는 pgm_name, files만 전달
```

#### 검증 사항
1. **파일 타입 검증**
   - `ladder_zip`: `.zip` 확장자만 허용
   - `template_xlsx`: `.xlsx` 확장자만 허용

2. **필수 파라미터 검증**
   - `pgm_name`, `create_user`: 필수
   - `pgm_id`: 제거됨 (서버 자동 생성)

---

### **2단계: 파일 검증 (핵심 로직)**

#### 검증 프로세스
```python
# program_upload_service.py

def validate_files(
    ladder_zip: UploadFile,
    template_xlsx: UploadFile,
    pgm_id: str  # 서버에서 생성된 ID
) -> Dict:
    """
    템플릿의 Logic ID와 ZIP 파일 목록 비교 검증
    
    Returns:
        {
            'required_files': List[str],      # 템플릿에 명시된 필수 파일
            'zip_files': List[str],           # ZIP 내부 파일 목록
            'matched_files': List[str],       # 일치하는 파일
            'missing_files': List[str],       # 누락된 파일
            'extra_files': List[str],         # 불필요한 파일
            'validation_passed': bool         # 검증 통과 여부
        }
    """
```

#### 구체적 검증 로직
```python
# Step 1: 템플릿 파일에서 필수 파일 목록 추출
def extract_required_files_from_template(template_xlsx: UploadFile, pgm_id: str) -> List[str]:
    """
    XLSX 템플릿 파일에서 Logic ID 컬럼을 읽어 필수 CSV 파일 목록 생성
    
    Logic ID 예시: "0000_11", "0001_11", "0002_11"
    변환 결과: ["0000_11.csv", "0001_11.csv", "0002_11.csv"]
    """
    import pandas as pd
    import io
    
    # 메모리에서 XLSX 읽기
    file_content = template_xlsx.file.read()
    template_xlsx.file.seek(0)  # 포인터 초기화
    
    df = pd.read_excel(io.BytesIO(file_content))
    
    # 필수 컬럼 확인
    if 'Logic ID' not in df.columns:
        raise HandledException(
            ResponseCode.REQUIRED_FIELD_MISSING,
            msg="템플릿 파일에 'Logic ID' 컬럼이 없습니다"
        )
    
    # Logic ID에서 필수 파일 목록 생성
    required_files = []
    for logic_id in df['Logic ID']:
        if pd.notna(logic_id):
            csv_filename = f"{str(logic_id).strip()}.csv"
            required_files.append(csv_filename)
    
    return list(set(required_files))  # 중복 제거


# Step 2: ZIP 파일 목록 추출
def extract_file_list_from_zip(ladder_zip: UploadFile) -> List[str]:
    """
    ZIP 파일 내부의 CSV 파일 목록 추출
    
    주의: 디렉토리는 제외, 파일명만 추출
    """
    import zipfile
    import io
    from pathlib import Path
    
    # 메모리에서 ZIP 읽기
    file_content = ladder_zip.file.read()
    ladder_zip.file.seek(0)  # 포인터 초기화
    
    zip_files = []
    with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_ref:
        for info in zip_ref.infolist():
            # 디렉토리 제외
            if not info.is_dir():
                # 파일명만 추출 (경로 제거)
                filename = Path(info.filename).name
                zip_files.append(filename)
    
    return zip_files


# Step 3: 파일 비교 및 검증
def compare_files(required_files: List[str], zip_files: List[str]) -> Dict:
    """
    필수 파일과 ZIP 파일 비교
    """
    required_set = set(required_files)
    zip_set = set(zip_files)
    
    matched = required_set & zip_set
    missing = required_set - zip_set
    extra = zip_set - required_set
    
    return {
        'required_files': list(required_set),
        'zip_files': list(zip_set),
        'matched_files': list(matched),
        'missing_files': list(missing),
        'extra_files': list(extra),
        'validation_passed': len(missing) == 0
    }
```

#### 검증 실패 처리
```python
if not validation_result['validation_passed']:
    # 누락 파일 목록 로깅
    logger.error(f"파일 검증 실패: pgm_id={pgm_id}, 누락 파일={validation_result['missing_files']}")
    
    # 에러 응답
    raise HandledException(
        ResponseCode.INVALID_DATA_FORMAT,
        msg=f"필수 파일이 누락되었습니다: {', '.join(validation_result['missing_files'])}"
    )
```

#### 불필요한 파일 제거 (검증 성공 시)
```python
if len(validation_result['extra_files']) > 0:
    logger.info(f"불필요한 파일 제거 예정: {validation_result['extra_files']}")
    # ZIP 파일을 재생성 (필수 파일만 포함)
    filtered_zip_bytes = filter_zip_files(
        ladder_zip,
        keep_files=validation_result['matched_files']
    )
```

```python
def filter_zip_files(ladder_zip: UploadFile, keep_files: List[str]) -> bytes:
    """
    ZIP에서 필요한 파일만 남기고 새로운 ZIP 생성
    """
    import zipfile
    import io
    from pathlib import Path
    
    # 원본 ZIP 읽기
    original_content = ladder_zip.file.read()
    ladder_zip.file.seek(0)
    
    # 새로운 ZIP 생성
    filtered_buffer = io.BytesIO()
    
    with zipfile.ZipFile(io.BytesIO(original_content), 'r') as original_zip:
        with zipfile.ZipFile(filtered_buffer, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            for info in original_zip.infolist():
                if not info.is_dir():
                    filename = Path(info.filename).name
                    if filename in keep_files:
                        # 필요한 파일만 복사
                        new_zip.writestr(info, original_zip.read(info.filename))
    
    filtered_buffer.seek(0)
    return filtered_buffer.read()
```

---

### **3단계: 파일 저장**

#### 저장 경로 구조
```
{upload_base_path}/
  └─ {pgm_id}/                # 예: PGM_1, PGM_2
      ├─ ladder_files/        # 레더 CSV 파일들 (ZIP 압축 해제)
      │   ├─ 0000_11.csv
      │   ├─ 0001_11.csv
      │   └─ 0002_11.csv
      │
      ├─ template/            # 템플릿 XLSX 파일
      │   └─ program_template.xlsx
      │
      └─ zip/                 # 원본 ZIP (선택사항)
          └─ ladder_files.zip
```

#### 파일 저장 로직
```python
# program_upload_service.py

def save_files(
    ladder_zip_bytes: bytes,      # 필터링된 ZIP
    template_xlsx: UploadFile,
    pgm_id: str,                  # 서버에서 자동 생성된 ID (예: PGM_1)
    user_id: str
) -> Dict:
    """
    검증된 파일들을 지정된 경로에 저장
    """
    
    # 1. 레더 파일 저장 (ZIP 압축 해제)
    # 기존 document_service.upload_zip_document() 재사용
    ladder_result = document_service.upload_zip_document(
        file=ladder_zip_bytes,  # 필터링된 ZIP
        pgm_id=pgm_id,          # ⭐ 서버 자동 생성 ID
        user_id=user_id,
        is_public=False,
        keep_zip_file=True      # 원본 ZIP도 저장
    )
    
    # 2. 템플릿 파일 저장
    # 기존 document_service.upload_document() 재사용
    template_result = document_service.upload_document(
        file=template_xlsx,
        user_id=user_id,
        is_public=False,
        document_type='plc_template',  # ⭐ 템플릿 타입
        metadata={'pgm_id': pgm_id}    # pgm_id 메타데이터
    )
    
    return {
        'ladder_files': ladder_result,
        'template_file': template_result
    }
```

**참고**: 
- `upload_zip_document()`는 자동으로 `DOCUMENTS` 테이블에 등록
- `document_type='plc_template'`이면 자동으로 `PGM_TEMPLATE` 테이블에도 파싱/저장

---

### **4단계: DOCUMENTS 테이블 등록**

#### 자동 등록 (3단계에서 처리됨)

**레더 CSV 파일들**:
```sql
-- document_service.save_extracted_file_to_db()에서 자동 생성

INSERT INTO DOCUMENTS (
    DOCUMENT_ID,
    DOCUMENT_NAME,
    ORIGINAL_FILENAME,
    FILE_KEY,
    UPLOAD_PATH,
    FILE_SIZE,
    FILE_TYPE,
    FILE_EXTENSION,
    DOCUMENT_TYPE,        -- 'PGM_LADDER_CSV' ⭐
    PGM_ID,               -- 'PGM_1' ⭐ (서버 자동 생성)
    USER_ID,
    IS_PUBLIC,
    METADATA_JSON,        -- {"extracted_from_zip": true, "original_zip_path": "0000_11.csv"}
    CREATE_DT,
    IS_DELETED
) VALUES (
    'doc_20251105_143022_a1b2c3d4',
    '0000_11.csv',
    '0000_11.csv',
    'PGM_1/ladder_files/0000_11.csv',
    '/uploads/PGM_1/ladder_files/0000_11.csv',
    2048,
    'text/csv',
    'csv',
    'PGM_LADDER_CSV',
    'PGM_1',
    'admin',
    FALSE,
    '{"extracted_from_zip": true, "original_zip_path": "0000_11.csv"}',
    NOW(),
    FALSE
);
```

**템플릿 XLSX 파일**:
```sql
-- document_service.upload_document()에서 자동 생성

INSERT INTO DOCUMENTS (
    DOCUMENT_ID,
    DOCUMENT_NAME,
    ORIGINAL_FILENAME,
    FILE_KEY,
    UPLOAD_PATH,
    FILE_SIZE,
    FILE_TYPE,
    FILE_EXTENSION,
    DOCUMENT_TYPE,        -- 'plc_template' ⭐
    PGM_ID,               -- 'PGM_1' ⭐ (서버 자동 생성)
    USER_ID,
    IS_PUBLIC,
    METADATA_JSON,
    CREATE_DT,
    IS_DELETED
) VALUES (
    'doc_20251105_143030_b2c3d4e5',
    'program_template.xlsx',
    'program_template.xlsx',
    'PGM_1/template/program_template.xlsx',
    '/uploads/PGM_1/template/program_template.xlsx',
    10240,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xlsx',
    'plc_template',
    'PGM_1',
    'admin',
    FALSE,
    '{"pgm_id": "PGM_1", "template_parse_result": {...}}',
    NOW(),
    FALSE
);
```

---

### **5단계: PROGRAMS 테이블 등록 (변경됨)**

#### 변경 사항
```diff
- # Before: create_program() + update_program() 호출
- program = program_service.create_program(...)
- program_crud.update_program(
-     pgm_id=pgm_id,
-     update_data={'document_id': template_document_id}  # DOCUMENT_ID 업데이트
- )

+ # After: create_program()만 호출 (DOCUMENT_ID 컬럼 제거됨)
+ program = program_service.create_program(
+     pgm_id=pgm_id,
+     pgm_name=pgm_name,
+     pgm_version=pgm_version,
+     description=description,
+     create_user=create_user,
+     notes=notes
+ )
```

#### 프로그램 생성 (단순화)
```python
# program_upload_service.py

def create_program_record(
    pgm_id: str,                  # 서버에서 자동 생성된 ID (예: PGM_1)
    pgm_name: str,
    pgm_version: Optional[str],
    description: Optional[str],
    create_user: str,
    notes: Optional[str]
) -> Program:
    """
    PROGRAMS 테이블에 프로그램 레코드 생성
    
    ⭐ 기존 program_service.create_program()만 사용
    ⭐ DOCUMENT_ID 컬럼 제거로 인해 추가 업데이트 불필요
    """
    
    # 기존 program_service.create_program() 재사용
    program = program_service.create_program(
        pgm_id=pgm_id,          # ⭐ 서버 자동 생성 ID
        pgm_name=pgm_name,
        pgm_version=pgm_version,
        description=description,
        create_user=create_user,
        notes=notes
    )
    
    # ❌ 제거됨: DOCUMENT_ID 업데이트 (컬럼이 제거되었으므로)
    # program_crud.update_program(
    #     pgm_id=pgm_id,
    #     update_data={'document_id': template_document_id}
    # )
    
    return program
```

#### PROGRAMS 테이블 구조 (변경됨)
```diff
PROGRAMS 테이블:
├─ PGM_ID (PK)
├─ PGM_NAME
├─ PGM_VERSION
├─ DESCRIPTION
├─ CREATE_DT
├─ CREATE_USER
├─ NOTES
- ├─ DOCUMENT_ID          # ❌ 제거됨
- ├─ LADDER_DOC_ID        # ❌ 제거됨
- └─ TEMPLATE_DOC_ID      # ❌ 제거됨
```

#### 문서 조회 방식 (역참조)
```python
# 프로그램의 템플릿 파일 조회
template_docs = document_crud.get_documents_by_pgm_id_and_type(
    pgm_id='PGM_1',
    document_type='plc_template'
)

# 프로그램의 레더 파일들 조회
ladder_docs = document_crud.get_documents_by_pgm_id_and_type(
    pgm_id='PGM_1',
    document_type='PGM_LADDER_CSV'
)
```

```sql
-- SQL로 직접 조회
SELECT * FROM DOCUMENTS 
WHERE PGM_ID = 'PGM_1' AND DOCUMENT_TYPE = 'plc_template';

SELECT * FROM DOCUMENTS 
WHERE PGM_ID = 'PGM_1' AND DOCUMENT_TYPE = 'PGM_LADDER_CSV';
```

---

## 🔧 서비스 클래스 설계

### ProgramUploadService (신규)

```python
# ai_backend/api/services/program_upload_service.py

class ProgramUploadService:
    """
    프로그램 파일 업로드 통합 서비스
    """
    
    def __init__(
        self,
        db: Session,
        sequence_service: SequenceService,      # ⭐ 추가됨
        document_service: DocumentService,
        template_service: TemplateService,
        program_service: ProgramService
    ):
        self.db = db
        self.sequence_service = sequence_service  # ⭐ 추가됨
        self.document_service = document_service
        self.template_service = template_service
        self.program_service = program_service
        self.program_crud = ProgramCrud(db)
    
    def upload_and_create_program(
        self,
        pgm_name: str,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        create_user: str,
        pgm_version: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        프로그램 파일 업로드 및 생성 (전체 워크플로우)
        
        트랜잭션 관리:
        - 모든 단계가 성공해야 커밋
        - 하나라도 실패하면 롤백
        """
        try:
            # 0. ⭐ PGM_ID 자동 생성 (서버)
            pgm_id = self.sequence_service.generate_pgm_id()
            logger.info(f"[Step 0] PGM_ID 자동 생성: {pgm_id}")
            
            # 1. 파일 타입 검증
            self._validate_file_types(ladder_zip, template_xlsx)
            
            # 2. 파일 검증 (Logic ID vs ZIP 파일 목록)
            validation_result = self._validate_files(
                ladder_zip, template_xlsx, pgm_id
            )
            
            # 3. 검증 실패 시 에러
            if not validation_result['validation_passed']:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"필수 파일 누락: {', '.join(validation_result['missing_files'])}"
                )
            
            # 4. 불필요한 파일 제거 (검증 통과 시)
            filtered_zip_bytes = self._filter_unnecessary_files(
                ladder_zip,
                validation_result['matched_files']
            )
            
            # 5. 파일 저장 (DOCUMENTS 테이블 자동 등록)
            save_result = self._save_files(
                filtered_zip_bytes,
                template_xlsx,
                pgm_id,      # ⭐ 자동 생성된 ID
                create_user
            )
            
            # 6. ⭐ 프로그램 생성 (단순화: create_program()만 호출)
            program = self.program_service.create_program(
                pgm_id=pgm_id,          # ⭐ 자동 생성된 ID
                pgm_name=pgm_name,
                pgm_version=pgm_version,
                description=description,
                create_user=create_user,
                notes=notes
            )
            
            # 7. 커밋
            self.db.commit()
            logger.info(f"[Success] 프로그램 생성 완료: pgm_id={pgm_id}")
            
            # 8. 결과 반환
            return {
                'program': program,
                'pgm_id': pgm_id,       # ⭐ 자동 생성된 ID 반환
                'validation_result': validation_result,
                'saved_files': save_result,
                'message': '프로그램이 성공적으로 생성되었습니다'
            }
            
        except Exception as e:
            # 롤백
            self.db.rollback()
            logger.error(f"프로그램 업로드 실패: {str(e)}")
            
            # 저장된 파일 삭제
            if 'save_result' in locals():
                self._cleanup_saved_files(save_result)
            
            raise
    
    # ❌ 제거됨: _validate_program_id() 메서드 (서버 자동 생성으로 불필요)
    
    def _validate_file_types(self, ladder_zip: UploadFile, template_xlsx: UploadFile):
        """파일 타입 검증"""
        if not ladder_zip.filename.endswith('.zip'):
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="레더 파일은 .zip 형식이어야 합니다"
            )
        
        if not template_xlsx.filename.endswith('.xlsx'):
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="템플릿 파일은 .xlsx 형식이어야 합니다"
            )
    
    def _validate_files(
        self,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        pgm_id: str
    ) -> Dict:
        """파일 검증 (Logic ID vs ZIP 파일 목록)"""
        # 템플릿에서 필수 파일 추출
        required_files = self._extract_required_files_from_template(
            template_xlsx, pgm_id
        )
        
        # ZIP에서 파일 목록 추출
        zip_files = self._extract_file_list_from_zip(ladder_zip)
        
        # 파일 비교
        return self._compare_files(required_files, zip_files)
    
    def _extract_required_files_from_template(
        self,
        template_xlsx: UploadFile,
        pgm_id: str
    ) -> List[str]:
        """템플릿에서 Logic ID 기반 필수 파일 목록 추출"""
        # (위에서 작성한 로직 사용)
        pass
    
    def _extract_file_list_from_zip(self, ladder_zip: UploadFile) -> List[str]:
        """ZIP에서 파일 목록 추출"""
        # (위에서 작성한 로직 사용)
        pass
    
    def _compare_files(
        self,
        required_files: List[str],
        zip_files: List[str]
    ) -> Dict:
        """파일 비교"""
        # (위에서 작성한 로직 사용)
        pass
    
    def _filter_unnecessary_files(
        self,
        ladder_zip: UploadFile,
        keep_files: List[str]
    ) -> bytes:
        """불필요한 파일 제거"""
        # (위에서 작성한 로직 사용)
        pass
    
    def _save_files(
        self,
        filtered_zip_bytes: bytes,
        template_xlsx: UploadFile,
        pgm_id: str,
        user_id: str
    ) -> Dict:
        """파일 저장"""
        # (위에서 작성한 로직 사용)
        pass
    
    def _cleanup_saved_files(self, save_result: Dict):
        """저장된 파일 삭제 (롤백 시)"""
        # 파일 시스템에서 파일 삭제
        pass
```

---

## 📝 Request/Response 모델

### Request
```python
# ai_backend/types/request/program_upload_request.py

from pydantic import BaseModel, Field
from typing import Optional

class ProgramUploadMetadata(BaseModel):
    """프로그램 메타데이터"""
    pgm_name: str = Field(..., description="프로그램 명칭")
    pgm_version: Optional[str] = Field(None, description="버전")
    description: Optional[str] = Field(None, description="설명")
    create_user: str = Field(..., description="생성자")
    notes: Optional[str] = Field(None, description="비고")
    
    # ❌ 제거됨: pgm_id (서버에서 자동 생성)
```

### Response
```python
# ai_backend/types/response/program_upload_response.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class ValidationResult(BaseModel):
    """파일 검증 결과"""
    required_files: List[str]
    zip_files: List[str]
    matched_files: List[str]
    missing_files: List[str]
    extra_files: List[str]
    validation_passed: bool

class SavedFileInfo(BaseModel):
    """저장된 파일 정보"""
    document_id: str
    document_name: str
    file_type: str
    file_size: int
    upload_path: str

class ProgramUploadResponse(BaseModel):
    """프로그램 업로드 응답"""
    
    # ⭐ 생성된 프로그램 정보 (pgm_id 추가됨)
    pgm_id: str                               # ⭐ 서버에서 자동 생성된 ID
    pgm_name: str
    pgm_version: Optional[str]
    description: Optional[str]
    create_user: str
    create_dt: datetime
    
    # 검증 결과
    validation_result: ValidationResult
    
    # 저장된 파일들
    saved_files: Dict[str, SavedFileInfo]
    
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
```

---

## 🔐 트랜잭션 관리

### 전체 워크플로우를 하나의 트랜잭션으로
```python
def upload_and_create_program(...):
    try:
        # 0. PGM_ID 자동 생성 (트랜잭션 포함)
        pgm_id = sequence_service.generate_pgm_id()
        
        # 1-6. 모든 단계 수행
        # ...
        
        # 모두 성공 시 커밋
        self.db.commit()
        
    except Exception as e:
        # 하나라도 실패 시 롤백
        self.db.rollback()
        
        # 파일 삭제
        self._cleanup_saved_files(save_result)
        
        raise
```

### 파일 저장 실패 시 롤백 전략
```python
# DB 롤백 + 파일 삭제 (권장)
try:
    # 파일 저장
    save_result = self._save_files(...)
    
    # DB 저장
    program = self.program_service.create_program(...)
    
    self.db.commit()
    
except Exception as e:
    self.db.rollback()
    
    # 저장된 파일 삭제
    self._cleanup_saved_files(save_result)
    
    raise
```

---

## 🚨 에러 핸들링

### 주요 에러 케이스

| 단계 | 에러 상황 | ResponseCode | 처리 방법 |
|------|-----------|--------------|-----------|
| 0 | 시퀀스 생성 실패 | UNDEFINED_ERROR | 즉시 중단 + 에러 로그 |
| 1 | 파일 타입 불일치 | DOCUMENT_INVALID_FILE_TYPE | 즉시 중단 |
| 2 | 필수 파일 누락 | INVALID_DATA_FORMAT | 즉시 중단 + 누락 파일 목록 |
| 2 | 템플릿 파싱 실패 | INVALID_DATA_FORMAT | 즉시 중단 + 상세 에러 |
| 3 | ZIP 압축 해제 실패 | DOCUMENT_UPLOAD_ERROR | 롤백 + 에러 로그 |
| 4 | DOCUMENTS 등록 실패 | DOCUMENT_UPLOAD_ERROR | 롤백 + 파일 삭제 |
| 5 | PROGRAMS 등록 실패 | UNDEFINED_ERROR | 롤백 + 파일 삭제 |

---

## 📊 데이터베이스 구조

### 최종 데이터 구조 (성공 시)

```
PROGRAM_SEQUENCE 테이블:
┌────┬─────────────┬────────────┐
│ ID │ LAST_NUMBER │ UPDATE_DT  │
├────┼─────────────┼────────────┤
│ 1  │ 3           │ 2025-11-05 │
└────┴─────────────┴────────────┘

PROGRAMS 테이블 (단순화됨):
┌─────────┬──────────────┬──────────┬────────────┐
│ PGM_ID  │ PGM_NAME     │ PGM_VER  │ CREATE_USER│
├─────────┼──────────────┼──────────┼────────────┤
│ PGM_1   │ Test Prog 1  │ v1.0     │ admin      │
│ PGM_2   │ Test Prog 2  │ v1.1     │ user1      │
│ PGM_3   │ Test Prog 3  │ v2.0     │ admin      │
└─────────┴──────────────┴──────────┴────────────┘
                             │
                             │ (역참조)
                             ▼
DOCUMENTS 테이블 (템플릿):
┌──────────────┬────────────────────┬──────────────┬────────┐
│ DOCUMENT_ID  │ DOCUMENT_NAME      │ DOCUMENT_TYPE│ PGM_ID │
├──────────────┼────────────────────┼──────────────┼────────┤
│ doc_xxx_xxx  │ template.xlsx      │ plc_template │ PGM_1  │
│ doc_yyy_yyy  │ template.xlsx      │ plc_template │ PGM_2  │
└──────────────┴────────────────────┴──────────────┴────────┘

DOCUMENTS 테이블 (레더 파일들):
┌──────────────┬────────────────┬────────────────┬────────┐
│ DOCUMENT_ID  │ DOCUMENT_NAME  │ DOCUMENT_TYPE  │ PGM_ID │
├──────────────┼────────────────┼────────────────┼────────┤
│ doc_aaa_aaa  │ 0000_11.csv    │ PGM_LADDER_CSV │ PGM_1  │
│ doc_bbb_bbb  │ 0001_11.csv    │ PGM_LADDER_CSV │ PGM_1  │
│ doc_ccc_ccc  │ 0002_11.csv    │ PGM_LADDER_CSV │ PGM_1  │
└──────────────┴────────────────┴────────────────┴────────┘

PGM_TEMPLATE 테이블:
┌─────────────┬────────┬───────────┬────────────┬──────────┐
│ DOCUMENT_ID │ PGM_ID │ FOLDER_ID │ LOGIC_ID   │ LOGIC_NAME│
├─────────────┼────────┼───────────┼────────────┼──────────┤
│ doc_xxx_xxx │ PGM_1  │ 0         │ 0000_11    │ Mode     │
│ doc_xxx_xxx │ PGM_1  │ 0         │ 0001_11    │ Input    │
│ doc_xxx_xxx │ PGM_1  │ 0         │ 0002_11    │ Interlock│
└─────────────┴────────┴───────────┴────────────┴──────────┘
```

---

## 🔍 주요 고려사항

### 1. **PGM_ID 생성 방식 (변경됨)**
- ✅ **서버 자동 생성 (PGM_1, PGM_2 형식)**
- ✅ 시퀀스 테이블 기반 (PROGRAM_SEQUENCE)
- ✅ Row Lock으로 동시성 제어
- ✅ 중복 불가능

### 2. **PROGRAMS 테이블 컬럼 (변경됨)**
- ❌ **제거됨**: DOCUMENT_ID, LADDER_DOC_ID, TEMPLATE_DOC_ID
- ✅ **역참조 사용**: DOCUMENTS.PGM_ID로 조회
- ✅ **인덱스 활용**: idx_pgm_id (이미 존재)

### 3. **트랜잭션 범위**
- ✅ **전체 워크플로우를 하나의 트랜잭션으로**
- PGM_ID 생성 → 파일 저장 → DB 저장 → 커밋
- 실패 시 파일 삭제 + DB 롤백

### 4. **파일 저장 순서**
1. ZIP 압축 해제 → 레더 파일 저장
2. 템플릿 파일 저장
3. 프로그램 레코드 생성

### 5. **에러 로깅**
```python
# 각 단계마다 상세 로그
logger.info(f"[Step 0] PGM_ID 자동 생성: {pgm_id}")
logger.info(f"[Step 1] 파일 타입 검증 시작: pgm_id={pgm_id}")
logger.info(f"[Step 2] 파일 검증 완료: matched={len(matched)}, missing={len(missing)}")
logger.error(f"[Step 3] 파일 저장 실패: {str(e)}")
```

---

## 📌 요약

### 핵심 설계 포인트
1. ✅ **PGM_ID 서버 자동 생성**: 시퀀스 테이블 기반 (PGM_1, PGM_2)
2. ✅ **PROGRAMS 테이블 단순화**: DOCUMENT_ID 등 외래키 컬럼 제거
3. ✅ **create_program()만 사용**: 별도 업데이트 제거
4. ✅ **기존 코드 재사용**: DocumentService, TemplateService, ProgramService
5. ✅ **새 서비스 추가**: ProgramUploadService (통합), SequenceService (ID 생성)
6. ✅ **검증 중심**: 템플릿 Logic ID vs ZIP 파일 목록
7. ✅ **트랜잭션 관리**: 전체 워크플로우 원자성 보장
8. ✅ **명확한 에러 핸들링**: 각 단계별 에러 정의

### 구현 우선순위
1. **1순위**: PROGRAM_SEQUENCE 테이블 + SequenceService 생성
2. **2순위**: ProgramUploadService._validate_files() (핵심 검증 로직)
3. **3순위**: ProgramUploadService.upload_and_create_program() (메인 워크플로우)
4. **4순위**: Request/Response 모델 정의
5. **5순위**: Router 엔드포인트 추가
6. **6순위**: 문서 업데이트

### API 요청/응답 예시
```python
# Request (Form Data)
{
    "pgm_name": "Test Program",
    "pgm_version": "v1.0",
    "description": "테스트 프로그램입니다",
    "create_user": "admin",
    "notes": "비고 사항",
    "ladder_zip": <binary>,
    "template_xlsx": <binary>
}

# Response
{
    "pgm_id": "PGM_1",              # ⭐ 서버 자동 생성
    "pgm_name": "Test Program",
    "pgm_version": "v1.0",
    "description": "테스트 프로그램입니다",
    "create_user": "admin",
    "create_dt": "2025-11-05T14:30:22",
    "validation_result": {
        "required_files": ["0000_11.csv", "0001_11.csv"],
        "zip_files": ["0000_11.csv", "0001_11.csv", "extra.csv"],
        "matched_files": ["0000_11.csv", "0001_11.csv"],
        "missing_files": [],
        "extra_files": ["extra.csv"],
        "validation_passed": true
    },
    "saved_files": {...},
    "summary": {
        "total_ladder_files": 2,
        "template_parsed": true,
        "template_row_count": 2
    },
    "message": "프로그램이 성공적으로 생성되었습니다"
}
```

---

이 설계를 바탕으로 코드 구현을 진행하시겠습니까? 추가로 궁금한 부분이나 수정이 필요한 부분이 있으시면 말씀해주세요! 🚀
