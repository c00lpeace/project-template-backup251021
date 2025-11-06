# 🏗️ PLC-Program Mapping System - 프로젝트 참조 가이드

> **최종 업데이트:** 2025-11-06 (수요일) - Phase 2 완료! 🎉  
> **목적:** Claude가 매번 파일을 검색하지 않고 빠르게 프로젝트 구조를 파악하기 위한 참조 문서

---

## 📂 프로젝트 루트 경로
```
D:\project-template-backup251021\chat-api\app\backend\
```

---

## 🔗 shared_core 패키지 구조 ⭐ (2025-11-05)

### 위치
```
D:\project-template-backup251021\shared_core/
├── models.py         # Document, DocumentChunk, ProcessingJob 모델
├── crud.py          # DocumentCRUD, DocumentChunkCRUD, ProcessingJobCRUD
├── services.py      # DocumentService, DocumentChunkService, ProcessingJobService
├── database.py      # DatabaseManager (PostgreSQL 전용)
├── __init__.py
├── setup.py
└── requirements.txt
```

### Document 모델 핵심 필드 (DOCUMENTS 테이블)
```python
# shared_core/models.py
class Document(Base):
    __tablename__ = "DOCUMENTS"
    
    # ⭐ ZIP 업로드 관련 핵심 필드
    document_id        # PRIMARY KEY
    document_name      # 파일명 (⭐ file_name 아님!)
    original_filename  # 원본 파일명
    file_key           # 파일 키 (예: "PGM001/folder/file.txt")
    upload_path        # 실제 저장 경로 (⭐ file_path 아님!)
    file_type          # MIME 타입 (예: "text/csv")
    file_extension     # 확장자 (예: "csv")
    document_type      # 문서 타입 (예: "PGM_LADDER_CSV")
    pgm_id             # 프로그램 ID
    metadata_json      # JSON 메타데이터
```

### DocumentService 상속 관계 (Phase 2 리팩토링 완료 ⭐ NEW)
```python
# ai_backend/api/services/document_service.py
from shared_core import DocumentService as BaseDocumentService

class DocumentService(BaseDocumentService):
    """
    BaseDocumentService로부터 상속:
    - create_document_from_file(), get_document()
    - _get_file_extension(), _get_mime_type(), _calculate_file_hash()
    
    FastAPI 전용 확장 (Phase 2 리팩토링 완료):
    - create_ladder_csv_document()         # 레더 CSV 문서 레코드 생성
    - create_template_document()           # 템플릿 문서 레코드 생성 + 자동 프로세서 호출
    - bulk_create_ladder_csv_documents()   # 레더 CSV 일괄 생성
    - upload_document()                    # 레거시 메서드 (호환성 유지)
    
    제거된 메서드 (FileStorageService로 이동):
    - ❌ upload_zip_document()
    - ❌ _extract_and_save_each_files()
    - ❌ save_extracted_file_to_db()
    - ❌ _save_original_zip()
    """
```

**상세 정보:** `docs/SHARED_CORE_INTEGRATION_PLAN.md` 참조

---

## ✨ 최근 변경사항

### 2025-11-06 - Phase 1.5 완료 (레더 CSV 구조 검증 추가) ⭐ NEW

**요약:**
- 레더 CSV 파일 구조 검증 로직 추가
- 해결방안 C: ZIP을 두 번 열기 (구조 + 내용)
- 디스크 저장 전에 오류 조기 발견
- 환경변수 기반 검증 규칙

**수정된 파일:**
| 파일 | 경로 | 변경사항 |
|------|------|----------|
| `simple_settings.py` | `ai_backend/config/` | 환경변수 8개 추가 + 편의 메서드 1개 |
| `file_validation_service.py` | `ai_backend/api/services/` | 메서드 2개 추가 |
| `program_upload_service.py` | `ai_backend/api/services/` | Step 8 추가 |

**추가된 환경변수:**
```python
# 레더 CSV 구조 검증 설정
pgm_ladder_csv_required_columns: str = "Step No.,Line Statement,..."
pgm_ladder_csv_header_row: int = 2  # 0-based index
pgm_ladder_csv_validate_file_identifier: bool = True
pgm_ladder_csv_validate_module_info: bool = True
pgm_ladder_csv_module_info_prefix: str = "Module Type Information:"
pgm_ladder_csv_min_data_rows: int = 1
pgm_ladder_csv_encoding: str = "utf-8"
pgm_ladder_csv_structure_validation_enabled: bool = True

# 편의 메서드
get_pgm_ladder_csv_required_columns() -> list
```

**추가된 메서드:**
```python
# FileValidationService
validate_ladder_csv_structure_from_bytes(csv_bytes, filename) -> Dict
validate_matched_ladder_csv_structures_in_memory(ladder_zip_file, matched_files) -> Dict
```

**워크플로우 변경:**
```
Step 1-2: 레더 ZIP 타입/크기 검증
Step 3:   ZIP 구조 검증 (손상 여부, 파일 목록만)
Step 4-5: 템플릿 타입/크기 검증
Step 6:   템플릿 구조 검증 (필수 컬럼, Logic ID 추출)
Step 7:   매칭 검증 (템플릿 Logic ID vs ZIP 파일 목록)
Step 8:   매칭된 CSV만 구조 검증 (메모리) ⭐ 신규
Step 9:   레더 ZIP 필터링
Step 10:  레더 ZIP 저장 및 압축 해제
Step 11:  템플릿 파일 저장
Step 12:  레더 CSV 문서 레코드 일괄 생성
Step 13:  템플릿 문서 레코드 생성 + 자동 파싱
Step 14:  프로그램 레코드 생성
Step 15:  커밋
```

**특징:**
- 해결방안 C 구현: ZIP을 두 번 열기
- 메모리에서만 처리, 디스크 저장 전에 오류 발견
- 환경변수로 검증 on/off 제어
- chardet 라이브러리로 인코딩 자동 감지 (선택사항)
- 하나라도 실패하면 전체 업로드 중단

**작업 시간:** 2시간

**다음 단계:** 성능 최적화 (선택사항)

---

### 2025-11-06 - 리팩토링 Phase 5 완료 (레거시 코드 제거 및 정리) ⭐ NEW

**요약:**
- 사용하지 않는 import 제거 (4개 파일)
- 코드 스타일 통일 확인
- Phase 0-4 규칙 준수 최종 검토
- 문서 업데이트

**수정된 파일:**
| 파일 | 경로 | 변경사항 |
|------|------|----------|
| `document_service.py` | `ai_backend/api/services/` | 사용하지 않는 import 제거 (Path) |
| `program_upload_service.py` | `ai_backend/api/services/` | 사용하지 않는 import 제거 (pandas) |
| `program_router.py` | `ai_backend/api/routers/` | 최종 검토 완료 |
| `dependencies.py` | `ai_backend/core/` | 중복 import 제거 (get_redis_client) |

**제거된 import:**
```python
# document_service.py
❌ from pathlib import Path  # 사용 안 함

# program_upload_service.py
❌ import pandas as pd  # 사용 안 함

# dependencies.py
❌ from ai_backend.cache.redis_client import get_redis_client  # 중복
```

**최종 검토 결과:**
- ✅ 환경변수 사용 확인 (settings.pgm_ladder_csv_doctype 등)
- ✅ 명확한 변수명 확인 (pgm_ladder_zip_file, pgm_template_file)
- ✅ 새 서비스 통합 확인 (FileValidationService, FileStorageService)
- ✅ 새 메서드 사용 확인 (create_ladder_csv_document 등)
- ✅ 트랜잭션 경계 명확화 확인
- ✅ 로깅 메시지 일관성 확인 (✅, ❌, 🎉 이모지 사용)

**작업 시간:** 1시간

**다음 단계:** 성능 최적화 (선택사항)

---

### 2025-11-06 - 리팩토링 Phase 4 완료 (Router 및 Response 모델 업데이트) ⭐

**요약:**
- Router 파라미터명 변경 (명확한 이름)
- dependencies.py에 새 서비스 주입
- API 메서드 호출 변경
- Swagger 문서 업데이트

**수정된 파일:**
| 파일 | 경로 | 변경사항 |
|------|------|----------|
| `program_router.py` | `ai_backend/api/routers/` | Phase 4 리팩토링 완료 |
| `dependencies.py` | `ai_backend/core/` | 새 서비스 주입 추가 |

**변경된 파라미터명:**
```python
# Before
@router.post("/programs/upload")
async def upload_program_files(
    ladder_zip: UploadFile,
    template_xlsx: UploadFile,
    ...
)

# After
@router.post("/programs/upload")
async def upload_program_files(
    pgm_ladder_zip_file: UploadFile,  # 명확한 변수명
    pgm_template_file: UploadFile,    # 명확한 변수명
    ...
)
```

**서비스 호출 변경:**
```python
# Before
result = program_upload_service.upload_and_create_program(
    ladder_zip=ladder_zip,
    template_xlsx=template_xlsx,
    ...
)

# After
result = program_upload_service.upload_program_with_files(
    pgm_ladder_zip_file=pgm_ladder_zip_file,
    pgm_template_file=pgm_template_file,
    ...
)
```

**dependencies.py 업데이트:**
```python
# Phase 4 추가
def get_file_validation_service() -> FileValidationService:
    return FileValidationService()

def get_file_storage_service() -> FileStorageService:
    return FileStorageService()

def get_program_upload_service(
    ...
    file_validation_service: FileValidationService = Depends(get_file_validation_service),
    file_storage_service: FileStorageService = Depends(get_file_storage_service),
    ...
) -> ProgramUploadService:
    return ProgramUploadService(
        ...
        file_validation_service=file_validation_service,
        file_storage_service=file_storage_service,
        ...
    )
```

**Swagger 문서 업데이트:**
- API 설명에 3단계 워크플로우 명시
- 파라미터 설명 명확화
- Response 모델은 기존 유지

**작업 시간:** 1.5시간

**다음 단계:** Phase 5 - 레거시 코드 제거 (선택사항)

---

### 2025-11-06 - 리팩토링 Phase 3 완료 (ProgramUploadService 리팩토링) ⭐

**요약:**
- ProgramUploadService에 새 서비스 통합 (FileValidationService, FileStorageService)
- 명확한 변수명 적용 (pgm_ladder_zip_file, pgm_template_file)
- 환경변수 기반 설정
- DocumentService 새 메서드 사용
- 트랜잭션 경계 명확화

**수정된 파일:**
| 파일 | 경로 | 변경사항 |
|------|------|----------|
| `program_upload_service.py` | `ai_backend/api/services/` | Phase 3 리팩토링 완료 |

**제거된 메서드 (6개):**
```python
❌ _validate_file_types()                    # → FileValidationService
❌ _validate_files()                         # → FileValidationService
❌ _extract_required_files_from_template()  # → FileValidationService
❌ _extract_file_list_from_zip()            # → FileValidationService
❌ _compare_files()                          # → FileValidationService
❌ _save_files()                             # → FileStorageService + DocumentService
❌ _create_upload_file_from_bytes()         # 비필요
❌ _cleanup_saved_files()                    # → FileStorageService.delete_files()
```

**변경된 메서드명:**
```python
# Before
upload_and_create_program(
    ladder_zip: UploadFile,
    template_xlsx: UploadFile,
    ...
)

# After
upload_program_with_files(
    pgm_ladder_zip_file: UploadFile,  # 명확한 변수명
    pgm_template_file: UploadFile,    # 명확한 변수명
    ...
)
```

**새 서비스 통합:**
```python
class ProgramUploadService:
    def __init__(
        self,
        db: Session,
        sequence_service: SequenceService,
        file_validation_service: FileValidationService,  # ⭐ NEW
        file_storage_service: FileStorageService,        # ⭐ NEW
        document_service: DocumentService,               # Phase 2 리팩토링
        template_service: TemplateService,
        program_service: ProgramService
    ):
        self.settings = settings  # 환경변수 주입
        ...
```

**워크플로우 및 트랜잭션 경계:**
```python
def upload_program_with_files(self, ...):
    # Phase 1: 검증 (DB 트랜잭션 외부)
    file_validation_service.validate_ladder_zip_file_type(...)
    file_validation_service.validate_template_file_structure(...)
    file_validation_service.validate_ladder_files_match(...)
    
    # Phase 2: 파일 저장 (DB 트랜잭션 외부)
    file_storage_service.save_and_extract_ladder_zip(...)
    file_storage_service.save_template_file(...)
    
    # Phase 3: DB 저장 (트랜잭션 시작)
    try:
        document_service.bulk_create_ladder_csv_documents(...)
        document_service.create_template_document(...)  # 자동 파싱
        program_service.create_program(...)
        self.db.commit()
    except:
        self.db.rollback()
        file_storage_service.delete_files(saved_file_paths)  # 롤백
        raise
```

**복잡도 감소:**
- 코드 라인 수: ~380줄 → ~350줄 (8% 감소)
- 메서드 수: 11개 → 2개 (9개 삭제)
- 의존성: 5개 → 7개 (필요한 서비스만 주입)
- 책임: 오케스트레이션만 담당

**작업 시간:** 3시간

**다음 단계:** Phase 4 - Router 및 Response 모델 업데이트

---

### 2025-11-06 - 리팩토링 Phase 2 완료 (DocumentService 단순화) ⭐

**요약:**
- DocumentService를 DB 저장 전담으로 단순화
- 파일 저장/검증 로직 제거 (다른 서비스로 이동)
- 환경변수 기반 document_type 설정
- ProgramDocumentProcessorFactory 통합
- 명확한 메서드명으로 가독성 향상

**수정된 파일:**
| 파일 | 경로 | 변경사항 |
|------|------|----------|
| `document_service.py` | `ai_backend/api/services/` | Phase 2 리팩토링 완료 |

**제거된 메서드 (deprecated 없이 삭제):**
```python
❌ upload_zip_document()           # → FileStorageService.save_and_extract_ladder_zip()
❌ _extract_and_save_each_files()  # → FileStorageService 내부 로직
❌ save_extracted_file_to_db()     # → create_ladder_csv_document()
❌ _save_original_zip()            # → FileStorageService 내부 로직
```

**추가된 메서드:**
```python
✅ create_ladder_csv_document()       # 레더 CSV 문서 레코드 생성
✅ create_template_document()         # 템플릿 문서 레코드 생성 + 자동 프로세서 호출
✅ bulk_create_ladder_csv_documents() # 레더 CSV 일괄 생성 (성능 최적화)
```

**환경변수 기반 설정:**
```python
# document_type은 환경변수에서 가져옴
document_type = settings.pgm_ladder_csv_doctype   # "PGM_LADDER_CSV"
document_type = settings.pgm_template_doctype     # "PGM_TEMPLATE_FILE"
```

**ProgramDocumentProcessorFactory 통합:**
```python
class DocumentService(BaseDocumentService):
    def __init__(self, db, upload_base_path=None, processor_factory=None):
        # processor_factory 주입
        self.processor_factory = processor_factory or ProgramDocumentProcessorFactory(...)
    
    def create_template_document(self, ...):
        # 1. DB 저장
        document = self.document_crud.create_document(...)
        
        # 2. 자동으로 템플릿 프로세서 호출 (파싱)
        processor = self.processor_factory.get_processor(document.document_type)
        processor.process(document)
        
        return document
```

**복잡도 감소:**
- 코드 라인 수: ~500줄 → ~400줄 (20% 감소)
- 메서드 수: 35개 → 31개 (4개 삭제)
- 의존성: 파일 저장/검증 로직 제거로 책임 명확화

**작업 시간:** 2시간

**다음 단계:** Phase 3 - ProgramUploadService 리팩토링

---

### 2025-11-06 - 리팩토링 Phase 1 완료 (새 컴포넌트 생성) ⭐

**요약:**
- FileValidationService 생성 (파일 검증 전담)
- FileStorageService 생성 (파일 저장 전담)
- ProgramDocumentProcessor 생성 (Strategy 패턴)

**생성된 파일:**

| 파일 | 경로 | 용도 |
|------|------|------|
| `file_validation_service.py` | `ai_backend/api/services/` | 파일 검증 전담 서비스 |
| `file_storage_service.py` | `ai_backend/api/services/` | 파일 저장 전담 서비스 |
| `program_document_processor.py` | `ai_backend/api/services/` | Strategy 패턴 문서 후처리 |

**특징:**
- 환경변수 기반 설정 사용 (`settings` 주입)
- 명확한 책임 분리 (검증, 저장, 후처리)
- Strategy 패턴으로 확장성 확보
- 상세한 로깅 (`logger.info`, `logger.warning`)

**작업 시간:** 2시간

**다음 단계:** Phase 2 - DocumentService 단순화 ✅ **(완료!)**

---

### 2025-11-06 - 리팩토링 Phase 0 완료 (환경변수 설정) ⭐

**요약:**
- 프로그램 업로드 전용 환경변수 11개 추가
- 편의 메서드 6개 추가
- .env.example 파일 생성

**추가된 파일:**
| 파일 | 경로 | 용도 |
|------|------|------|
| `simple_settings.py` | `ai_backend/config/` | 환경변수 설정 클래스 확장 |
| `.env.example` | `backend/` | 환경변수 템플릿 |

**주요 환경변수:**
```python
# 파일 크기
pgm_ladder_zip_max_size: 100MB
pgm_template_max_size: 10MB

# 문서 타입 (대문자)
pgm_ladder_csv_doctype: "PGM_LADDER_CSV"
pgm_template_doctype: "PGM_TEMPLATE_FILE"
pgm_ladder_zip_doctype: "PGM_LADDER_ZIP"

# 디렉토리 구조
pgm_ladder_dir_name: "ladder_files"
pgm_template_dir_name: "template"
pgm_zip_dir_name: "zip"
```

**사용 예시:**
```python
from ai_backend.config.simple_settings import settings

# MB 단위로 크기 확인
max_size_mb = settings.get_pgm_ladder_zip_max_size_mb()  # 100.0

# 템플릿 필수 컬럼 리스트
columns = settings.get_pgm_template_required_columns()  # ["Logic ID", "Folder ID", "Logic Name"]

# 디렉토리 경로 생성
ladder_dir = settings.get_ladder_files_dir("PGM_1")  # "./uploads/PGM_1/ladder_files"
```

**상세 문서:** `docs/CREATE_PROGRAM_LOGIC_REFACTORING_PLAN.md` 참조

**다음 단계:** Phase 1 - 새 컴포넌트 생성 (FileValidationService, FileStorageService, ProgramDocumentProcessor)

---

### 2025-11-05 - 프로그램 업로드 서비스 구현 (Phase 2 완료) ⭐

**요약:**
- 프로그램 파일 업로드 통합 워크플로우 구현
- ZIP 파일과 템플릿 검증 로직
- 서버 자동 PGM_ID 생성 통합

**생성된 파일:**
| 파일 | 경로 | 용도 |
|------|------|------|
| `program_upload_service.py` | `ai_backend/api/services/` | 프로그램 업로드 통합 서비스 |
| `ProgramUploadResponse` | `ai_backend/types/response/program_response.py` | 업로드 응답 모델 |
| `ValidationResult` | `ai_backend/types/response/program_response.py` | 검증 결과 모델 |

**API 엔드포인트:**
```python
POST /programs/upload
# 요청: pgm_name, ladder_zip, template_xlsx, create_user
# 응답: pgm_id, validation_result, saved_files, summary
```

**주요 기능:**
1. PGM_ID 자동 생성 (sequence_service 활용)
2. 템플릿 Logic ID vs ZIP 파일 목록 검증
3. 불필요한 파일 자동 제거
4. 트랜잭션 안정성 보장 (롤백 지원)

**상세 문서:** `docs/CREATE_PROGRAM_LOGIC_PLAN.md` 참조 ⭐

---

### 2025-11-05 - PROGRAM_SEQUENCE 테이블 추가 (Phase 1 완료) ⭐

**요약:**
- PGM_ID 서버 자동 생성 시스템 구축
- 시퀀스 테이블 기반 ID 생성 (PGM_1, PGM_2, PGM_3 ...)
- 트랜잭션 안전성 보장 (Row Lock)

**생성된 파일:**
| 파일 | 경로 | 용도 |
|------|------|------|
| `sequence_models.py` | `ai_backend/database/models/` | ProgramSequence 모델 |
| `sequence_crud.py` | `ai_backend/database/crud/` | 시퀀스 CRUD 로직 |
| `sequence_service.py` | `ai_backend/api/services/` | 시퀀스 비즈니스 로직 |
| `001_add_program_sequence_table.sql` | `migrations/` | 테이블 생성 마이그레이션 |

**사용 예시:**
```python
from ai_backend.api.services.sequence_service import SequenceService

sequence_service = SequenceService(db)
pgm_id = sequence_service.generate_pgm_id()  # 'PGM_1', 'PGM_2' ...
```

**상세 문서:** `docs/CREATE_PROGRAM_LOGIC_PLAN.md` 참조 ⭐

---

### 2025-11-05 - ZIP 업로드 필드명 표준화 및 구조 개편

**요약:**
- shared_core Document 모델과 필드명 통일
- 메서드명 변경: `_extract_and_save_to_db()` → `_extract_and_save_each_files()`
- 폴더 구조: `/uploads/zipfiles/` → `/uploads/{pgm_id}/zip/`
- document_type 고정값: `PGM_LADDER_CSV`, `PGM_LADDER_ZIP`
- document_id 생성: UUID → `doc_YYYYMMDD_HHMMSS_xxxxxxxx`

**주요 변경 필드:**
| 변경 전 | 변경 후 | 비고 |
|---------|---------|------|
| `file_name` | `document_name` | shared_core 표준 |
| `file_path` | `upload_path` | shared_core 표준 |
| - | `original_filename` | 신규 추가 |
| - | `file_key` | 신규 추가 |
| - | `file_type` | MIME 타입 추가 |

**상세 문서:** `docs/ZIP_UPLOAD_CHANGES_20251105.md` 참조 ⭐

---

### 2025-11-04 - ZIP 업로드 로직 최적화

**개요:**
- pgm_id 검증을 soft validation으로 변경
- 임시파일 제거, 메모리에서 직접 처리
- 새로운 메서드 `save_extracted_file_to_db()` 추가

---

### 2025-11-02 - ZIP 파일 업로드 PGM_ID 기반 시스템 개편

**개요:**
- ZIP 압축 해제 후 각 파일을 DOCUMENTS 테이블에 독립적으로 저장
- PGM_ID로 프로그램별 문서 관리
- 원본 ZIP 파일 저장 선택 기능

**폴더 구조:**
```
/uploads/
  └─ {pgm_id}/
      ├─ folder/file.txt  # 추출 파일
      └─ zip/             # 원본 ZIP
          └─ archive.zip
```

---

### 2025-10-20 - Excel 업로드 및 에러 처리 개선

**수정 사항:**
- metadata 파라미터 전달 문제 해결
- file_path 키 에러 해결
- HandledException 사용법 수정
- openpyxl 추가

---

### 2025-10-19 - 템플릿 관리 기능 구현 완료

**구현 완료:**
- Excel 파일 업로드 통합 (`document_type="pgm_template"`)
- 자동 Excel 파싱 및 PGM_TEMPLATE 테이블 저장
- 계층 구조 조회 (Folder → Sub Folder → Logic)

---

### 2025-10-18 - PLC API 엔드포인트 단수/복수 구분

**변경 사항:**
- 단일 리소스: `/plc/{plc_id}`
- 컬렉션: `/plcs`
- RESTful 설계 개선

---

## 🗂️ 디렉토리 구조

```
ai_backend/
├── api/
│   ├── routers/
│   │   ├── document_router.py    # 문서 관리 API (ZIP 포함)
│   │   ├── plc_router.py
│   │   ├── program_router.py
│   │   └── template_router.py
│   │
│   └── services/
│       ├── document_service.py        # ⭐ ZIP 업로드 로직
│       ├── sequence_service.py        # ⭐ PGM_ID 자동 생성
│       ├── program_upload_service.py  # ⭐ 프로그램 업로드 통합 (Phase 2 NEW)
│       ├── plc_service.py
│       ├── program_service.py
│       └── template_service.py
│
├── database/
│   ├── models/
│   │   ├── plc_models.py
│   │   ├── program_models.py
│   │   ├── sequence_models.py    # ⭐ PROGRAM_SEQUENCE 모델 (NEW)
│   │   └── template_models.py
│   │
│   └── crud/
│       ├── document_crud.py      # DocumentCRUD (shared_core CRUD)
│       ├── sequence_crud.py      # ⭐ 시퀀스 CRUD (NEW)
│       ├── plc_crud.py
│       └── program_crud.py
│
└── types/
    └── response/
        └── plc_hierarchy_response.py

migrations/
├── 001_add_program_sequence_table.sql          # ⭐ 테이블 생성 (NEW)
├── 001_add_program_sequence_table_rollback.sql # ⭐ 롤백 (NEW)
└── README.md                                    # ⭐ 마이그레이션 가이드 (NEW)
```

---

## 🔗 API 엔드포인트 요약

### Program Upload API ⭐ NEW (Phase 2)
```
POST /programs/upload  # 프로그램 파일 업로드 및 생성
# 요청: pgm_name, ladder_zip, template_xlsx, create_user
# 응답: pgm_id, validation_result, saved_files, summary
# 특징: PGM_ID 서버 자동 생성, 파일 검증, 트랜잭션 보장
```

### Document API
```
POST   /v1/upload              # 일반 파일 업로드
POST   /v1/upload-zip          # ZIP 파일 업로드 ⭐
GET    /v1/documents           # 문서 목록 조회 (pgm_id 필터 가능)
GET    /v1/documents/{id}      # 문서 조회
GET    /v1/documents/{id}/download  # 문서 다운로드
DELETE /v1/documents/{id}      # 문서 삭제
```

### ZIP 업로드 Flow
```
Client
    ↓
POST /v1/upload-zip (file, pgm_id, keep_zip_file)
    ↓
document_service.upload_zip_document()
    ↓
1. _extract_and_save_each_files()
   - ZIP 압축 해제 (메모리)
   - save_extracted_file_to_db() → DOCUMENTS 테이블
   - document_type = 'PGM_LADDER_CSV'
    ↓
2. _save_original_zip() (선택)
   - /uploads/{pgm_id}/zip/ 저장
   - document_type = 'PGM_LADDER_ZIP'
    ↓
Response: 추출 파일 목록 + 통계
```

---

## 🔍 빠른 검색 키워드

- **PGM_ID 생성**: sequence_service.py, sequence_crud.py, sequence_models.py ⭐
- **프로그램 업로드**: program_upload_service.py, POST /programs/upload ⭐ NEW (Phase 2)
- **ZIP 업로드**: document_service.py, upload_zip_document, save_extracted_file_to_db
- **shared_core**: models.py, crud.py, services.py, Document 모델
- **PLC 관련**: plc_models.py, plc_service.py, plc_router.py
- **프로그램 관련**: program_models.py, program_service.py
- **템플릿 관련**: template_models.py, template_service.py

---

## 📚 참조 문서

1. **PROJECT_REFERENCE_GUIDE.md** (현재 문서)
   - 프로젝트 전체 개요

2. **DATABASE_SCHEMA_REFERENCE.md**
   - 테이블 스키마 상세

3. **CREATE_PROGRAM_LOGIC_PLAN.md** ⭐ NEW
   - 프로그램 생성 프로세스 상세 설계

4. **ZIP_UPLOAD_CHANGES_20251105.md**
   - ZIP 업로드 최신 변경사항 상세

5. **SHARED_CORE_INTEGRATION_PLAN.md**
   - shared_core 통합 계획

---

## 🚀 서버 실행

```bash
cd D:\project-template-backup251021\chat-api\app\backend
python -m uvicorn ai_backend.main:app --reload --port 8000
```

**Swagger UI:** http://localhost:8000/docs

---

## 🗄️ 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
mysql -u [username] -p [database] < migrations/001_add_program_sequence_table.sql

# Python에서 시퀀스 사용
from ai_backend.api.services.sequence_service import SequenceService
sequence_service = SequenceService(db)
pgm_id = sequence_service.generate_pgm_id()  # PGM_1, PGM_2, PGM_3 ...
```

---

**이 문서를 활용하면 Claude가 매번 파일을 검색하지 않고도 프로젝트 구조를 빠르게 파악할 수 있습니다!** 🚀
