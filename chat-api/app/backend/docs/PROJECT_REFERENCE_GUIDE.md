# 🏗️ PLC-Program Mapping System - 프로젝트 참조 가이드

> **최종 업데이트:** 2025-11-05 (화요일) - Phase 2 완료! 🎉  
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

### DocumentService 상속 관계
```python
# ai_backend/api/services/document_service.py
from shared_core import DocumentService as BaseDocumentService

class DocumentService(BaseDocumentService):
    """
    BaseDocumentService로부터 상속:
    - create_document_from_file(), get_document()
    - _get_file_extension(), _get_mime_type(), _calculate_file_hash()
    
    FastAPI 전용 확장:
    - upload_document(), upload_zip_document()
    - save_extracted_file_to_db()
    - _extract_and_save_each_files()
    - _save_original_zip()
    """
```

**상세 정보:** `docs/SHARED_CORE_INTEGRATION_PLAN.md` 참조

---

## ✨ 최근 변경사항

### 2025-11-05 - 프로그램 업로드 서비스 구현 (Phase 2 완료) ⭐ NEW

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
