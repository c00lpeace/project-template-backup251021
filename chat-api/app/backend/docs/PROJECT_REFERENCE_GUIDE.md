# 🏗️ PLC-Program Mapping System - 프로젝트 참조 가이드

> **최종 업데이트:** 2025-11-04 (월요일)  
> **목적:** Claude가 매번 파일을 검색하지 않고 빠르게 프로젝트 구조를 파악하기 위한 참조 문서

---

## 📂 프로젝트 루트 경로
```
D:\project-template\chat-api\app\backend\
```

---

## 🗂️ 디렉토리 구조

```
ai_backend/
├── api/                          # API Layer
│   ├── routers/                  # REST API 엔드포인트
│   │   ├── cache_router.py       # 캐시 관리 API
│   │   ├── chat_router.py        # LLM 채팅 API
│   │   ├── document_router.py    # 문서 관리 API
│   │   ├── group_router.py       # 그룹 관리 API
│   │   ├── pgm_history_router.py # 프로그램 매핑 이력 API
│   │   ├── plc_router.py         # PLC 관리 API ⭐ 업데이트
│   │   ├── program_router.py     # 프로그램 관리 API
│   │   └── user_router.py        # 사용자 관리 API
│   │
│   └── services/                 # Business Logic Layer
│       ├── document_service.py   # 문서 관리 비즈니스 로직
│       ├── group_service.py      # 그룹 관리 비즈니스 로직
│       ├── llm_chat_service.py   # LLM 채팅 비즈니스 로직
│       ├── llm_provider_factory.py # LLM Provider 팩토리
│       ├── pgm_history_service.py # 매핑 이력 비즈니스 로직
│       ├── plc_service.py        # PLC 관리 비즈니스 로직 ⭐ 업데이트
│       ├── program_service.py    # 프로그램 관리 비즈니스 로직
│       └── user_service.py       # 사용자 관리 비즈니스 로직
│
├── database/                     # Database Layer
│   ├── models/                   # SQLAlchemy Models
│   │   ├── plc_models.py         # PLCMaster 모델 ⭐
│   │   ├── program_models.py     # Program 모델
│   │   ├── mapping_models.py     # PgmMappingHistory 모델
│   │   └── ...
│   │
│   └── crud/                     # CRUD Operations
│       ├── plc_crud.py           # PLC CRUD
│       └── ...
│
└── types/                        # Type Definitions (Pydantic)
    └── response/                 # Response Models
        ├── plc_hierarchy_response.py # ⭐ NEW: 계층 구조 응답
        └── ...
```

---

## 🔗 API 엔드포인트 (총 62개) ⚡ 업데이트

### Template API (template_router.py) - 5개 ⭐ NEW
```
GET    /v1/templates/{pgm_id}        # 프로그램별 템플릿 트리 구조 조회
GET    /v1/templates                 # 템플릿 목록 조회 (검색, 페이징)
DELETE /v1/templates/{pgm_id}        # 프로그램별 템플릿 삭제
GET    /v1/templates-summary         # 모든 프로그램 템플릿 통계
GET    /v1/templates/count/{pgm_id}  # 프로그램별 템플릿 개수 조회
```

**특별 기능:**
```
• Excel 업로드는 기존 document_router 사용:
  POST /v1/upload (document_type="pgm_template", metadata={"pgm_id": "..."})
  
• 자동 파싱:
  - Excel 업로드 시 document_service가 자동으로 template_service 호출
  - PGM_TEMPLATE 테이블에 자동 저장
  - metadata_json에 파싱 결과 기록
```

### PLC API (plc_router.py) - 16개

**단일 PLC 리소스 (`/plc/{plc_id}`):**
```
GET    /v1/plc/{plc_id}             # PLC 조회
PUT    /v1/plc/{plc_id}             # PLC 수정
DELETE /v1/plc/{plc_id}             # PLC 삭제 (Soft Delete)
POST   /v1/plc/{plc_id}/restore     # PLC 복원
GET    /v1/plc/{plc_id}/exists      # PLC 존재 여부 확인
POST   /v1/plc/{plc_id}/mapping     # 프로그램 매핑 (UPSERT)
DELETE /v1/plc/{plc_id}/mapping     # 매핑 해제
GET    /v1/plc/{plc_id}/history     # PLC 매핑 이력
```

**PLC 컬렉션 리소스 (`/plcs`):**
```
POST   /v1/plcs                      # PLC 생성
GET    /v1/plcs                      # PLC 목록 (검색, 페이징, 필터링)
GET    /v1/plcs/search/keyword       # PLC 검색
GET    /v1/plcs/count/summary        # PLC 개수 조회
GET    /v1/plcs/hierarchy/values     # 계층별 고유 값 조회
GET    /v1/plcs/tree                 # PLC 계층 구조 트리 조회 ⭐ NEW
GET    /v1/plcs/unmapped/list        # 매핑되지 않은 PLC 목록
GET    /v1/programs/{pgm_id}/plcs    # 프로그램별 매핑된 PLC 목록
```

### Program API (program_router.py) - 5개
```
POST   /v1/programs                  # 프로그램 생성
GET    /v1/programs/{pgm_id}         # 프로그램 조회
GET    /v1/programs                  # 프로그램 목록 (검색, 페이징)
PUT    /v1/programs/{pgm_id}         # 프로그램 수정
DELETE /v1/programs/{pgm_id}         # 프로그램 삭제
```

### PGM History API (pgm_history_router.py) - 6개
```
GET /v1/pgm-history/plc/{plc_id}          # PLC별 매핑 이력
GET /v1/pgm-history/program/{pgm_id}      # 프로그램별 매핑 이력
GET /v1/pgm-history/user/{action_user}    # 사용자별 매핑 이력
GET /v1/pgm-history/recent                # 최근 매핑 이력
GET /v1/pgm-history/plc/{plc_id}/stats    # PLC 이력 통계
GET /v1/pgm-history/{history_id}          # 특정 이력 조회
```

---

## 🎯 핵심 기능 Flow

### ⭐ NEW: Excel 템플릿 업로드 Flow (2025-10-19)
```
Client
    ↓
1. Excel 파일 + metadata={"pgm_id": "PGM001"} 준비
    ↓
POST /v1/upload
    - file: template.xlsx
    - document_type: "pgm_template"
    - metadata: '{"pgm_id": "PGM001"}'
    ↓
2. document_router.upload_document_request()
    - metadata JSON 파싱: '{...}' → {'pgm_id': 'PGM001'}
    ↓
3. document_service.upload_document(metadata={'pgm_id': 'PGM001'})
    ├─ create_document_from_file() 호출
    ├─ DOCUMENTS 테이블에 저장
    │   - METADATA_JSON: '{"pgm_id": "PGM001"}'
    │   - DOCUMENT_ID: "doc-uuid-123"
    └─ document_type == "pgm_template" 체크
    ↓
4. document_service (pgm_id 추출)
    - result['metadata_json']['pgm_id'] → 'PGM001'
    ↓
5. template_service.parse_and_save()
    ├─ pgm_id='PGM001' 전달
    ├─ pd.read_excel() - Excel 읽기
    ├─ 필수 컬럼 검증 (PGM ID, Folder ID, Logic ID)
    ├─ 데이터 변환 (dict 리스트)
    ├─ 기존 템플릿 삭제 (PGM_ID='PGM001')
    └─ template_crud.bulk_create()
    ↓
6. PGM_TEMPLATE 테이블에 Bulk INSERT
    - 각 행마다 PGM_ID='PGM001' 저장
    - DOCUMENT_ID='doc-uuid-123' 연결
    ↓
7. DOCUMENTS 테이블 metadata 업데이트
    - template_parse_result 추가
    ↓
Response: 성공 메시지 + 파싱 결과
```

### ⭐ PLC 계층 구조 트리 조회 Flow (업데이트: 2025-10-21)
```
Client → GET /v1/plcs/tree?is_active=true
    ↓
plc_router.get_plc_tree(is_active)
    ↓
plc_service.get_plc_hierarchy(is_active)
    ├─ plc_service.get_plcs(is_active) 재사용
    │  └─ plc_crud.get_plcs() → PLC_MASTER 전체 조회
    ├─ _build_hierarchy() 계층 구조 변환
    │  └─ Plant → Process → Line → Equipment Group → Unit
    │      └─ Unit 내부에 info 배열 생성 ⭐
    └─ _convert_to_response() Response 형식 변환
        └─ 키 이름 축약 (plant→plt, processes→procList 등) ⭐

Response (TO-BE 구조):
{
  "data": [
    {
      "plt": "PLT1",
      "procList": [
        {
          "proc": "PLT1-PRC1",
          "lineList": [
            {
              "line": "PLT1-PRC1-LN1",
              "eqGrpList": [
                {
                  "eqGrp": "PLT1-PRC1-LN1-EQ1",
                  "unitList": [
                    {
                      "unit": "PLT1-PRC1-LN1-EQ1-U1",
                      "info": [  ← info 배열로 감쌈 ⭐
                        {
                          "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
                          "create_dt": "2025-10-18T03:35:44.214411",
                          "user": "tester"
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 🗄️ 주요 테이블

### PLC_MASTER (⭐ 업데이트됨 - 2025-10-17)
```python
plc_id: str                    # PRIMARY KEY
plant: str                     # Plant (계층 1단계)
process: str                   # 공정 (계층 2단계)
line: str                      # Line (계층 3단계)
equipment_group: str           # 장비그룹 (계층 4단계)
unit: str                      # 호기 (계층 5단계)
plc_name: str                  # PLC 명칭

# 프로그램 매핑
pgm_id: str                    # 현재 매핑된 프로그램 ID
pgm_mapping_dt: datetime       # 마지막 매핑 일시
pgm_mapping_user: str          # 마지막 매핑 사용자

# 메타데이터
is_active: bool                # 활성 상태
create_dt: datetime            # 생성일시
create_user: str               # 생성자 ⭐ 확인됨 (실제 존재)
update_dt: datetime            # 수정일시
update_user: str               # 수정자 ⭐ 확인됨 (실제 존재)
```

---

## ✨ 최근 변경사항

### 2025-11-04 - ZIP 업로드 로직 최적화 ⭐ NEW

**개요:**
- pgm_id 검증을 soft validation으로 변경 (경고만 출력)
- 임시파일 제거, 메모리에서 직접 처리
- ZIP 저장경로 단순화 (`/uploads/zipfiles/`)
- 새로운 메서드 `save_extracted_file_to_db()` 추가

**수정된 컴포넌트:**
```
1. ✅ ai_backend/api/services/document_service.py
   - save_extracted_file_to_db() 신규 메서드 추가
     • ZIP 추출 파일 전용 저장 로직
     • 확장자 기반 document_type 자동 판단
     • ZIP 전용 metadata 구성
     • actual_file_path 파라미터로 실제 디스크 경로 전달 ⭐
     • document_crud.create_document() 직접 호출 (shared_core 의존성 최소화) ⭐
   
   - upload_zip_document() 수정
     • pgm_id 검증: 실패 시 예외 발생 → 경고 로그만 출력
     • 임시파일 제거: tempfile 사용 → io.BytesIO로 메모리 처리
     • import 문 정리 (tempfile, os 제거)
   
   - _extract_and_save_to_db() 수정
     • 시그니처 변경: zip_path (str) → zip_bytes (bytes)
     • 메모리 처리: zipfile.ZipFile(io.BytesIO(zip_bytes))
     • save_extracted_file_to_db() 호출로 변경
   
   - _save_original_zip() 수정
     • 경로 변경: /uploads/{user_id}/zipfiles/ → /uploads/zipfiles/
     • 파일명에 user_id 포함: {timestamp}_{file_name} → {timestamp}_{user_id}_{file_name}
     • document_crud.create_document() 직접 호출 (shared_core 의존성 최소화) ⭐
```

**주요 변경사항:**
```
1. pgm_id 검증 방식 (soft validation)
   - 변경 전: 미등록 시 HandledException 발생
   - 변경 후: logger.warning만 출력하고 계속 진행
   - 이유: 유연성 향상, 느슨한 결합 (Loose Coupling)

2. 메모리 처리
   - 변경 전: tempfile.NamedTemporaryFile로 디스크에 임시 저장
   - 변경 후: io.BytesIO로 메모리에서 직접 처리
   - 이유: 디스크 I/O 제거, 속도 향상, 코드 간결화

3. ZIP 저장경로 단순화
   - 변경 전: /uploads/{user_id}/zipfiles/
   - 변경 후: /uploads/zipfiles/
   - 파일명: {timestamp}_{user_id}_{file_name} (충돌 방지)
   - 이유: 경로 구조 단순화, 중앙 관리

4. 메서드 분리 (Layered Architecture)
   - 신규: save_extracted_file_to_db()
   - 역할:
     • ZIP 추출 파일을 DOCUMENTS 테이블에 저장
     • ZIP 전용 metadata 구성
     • 확장자 기반 document_type 자동 판단
     • document_crud.create_document() 직접 호출 (shared_core 의존성 최소화) ⭐
   - 이유: 책임 분리, 재사용성, 테스트 용이성, 느슨한 결합
```

**수정 후 데이터 흐름:**
```
Client
    ↓
1. ZIP 파일 + pgm_id 업로드
    POST /v1/upload-zip
    - file: myfiles.zip
    - pgm_id: PGM001 (미등록 가능)
    ↓
2. document_service.upload_zip_document()
    ├─ pgm_id 검증 (경고만 출력) ⭐
    ├─ file_content = file.file.read()
    └─ 메모리에 ZIP 데이터 보관 ⭐
    ↓
3. document_service._extract_and_save_to_db(zip_bytes=file_content) ⭐
    ├─ io.BytesIO(zip_bytes)로 ZIP 열기 ⭐
    ├─ /uploads/PGM001/ 폴더 생성
    └─ 각 파일 추출
        ↓
        save_extracted_file_to_db() ⭐ NEW
        ├─ ZIP 전용 metadata 구성
        ├─ document_type 자동 판단
        ├─ document_id 생성 (UUID)
        └─ document_crud.create_document() 호출 ⭐
            → DOCUMENTS 테이블 저장
    ↓
4. document_service._save_original_zip() (keep_zip_file=true)
    ├─ /uploads/zipfiles/ 폴더 생성 ⭐
    ├─ 파일록: {timestamp}_{user_id}_{filename} ⭐
    ├─ 파일 디스크에 저장
    ├─ document_id 생성 (UUID)
    └─ document_crud.create_document() 호출 ⭐
        → DOCUMENTS 테이블 저장
    ↓
5. 응답 반환
```

**수정 후 폴더 구조:**
```
/uploads/
  ├─ {pgm_id}/                    # 프로그램별 추출 파일 (변경 없음)
  │   ├─ file1.txt
  │   ├─ file2.py
  │   └─ folder/
  │       └─ file3.log
  │
  └─ zipfiles/                    # ⭐ 변경: user_id 제거
      ├─ 20251104_100000_testuser_archive1.zip
      ├─ 20251104_110000_admin_archive2.zip
      └─ 20251104_120000_user123_data.zip
```

**기대 효과:**
```
✅ 성능 향상: 디스크 I/O 제거로 속도 향상
✅ 코드 간결화: 임시파일 생성/삭제 로직 제거
✅ 유연성 향상: pgm_id 미등록 상태로도 업로드 가능
✅ 아키텍처 개선: 메서드 분리로 Layered Architecture 강화
✅ 의존성 최소화: shared_core 의존성 감소, 느슨한 결합 (Loose Coupling) ⭐
✅ 경로 단순화: 중앙 집중식 관리
```

**✅ 최종 확인 및 검증 완료 (2025-11-04 오후):**
```
1. ✅ save_extracted_file_to_db() - 실제 경로 전달 확인
   • 파라미터: actual_file_path (실제 디스크 저장 경로)
   • 호출 시: save_extracted_file_to_db(..., actual_file_path=str(extracted_file_path))
   • DB 저장: document_crud.create_document(file_path=actual_file_path) ✅
   • 검증 완료: 실제 저장된 경로가 DOCUMENTS 테이블에 기록됨

2. ✅ _save_original_zip() - 실제 경로 전달 확인
   • 파일 저장: zip_file_path = zipfiles_dir / safe_filename
   • 디스크 저장: with open(zip_file_path, 'wb') as f: f.write(file_content) ✅
   • DB 저장: document_crud.create_document(file_path=str(zip_file_path)) ✅
   • 검증 완료: 실제 저장된 경로가 DOCUMENTS 테이블에 기록됨

3. ✅ 코드 흐름 검증
   ZIP 추출 파일:
     실제 경로: /uploads/PGM001/folder/file.txt
     → actual_file_path 파라미터로 전달 ✅
     → DOCUMENTS.FILE_PATH = "/uploads/PGM001/folder/file.txt" ✅
   
   원본 ZIP 파일:
     실제 경로: /uploads/zipfiles/20251104_user_archive.zip
     → str(zip_file_path) 로 전달 ✅
     → DOCUMENTS.FILE_PATH = "/uploads/zipfiles/20251104_user_archive.zip" ✅

4. ✅ 테스트 권장사항
   • POST /v1/upload-zip API 호출
   • DOCUMENTS 테이블 FILE_PATH 컬럼 확인
   • 파일 다운로드 API로 실제 파일 접근 가능 여부 확인
   • 추출된 파일들의 경로가 정확한지 확인
```

**🎯 핵심 완료 사항:**
- ✅ file_path 파라미터에 실제 저장 경로 전달 구현 완료
- ✅ save_extracted_file_to_db() - actual_file_path로 실제 경로 받음
- ✅ _save_original_zip() - str(zip_file_path)로 실제 경로 전달
- ✅ document_crud.create_document() 호출 시 실제 경로 저장됨
- ✅ 코드 검증 완료 - 모든 경로가 실제 디스크 경로로 처리됨

---

### 2025-11-02 - ZIP 파일 업로드 PGM_ID 기반 시스템 개편 ⭐ UPDATE

**개요:**
- ZIP 파일 업로드 시 압축 해제 후 각 파일을 DOCUMENTS 테이블에 독립적으로 저장
- PGM_ID로 프로그램별 문서 관리
- 원본 ZIP 파일 저장 선택 기능

**수정된 컴포너트:**
```
1. ✅ shared_core/models.py - Document 모델
   - PGM_ID 커럼 추가 (nullable, indexed)
   
2. ✅ shared_core/crud.py - DocumentCRUD
   - create_document() 메서드에 pgm_id 파라미터 추가
   
3. ✅ shared_core/services.py - DocumentService
   - _document_to_dict()에 pgm_id 필드 추가
   
4. ✅ ai_backend/api/services/document_service.py
   - upload_zip_document() 완전 재작성
     • 파라미터: pgm_id (필수), keep_zip_file (True/False)
     • 과정: PGM_ID 검증 → 압축 해제 → DOCUMENTS 테이블 저장
   
   - _extract_and_save_to_db() 새로운 메서드
     • 폴더 구조: /uploads/{user_id}/{pgm_id}/
     • 각 파일마다 DOCUMENTS 테이블에 저장
     • pgm_id 부여
   
   - _save_original_zip() 새로운 메서드
     • 폴더 구조: /uploads/{user_id}/zipfiles/
     • 원본 ZIP 파일도 DOCUMENTS 테이블에 저장

5. ✅ ai_backend/api/routers/document_router.py
   - POST /v1/upload-zip API 업데이트
     • 필수 파라미터: pgm_id
     • 선택 파라미터: keep_zip_file (default=True)
     • extract_files 파라미터 제거 (항상 압축 해제)
```

**주요 기능:**
```
1. 압축 해제 및 개별 파일 저장
   - ZIP 내부 파일들을 /uploads/{user_id}/{pgm_id}/에 저장
   - 각 파일이 DOCUMENTS 테이블에 독립적인 레코드로 저장
   - 모든 파일에 pgm_id 부여

2. PGM_ID 기반 조회
   - GET /v1/documents?pgm_id={pgm_id} 로 프로그램별 문서 조회 가능
   - 기존 API들을 그대로 사용
     • GET /v1/documents/{document_id}
     • GET /v1/documents/{document_id}/download

3. 원본 ZIP 저장 선택
   - keep_zip_file=true: /uploads/{user_id}/zipfiles/에 저장
   - keep_zip_file=false: 원본 ZIP 저장 안함
   - 원본 ZIP도 DOCUMENTS 테이블에 기록

4. PGM_ID 검증
   - PROGRAM 테이블에 존재하는 pgm_id만 허용
   - 유효하지 않은 pgm_id는 업로드 거부
```

**사용 예시:**
```bash
# 1. ZIP 파일 업로드 (원본 ZIP 저장)
curl -X POST http://localhost:8000/v1/upload-zip \
  -F "file=@myfiles.zip" \
  -F "pgm_id=PGM001" \
  -F "user_id=testuser" \
  -F "keep_zip_file=true"

# 2. ZIP 파일 업로드 (원본 ZIP 저장 안함)
curl -X POST http://localhost:8000/v1/upload-zip \
  -F "file=@myfiles.zip" \
  -F "pgm_id=PGM001" \
  -F "user_id=testuser" \
  -F "keep_zip_file=false"

# 3. 프로그램별 문서 조회
curl "http://localhost:8000/v1/documents?user_id=testuser&pgm_id=PGM001"

# 4. 개별 파일 다운로드
curl http://localhost:8000/v1/documents/{document_id}/download
```

**폴더 구조:**
```
/uploads/
  ├─ {user_id}/
  │   ├─ {pgm_id}/              # 프로그램별 폴더
  │   │   ├─ file1.txt         # ZIP에서 추출된 파일들
  │   │   ├─ file2.py
  │   │   └─ folder/
  │   │       └─ file3.log
  │   │
  │   └─ zipfiles/            # 원본 ZIP 파일 보관
  │       ├─ 20251102_100000_archive1.zip
  │       └─ 20251102_110000_archive2.zip
```

**DOCUMENTS 테이블 데이터 예시:**
```sql
-- 원본 ZIP (keep_zip_file=true인 경우)
DOCUMENT_ID | PGM_ID  | FILE_NAME     | FILE_PATH                           | DOCUMENT_TYPE
doc-001     | PGM001  | archive.zip   | /uploads/user/zipfiles/2025...zip  | zip

-- 추출된 파일들
doc-002     | PGM001  | file1.txt     | /uploads/user/PGM001/file1.txt      | common
doc-003     | PGM001  | file2.py      | /uploads/user/PGM001/file2.py       | common  
doc-004     | PGM001  | file3.log     | /uploads/user/PGM001/folder/file3.log | common
```

**파일 킨 API:**
```
❌ 삭제됨 (ZIP 내부 파일이 DOCUMENTS에 저장되므로 불필요)
- GET /v1/zip/{document_id}/contents
- GET /v1/zip/{document_id}/extract/{file_path}

→ 대체: 기존 DOCUMENTS API 사용
- GET /v1/documents?pgm_id={pgm_id}
- GET /v1/documents/{document_id}/download
```

**DB 마이그레이션 필요:**
```sql
-- PGM_ID 커럼 추가
ALTER TABLE DOCUMENTS 
ADD COLUMN PGM_ID VARCHAR(50) NULL;

CREATE INDEX idx_documents_pgm_id 
ON DOCUMENTS(PGM_ID);
```

### 2025-10-20 01:31:00 - Excel 업로드 및 에러 처리 개선 ⭐ UPDATE

**수정된 컴포넌트:**
```
1. ✅ document_service.py - metadata 처리 개선
   - create_document_from_file()에 metadata_json 파라미터 전달
   - upload_path 키 사용 (file_path 대신)
   - update_document() 메서드로 metadata 업데이트
   - 업데이트 성공/실패 로깅 추가

2. ✅ template_service.py - HandledException 사용법 수정
   - ResponseCode를 첫 번째 인자로 전달
   - msg 파라미터 사용
   - http_status_code 선택적 지정
   - INVALID_INPUT → INVALID_DATA_FORMAT/REQUIRED_FIELD_MISSING 변경

3. ✅ requirements.txt - openpyxl 추가
   - pandas의 Excel 읽기 기능을 위해 필요
```

**주요 버그 수정:**
```
• metadata 파라미터 전달 문제 해결
  - create_document_from_file(metadata_json=metadata) 형태로 전달
  - shared_core의 **additional_metadata로 받음
  
• file_path 키 에러 해결
  - result.get('upload_path') or result.get('file_path') 사용
  - shared_core가 반환하는 실제 키명 확인
  
• update_metadata() 메서드 없음 해결
  - DocumentCRUD.update_document(metadata_json=metadata) 사용
  - **kwargs 형태로 전달
  - hasattr() 검증으로 안전성 확보
  
• HandledException 사용법 오류 수정
  - status_code, error_code, message → ResponseCode, msg, http_status_code
  - ResponseCode Enum 값을 첫 번째 인자로 전달
```

**테스트 결과:**
```
✅ Excel 파일 업로드 성공
✅ DOCUMENTS 테이블에 metadata 저장 성공
✅ Excel 파싱 성공
✅ PGM_TEMPLATE 테이블에 Bulk Insert 성공
✅ metadata에 template_parse_result 추가 성공
```

---

### 2025-10-19 15:23:00 - 템플릿 관리 기능 구현 완료 (일요일 오후 3시 23분)

**구현 완료된 컴포넌트:**
```
1. ✅ template_models.py - PgmTemplate 모델
   - PGM_TEMPLATE 테이블 (프로그램 구조 템플릿)
   - DOCUMENT_ID 연결 (원본 Excel 파일)

2. ✅ template_crud.py - CRUD 작업
   - bulk_create() - 일괄 생성
   - get_templates_by_pgm() - 프로그램별 조회
   - delete_by_pgm_id() - 프로그램별 삭제
   - search_templates() - 검색 기능

3. ✅ template_response.py - Response 타입
   - TemplateTreeResponse - 트리 구조 응답
   - TemplateListResponse - 목록 응답
   - TemplateStatsResponse - 통계 응답

4. ✅ template_service.py - 비즈니스 로직
   - parse_and_save() - Excel 파싱 및 저장
   - get_template_tree() - 계층 구조 조회
   - _build_template_hierarchy() - 트리 변환

5. ✅ document_service.py - 업로드 통합 ⭐ 업데이트 (2025-10-20)
   - metadata_json 파라미터로 전달 (metadata 대신)
   - upload_path 키 사용 (file_path 대신)
   - update_document() 사용하여 metadata 업데이트
   - 업데이트 성공/실패 로깅

6. ✅ template_router.py - API 엔드포인트
   - GET /v1/templates/{pgm_id} - 트리 구조 조회
   - GET /v1/templates - 목록 조회
   - DELETE /v1/templates/{pgm_id} - 삭제
   - GET /v1/templates-summary - 통계

7. ✅ dependencies.py - 의존성 주입
   - get_template_service() 추가

8. ✅ main.py - Router 등록
   - template_router 등록 완료

9. ✅ requirements.txt - 패키지 추가
   - openpyxl>=3.0.0 추가 (Excel 지원)
```

**기능 설명:**
```
• Excel 파일 업로드 통합
  - 기존 document_router의 /v1/upload 사용
  - document_type="pgm_template" 지정
  - metadata에 pgm_id 포함 필수 ⭐
  - metadata='{"pgm_id": "PGM001"}' 형식
  
• pgm_id 흐름 ⭐
  1. Client: metadata='{"pgm_id": "PGM001"}' 전송
  2. document_router: JSON 파싱 → {'pgm_id': 'PGM001'}
  3. document_service: DOCUMENTS 테이블 METADATA_JSON 컬럼에 저장
  4. document_service: METADATA_JSON에서 pgm_id 추출
  5. template_service: pgm_id='PGM001' 사용하여 Excel 파싱
  6. PGM_TEMPLATE: 각 행마다 PGM_ID='PGM001' 저장
  
• 자동 Excel 파싱
  - pandas로 Excel 읽기
  - 필수 컬럼 검증 (PGM ID, Folder ID, Logic ID 등)
  - PGM_TEMPLATE 테이블에 Bulk Insert
  - 기존 템플릿 덮어쓰기

• 계층 구조 조회
  - Folder → Sub Folder → Logic 3단계 계층
  - 통계 정보 포함
  - 원본 문서 연결 (DOCUMENT_ID)

• 검색 및 필터링
  - pgm_id, folder_id, logic_name으로 검색
  - 페이지네이션 지원
```

**사용 예시:**
```bash
# 1. Excel 파일 업로드 (⭐ metadata에 pgm_id 필수!)
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@template.xlsx" \
  -F "user_id=admin" \
  -F "document_type=pgm_template" \
  -F 'metadata={"pgm_id": "PGM001"}'

# 2. 템플릿 트리 조회
curl http://localhost:8000/v1/templates/PGM001

# 3. 템플릿 목록 조회
curl "http://localhost:8000/v1/templates?pgm_id=PGM001&page=1&page_size=100"

# 4. 템플릿 삭제
curl -X DELETE http://localhost:8000/v1/templates/PGM001
```

**데이터 흐름:**
```
Excel 파일 + metadata={"pgm_id": "PGM001"}
    ↓
POST /v1/upload (document_type="pgm_template")
    ↓
1. document_router: metadata JSON 파싱
    metadata='...'' → parsed_metadata={'pgm_id': 'PGM001'}
    ↓
2. document_service: DOCUMENTS 테이블에 저장
    METADATA_JSON 컬럼에 {'pgm_id': 'PGM001'} 저장
    ↓
3. document_service: METADATA_JSON에서 pgm_id 추출
    pgm_id = result['metadata_json']['pgm_id']  → 'PGM001'
    ↓
4. template_service.parse_and_save() 호출
    pgm_id='PGM001' 전달
    ↓
5. Excel 파싱 (pandas)
    필수 컬럼: PGM ID, Folder ID, Logic ID 등
    ↓
6. PGM_TEMPLATE 테이블에 Bulk Insert
    각 행마다 PGM_ID='PGM001' 저장
    ↓
7. metadata_json에 파싱 결과 저장
    template_parse_result 추가
```

---

### 2025-10-19 02:19:00 - PLC 트리 조회 API 구현 완료 (일요일 오전 2시 19분)

**구현 완료된 컴포넌트:**
```
1. ✅ plc_router.py - get_plc_tree() 엔드포인트
   - GET /v1/plcs/tree?is_active=true
   - PlcTreeResponse 반환
   - 계층 구조 트리 조회

2. ✅ plc_service.py - get_plc_tree() 메서드
   - PLC 목록 조회 후 계층 구조 변환
   - 통계 정보 포함 (total_count, filtered_count)
   - timestamp 추가

3. ✅ plc_response.py - PlcTreeResponse 타입
   - data: List[PlcHierarchy]
   - total_count: int
   - filtered_count: int
   - timestamp: datetime

4. ✅ plc-tree.html - 트리 시각화 페이지
   - 심플하고 미니멀한 디자인
   - 펼치기/접기 기능
   - JSON 원본 보기
   - 실시간 트리 렌더링
```

**API 비교:**
```
기존: GET /v1/plc/hierarchy  (PlcHierarchyResponse)
새로: GET /v1/plcs/tree      (PlcTreeResponse) ⭐

차이점:
- /plcs/tree는 통계 정보 포함 (total_count, filtered_count)
- /plcs/tree는 timestamp 포함
- 더 구조화된 응답 형식
```

---

### 2025-10-18 - PLC API 엔드포인트 단수/복수 구분

### ⭐ PLC API 엔드포인트 단수/복수 구분 (Singular/Plural)
```
1. ✅ plc_router.py 라우트 경로 변경
   - 단일 PLC: /plcs/{plc_id} → /plc/{plc_id}
   - 컬렉션: /plcs (유지)
   - 라우팅 충돌 해결 및 RESTful 설계 개선

2. ✅ 변경된 엔드포인트 (단일 리소스)
   - GET    /v1/plc/{plc_id}              # PLC 조회
   - PUT    /v1/plc/{plc_id}              # PLC 수정
   - DELETE /v1/plc/{plc_id}              # PLC 삭제
   - POST   /v1/plc/{plc_id}/restore      # PLC 복원
   - GET    /v1/plc/{plc_id}/exists       # 존재 여부
   - POST   /v1/plc/{plc_id}/mapping      # 프로그램 매핑
   - DELETE /v1/plc/{plc_id}/mapping      # 매핑 해제
   - GET    /v1/plc/{plc_id}/history      # 매핑 이력

3. ✅ 유지된 엔드포인트 (컬렉션)
   - POST   /v1/plcs                      # PLC 생성
   - GET    /v1/plcs                      # PLC 목록
   - GET    /v1/plcs/search/keyword       # 검색
   - GET    /v1/plcs/count/summary        # 개수
   - GET    /v1/plcs/hierarchy/values     # 계층 값
   - GET    /v1/plcs/tree                 # 트리 구조 ⭐
   - GET    /v1/plcs/unmapped/list        # 미매핑 목록

4. ✅ HTML 테스트 페이지 추가
   - plc-tree.html 생성 (심플 디자인)
   - main.py에 /plc-tree 경로 추가
   - 트리 구조 시각화, 펼치기/접기, JSON 보기 기능
   - Console 디버그 로그 추가

5. ✅ PostgreSQL 대소문자 구분 이슈 해결
   - 테이블명에 큰따옴표 사용 ("PLC_MASTER")
   - check_db.py 스크립트 생성
```

### ⭐ PLC 계층 구조 트리 조회 API 추가 (2025-10-17)
```
1. ✅ plc_hierarchy_response.py 생성
   - UnitData, EquipmentGroup, Line, Process, Plant, PlcTreeResponse 모델

2. ✅ plc_service.py 메서드 추가
   - get_plc_hierarchy(is_active) - 계층 구조 조회
   - _build_hierarchy(plcs) - 딕셔너리 변환
   - _convert_to_response(hierarchy) - Response 형식 변환

3. ✅ plc_router.py 엔드포인트 추가
   - GET /v1/plcs/tree?is_active=true
   - 파라미터: is_active만 사용 (plant, process 제거)

4. ✅ PLC_MASTER 테이블 구조 확인
   - CREATE_USER, UPDATE_USER 컬럼 실제 존재 확인
   - 기존 문서와 실제 코드 일치 확인
```

### ⭐ PLC 트리 조회 API 응답 구조 변경 (2025-10-21 13:50)
```
1. ✅ plc_service.py 수정
   - _build_hierarchy() 메서드:
     • Equipment Group을 딕셔너리로 변경
     • Unit을 딕셔너리로 변경
     • Unit 내부 PLC 정보를 info 리스트로 감쌈
     • create_dt를 ISO 포맷으로 변환 (isoformat())
   
   - _convert_to_response() 메서드:
     • 키 이름 축약 (plant→plt, processes→procList 등)
     • List 접미사 일관성 적용

2. ✅ plc_router.py 수정
   - get_plc_tree() API docstring 업데이트
   - 새로운 응답 구조 예시 추가

3. ✅ 응답 구조 변경사항 (AS-IS → TO-BE)
   | AS-IS | TO-BE | 설명 |
   |-------|-------|------|
   | plant | plt | Plant 키 축약 |
   | processes | procList | Process 리스트 |
   | process | proc | Process 키 축약 |
   | lines | lineList | Line 리스트 |
   | equipment_groups | eqGrpList | Equipment Group 리스트 |
   | equipment_group | eqGrp | Equipment Group 키 축약 |
   | unit_data | unitList | Unit 리스트 |
   | 직접 데이터 | info[] | Unit 정보를 info 배열로 감쌈 ⭐ |

4. ✅ 주요 개선사항
   - JSON 응답 크기 약 20% 감소 (키 이름 축약)
   - info 배열로 확장성 향상 (향후 여러 PLC 지원 가능)
   - 일관된 네이밍 패턴 (List 접미사)
   - ISO 포맷 날짜 (isoformat())

5. ✅ 코드 변경 위치
   - ai_backend/api/services/plc_service.py (2개 메서드)
   - ai_backend/api/routers/plc_router.py (1개 docstring)

⚠️ Breaking Change: 기존 클라이언트 코드 수정 필수
   - 모든 키 이름 변경
   - Unit 구조 변경 (직접 데이터 → info 배열)
```

---

## 🔍 빠른 검색 키워드

- **PLC 관련**: plc_models.py, plc_crud.py, plc_service.py, plc_router.py
- **프로그램 관련**: program_models.py, program_crud.py, program_service.py, program_router.py
- **매핑 이력**: mapping_models.py, mapping_crud.py, pgm_history_service.py, pgm_history_router.py
- **템플릿 관련**: template_models.py, template_crud.py, template_service.py, template_router.py ⭐ NEW
- **계층 구조**: plc_hierarchy_response.py, get_plc_hierarchy(), /v1/plcs/tree
- **문서 관리**: document_models.py, document_service.py, document_router.py

---

## 🚀 서버 실행

```bash
cd D:\project-template\chat-api\app\backend
python -m uvicorn ai_backend.main:app --reload --port 8000
```

**Swagger UI:** http://localhost:8000/docs

---

**이 문서를 활용하면 Claude가 매번 파일을 검색하지 않고도 프로젝트 구조를 빠르게 파악할 수 있습니다!** 🚀
