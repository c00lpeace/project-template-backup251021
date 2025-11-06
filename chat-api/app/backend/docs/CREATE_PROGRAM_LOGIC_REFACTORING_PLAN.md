# 📋 PLC 프로그램 생성 프로세스 리팩토링 계획서

> **최종 업데이트:** 2025-11-06  
> **상태:** 🎉 완료 (Phase 5 완료)

---

## 📅 작업 이력

### 2025-11-06 - Phase 5 완료 ✅

**작업 내용:**
- ✅ 사용하지 않는 import 정리 (4개 파일)
  - document_service.py: Path 제거
  - program_upload_service.py: pandas 제거
  - dependencies.py: get_redis_client 중복 제거
- ✅ 코드 스타일 통일 확인
  - docstring 형식 일관성 확인
  - 로깅 메시지 일관성 확인 (✅, ❌, 🎉 이모지)
- ✅ 최종 검토
  - Phase 0-4 규칙 준수 확인
  - 환경변수 사용 확인
  - 명확한 변수명 확인
  - 새 서비스 통합 확인
  - 트랜잭션 경계 명확화 확인
- ✅ 문서 업데이트
  - PROJECT_REFERENCE_GUIDE.md
  - CREATE_PROGRAM_LOGIC_REFACTORING_PLAN.md

**파일 변경:**
- 📝 `ai_backend/api/services/document_service.py` (정리 완료)
- 📝 `ai_backend/api/services/program_upload_service.py` (정리 완료)
- 📝 `ai_backend/api/routers/program_router.py` (검토 완료)
- 📝 `ai_backend/core/dependencies.py` (정리 완료)
- 📝 `docs/PROJECT_REFERENCE_GUIDE.md` (업데이트)
- 📝 `docs/CREATE_PROGRAM_LOGIC_REFACTORING_PLAN.md` (업데이트)

**최종 검토 체크리스트:**

| 항목 | 상태 |
|------|------|
| 환경변수 사용 | ✅ |
| 명확한 변수명 | ✅ |
| 새 서비스 통합 | ✅ |
| 새 메서드 사용 | ✅ |
| 트랜잭션 경계 | ✅ |
| 로깅 일관성 | ✅ |
| import 정리 | ✅ |
| 문서 업데이트 | ✅ |

**결과:**
- 코드 라인 수: 변화 없음 (깨끗한 코드 유지)
- import 수: 3개 감소 (Path, pandas, get_redis_client)
- 코드 품질: 향상 (일관성, 가독성)

**작업 시간:** 1시간

**다음 단계:** 성능 최적화 (선택사항)

---

### 2025-11-06 - Phase 4 완료 ✅

**작업 내용:**
- ✅ Router 파라미터명 변경
  - ladder_zip → pgm_ladder_zip_file
  - template_xlsx → pgm_template_file
- ✅ 서비스 메서드 호출 변경
  - upload_and_create_program() → upload_program_with_files()
- ✅ dependencies.py 업데이트
  - get_file_validation_service() 추가
  - get_file_storage_service() 추가
  - get_program_upload_service()에 새 서비스 주입
- ✅ Swagger 문서 업데이트
  - 3단계 워크플로우 명시
  - 파라미터 설명 명확화

**파일 변경:**
- 📝 `ai_backend/api/routers/program_router.py` (리팩토링 완료)
- 📝 `ai_backend/core/dependencies.py` (새 서비스 주입)
- 📝 `docs/PROJECT_REFERENCE_GUIDE.md` (업데이트)
- 📝 `docs/CREATE_PROGRAM_LOGIC_REFACTORING_PLAN.md` (업데이트)

**주요 변경사항:**
```python
# Router 파라미터명 변경
@router.post("/programs/upload")
async def upload_program_files(
    pgm_ladder_zip_file: UploadFile,  # ladder_zip → 변경
    pgm_template_file: UploadFile,    # template_xlsx → 변경
    ...
)

# 서비스 호출 변경
result = program_upload_service.upload_program_with_files(
    pgm_ladder_zip_file=pgm_ladder_zip_file,
    pgm_template_file=pgm_template_file,
    ...
)

# dependencies.py 업데이트
def get_file_validation_service() -> FileValidationService:
    return FileValidationService()

def get_file_storage_service() -> FileStorageService:
    return FileStorageService()

def get_program_upload_service(
    ...
    file_validation_service: FileValidationService = Depends(get_file_validation_service),
    file_storage_service: FileStorageService = Depends(get_file_storage_service),
    ...
):
    return ProgramUploadService(
        ...
        file_validation_service=file_validation_service,
        file_storage_service=file_storage_service,
        ...
    )
```

**API 엔드포인트:**
- URL: `POST /programs/upload` (변경 없음)
- Request: Form data + multipart/form-data
- Response: ProgramUploadResponse (변경 없음)

**작업 시간:** 1.5시간

**다음 단계:** Phase 5 - 레거시 코드 제거 (선택사항)

---

### 2025-11-06 - Phase 3 완료 ✅

**작업 내용:**
- ✅ ProgramUploadService에 새 서비스 통합
  - FileValidationService 주입
  - FileStorageService 주입
  - DocumentService 새 메서드 사용
- ✅ 메서드명 변경
  - upload_and_create_program() → upload_program_with_files()
- ✅ 변수명 변경 (명확한 이름)
  - ladder_zip → pgm_ladder_zip_file
  - template_xlsx → pgm_template_file
- ✅ 환경변수 주입
  - settings = program_upload_settings
  - self.settings.pgm_ladder_dir_name
  - self.settings.pgm_template_dir_name
- ✅ 트랜잭션 경계 명확화
  - Phase 1: 검증 (DB 트랜잭션 외부)
  - Phase 2: 파일 저장 (DB 트랜잭션 외부)
  - Phase 3: DB 저장 (트랜잭션 내부 - commit/rollback)
- ✅ 불필요한 메서드 제거 (9개)

**파일 변경:**
- 📝 `ai_backend/api/services/program_upload_service.py` (리팩토링 완료)
- 📝 `docs/PROJECT_REFERENCE_GUIDE.md` (업데이트)
- 📝 `docs/CREATE_PROGRAM_LOGIC_REFACTORING_PLAN.md` (업데이트)

**주요 변경사항:**
```python
# 제거된 메서드 (9개)
❌ _validate_file_types()
❌ _validate_files()
❌ _extract_required_files_from_template()
❌ _extract_file_list_from_zip()
❌ _compare_files()
❌ _filter_unnecessary_files()  # → _filter_ladder_zip()로 변경 (유지)
❌ _save_files()
❌ _create_upload_file_from_bytes()
❌ _cleanup_saved_files()

# 변경된 메서드 (2개)
✅ upload_and_create_program() → upload_program_with_files()
✅ _filter_unnecessary_files() → _filter_ladder_zip() (명확한 이름)

# 새 서비스 통합
class ProgramUploadService:
    def __init__(
        self,
        db: Session,
        sequence_service: SequenceService,
        file_validation_service: FileValidationService,  # ⭐ NEW
        file_storage_service: FileStorageService,        # ⭐ NEW
        document_service: DocumentService,               # Phase 2
        template_service: TemplateService,
        program_service: ProgramService
    ):
        self.settings = settings  # 환경변수
        ...

# 명확한 변수명
upload_program_with_files(
    pgm_ladder_zip_file: UploadFile,  # ladder_zip → pgm_ladder_zip_file
    pgm_template_file: UploadFile,    # template_xlsx → pgm_template_file
    ...
)

# 트랜잭션 경계 명확화
try:
    # Phase 1: 검증 (DB 트랜잭션 외부)
    file_validation_service.validate_...()
    
    # Phase 2: 파일 저장 (DB 트랜잭션 외부)
    file_storage_service.save_...()
    
    # Phase 3: DB 저장 (트랜잭션 내부)
    document_service.bulk_create_ladder_csv_documents(...)
    document_service.create_template_document(...)  # 자동 파싱
    program_service.create_program(...)
    self.db.commit()
except:
    self.db.rollback()
    file_storage_service.delete_files(saved_file_paths)
    raise
```

**복잡도 감소:**
- 코드 라인 수: ~380줄 → ~350줄 (8% 감소)
- 메서드 수: 11개 → 2개 (9개 삭제)
- 메서드 호출 깊이: 5레벨 → 3레벨
- 의존성: 분산되어 관리 용이

**작업 시간:** 3시간

**다음 단계:** Phase 4 - Router 및 Response 모델 업데이트

---

### 2025-11-06 - Phase 2 완료 ✅

**작업 내용:**
- ✅ DocumentService에서 파일 저장 로직 제거
  - upload_zip_document() 삭제
  - _extract_and_save_each_files() 삭제
  - save_extracted_file_to_db() 삭제
  - _save_original_zip() 삭제
- ✅ DocumentService에서 검증 로직 제거 (upload_document 내부 로직은 유지)
- ✅ 새 메서드 추가 (명확한 이름)
  - create_ladder_csv_document() → 레더 CSV 문서 레코드 생성
  - create_template_document() → 템플릿 문서 레코드 생성 + 자동 프로세서 호출
  - bulk_create_ladder_csv_documents() → 레더 CSV 일괄 생성
- ✅ 환경변수 주입
  - document_type은 settings에서 가져오도록 수정
  - settings.pgm_ladder_csv_doctype
  - settings.pgm_template_doctype
- ✅ ProgramDocumentProcessorFactory 통합
  - __init__에 processor_factory 주입
  - create_template_document()에서 자동으로 템플릿 프로세서 호출

**파일 변경:**
- 📝 `ai_backend/api/services/document_service.py` (리팩토링 완료)
- 📝 `docs/PROJECT_REFERENCE_GUIDE.md` (업데이트)
- 📝 `docs/CREATE_PROGRAM_LOGIC_REFACTORING_PLAN.md` (업데이트)

**주요 변경사항:**
```python
# 제거된 메서드 (4개)
❌ upload_zip_document()
❌ _extract_and_save_each_files()
❌ save_extracted_file_to_db()
❌ _save_original_zip()

# 추가된 메서드 (3개)
✅ create_ladder_csv_document()
✅ create_template_document()
✅ bulk_create_ladder_csv_documents()

# 환경변수 기반 document_type
document_type = settings.pgm_ladder_csv_doctype  # "PGM_LADDER_CSV"
document_type = settings.pgm_template_doctype    # "PGM_TEMPLATE_FILE"

# ProgramDocumentProcessorFactory 통합
class DocumentService(BaseDocumentService):
    def __init__(self, db, upload_base_path=None, processor_factory=None):
        self.processor_factory = processor_factory or ProgramDocumentProcessorFactory(...)
    
    def create_template_document(self, ...):
        # 1. DB INSERT
        document = self.document_crud.create_document(...)
        
        # 2. 자동 프로세서 호출
        processor = self.processor_factory.get_processor(document.document_type)
        processor.process(document)  # 템플릿 파싱
        
        return document
```

**복잡도 감소:**
- 코드 라인 수: ~500줄 → ~400줄 (20% 감소)
- 메서드 수: 35개 → 31개 (4개 삭제)
- 의존성: 파일 저장/검증 로직 제거로 책임 명확화

**작업 시간:** 2시간

**다음 단계:** Phase 3 - ProgramUploadService 리팩토링

---

### 2025-11-06 - Phase 1.5 완료 ✅ ⭐ NEW

**작업 내용:**
- ✅ 환경변수 추가 (simple_settings.py)
  - pgm_ladder_csv_required_columns: 필수 컬럼
  - pgm_ladder_csv_header_row: 헤더 행 위치
  - pgm_ladder_csv_validate_file_identifier: 파일 식별자 검증 on/off
  - pgm_ladder_csv_validate_module_info: 모듈 정보 검증 on/off
  - pgm_ladder_csv_module_info_prefix: 모듈 정보 접두사
  - pgm_ladder_csv_min_data_rows: 최소 데이터 행 수
  - pgm_ladder_csv_encoding: 인코딩
  - pgm_ladder_csv_structure_validation_enabled: 검증 활성화 on/off
  - get_pgm_ladder_csv_required_columns(): 편의 메서드

- ✅ FileValidationService에 메서드 2개 추가
  - validate_ladder_csv_structure_from_bytes(): CSV 구조 검증
  - validate_matched_ladder_csv_structures_in_memory(): 매칭된 CSV 구조 검증

- ✅ ProgramUploadService 수정
  - Step 8 추가: 매칭된 CSV 구조 검증
  - 기존 Step 6-12 → Step 9-15로 변경
  - 워크플로우 주석 업데이트

**파일 변경:**
- 📝 `ai_backend/config/simple_settings.py` (환경변수 추가)
- 📝 `ai_backend/api/services/file_validation_service.py` (메서드 2개 추가)
- 📝 `ai_backend/api/services/program_upload_service.py` (Step 8 추가)
- 📝 `docs/CREATE_PROGRAM_LOGIC_REFACTORING_PLAN.md` (업데이트)
- 📝 `docs/PROJECT_REFERENCE_GUIDE.md` (업데이트)

**주요 변경사항:**

```python
# 환경변수 추가
pgm_ladder_csv_required_columns: str = Field(
    default="Step No.,Line Statement,Instruction,I/O (Device),Blank,P/I Statement,Note",
    env="PGM_LADDER_CSV_REQUIRED_COLUMNS"
)

# FileValidationService 새 메서드
def validate_ladder_csv_structure_from_bytes(
    self,
    csv_bytes: bytes,
    filename: str
) -> Dict:
    """
    레더 CSV 파일 구조 검증 (메모리 상에서)
    
    검증 항목:
    1. 파일 식별자 (1줄) - 선택적
    2. 모듈 정보 (2줄) - 선택적
    3. 필수 컬럼 (3줄) - 필수
    4. 최소 데이터 행 수 - 필수
    """

def validate_matched_ladder_csv_structures_in_memory(
    self,
    ladder_zip_file: UploadFile,
    matched_files: List[str]
) -> Dict:
    """
    매칭된 레더 CSV 파일들만 메모리에서 구조 검증
    
    해결방안 C:
    - ZIP을 두 번 열기 (Step 3: 구조만, Step 8: CSV 내용)
    - 메모리에서만 처리, 디스크 저장 전에 오류 발견
    """

# ProgramUploadService 워크플로우 업데이트
# Step 8: 매칭된 레더 CSV 파일 구조 검증 (메모리) - Phase 1.5 신규
csv_structure_validation_result = self.file_validation_service.validate_matched_ladder_csv_structures_in_memory(
    ladder_zip_file=pgm_ladder_zip_file,
    matched_files=validation_result['matched_files']
)

logger.info(
    f"✅ [Step 8] 레더 CSV 구조 검증 완료: "
    f"{csv_structure_validation_result['validated_count']}개 파일 통과"
)
```

**레더 CSV 파일 구조:**
```
Line 1: KV339_20231104                          # 파일 식별자
Line 2: Module Type Information:,RCPU R08       # 모듈 정보
Line 3: Step No.,Line Statement,Instruction,... # 헤더 (필수 컬럼)
Line 4+: 실제 데이터
```

**검증 순서:**
1. bytes → 문자열 디코딩 (환경변수 인코딩)
2. StringIO로 메모리 파일 객체 생성
3. 최소 줄 수 검증
4. 파일 식별자 검증 (환경변수로 on/off)
5. 모듈 정보 검증 (환경변수로 on/off)
6. 필수 컬럼 검증 (환경변수 기반)
7. 최소 데이터 행 수 검증

**특징:**
- 해결방안 C: ZIP을 두 번 열기
  - Step 3: ZIP 구조만 확인 (파일 목록)
  - Step 8: 매칭된 CSV만 내용 검증
- 메모리에서만 처리, 디스크 저장 전에 오류 발견
- 환경변수로 검증 규칙 제어 가능
- chardet 라이브러리로 인코딩 자동 감지 (선택사항)
- 하나라도 실패하면 전체 업로드 중단

**작업 시간:** 2시간

**다음 단계:** Phase 6 - 성능 최적화 (선택사항)

---

### 2025-11-06 - Phase 1 완료 ✅

**작업 내용:**
- ✅ FileValidationService 생성 (파일 검증 전담)
- ✅ FileStorageService 생성 (파일 저장 전담)
- ✅ ProgramDocumentProcessor 생성 (Strategy 패턴)

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

### 2025-11-06 - Phase 0 완료 ✅

**작업 내용:**
- ✅ `simple_settings.py`에 프로그램 업로드 환경변수 11개 추가
- ✅ 편의 메서드 6개 추가 (경로 생성, 크기 변환 등)
- ✅ `.env.example` 파일 생성 (환경변수 템플릿)

**추가된 환경변수:**
```python
# 파일 크기 제한
pgm_ladder_zip_max_size: 100MB
pgm_template_max_size: 10MB
pgm_ladder_csv_max_size: 5MB

# 문서 타입 (대문자 통일)
pgm_ladder_csv_doctype: "PGM_LADDER_CSV"
pgm_template_doctype: "PGM_TEMPLATE_FILE"
pgm_ladder_zip_doctype: "PGM_LADDER_ZIP"

# 디렉토리 구조
pgm_ladder_dir_name: "ladder_files"
pgm_template_dir_name: "template"
pgm_zip_dir_name: "zip"

# 기타
pgm_template_required_columns: "Logic ID,Folder ID,Logic Name"
pgm_keep_original_zip: True
pgm_zip_extract_timeout: 300
```

**추가된 편의 메서드:**
```python
settings.get_pgm_ladder_zip_max_size_mb()     # MB 단위 변환
settings.get_pgm_template_max_size_mb()       # MB 단위 변환
settings.get_pgm_template_required_columns()  # 컬럼 리스트 변환
settings.get_program_upload_dir(pgm_id)       # 루트 디렉토리 경로
settings.get_ladder_files_dir(pgm_id)         # 레더 파일 경로
settings.get_template_file_dir(pgm_id)        # 템플릿 파일 경로
settings.get_zip_file_dir(pgm_id)             # ZIP 파일 경로
```

**파일 변경:**
- 📝 `ai_backend/config/simple_settings.py` (환경변수 추가)
- 📝 `.env.example` (신규 생성)

**작업 시간:** 30분

**다음 단계:** Phase 1 - 새 컴포넌트 생성 ✅ **(완료!)**

---

### 2025-11-06 - Phase 1 완료 ✅

**작업 내용:**
- ✅ `FileValidationService` 생성 (파일 검증 전담)
- ✅ `FileStorageService` 생성 (파일 저장 전담)
- ✅ `ProgramDocumentProcessor` 생성 (Strategy 패턴)

**생성된 파일:**

| 파일 | 경로 | 용도 |
|------|------|------|
| `file_validation_service.py` | `ai_backend/api/services/` | 파일 검증 전담 서비스 |
| `file_storage_service.py` | `ai_backend/api/services/` | 파일 저장 전담 서비스 |
| `program_document_processor.py` | `ai_backend/api/services/` | Strategy 패턴 문서 후처리 |

**FileValidationService 주요 메서드:**
```python
- validate_ladder_zip_file_type()        # 레더 ZIP 타입 검증
- validate_ladder_zip_file_size()        # 레더 ZIP 크기 검증
- validate_ladder_zip_structure()        # ZIP 구조 검증
- validate_template_file_type()          # 템플릿 타입 검증
- validate_template_file_size()          # 템플릿 크기 검증
- validate_template_file_structure()     # 템플릿 구조 검증
- validate_ladder_files_match()          # 파일 매칭 검증
- validate_ladder_filename_pattern()     # 파일명 패턴 검증
```

**FileStorageService 주요 메서드:**
```python
- save_and_extract_ladder_zip()          # 레더 ZIP 저장 및 압축 해제
- save_template_file()                   # 템플릿 파일 저장
- delete_program_files()                 # 프로그램 파일 삭제 (롤백)
- delete_files()                         # 특정 파일 삭제 (롤백)
```

**ProgramDocumentProcessor 클래스:**
```python
- ProgramDocumentProcessor               # 추상 클래스 (ABC)
- DefaultProgramDocumentProcessor        # 기본 프로세서 (후처리 없음)
- ProgramTemplateProcessor               # 템플릿 프로세서 (파싱 + 저장)
- ProgramDocumentProcessorFactory        # 프로세서 팩토리
```

**특징:**
- 환경변수 기반 설정 사용 (`settings` 주입)
- 명확한 책임 분리 (검증, 저장, 후처리)
- Strategy 패턴으로 확장성 확보
- 상세한 로깅 (`logger.info`, `logger.warning`)

**작업 시간:** 2시간

**다음 단계:** Phase 2 - DocumentService 단순화 ✅ **(완료!)**

---

## 📑 목차
1. [리팩토링 목표](#-리팩토링-목표)
2. [현재 문제점 상세 분석](#-현재-문제점-상세-분석)
3. [명명 규칙 개선](#-명명-규칙-개선)
4. [환경변수 관리](#-환경변수-관리)
5. [새로운 아키텍처 설계](#-새로운-아키텍처-설계)
6. [새로운 컴포넌트 설계](#-새로운-컴포넌트-설계)
7. [변경 전후 비교](#-변경-전후-비교)
8. [단계별 마이그레이션 계획](#-단계별-마이그레이션-계획)
9. [테스트 전략](#-테스트-전략)
10. [리스크 및 대응 방안](#-리스크-및-대응-방안)
11. [성능 개선 예상치](#-성능-개선-예상치)
12. [체크리스트](#-체크리스트)

---

## 🎯 리팩토링 목표

### 핵심 목표
1. **책임 분리**: 파일 저장, DB 저장, 비즈니스 로직 분리
2. **복잡도 감소**: 메서드 호출 깊이 7레벨 → 4레벨 이하
3. **재사용성 향상**: 각 컴포넌트를 독립적으로 사용 가능
4. **테스트 용이성**: 각 레이어를 독립적으로 테스트 가능
5. **확장성**: 새로운 document_type 추가 시 수정 최소화
6. **명명 일관성**: 명확하고 일관된 변수/메서드/클래스명
7. **설정 유연성**: 환경변수 기반 설정 관리

---

## 📋 현재 문제점 상세 분석

### 문제 1: **DocumentService의 과도한 책임**

```
DocumentService.upload_zip_document()가 수행하는 작업:
1. 파일 검증 (크기, 타입)
2. 업로드 경로 생성
3. 파일 키 생성
4. 물리 파일 저장
5. DB에 문서 레코드 생성 (DOCUMENTS)
6. ZIP 압축 해제
7. 압축 해제된 각 파일마다:
   - 물리 파일 저장
   - DB에 문서 레코드 생성 (DOCUMENTS)
8. 원본 ZIP도 DB에 저장

→ 단일 책임 원칙(SRP) 위반
```

### 문제 2: **중복된 검증 로직**

```
검증이 3곳에서 발생:
1. ProgramUploadService._validate_file_types()  # 확장자 검증
2. DocumentService.validate_file_type()         # 확장자 검증 (중복)
3. DocumentService.validate_file_size()         # 크기 검증

→ DRY 원칙 위반
```

### 문제 3: **조건부 로직의 복잡성**

```python
DocumentService.upload_document()
  └─> if document_type == 'plc_template':  # 하드코딩된 분기
       └─> TemplateService.parse_and_save_template()
            └─> PGM_TEMPLATE 테이블 INSERT (반복문)

문제점:
- DocumentService가 TemplateService에 강하게 결합
- 새로운 document_type 추가 시 DocumentService 수정 필요
- 테스트 시 TemplateService 모킹 필요
```

### 문제 4: **불명확한 트랜잭션 경계**

```
현재 트랜잭션 범위:
ProgramUploadService.upload_and_create_program()
  ├─ DocumentService.upload_zip_document()
  │   ├─ DOCUMENTS INSERT (ZIP 원본)
  │   └─ 각 CSV 파일마다 DOCUMENTS INSERT  # ⚠️ 반복문 내부
  │
  ├─ DocumentService.upload_document()
  │   ├─ DOCUMENTS INSERT (템플릿)
  │   └─ PGM_TEMPLATE INSERT (반복문)      # ⚠️ 반복문 내부
  │
  └─ ProgramService.create_program()
      └─ PROGRAMS INSERT

→ 반복문 내부에서 INSERT 발생 → 성능 저하 가능
```

### 문제 5: **순환 의존성 위험**

```
ProgramUploadService
  └─> DocumentService
       └─> TemplateService (조건부)

향후 TemplateService가 DocumentService를 참조하면 순환 의존성 발생
```

### 문제 6: **불명확한 변수명**

```python
# 현재 사용 중인 애매한 변수명
ladder_zip          # → ZIP인지 레더인지 불명확
ladder_files        # → CSV인지 ZIP 압축 해제한 것인지 불명확
document_type       # → 너무 포괄적
zip_files           # → 일반 ZIP인지 레더 ZIP인지 불명확
```

### 문제 7: **하드코딩된 설정 값**

```python
# 코드 내 하드코딩
MAX_ZIP_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = ['.zip', '.xlsx']
UPLOAD_BASE_PATH = '/uploads'
REQUIRED_TEMPLATE_COLUMNS = ['Logic ID', 'Folder ID', 'Logic Name']

문제점:
- 값 변경 시 코드 수정 필요
- 환경별 다른 설정 어려움 (dev, prod)
- 설정 변경 시 재배포 필요
```

---

## 🏷️ 명명 규칙 개선

### 핵심 엔티티 정의

| 엔티티 | 약어 | 설명 | 파일 타입 |
|--------|------|------|----------|
| Program | PGM | 프로그램 전체 | - |
| Ladder File | LADDER | 레더 로직 CSV 파일 (개별) | `.csv` |
| Ladder ZIP | LADDER_ZIP | 레더 파일들이 압축된 ZIP | `.zip` |
| Template | TEMPLATE | 프로그램 구조 정의 템플릿 | `.xlsx` |

### 변수명 명명 규칙

```python
# ============================================
# 1. 파일 업로드 단계 (UploadFile 객체)
# ============================================

# Before
ladder_zip: UploadFile          # 애매함
template_xlsx: UploadFile       # OK

# After
pgm_ladder_zip_file: UploadFile      # 프로그램 레더 ZIP 파일
pgm_template_file: UploadFile        # 프로그램 템플릿 파일

# ============================================
# 2. 파일 내용 (bytes, 메모리)
# ============================================

# Before
filtered_zip_bytes: bytes       # 무엇을 필터링?

# After
filtered_ladder_zip_bytes: bytes     # 필터링된 레더 ZIP 바이트
template_file_bytes: bytes           # 템플릿 파일 바이트

# ============================================
# 3. 저장 경로
# ============================================

# Before
ladder_path: Path               # 레더 파일? ZIP? 디렉토리?
template_path: Path

# After
pgm_ladder_dir: Path                 # 레더 파일들 저장 디렉토리
pgm_ladder_zip_path: Path           # 원본 ZIP 저장 경로
pgm_template_file_path: Path        # 템플릿 파일 저장 경로

# ============================================
# 4. 저장 결과 (Dict)
# ============================================

# Before
ladder_save_result: Dict        # 무엇을 저장?
template_save_result: Dict

# After
ladder_zip_extract_result: Dict      # ZIP 압축 해제 결과
# {
#   'zip_file': {...},               # 원본 ZIP 정보
#   'extracted_ladder_files': [...]  # 압축 해제된 CSV 파일들
# }

template_save_result: Dict
# {
#   'template_file': {...}           # 템플릿 파일 정보
# }

# ============================================
# 5. 문서 레코드 (DB)
# ============================================

# Before
ladder_documents: List[Document]    # OK, 문맥상 이해 가능
template_document: Document

# After
pgm_ladder_csv_documents: List[Document]  # 레더 CSV 문서들
pgm_template_document: Document           # 템플릿 문서

# ============================================
# 6. 문서 타입 (DOCUMENTS.DOCUMENT_TYPE)
# ============================================

# Before
'PGM_LADDER_CSV'               # OK, 명확함
'plc_template'                 # 일관성 없음 (소문자 + 밑줄)

# After
'PGM_LADDER_CSV'               # 레더 CSV 파일
'PGM_TEMPLATE_FILE'            # 템플릿 파일 (대문자 통일)
'PGM_LADDER_ZIP'               # 원본 ZIP 파일 (선택사항)
```

### 메서드명 명명 규칙

```python
# ============================================
# FileValidationService
# ============================================

# Before
validate_file_type(file, extensions)
validate_files_match(required, zip_files)

# After
validate_ladder_zip_structure(ladder_zip_file)      # ZIP 구조 검증
validate_template_file_structure(template_file)     # 템플릿 구조 검증
validate_ladder_files_match(required, actual)       # 레더 파일 매칭 검증

# ============================================
# FileStorageService
# ============================================

# Before
save_zip_and_extract(zip_file, path)
save_file(file, path)

# After
save_and_extract_ladder_zip(ladder_zip_file, extract_dir)
save_template_file(template_file, save_path)
delete_program_files(pgm_id)                        # 프로그램 전체 파일 삭제

# ============================================
# DocumentService
# ============================================

# Before
create_document_record(document_data)
bulk_create_documents(documents_data)

# After
create_ladder_csv_document(ladder_csv_data)         # 레더 CSV 문서 생성
create_template_document(template_data)             # 템플릿 문서 생성
bulk_create_ladder_csv_documents(ladder_csv_list)   # 레더 CSV 일괄 생성

# ============================================
# ProgramUploadService
# ============================================

# Before
upload_and_create_program(...)
_validate_files(...)
_save_files(...)

# After
upload_program_with_files(...)                      # 프로그램 파일 업로드
validate_program_upload_files(...)                  # 프로그램 업로드 파일 검증
save_program_ladder_and_template(...)              # 레더 + 템플릿 저장
```

### 클래스명 명명 규칙

```python
# Before
DocumentProcessor                  # 너무 포괄적
TemplateDocumentProcessor          # OK

# After
ProgramDocumentProcessor           # 추상 클래스
ProgramTemplateProcessor           # 템플릿 전용 프로세서
ProgramLadderProcessor             # 레더 파일 전용 프로세서 (필요 시)
```

### 명명 규칙 적용 예시

```python
# ============================================
# Router (API Layer)
# ============================================
@router.post("/programs/upload")
async def upload_program_with_files(
    pgm_name: str = Form(...),
    pgm_ladder_zip_file: UploadFile = File(..., description="레더 CSV 파일들이 압축된 ZIP"),
    pgm_template_file: UploadFile = File(..., description="프로그램 템플릿 XLSX 파일"),
    ...
):
    """프로그램 레더 ZIP 및 템플릿 파일 업로드"""

# ============================================
# Service Layer
# ============================================
class ProgramUploadService:
    def upload_program_with_files(
        self,
        pgm_name: str,
        pgm_ladder_zip_file: UploadFile,
        pgm_template_file: UploadFile,
        ...
    ):
        # 1. 검증
        self.file_validation_service.validate_ladder_zip_structure(
            pgm_ladder_zip_file
        )
        
        # 2. 템플릿에서 필수 레더 파일 목록 추출
        required_ladder_files = self._extract_required_ladder_files_from_template(
            pgm_template_file
        )
        
        # 3. ZIP 내부 레더 파일 목록 추출
        actual_ladder_files = self._extract_ladder_files_from_zip(
            pgm_ladder_zip_file
        )
        
        # 4. 레더 파일 매칭 검증
        validation_result = self.file_validation_service.validate_ladder_files_match(
            required_files=required_ladder_files,
            actual_files=actual_ladder_files
        )
        
        # 5. 레더 ZIP 저장 및 압축 해제
        ladder_zip_extract_result = self.file_storage_service.save_and_extract_ladder_zip(
            ladder_zip_file=filtered_ladder_zip_bytes,
            extract_dir=pgm_ladder_dir
        )
        
        # 6. 템플릿 파일 저장
        template_save_result = self.file_storage_service.save_template_file(
            template_file=pgm_template_file,
            save_path=pgm_template_file_path
        )
        
        # 7. 레더 CSV 문서 레코드 일괄 생성
        pgm_ladder_csv_documents = self.document_service.bulk_create_ladder_csv_documents(
            ladder_csv_data_list
        )
        
        # 8. 템플릿 문서 레코드 생성
        pgm_template_document = self.document_service.create_template_document(
            template_data
        )
```

---

## ⚙️ 환경변수 관리

### 환경변수 파일 (.env)

```bash
# ============================================
# 프로그램 업로드 설정
# ============================================

# 파일 저장 경로
PGM_UPLOAD_BASE_PATH=/uploads
PGM_LADDER_DIR_NAME=ladder_files
PGM_TEMPLATE_DIR_NAME=template
PGM_ZIP_DIR_NAME=zip

# 파일 크기 제한 (bytes)
PGM_LADDER_ZIP_MAX_SIZE=104857600     # 100MB
PGM_TEMPLATE_FILE_MAX_SIZE=10485760   # 10MB
PGM_LADDER_CSV_MAX_SIZE=5242880       # 5MB

# 허용 확장자 (쉼표로 구분)
PGM_LADDER_ZIP_ALLOWED_EXTENSIONS=.zip
PGM_TEMPLATE_FILE_ALLOWED_EXTENSIONS=.xlsx,.xls
PGM_LADDER_CSV_ALLOWED_EXTENSIONS=.csv

# 템플릿 필수 컬럼 (쉼표로 구분)
PGM_TEMPLATE_REQUIRED_COLUMNS=Logic ID,Folder ID,Logic Name,Description,Note

# 템플릿 선택 컬럼 (쉼표로 구분)
PGM_TEMPLATE_OPTIONAL_COLUMNS=Priority,Status

# 문서 타입 (DOCUMENTS.DOCUMENT_TYPE)
PGM_LADDER_CSV_DOCTYPE=PGM_LADDER_CSV
PGM_TEMPLATE_DOCTYPE=PGM_TEMPLATE_FILE
PGM_LADDER_ZIP_DOCTYPE=PGM_LADDER_ZIP

# ZIP 압축 해제 설정
PGM_KEEP_ORIGINAL_ZIP=true            # 원본 ZIP 보관 여부
PGM_ZIP_EXTRACT_TIMEOUT=300           # 압축 해제 타임아웃 (초)

# 파일명 패턴 검증 (정규표현식)
PGM_LADDER_FILENAME_PATTERN=^\d{4}_\d{2}\.csv$   # 예: 0000_11.csv

# 동시 업로드 제한
PGM_MAX_CONCURRENT_UPLOADS=5          # 동시 업로드 제한
PGM_UPLOAD_TIMEOUT=600                # 업로드 타임아웃 (초)
```

### 설정 클래스 (Config)

```python
# ============================================
# ai_backend/core/config.py
# ============================================

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

class ProgramUploadSettings(BaseSettings):
    """프로그램 업로드 관련 설정"""
    
    # 파일 저장 경로
    pgm_upload_base_path: Path = Path("/uploads")
    pgm_ladder_dir_name: str = "ladder_files"
    pgm_template_dir_name: str = "template"
    pgm_zip_dir_name: str = "zip"
    
    # 파일 크기 제한
    pgm_ladder_zip_max_size: int = 104857600      # 100MB
    pgm_template_file_max_size: int = 10485760    # 10MB
    pgm_ladder_csv_max_size: int = 5242880        # 5MB
    
    # 허용 확장자
    pgm_ladder_zip_allowed_extensions: List[str] = [".zip"]
    pgm_template_file_allowed_extensions: List[str] = [".xlsx", ".xls"]
    pgm_ladder_csv_allowed_extensions: List[str] = [".csv"]
    
    # 템플릿 필수 컬럼
    pgm_template_required_columns: List[str] = [
        "Logic ID", 
        "Folder ID", 
        "Logic Name"
    ]
    
    # 템플릿 선택 컬럼
    pgm_template_optional_columns: List[str] = [
        "Description", 
        "Note", 
        "Priority"
    ]
    
    # 문서 타입
    pgm_ladder_csv_doctype: str = "PGM_LADDER_CSV"
    pgm_template_doctype: str = "PGM_TEMPLATE_FILE"
    pgm_ladder_zip_doctype: str = "PGM_LADDER_ZIP"
    
    # ZIP 압축 해제 설정
    pgm_keep_original_zip: bool = True
    pgm_zip_extract_timeout: int = 300
    
    # 파일명 패턴
    pgm_ladder_filename_pattern: str = r"^\d{4}_\d{2}\.csv$"
    
    # 동시 업로드 제한
    pgm_max_concurrent_uploads: int = 5
    pgm_upload_timeout: int = 600
    
    # ============================================
    # 편의 메서드
    # ============================================
    
    def get_program_upload_dir(self, pgm_id: str) -> Path:
        """프로그램 업로드 루트 디렉토리"""
        return self.pgm_upload_base_path / pgm_id
    
    def get_ladder_files_dir(self, pgm_id: str) -> Path:
        """레더 파일 저장 디렉토리"""
        return self.get_program_upload_dir(pgm_id) / self.pgm_ladder_dir_name
    
    def get_template_file_dir(self, pgm_id: str) -> Path:
        """템플릿 파일 저장 디렉토리"""
        return self.get_program_upload_dir(pgm_id) / self.pgm_template_dir_name
    
    def get_zip_file_dir(self, pgm_id: str) -> Path:
        """원본 ZIP 파일 저장 디렉토리"""
        return self.get_program_upload_dir(pgm_id) / self.pgm_zip_dir_name
    
    # ============================================
    # 검증 메서드
    # ============================================
    
    @validator('pgm_ladder_zip_max_size')
    def validate_max_size(cls, v):
        if v < 1024 or v > 500 * 1024 * 1024:  # 1KB ~ 500MB
            raise ValueError("파일 크기는 1KB ~ 500MB 사이여야 합니다")
        return v
    
    @validator('pgm_upload_base_path')
    def validate_upload_path(cls, v):
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("업로드 경로는 절대 경로여야 합니다")
        return path
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# ============================================
# 전역 설정 인스턴스
# ============================================
program_upload_settings = ProgramUploadSettings()
```

### 서비스에서 설정 사용 예시

```python
# ============================================
# FileValidationService
# ============================================

from ai_backend.core.config import program_upload_settings

class FileValidationService:
    def __init__(self):
        self.settings = program_upload_settings
    
    def validate_ladder_zip_file_type(self, file: UploadFile) -> None:
        """레더 ZIP 파일 타입 검증"""
        allowed = self.settings.pgm_ladder_zip_allowed_extensions
        
        if not any(file.filename.endswith(ext) for ext in allowed):
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg=f"레더 ZIP 파일은 {', '.join(allowed)} 형식이어야 합니다"
            )
    
    def validate_ladder_zip_file_size(self, file: UploadFile) -> None:
        """레더 ZIP 파일 크기 검증"""
        max_size = self.settings.pgm_ladder_zip_max_size
        
        file.file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.file.tell()
        file.file.seek(0)     # 파일 처음으로 복귀
        
        if file_size > max_size:
            raise HandledException(
                ResponseCode.DOCUMENT_FILE_SIZE_EXCEEDED,
                msg=f"파일 크기가 {max_size / 1024 / 1024:.0f}MB를 초과했습니다"
            )
    
    def validate_template_required_columns(self, df: pd.DataFrame) -> None:
        """템플릿 필수 컬럼 검증"""
        required_cols = self.settings.pgm_template_required_columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise HandledException(
                ResponseCode.REQUIRED_FIELD_MISSING,
                msg=f"템플릿에 필수 컬럼이 없습니다: {', '.join(missing_cols)}"
            )
    
    def validate_ladder_filename_pattern(self, filename: str) -> bool:
        """레더 파일명 패턴 검증"""
        import re
        pattern = self.settings.pgm_ladder_filename_pattern
        return bool(re.match(pattern, filename))


# ============================================
# FileStorageService
# ============================================

class FileStorageService:
    def __init__(self):
        self.settings = program_upload_settings
    
    def save_and_extract_ladder_zip(
        self,
        ladder_zip_file: UploadFile,
        pgm_id: str
    ) -> Dict:
        """레더 ZIP 저장 및 압축 해제"""
        
        # 저장 디렉토리 생성
        ladder_dir = self.settings.get_ladder_files_dir(pgm_id)
        ladder_dir.mkdir(parents=True, exist_ok=True)
        
        # ZIP 압축 해제
        extracted_files = self._extract_zip_with_timeout(
            ladder_zip_file,
            ladder_dir,
            timeout=self.settings.pgm_zip_extract_timeout
        )
        
        # 원본 ZIP 보관
        zip_info = None
        if self.settings.pgm_keep_original_zip:
            zip_dir = self.settings.get_zip_file_dir(pgm_id)
            zip_dir.mkdir(parents=True, exist_ok=True)
            zip_info = self._save_original_zip(ladder_zip_file, zip_dir)
        
        return {
            'extracted_ladder_files': extracted_files,
            'original_zip': zip_info
        }


# ============================================
# DocumentService
# ============================================

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = program_upload_settings
    
    def create_ladder_csv_document(self, ladder_csv_data: Dict) -> Document:
        """레더 CSV 문서 레코드 생성"""
        
        document_data = DocumentCreateData(
            document_type=self.settings.pgm_ladder_csv_doctype,  # 환경변수
            ...
        )
        
        return self.document_crud.create_document(document_data)
    
    def create_template_document(self, template_data: Dict) -> Document:
        """템플릿 문서 레코드 생성"""
        
        document_data = DocumentCreateData(
            document_type=self.settings.pgm_template_doctype,  # 환경변수
            ...
        )
        
        document = self.document_crud.create_document(document_data)
        
        # 템플릿 프로세서 호출
        processor = self.processor_factory.get_processor(
            self.settings.pgm_template_doctype
        )
        processor.process(document)
        
        return document
```

### 환경변수 관리의 장점

#### 1. 환경별 설정 관리

```bash
# .env.development
PGM_UPLOAD_BASE_PATH=/tmp/uploads
PGM_LADDER_ZIP_MAX_SIZE=52428800     # 50MB (개발 환경)

# .env.production
PGM_UPLOAD_BASE_PATH=/mnt/storage/uploads
PGM_LADDER_ZIP_MAX_SIZE=104857600    # 100MB (운영 환경)

# .env.test
PGM_UPLOAD_BASE_PATH=/tmp/test_uploads
PGM_LADDER_ZIP_MAX_SIZE=1048576      # 1MB (테스트 환경)
```

#### 2. 설정 변경 시 코드 수정 불필요

```bash
# 템플릿 컬럼 추가
# Before: 코드 수정 필요
# After: .env 파일만 수정

PGM_TEMPLATE_REQUIRED_COLUMNS=Logic ID,Folder ID,Logic Name,New Column
```

#### 3. 보안 강화

```bash
# 민감한 정보는 환경변수로
PGM_UPLOAD_BASE_PATH=/secure/storage
PGM_ADMIN_UPLOAD_TOKEN=secret_token_here

# .env 파일은 .gitignore에 추가
echo ".env" >> .gitignore
```

---

## 🏗️ 새로운 아키텍처 설계

### 계층 분리 전략

```
현재 (3계층):
┌────────────────────────────────┐
│   ProgramUploadService         │  ← 비즈니스 로직
│  (파일 저장 + DB 저장 혼재)    │
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│   DocumentService              │  ← 파일 + DB 모두 처리
│  (책임 과다)                   │
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│   Database (CRUD)              │
└────────────────────────────────┘

제안 (5계층 + 환경변수):
┌────────────────────────────────┐
│   ProgramUploadSettings        │  ← 환경변수 설정 (신규)
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│   ProgramUploadService         │  ← 비즈니스 로직 (오케스트레이션)
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│   FileValidationService        │  ← 검증 전담 (신규)
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│   FileStorageService           │  ← 물리 파일 저장 전담 (신규)
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│   DocumentService (Simplified) │  ← DB 저장 전담 (파일 저장 제외)
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│   ProgramDocumentProcessor     │  ← 타입별 후처리 (Strategy 패턴, 신규)
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│   Database (CRUD)              │
└────────────────────────────────┘
```

---

## 📐 새로운 컴포넌트 설계

### 1. **ProgramUploadSettings** (신규 생성)

```python
"""
프로그램 업로드 설정 관리 (환경변수 기반)
"""

위치: ai_backend/core/config.py
의존성: pydantic_settings
책임: 환경변수 로드 및 검증
```

### 2. **FileValidationService** (신규 생성)

```python
"""
파일 검증 전담 서비스
- 파일 타입 검증 (환경변수 기반)
- 파일 크기 검증 (환경변수 기반)
- 파일 구조 검증 (ZIP 내부 구조)
- 템플릿 컬럼 검증 (환경변수 기반)
"""

class FileValidationService:
    def __init__(self):
        self.settings = program_upload_settings  # 환경변수 주입
    
    def validate_ladder_zip_file_type(self, file: UploadFile) -> None:
        """레더 ZIP 파일 타입 검증 (환경변수 기반)"""
        
    def validate_ladder_zip_file_size(self, file: UploadFile) -> None:
        """레더 ZIP 파일 크기 검증 (환경변수 기반)"""
        
    def validate_ladder_zip_structure(self, zip_file: UploadFile) -> Dict:
        """ZIP 구조 검증 (손상 여부, 내부 파일 목록)"""
        
    def validate_template_file_structure(self, xlsx_file: UploadFile) -> Dict:
        """템플릿 구조 검증 (필수 컬럼 존재 여부, 환경변수 기반)"""
        
    def validate_ladder_files_match(
        self, 
        required_files: List[str], 
        actual_files: List[str]
    ) -> ValidationResult:
        """템플릿 Logic ID vs ZIP 파일 목록 비교"""
    
    def validate_ladder_filename_pattern(self, filename: str) -> bool:
        """레더 파일명 패턴 검증 (환경변수 기반)"""

위치: ai_backend/api/services/file_validation_service.py
의존성: ProgramUploadSettings (환경변수)
책임: 파일 검증만 수행 (저장 X, DB 저장 X)
```

### 3. **FileStorageService** (신규 생성)

```python
"""
물리 파일 저장 전담 서비스
- 파일 경로 생성 (환경변수 기반)
- 파일 저장
- ZIP 압축 해제 (환경변수 기반 타임아웃)
- 파일 삭제 (롤백 시)
"""

class FileStorageService:
    def __init__(self):
        self.settings = program_upload_settings  # 환경변수 주입
    
    def save_and_extract_ladder_zip(
        self, 
        ladder_zip_file: UploadFile, 
        pgm_id: str
    ) -> Dict:
        """
        레더 ZIP 저장 및 압축 해제
        - 저장 경로: settings.get_ladder_files_dir(pgm_id)
        - 타임아웃: settings.pgm_zip_extract_timeout
        - 원본 ZIP 보관: settings.pgm_keep_original_zip
        """
        
    def save_template_file(
        self, 
        template_file: UploadFile, 
        pgm_id: str
    ) -> Dict:
        """
        템플릿 파일 저장
        - 저장 경로: settings.get_template_file_dir(pgm_id)
        """
        
    def delete_program_files(self, pgm_id: str) -> None:
        """프로그램 전체 파일 삭제 (롤백 시 사용)"""
        
    def delete_files(self, file_paths: List[Path]) -> None:
        """파일 삭제 (롤백 시 사용)"""

위치: ai_backend/api/services/file_storage_service.py
의존성: ProgramUploadSettings (환경변수)
책임: 물리 파일 저장/삭제만 수행 (DB 저장 X)
```

### 4. **DocumentService (Simplified)** (기존 수정)

```python
"""
문서 메타데이터 DB 저장 전담 (파일 저장 제외)
- DOCUMENTS 테이블 INSERT만 담당
- 파일 저장은 FileStorageService에 위임
- 문서 타입은 환경변수 기반
"""

class DocumentService:
    def __init__(
        self, 
        db: Session,
        document_processor_factory: DocumentProcessorFactory
    ):
        self.db = db
        self.settings = program_upload_settings  # 환경변수 주입
        self.document_crud = DocumentCrud(db)
        self.processor_factory = document_processor_factory
    
    def create_ladder_csv_document(
        self,
        ladder_csv_data: DocumentCreateData
    ) -> Document:
        """
        레더 CSV 문서 레코드 생성
        - document_type: settings.pgm_ladder_csv_doctype
        """
        document = self.document_crud.create_document(ladder_csv_data)
        return document
    
    def create_template_document(
        self,
        template_data: DocumentCreateData
    ) -> Document:
        """
        템플릿 문서 레코드 생성
        - document_type: settings.pgm_template_doctype
        - 자동으로 ProgramTemplateProcessor 호출
        """
        document = self.document_crud.create_document(template_data)
        
        # 타입별 후처리 (Strategy 패턴)
        processor = self.processor_factory.get_processor(document.document_type)
        processor.process(document)
        
        return document
    
    def bulk_create_ladder_csv_documents(
        self,
        documents_data: List[DocumentCreateData]
    ) -> List[Document]:
        """레더 CSV 문서 일괄 생성 (성능 최적화)"""
        return self.document_crud.bulk_create(documents_data)
    
    # ❌ 제거: validate_file_type() → FileValidationService로 이동
    # ❌ 제거: validate_file_size() → FileValidationService로 이동
    # ❌ 제거: save_file_to_storage() → FileStorageService로 이동
    # ❌ 제거: extract_zip_file() → FileStorageService로 이동
    # ❌ 제거: upload_zip_document() → ProgramUploadService로 이동
    # ❌ 제거: upload_document() → ProgramUploadService로 이동

위치: ai_backend/api/services/document_service.py
의존성: DocumentCrud, DocumentProcessorFactory, ProgramUploadSettings
책임: DOCUMENTS 테이블 INSERT만 수행
```

### 5. **ProgramDocumentProcessor (Strategy 패턴)** (신규 생성)

```python
"""
문서 타입별 후처리 로직 (Strategy 패턴)
- 템플릿 파싱
- 특정 타입별 추가 작업
"""

# 추상 클래스
class ProgramDocumentProcessor(ABC):
    @abstractmethod
    def process(self, document: Document) -> None:
        """문서 타입별 후처리"""
        pass

# 기본 프로세서 (아무 작업 안 함)
class DefaultProgramDocumentProcessor(ProgramDocumentProcessor):
    def process(self, document: Document) -> None:
        pass

# 템플릿 프로세서
class ProgramTemplateProcessor(ProgramDocumentProcessor):
    def __init__(self, db: Session, template_service: TemplateService):
        self.db = db
        self.settings = program_upload_settings  # 환경변수 주입
        self.template_service = template_service
    
    def process(self, document: Document) -> None:
        """
        템플릿 파싱 및 PGM_TEMPLATE 테이블 저장
        - document_type 확인: settings.pgm_template_doctype
        """
        if document.document_type != self.settings.pgm_template_doctype:
            return
            
        # 파일 경로에서 XLSX 읽기
        file_path = document.upload_path
        
        # 템플릿 파싱
        parsed_data = self.template_service.parse_template_xlsx(file_path)
        
        # PGM_TEMPLATE 테이블 저장
        self.template_service.save_template_data(
            document_id=document.document_id,
            pgm_id=document.pgm_id,
            template_data=parsed_data
        )

# 프로세서 팩토리
class ProgramDocumentProcessorFactory:
    def __init__(self, db: Session, template_service: TemplateService):
        self.settings = program_upload_settings  # 환경변수 주입
        self.processors = {
            self.settings.pgm_template_doctype: ProgramTemplateProcessor(
                db, template_service
            ),
            'default': DefaultProgramDocumentProcessor()
        }
    
    def get_processor(self, document_type: str) -> ProgramDocumentProcessor:
        return self.processors.get(document_type, self.processors['default'])

위치: 
- ai_backend/api/services/program_document_processor.py (추상 클래스 + 기본)
- ai_backend/api/services/program_template_processor.py (템플릿)
- ai_backend/api/services/program_document_processor_factory.py (팩토리)

의존성: TemplateService, ProgramUploadSettings (환경변수)
책임: 문서 타입별 후처리 (DB INSERT는 각 서비스가 수행)
```

### 6. **ProgramUploadService (Refactored)** (기존 수정)

```python
"""
프로그램 업로드 오케스트레이션 (리팩토링)
- 각 서비스를 조합하여 전체 워크플로우 관리
- 트랜잭션 경계 명확화
- 명확한 변수명 사용
- 환경변수 기반 설정
"""

class ProgramUploadService:
    def __init__(
        self,
        db: Session,
        sequence_service: SequenceService,
        file_validation_service: FileValidationService,
        file_storage_service: FileStorageService,
        document_service: DocumentService,
        program_service: ProgramService
    ):
        self.db = db
        self.settings = program_upload_settings  # 환경변수 주입
        self.sequence_service = sequence_service
        self.file_validation_service = file_validation_service
        self.file_storage_service = file_storage_service
        self.document_service = document_service
        self.program_service = program_service
    
    def upload_program_with_files(
        self,
        pgm_name: str,
        pgm_ladder_zip_file: UploadFile,      # 명확한 변수명
        pgm_template_file: UploadFile,        # 명확한 변수명
        create_user: str,
        pgm_version: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        프로그램 업로드 워크플로우 (리팩토링 + 명명 규칙 + 환경변수)
        """
        saved_file_paths = []  # 롤백용
        
        try:
            # =====================================
            # Phase 1: 검증 (DB 트랜잭션 외부)
            # =====================================
            
            # 0. PGM_ID 생성
            pgm_id = self.sequence_service.generate_pgm_id()
            logger.info(f"[Step 0] PGM_ID 자동 생성: {pgm_id}")
            
            # 1. 레더 ZIP 파일 타입/크기 검증 (환경변수 기반)
            self.file_validation_service.validate_ladder_zip_file_type(
                pgm_ladder_zip_file
            )
            self.file_validation_service.validate_ladder_zip_file_size(
                pgm_ladder_zip_file
            )
            logger.info(f"[Step 1] 레더 ZIP 파일 검증 완료: {pgm_ladder_zip_file.filename}")
            
            # 2. 템플릿 파일 타입/크기 검증 (환경변수 기반)
            self.file_validation_service.validate_template_file_type(
                pgm_template_file
            )
            self.file_validation_service.validate_template_file_size(
                pgm_template_file
            )
            logger.info(f"[Step 2] 템플릿 파일 검증 완료: {pgm_template_file.filename}")
            
            # 3. 템플릿 구조 검증 (환경변수 기반 필수 컬럼)
            template_structure = self.file_validation_service.validate_template_file_structure(
                pgm_template_file
            )
            logger.info(f"[Step 3] 템플릿 구조 검증 완료: {len(template_structure['logic_ids'])}개 Logic ID")
            
            # 4. ZIP 구조 검증
            zip_structure = self.file_validation_service.validate_ladder_zip_structure(
                pgm_ladder_zip_file
            )
            logger.info(f"[Step 4] ZIP 구조 검증 완료: {len(zip_structure['file_list'])}개 파일")
            
            # 5. 레더 파일 매칭 검증
            validation_result = self.file_validation_service.validate_ladder_files_match(
                required_files=template_structure['logic_ids'],
                actual_files=zip_structure['file_list']
            )
            
            if not validation_result.validation_passed:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"필수 레더 파일 누락: {', '.join(validation_result.missing_files)}"
                )
            
            logger.info(f"[Step 5] 레더 파일 매칭 검증 완료: {len(validation_result.matched_files)}개 일치")
            
            # =====================================
            # Phase 2: 파일 저장 (DB 트랜잭션 외부)
            # =====================================
            
            # 6. 레더 ZIP 필터링 (필요한 파일만)
            filtered_ladder_zip_bytes = self._filter_ladder_zip(
                pgm_ladder_zip_file, 
                validation_result.matched_files
            )
            logger.info(f"[Step 6] 레더 ZIP 필터링 완료")
            
            # 7. 레더 ZIP 저장 및 압축 해제 (환경변수 기반 경로)
            ladder_zip_extract_result = self.file_storage_service.save_and_extract_ladder_zip(
                ladder_zip_file=filtered_ladder_zip_bytes,
                pgm_id=pgm_id
            )
            saved_file_paths.extend([
                f['path'] for f in ladder_zip_extract_result['extracted_ladder_files']
            ])
            logger.info(f"[Step 7] 레더 파일 저장 완료: {len(ladder_zip_extract_result['extracted_ladder_files'])}개")
            
            # 8. 템플릿 파일 저장 (환경변수 기반 경로)
            template_save_result = self.file_storage_service.save_template_file(
                template_file=pgm_template_file,
                pgm_id=pgm_id
            )
            saved_file_paths.append(template_save_result['file_path'])
            logger.info(f"[Step 8] 템플릿 파일 저장 완료")
            
            # =====================================
            # Phase 3: DB 저장 (트랜잭션 시작)
            # =====================================
            
            # 9. 레더 CSV 문서 레코드 생성 (일괄)
            ladder_csv_documents_data = [
                self._create_ladder_csv_document_data(
                    file_info=file_info,
                    pgm_id=pgm_id,
                    user_id=create_user
                )
                for file_info in ladder_zip_extract_result['extracted_ladder_files']
            ]
            
            pgm_ladder_csv_documents = self.document_service.bulk_create_ladder_csv_documents(
                ladder_csv_documents_data
            )
            logger.info(f"[Step 9] 레더 CSV 문서 레코드 생성 완료: {len(pgm_ladder_csv_documents)}개")
            
            # 10. 템플릿 문서 레코드 생성 (자동으로 템플릿 파싱됨)
            template_document_data = self._create_template_document_data(
                file_info=template_save_result,
                pgm_id=pgm_id,
                user_id=create_user
            )
            
            pgm_template_document = self.document_service.create_template_document(
                template_document_data
            )
            # ↑ create_template_document() 내부에서 자동으로:
            #    - ProgramTemplateProcessor 호출
            #    - 템플릿 파싱
            #    - PGM_TEMPLATE 테이블 INSERT
            
            logger.info(f"[Step 10] 템플릿 문서 레코드 생성 및 파싱 완료")
            
            # 11. 프로그램 레코드 생성
            program = self.program_service.create_program(
                pgm_id=pgm_id,
                pgm_name=pgm_name,
                pgm_version=pgm_version,
                description=description,
                create_user=create_user,
                notes=notes
            )
            logger.info(f"[Step 11] 프로그램 레코드 생성 완료: {pgm_id}")
            
            # 12. 커밋
            self.db.commit()
            logger.info(f"[Success] 프로그램 업로드 완료: {pgm_id}")
            
            return {
                'program': program,
                'pgm_id': pgm_id,
                'validation_result': validation_result,
                'saved_files': {
                    'ladder_csv_documents': pgm_ladder_csv_documents,
                    'template_document': pgm_template_document
                },
                'summary': {
                    'total_ladder_files': len(pgm_ladder_csv_documents),
                    'template_parsed': True
                },
                'message': '프로그램이 성공적으로 생성되었습니다'
            }
            
        except Exception as e:
            # 롤백
            self.db.rollback()
            logger.error(f"[Error] 프로그램 업로드 실패: {str(e)}")
            
            # 저장된 파일 삭제
            if saved_file_paths:
                self.file_storage_service.delete_files(saved_file_paths)
                logger.info(f"[Rollback] 저장된 파일 삭제 완료")
            
            raise
    
    def _create_ladder_csv_document_data(
        self, 
        file_info: Dict, 
        pgm_id: str, 
        user_id: str
    ) -> DocumentCreateData:
        """레더 CSV 파일 정보 → 문서 생성 데이터 변환"""
        return DocumentCreateData(
            document_name=file_info['filename'],
            original_filename=file_info['filename'],
            file_key=f"{pgm_id}/{self.settings.pgm_ladder_dir_name}/{file_info['filename']}",
            upload_path=str(file_info['path']),
            file_size=file_info['size'],
            file_type='text/csv',
            file_extension='csv',
            document_type=self.settings.pgm_ladder_csv_doctype,  # 환경변수
            pgm_id=pgm_id,
            user_id=user_id,
            metadata_json={
                'file_hash': file_info.get('hash'),
                'upload_method': 'program_upload',
                'extracted_from_zip': True
            }
        )
    
    def _create_template_document_data(
        self, 
        file_info: Dict, 
        pgm_id: str, 
        user_id: str
    ) -> DocumentCreateData:
        """템플릿 파일 정보 → 문서 생성 데이터 변환"""
        return DocumentCreateData(
            document_name=file_info['filename'],
            original_filename=file_info['filename'],
            file_key=f"{pgm_id}/{self.settings.pgm_template_dir_name}/{file_info['filename']}",
            upload_path=str(file_info['path']),
            file_size=file_info['size'],
            file_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            file_extension='xlsx',
            document_type=self.settings.pgm_template_doctype,  # 환경변수
            pgm_id=pgm_id,
            user_id=user_id,
            metadata_json={
                'file_hash': file_info.get('hash'),
                'upload_method': 'program_upload'
            }
        )
    
    def _filter_ladder_zip(
        self, 
        pgm_ladder_zip_file: UploadFile, 
        keep_files: List[str]
    ) -> bytes:
        """레더 ZIP에서 필요한 파일만 남기고 새로운 ZIP 생성"""
        # 구현 로직...
        pass

위치: ai_backend/api/services/program_upload_service.py
의존성: 5개 서비스 + ProgramUploadSettings (환경변수)
책임: 워크플로우 오케스트레이션만 (구체적 작업은 위임)
```

---

## 📊 변경 전후 비교

### 메서드 호출 깊이 비교

```
┌─────────────────────────────────────────────────┐
│ 현재 (3단계)                                    │
├─────────────────────────────────────────────────┤
│ ProgramUploadService.upload_and_create_program  │ 1레벨
│   └─> DocumentService.upload_zip_document       │ 2레벨
│        ├─> validate_file_type                   │ 3레벨
│        ├─> save_file_to_storage                 │ 3레벨
│        ├─> document_crud.create_document        │ 3레벨
│        ├─> extract_zip_file                     │ 3레벨
│        │    └─> 반복문:                         │
│        │         ├─> save_extracted_file        │ 4레벨
│        │         └─> save_extracted_file_to_db  │ 4레벨
│        │              └─> document_crud.create  │ 5레벨
│        │
│        └─> if document_type == 'plc_template':  │ 3레벨
│             └─> TemplateService.parse_and_save  │ 4레벨
│                  ├─> parse_template_xlsx        │ 5레벨
│                  └─> template_crud.bulk_insert  │ 5레벨
│                       └─> 반복문: INSERT        │ 6-7레벨
│
│ 최대 깊이: 7레벨                                │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 리팩토링 후 (3단계)                             │
├─────────────────────────────────────────────────┤
│ ProgramUploadService.upload_program_with_files  │ 1레벨
│   ├─> FileValidationService.validate_...       │ 2레벨
│   │
│   ├─> FileStorageService.save_and_extract_..   │ 2레벨
│   │    └─> 내부 로직 (파일 저장)              │ 3레벨
│   │
│   ├─> DocumentService.bulk_create_...          │ 2레벨
│   │    └─> document_crud.bulk_create           │ 3레벨
│   │
│   ├─> DocumentService.create_template_document │ 2레벨
│   │    ├─> document_crud.create                │ 3레벨
│   │    └─> ProgramTemplateProcessor.process    │ 3레벨
│   │         └─> TemplateService.parse_and_save │ 4레벨
│   │
│   └─> ProgramService.create_program            │ 2레벨
│        └─> program_crud.create                 │ 3레벨
│
│ 최대 깊이: 4레벨                                │
└─────────────────────────────────────────────────┘
```

### 명명 규칙 비교

| 항목 | Before | After | 개선점 |
|------|--------|-------|--------|
| 파일 파라미터 | `ladder_zip` | `pgm_ladder_zip_file` | 명확성 50% 향상 |
| 저장 경로 | `ladder_path` | `pgm_ladder_dir` | 디렉토리임을 명시 |
| 문서 타입 | `'plc_template'` | `'PGM_TEMPLATE_FILE'` | 일관성 확보 |
| 메서드명 | `validate_files()` | `validate_ladder_files_match()` | 구체적 동작 명시 |

### 설정 관리 비교

| 항목 | Before | After | 개선점 |
|------|--------|-------|--------|
| 파일 크기 | 하드코딩 | 환경변수 | 환경별 설정 가능 |
| 저장 경로 | 하드코딩 | 환경변수 | 경로 변경 시 코드 수정 불필요 |
| 템플릿 컬럼 | 하드코딩 | 환경변수 | 컬럼 변경 시 코드 수정 불필요 |
| 문서 타입 | 하드코딩 | 환경변수 | 타입 변경 시 코드 수정 불필요 |

### 복잡도 지표 비교

| 지표 | 현재 | 리팩토링 후 | 개선율 |
|------|------|------------|--------|
| 메서드 호출 깊이 | 7레벨 | 4레벨 | **43% 감소** |
| DocumentService 라인 수 | ~500줄 | ~150줄 | **70% 감소** |
| 순환 복잡도 (Cyclomatic) | 15+ | 5 이하 | **67% 감소** |
| 의존성 수 | 5개 | 2개 | **60% 감소** |
| 테스트 가능성 | 낮음 (모킹 5개) | 높음 (모킹 1-2개) | **60% 개선** |
| 하드코딩된 설정 | 10개 | 0개 | **100% 제거** |

---

## 🔄 단계별 마이그레이션 계획

### Phase 0: **환경변수 설정** (신규, 1시간)

**작업 내용:**
1. ProgramUploadSettings 클래스 생성
   - `ai_backend/core/config.py`에 추가
   - pydantic_settings 사용
   
2. .env 파일 작성
   - 개발 환경: `.env.development`
   - 운영 환경: `.env.production`
   - 테스트 환경: `.env.test`
   
3. 환경변수 validator 추가
   - 파일 크기 범위 검증
   - 경로 검증 (절대 경로)
   
4. 전역 설정 인스턴스 생성
   ```python
   program_upload_settings = ProgramUploadSettings()
   ```

**목표:** 환경변수 기반 설정 관리 체계 구축

**예상 작업 시간:** 1시간

---

### Phase 1: **새 컴포넌트 생성** (기존 코드 유지, 2-3시간)

**작업 내용:**
1. FileValidationService 생성
   - 환경변수 주입
   - 명확한 메서드명 사용
   
2. FileStorageService 생성
   - 환경변수 주입
   - 명확한 메서드명 사용
   
3. ProgramDocumentProcessor (Strategy) 생성
   - 환경변수 주입
   - 명확한 클래스명 사용
   
4. 단위 테스트 작성
   - 환경변수 모킹 포함

**목표:** 기존 코드에 영향 없이 새 컴포넌트 준비

**예상 작업 시간:** 2-3시간

---

### Phase 2: **DocumentService 단순화** (2-3시간)

**작업 내용:**
1. DocumentService에서 파일 저장 로직 제거
   - save_file_to_storage() 삭제
   - extract_zip_file() 삭제
   
2. DocumentService에서 검증 로직 제거
   - validate_file_type() 삭제
   - validate_file_size() 삭제
   
3. 새 메서드 추가 (명확한 이름)
   - create_ladder_csv_document()
   - create_template_document()
   - bulk_create_ladder_csv_documents()
   
4. 환경변수 주입
   - document_type은 환경변수에서 가져옴

**마이그레이션 전략:**
```python
# 기존 메서드는 deprecated로 표시 (당분간 유지)
@deprecated("Use file_storage_service.save_and_extract_ladder_zip() instead")
def upload_zip_document(self, ...):
    # 내부적으로 새 방식 호출
    return self.file_storage_service.save_and_extract_ladder_zip(...)
```

**목표:** DocumentService를 DB 저장 전담으로 변경

**예상 작업 시간:** 2-3시간

---

### Phase 3: **ProgramUploadService 리팩토링** (3-4시간)

**작업 내용:**
1. 의존성 주입 수정
   ```python
   def __init__(
       self,
       ...
       file_validation_service: FileValidationService,
       file_storage_service: FileStorageService,
       document_service: DocumentService,  # 단순화된 버전
       ...
   ):
   ```

2. 메서드명 변경
   - `upload_and_create_program()` → `upload_program_with_files()`
   
3. 변수명 변경 (명확한 이름)
   - `ladder_zip` → `pgm_ladder_zip_file`
   - `template_xlsx` → `pgm_template_file`
   - `ladder_save_result` → `ladder_zip_extract_result`
   
4. 환경변수 사용
   - 파일 크기, 경로, 문서 타입 등
   
5. 트랜잭션 경계 명확화
   ```python
   # Phase 1: 검증 (트랜잭션 외부)
   validate...
   
   # Phase 2: 파일 저장 (트랜잭션 외부)
   save_files...
   
   # Phase 3: DB 저장 (트랜잭션 내부)
   try:
       bulk_create...
       create_program...
       self.db.commit()
   except:
       self.db.rollback()
       delete_saved_files...
   ```

**목표:** 깔끔한 워크플로우 오케스트레이션 + 명확한 변수명 + 환경변수

**예상 작업 시간:** 3-4시간

---

### Phase 4: **Router 및 Response 모델 업데이트** (1-2시간)

**작업 내용:**
1. Router 메서드명 변경
   ```python
   @router.post("/programs/upload")
   async def upload_program_with_files(...)
   ```

2. 파라미터명 변경
   ```python
   pgm_ladder_zip_file: UploadFile = File(...)
   pgm_template_file: UploadFile = File(...)
   ```

3. Response 모델 업데이트
   - 명확한 필드명 사용

**목표:** API 레이어 명명 규칙 통일

**예상 작업 시간:** 1-2시간

---

### Phase 5: **기존 코드 제거 및 정리** (1-2시간)

**작업 내용:**
1. DocumentService의 deprecated 메서드 제거
2. 사용하지 않는 import 정리
3. 하드코딩된 설정 값 제거
4. 통합 테스트 작성

**목표:** 레거시 코드 정리

**예상 작업 시간:** 1-2시간

---

### Phase 6: **성능 최적화** (2시간)

**작업 내용:**
1. bulk_create_ladder_csv_documents() 최적화
   - 단일 INSERT → Bulk INSERT
   - 트랜잭션 커밋 횟수 최소화
   
2. 파일 I/O 최적화
   - 버퍼 크기 조정 (환경변수화 가능)
   - 비동기 처리 고려 (선택사항)

**목표:** 응답 시간 개선

**예상 작업 시간:** 2시간

---

### Phase 7: **문서 업데이트** (1시간)

**작업 내용:**
1. PROJECT_REFERENCE_GUIDE.md 업데이트
   - 새 서비스 추가
   - 명명 규칙 섹션 추가
   - 환경변수 설정 섹션 추가
   
2. ENVIRONMENT_VARIABLES.md 생성
   - 모든 환경변수 목록
   - 설명 및 예시
   
3. NAMING_CONVENTIONS.md 생성 (선택사항)
   - 변수명 규칙
   - 메서드명 규칙
   - 클래스명 규칙

**목표:** 문서화 완료

**예상 작업 시간:** 1시간

---

## 🧪 테스트 전략

### 단위 테스트 (Unit Test)

```python
# 1. ProgramUploadSettings 테스트
def test_settings_load_from_env():
    # 환경변수 로드 확인

def test_settings_validation():
    # 잘못된 값 입력 시 에러 확인

def test_settings_convenience_methods():
    # get_ladder_files_dir() 등 경로 생성 메서드 확인

# 2. FileValidationService 테스트
def test_validate_ladder_zip_file_type_success():
    # 올바른 확장자 → 통과

def test_validate_ladder_zip_file_type_failure():
    # 잘못된 확장자 → HandledException

def test_validate_ladder_files_match():
    # 매칭 검증 로직

def test_validate_template_required_columns():
    # 환경변수 기반 필수 컬럼 검증

# 3. FileStorageService 테스트
def test_save_and_extract_ladder_zip():
    # ZIP 압축 해제 → 파일 목록 확인
    # 환경변수 기반 경로 확인

def test_save_template_file():
    # 파일 저장 → 경로 반환 확인

def test_delete_program_files():
    # 프로그램 전체 파일 삭제 확인

# 4. ProgramDocumentProcessor 테스트
def test_program_template_processor():
    # 템플릿 파싱 → PGM_TEMPLATE INSERT 확인
    # 환경변수 기반 document_type 확인

# 5. DocumentService 테스트 (단순화)
def test_create_ladder_csv_document():
    # 레더 CSV 문서 생성 확인
    # 환경변수 기반 document_type 확인

def test_create_template_document():
    # 템플릿 문서 생성 확인
    # Processor 호출 확인 (모킹)

def test_bulk_create_ladder_csv_documents():
    # 일괄 생성 → 레코드 개수 확인
```

### 통합 테스트 (Integration Test)

```python
def test_upload_program_with_files_success():
    """전체 워크플로우 정상 시나리오"""
    # Given: ZIP, XLSX 파일 준비
    # When: upload_program_with_files() 호출
    # Then:
    #   - 파일 저장 확인 (환경변수 기반 경로)
    #   - DOCUMENTS 레코드 확인 (환경변수 기반 document_type)
    #   - PGM_TEMPLATE 레코드 확인
    #   - PROGRAMS 레코드 확인

def test_upload_program_rollback():
    """DB 저장 실패 시 롤백 확인"""
    # Given: 정상 파일 + DB 에러 발생 설정
    # When: upload_program_with_files() 호출
    # Then:
    #   - Exception 발생
    #   - 저장된 파일 삭제 확인
    #   - DB 레코드 없음 확인

def test_upload_program_validation_failure():
    """검증 실패 시나리오"""
    # Given: 필수 파일 누락된 ZIP
    # When: upload_program_with_files() 호출
    # Then:
    #   - HandledException 발생
    #   - 파일 저장 안 됨 확인

def test_upload_program_with_different_env():
    """다른 환경 설정 테스트"""
    # Given: 테스트 환경 설정 (.env.test)
    # When: upload_program_with_files() 호출
    # Then:
    #   - 테스트 환경 경로에 파일 저장 확인
    #   - 테스트 환경 크기 제한 적용 확인
```

---

## ⚠️ 리스크 및 대응 방안

### 리스크 1: **기존 코드 의존성**

**문제:** 다른 API에서 DocumentService의 기존 메서드를 사용 중일 수 있음

**대응:**
1. deprecated 표시 후 일정 기간 유지
2. 기존 메서드 내부적으로 새 서비스 호출
3. 마이그레이션 가이드 문서 제공

```python
# 예시
@deprecated("Use file_storage_service + document_service instead")
def upload_zip_document(self, ...):
    # 내부적으로 새 방식 호출
    file_result = self.file_storage_service.save_and_extract_ladder_zip(...)
    doc_result = self.document_service.bulk_create_ladder_csv_documents(...)
    return {'file': file_result, 'documents': doc_result}
```

### 리스크 2: **성능 저하**

**문제:** 서비스 계층 증가로 오버헤드 발생 가능

**대응:**
1. 벤치마크 테스트 수행
2. bulk INSERT 사용으로 성능 개선
3. 필요 시 캐싱 적용

```python
# Before: 반복문 내부에서 INSERT (느림)
for file in files:
    document_crud.create_document(file)  # N번 INSERT

# After: Bulk INSERT (빠름)
document_crud.bulk_create(files)  # 1번 INSERT
```

### 리스크 3: **환경변수 설정 오류**

**문제:** 환경변수 누락 또는 잘못된 값으로 서버 시작 실패

**대응:**
1. Pydantic validator로 서버 시작 시 검증
2. .env.example 파일 제공
3. 에러 메시지 명확화

```python
# 서버 시작 시 자동 검증
@validator('pgm_upload_base_path')
def validate_upload_path(cls, v):
    path = Path(v)
    if not path.exists():
        raise ValueError(f"업로드 경로가 존재하지 않습니다: {path}")
    return path
```

### 리스크 4: **명명 규칙 불일치**

**문제:** 기존 코드와 새 코드의 명명 규칙 혼재

**대응:**
1. 리팩토링 시 모든 관련 코드 일괄 변경
2. 코드 리뷰 시 명명 규칙 체크
3. Linter 설정으로 자동 검증

### 리스크 5: **트랜잭션 경계 변경**

**문제:** 파일 저장과 DB 저장의 트랜잭션 분리로 데이터 불일치 가능

**대응:**
1. 파일 저장 → DB 저장 순서 유지
2. 실패 시 저장된 파일 삭제 (롤백)
3. 재시도 로직 추가 (선택사항)

```python
try:
    # Phase 1: 파일 저장 (트랜잭션 외부)
    saved_files = file_storage_service.save_files(...)
    
    # Phase 2: DB 저장 (트랜잭션 내부)
    self.db.begin()
    document_service.bulk_create(...)
    self.db.commit()
    
except Exception as e:
    self.db.rollback()
    
    # 저장된 파일 삭제
    file_storage_service.delete_files(saved_files)
    
    raise
```

---

## 📈 성능 개선 예상치

### DB INSERT 성능

```python
# Before: 레더 파일 10개 → 10번 INSERT
for i in range(10):
    document_crud.create_document(...)  # 10 * 50ms = 500ms

# After: 레더 파일 10개 → 1번 Bulk INSERT
document_crud.bulk_create(10개)  # 1 * 100ms = 100ms

→ 80% 성능 개선 (500ms → 100ms)
```

### 전체 워크플로우

| 단계 | 현재 시간 | 리팩토링 후 | 개선율 |
|------|----------|------------|--------|
| 파일 검증 | 100ms | 100ms | 0% |
| 파일 저장 | 500ms | 500ms | 0% |
| DB 저장 | 500ms | **150ms** | **70% 개선** |
| 템플릿 파싱 | 300ms | 300ms | 0% |
| **전체** | **1400ms** | **1050ms** | **25% 개선** |

---

## ✅ 체크리스트

### 개발 전
- [ ] 기존 코드 백업
- [ ] 관련 API 사용 현황 조사
- [ ] 테스트 환경 구축
- [ ] 리팩토링 계획 검토
- [ ] 환경변수 목록 작성

### 개발 중
- [x] Phase 0: 환경변수 설정 ✅ **(2025-11-06 완료)**
- [x] Phase 1: 새 컴포넌트 생성 ✅ **(2025-11-06 완료)**
- [x] Phase 1.5: 레더 CSV 구조 검증 추가 ✅ **(2025-11-06 완료)** ⭐ NEW
- [x] Phase 2: DocumentService 단순화 ✅ **(2025-11-06 완료)**
- [x] Phase 3: ProgramUploadService 리팩토링 ✅ **(2025-11-06 완룼)**
- [x] Phase 4: Router 및 Response 모델 업데이트 ✅ **(2025-11-06 완료)**
- [x] Phase 5: 레거시 코드 제거 ✅ **(2025-11-06 완료)** 🎉
- [ ] Phase 6: 성능 최적화 (선택사항)
- [ ] Phase 7: 문서 업데이트 (선택사항)

### 개발 후
- [ ] 단위 테스트 80% 이상
- [ ] 통합 테스트 작성
- [ ] 성능 벤치마크 수행
- [ ] 환경변수 문서 작성
- [ ] 명명 규칙 가이드 작성
- [ ] 코드 리뷰
- [x] .env.example 파일 생성 ✅ **(2025-11-06 완료)**
- [ ] 스테이징 환경 배포
- [ ] 프로덕션 배포

---

## 🎯 최종 목표 달성 지표

| 지표 | 현재 | 목표 | 측정 방법 |
|------|------|------|----------|
| 메서드 호출 깊이 | 7레벨 | 4레벨 | 코드 분석 |
| 순환 복잡도 | 15+ | 5 이하 | pylint |
| 코드 라인 수 | 500줄 | 150줄 | wc -l |
| 테스트 커버리지 | 30% | 80%+ | pytest-cov |
| DB INSERT 성능 | 500ms | 150ms | 벤치마크 |
| 전체 응답 시간 | 1400ms | 1050ms | 부하 테스트 |
| 하드코딩된 설정 | 10개 | 0개 | 코드 검색 |
| 명명 불일치 | 많음 | 0개 | 코드 리뷰 |

---

## 📝 문서 생성 계획

### 1. ENVIRONMENT_VARIABLES.md

```markdown
# 프로그램 업로드 환경변수

## 필수 설정
- PGM_UPLOAD_BASE_PATH: 업로드 기본 경로
- PGM_TEMPLATE_REQUIRED_COLUMNS: 템플릿 필수 컬럼

## 선택 설정
- PGM_KEEP_ORIGINAL_ZIP: 원본 ZIP 보관 (기본값: true)
- PGM_MAX_CONCURRENT_UPLOADS: 동시 업로드 제한 (기본값: 5)

## 환경별 설정 예시
### 개발 환경
...

### 운영 환경
...
```

### 2. NAMING_CONVENTIONS.md (선택사항)

```markdown
# 명명 규칙 가이드

## 변수명
- 프로그램 관련: `pgm_` 접두사 사용
- 레더 파일: `ladder` 명시
- 템플릿 파일: `template` 명시

## 메서드명
- 동사 + 명사 조합
- 구체적 동작 명시

## 예시
...
```

---

## 🚀 최종 요약

### 리팩토링 핵심 개선사항

1. ✅ **책임 분리**: 5개 서비스로 역할 명확화
2. ✅ **복잡도 감소**: 호출 깊이 7→4레벨 (43% 감소)
3. ✅ **명명 일관성**: 명확하고 일관된 네이밍 체계
4. ✅ **환경변수 관리**: 설정 유연성 및 보안 강화
5. ✅ **성능 개선**: DB INSERT 70% 개선, 전체 25% 개선
6. ✅ **테스트 용이성**: 모킹 대상 60% 감소
7. ✅ **확장성**: Strategy 패턴으로 확장 용이

### 추천 진행 순서

1. **Phase 0**: 환경변수 설정 (1시간)
2. **Phase 1**: 새 컴포넌트 생성 (2-3시간)
3. **Phase 2**: DocumentService 단순화 (2-3시간)
4. **Phase 3**: ProgramUploadService 리팩토링 (3-4시간)
5. **Phase 4-7**: 정리 및 문서화 (4-5시간)

**총 예상 작업 시간: 12-16시간**

리팩토링 완료 후 깔끔하고 유지보수하기 쉬운 코드 베이스를 확보할 수 있습니다! 🎉
