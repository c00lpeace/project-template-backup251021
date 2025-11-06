# 🚀 다음 단계 제안 - 상세 설명

## 📋 목차

1. [Phase 6: 성능 최적화](#phase-6-성능-최적화)
2. [통합 테스트 작성](#통합-테스트-작성)
3. [API 문서 보강](#api-문서-보강)
4. [추가 개선 제안](#추가-개선-제안)
5. [우선순위 및 로드맵](#우선순위-및-로드맵)

---

## Phase 6: 성능 최적화

### 🎯 목표
프로그램 업로드 전체 워크플로우의 처리 시간을 25-40% 단축

### 📊 현재 성능 분석

**현재 예상 처리 시간 (100개 레더 파일 기준):**
```
┌─────────────────────────────────────────────┐
│ Phase 1: 검증                    → 500ms    │
│  ├─ 파일 타입/크기 검증          100ms      │
│  ├─ 템플릿 구조 검증             200ms      │
│  ├─ ZIP 구조 검증                100ms      │
│  └─ 레더 파일 매칭 검증          100ms      │
│                                              │
│ Phase 2: 파일 저장               → 2000ms   │
│  ├─ ZIP 압축 해제                1500ms     │
│  └─ 템플릿 파일 저장             500ms      │
│                                              │
│ Phase 3: DB 저장                 → 1500ms   │
│  ├─ 레더 CSV 문서 일괄 생성      500ms      │
│  ├─ 템플릿 문서 생성 + 파싱      800ms      │
│  └─ 프로그램 레코드 생성         200ms      │
│                                              │
│ 전체 시간:                       4000ms      │
└─────────────────────────────────────────────┘
```

### 🔧 최적화 항목

#### 1. Bulk INSERT 최적화 (Phase 3 DB 저장)

**현재 문제:**
```python
# ai_backend/api/services/document_service.py
def bulk_create_ladder_csv_documents(self, documents_data: List[Dict]) -> List[Document]:
    documents = []
    for data in documents_data:
        # 개별 INSERT (N번 호출)
        document = self.document_crud.create_document(...)
        documents.append(document)
    return documents
```

**문제점:**
- 100개 파일 → 100번 INSERT 실행
- 각 INSERT마다 DB 왕복 (Network I/O)
- 트랜잭션 오버헤드

**최적화 방안:**
```python
# SQLAlchemy bulk_insert_mappings 사용
def bulk_create_ladder_csv_documents(self, documents_data: List[Dict]) -> List[Document]:
    """
    성능 최적화: bulk_insert_mappings 사용
    - 100개 INSERT → 1번 Batch INSERT
    - 예상 성능 향상: 500ms → 100ms (80% 개선)
    """
    # 1. Document 객체 리스트 생성 (메모리)
    document_dicts = []
    for data in documents_data:
        document_dict = {
            'document_id': generate_id(),
            'document_name': data['document_name'],
            'user_id': data['user_id'],
            ...
        }
        document_dicts.append(document_dict)
    
    # 2. Bulk INSERT (1번 실행)
    self.db.bulk_insert_mappings(Document, document_dicts)
    
    # 3. 생성된 레코드 조회 (1번 SELECT)
    document_ids = [d['document_id'] for d in document_dicts]
    documents = self.db.query(Document).filter(
        Document.document_id.in_(document_ids)
    ).all()
    
    return documents
```

**예상 효과:**
- **처리 시간:** 500ms → 100ms (80% 개선)
- **DB 왕복:** 100번 → 2번 (98% 감소)
- **CPU 사용률:** 30% 감소

---

#### 2. 템플릿 파싱 최적화 (Phase 3 DB 저장)

**현재 문제:**
```python
# ai_backend/api/services/template_service.py
def parse_and_save_template(self, document_id: str, pgm_id: str, file_path: str):
    # Excel 파일 읽기 (느림)
    df = pd.read_excel(file_path)  # 800ms
    
    # 각 행마다 INSERT (N번)
    for _, row in df.iterrows():
        self.template_crud.create_template_row(
            pgm_id=pgm_id,
            folder_id=row['Folder ID'],
            logic_id=row['Logic ID'],
            ...
        )
```

**문제점:**
- pandas read_excel이 느림 (800ms)
- 반복문 내부에서 INSERT (N번)
- 템플릿 행이 많을수록 시간 증가 (선형)

**최적화 방안:**

**방안 1: openpyxl 직접 사용**
```python
# pandas 대신 openpyxl 직접 사용
from openpyxl import load_workbook

def parse_template_optimized(self, file_path: str) -> List[Dict]:
    """
    성능 최적화: openpyxl 직접 사용
    - pandas 오버헤드 제거
    - 예상 성능 향상: 800ms → 300ms (62% 개선)
    """
    wb = load_workbook(file_path, read_only=True)  # 읽기 전용 모드
    ws = wb.active
    
    # 헤더 추출
    headers = [cell.value for cell in ws[1]]
    
    # 데이터 추출 (제네레이터)
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        row_dict = dict(zip(headers, row))
        rows.append(row_dict)
    
    return rows
```

**방안 2: Bulk INSERT 적용**
```python
def save_template_data_optimized(
    self, 
    pgm_id: str, 
    template_data: List[Dict]
):
    """
    성능 최적화: bulk_insert_mappings 사용
    - N번 INSERT → 1번 Batch INSERT
    """
    template_dicts = [
        {
            'pgm_id': pgm_id,
            'folder_id': row['Folder ID'],
            'logic_id': row['Logic ID'],
            ...
        }
        for row in template_data
    ]
    
    self.db.bulk_insert_mappings(PgmTemplate, template_dicts)
```

**예상 효과:**
- **처리 시간:** 800ms → 300ms (62% 개선)
- **메모리 사용:** 40% 감소 (read_only 모드)
- **확장성:** 1000행 템플릿도 1초 이내 처리

---

#### 3. 파일 I/O 최적화 (Phase 2 파일 저장)

**현재 문제:**
```python
# ai_backend/api/services/file_storage_service.py
def save_and_extract_ladder_zip(self, ladder_zip_bytes: bytes, pgm_id: str):
    # ZIP 압축 해제 (동기 방식)
    with zipfile.ZipFile(io.BytesIO(ladder_zip_bytes), 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            # 각 파일마다 동기 I/O
            content = zip_ref.read(file_info.filename)
            file_path = ladder_dir / file_info.filename
            file_path.write_bytes(content)  # 동기 쓰기
```

**문제점:**
- 동기 I/O → 파일 100개 저장 시 1.5초
- CPU 대기 시간 증가
- 병렬 처리 불가

**최적화 방안:**

**방안 1: 버퍼 크기 조정**
```python
# 버퍼 크기를 늘려서 I/O 횟수 감소
BUFFER_SIZE = 1024 * 1024  # 1MB (기본 64KB → 1MB)

def save_file_with_buffer(self, content: bytes, file_path: Path):
    """
    성능 최적화: 버퍼 크기 조정
    - 예상 성능 향상: 1500ms → 1200ms (20% 개선)
    """
    with open(file_path, 'wb', buffering=BUFFER_SIZE) as f:
        f.write(content)
```

**방안 2: 비동기 I/O (선택사항)**
```python
import asyncio
import aiofiles

async def save_files_async(self, files_data: List[Dict]):
    """
    성능 최적화: 비동기 파일 저장
    - 예상 성능 향상: 1500ms → 800ms (47% 개선)
    - 주의: FastAPI 비동기 엔드포인트 필요
    """
    tasks = []
    for file_data in files_data:
        task = self._save_file_async(
            file_data['content'], 
            file_data['path']
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)

async def _save_file_async(self, content: bytes, file_path: Path):
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
```

**예상 효과:**
- **버퍼 최적화:** 1500ms → 1200ms (20% 개선)
- **비동기 I/O:** 1500ms → 800ms (47% 개선)
- **CPU 사용률:** 25% 감소

---

#### 4. 메모리 최적화

**현재 문제:**
```python
# 전체 ZIP을 메모리에 로드
original_content = pgm_ladder_zip_file.file.read()  # 100MB 메모리 사용
```

**최적화 방안:**
```python
# 스트리밍 방식으로 처리
def extract_zip_streaming(self, zip_file: UploadFile, extract_dir: Path):
    """
    메모리 최적화: 스트리밍 방식
    - 메모리 사용: 100MB → 10MB (90% 감소)
    """
    with zipfile.ZipFile(zip_file.file, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            # 청크 단위로 읽기/쓰기
            with zip_ref.open(file_info.filename) as source:
                target_path = extract_dir / file_info.filename
                with open(target_path, 'wb') as target:
                    while True:
                        chunk = source.read(8192)  # 8KB 청크
                        if not chunk:
                            break
                        target.write(chunk)
```

**예상 효과:**
- **메모리 사용:** 100MB → 10MB (90% 감소)
- **대용량 파일 처리 가능:** 500MB ZIP도 처리 가능

---

### 📈 최적화 후 예상 성능

```
┌─────────────────────────────────────────────┐
│ Phase 1: 검증                    → 500ms    │ (변화 없음)
│                                              │
│ Phase 2: 파일 저장               → 1200ms   │ ⬇️ 800ms 감소 (40%)
│  ├─ ZIP 압축 해제 (버퍼 최적화)  700ms      │
│  └─ 템플릿 파일 저장             500ms      │
│                                              │
│ Phase 3: DB 저장                 → 600ms    │ ⬇️ 900ms 감소 (60%)
│  ├─ 레더 CSV 일괄 생성 (Bulk)    100ms      │
│  ├─ 템플릿 파싱 + 저장 (최적화)  300ms      │
│  └─ 프로그램 레코드 생성         200ms      │
│                                              │
│ 전체 시간:                       2300ms      │ ⬇️ 1700ms 감소 (42%)
└─────────────────────────────────────────────┘
```

**개선 효과:**
- **전체 처리 시간:** 4000ms → 2300ms (42% 개선)
- **DB 처리 시간:** 1500ms → 600ms (60% 개선)
- **메모리 사용량:** 90% 감소
- **확장성:** 대용량 파일 처리 가능

---

### 🛠️ 작업 순서

#### Step 1: Bulk INSERT 최적화 (우선순위 1)
```
1. DocumentService.bulk_create_ladder_csv_documents() 수정
2. TemplateService.save_template_data() 수정
3. 단위 테스트 작성
4. 벤치마크 측정 (Before/After)

예상 시간: 2시간
```

#### Step 2: 템플릿 파싱 최적화 (우선순위 2)
```
1. openpyxl 직접 사용으로 변경
2. read_only 모드 적용
3. 단위 테스트 작성
4. 벤치마크 측정

예상 시간: 1.5시간
```

#### Step 3: 파일 I/O 최적화 (우선순위 3)
```
1. 버퍼 크기 조정
2. (선택) 비동기 I/O 적용
3. 메모리 최적화 (스트리밍)
4. 통합 테스트

예상 시간: 2시간
```

#### Step 4: 성능 벤치마크 (필수)
```
1. 테스트 데이터셋 준비 (10, 50, 100, 500개 파일)
2. locust 또는 pytest-benchmark로 부하 테스트
3. 결과 분석 및 문서화
4. 병목 지점 추가 확인

예상 시간: 1.5시간
```

**총 예상 시간:** 7시간

---

## 통합 테스트 작성

### 🎯 목표
프로그램 업로드 워크플로우의 안정성을 80% → 95%로 향상

### 📋 테스트 범위

#### 1. 정상 시나리오 테스트

**test_upload_program_success.py**
```python
"""
프로그램 업로드 성공 시나리오 테스트

테스트 케이스:
1. 정상 파일 업로드 (10개 레더 파일)
2. 정상 파일 업로드 (100개 레더 파일)
3. 정상 파일 업로드 (대용량 ZIP 50MB)
4. 정상 파일 업로드 (특수문자 포함 파일명)
5. 정상 파일 업로드 (한글 파일명)

검증 항목:
- PGM_ID 자동 생성 확인
- 파일 저장 경로 확인
- DOCUMENTS 레코드 생성 확인
- PGM_TEMPLATE 레코드 생성 확인
- PROGRAMS 레코드 생성 확인
- 응답 시간 (4초 이내)
"""

def test_upload_program_with_10_files(client, test_files):
    """10개 레더 파일 업로드 테스트"""
    # Given: 10개 레더 파일 + 템플릿
    ladder_zip = create_test_zip(10)
    template_xlsx = create_test_template(10)
    
    # When: 업로드 API 호출
    response = client.post(
        "/programs/upload",
        files={
            "pgm_ladder_zip_file": ladder_zip,
            "pgm_template_file": template_xlsx
        },
        data={
            "pgm_name": "Test Program",
            "create_user": "test_user"
        }
    )
    
    # Then: 검증
    assert response.status_code == 201
    data = response.json()
    
    # PGM_ID 확인
    assert data['pgm_id'].startswith('PGM_')
    
    # 파일 저장 확인
    assert len(data['saved_files']['ladder_csv_documents']) == 10
    assert data['saved_files']['template_document'] is not None
    
    # DB 레코드 확인
    pgm = db.query(Programs).filter_by(pgm_id=data['pgm_id']).first()
    assert pgm is not None
    assert pgm.pgm_name == "Test Program"
    
    # 파일 존재 확인
    for doc in data['saved_files']['ladder_csv_documents']:
        file_path = Path(doc['upload_path'])
        assert file_path.exists()

def test_upload_program_with_100_files(client, test_files):
    """100개 레더 파일 업로드 테스트 (성능 확인)"""
    import time
    
    ladder_zip = create_test_zip(100)
    template_xlsx = create_test_template(100)
    
    start_time = time.time()
    response = client.post("/programs/upload", ...)
    elapsed_time = time.time() - start_time
    
    # 성능 확인 (4초 이내)
    assert elapsed_time < 4.0
    assert response.status_code == 201
    
    # 파일 개수 확인
    data = response.json()
    assert len(data['saved_files']['ladder_csv_documents']) == 100

def test_upload_program_with_large_zip(client):
    """대용량 ZIP (50MB) 업로드 테스트"""
    ladder_zip = create_large_test_zip(50 * 1024 * 1024)  # 50MB
    template_xlsx = create_test_template(10)
    
    response = client.post("/programs/upload", ...)
    
    assert response.status_code == 201
```

---

#### 2. 검증 실패 시나리오 테스트

**test_upload_program_validation_errors.py**
```python
"""
검증 실패 시나리오 테스트

테스트 케이스:
1. 파일 타입 오류 (ZIP 대신 PDF)
2. 파일 크기 초과 (101MB)
3. 템플릿 구조 오류 (필수 컬럼 누락)
4. 레더 파일 누락 (템플릿에 있지만 ZIP에 없음)
5. ZIP 손상 (압축 해제 실패)
6. 템플릿 손상 (읽기 실패)

검증 항목:
- 적절한 에러 코드 반환
- 명확한 에러 메시지
- 파일 저장 안 됨 확인
- DB 레코드 생성 안 됨 확인
- 롤백 확인 (파일 삭제)
"""

def test_invalid_file_type(client):
    """잘못된 파일 타입 업로드"""
    # Given: ZIP 대신 PDF
    invalid_file = create_pdf_file()
    template_xlsx = create_test_template(10)
    
    # When: 업로드 시도
    response = client.post(
        "/programs/upload",
        files={
            "pgm_ladder_zip_file": invalid_file,
            "pgm_template_file": template_xlsx
        },
        data={"pgm_name": "Test", "create_user": "test"}
    )
    
    # Then: 검증
    assert response.status_code == 400
    data = response.json()
    assert "ZIP" in data['message']
    assert "지원하지 않는 파일 형식" in data['message']
    
    # 파일 저장 안 됨 확인
    assert not Path(f"uploads/PGM_*").exists()

def test_file_size_exceeded(client):
    """파일 크기 초과"""
    # Given: 101MB ZIP (환경변수: pgm_ladder_zip_max_size=100MB)
    large_zip = create_large_test_zip(101 * 1024 * 1024)
    template_xlsx = create_test_template(10)
    
    # When: 업로드 시도
    response = client.post("/programs/upload", ...)
    
    # Then: 검증
    assert response.status_code == 400
    assert "크기" in response.json()['message']
    assert "100MB" in response.json()['message']

def test_missing_required_columns_in_template(client):
    """템플릿 필수 컬럼 누락"""
    # Given: Logic ID 컬럼이 없는 템플릿
    ladder_zip = create_test_zip(10)
    invalid_template = create_template_without_logic_id()
    
    # When: 업로드 시도
    response = client.post("/programs/upload", ...)
    
    # Then: 검증
    assert response.status_code == 400
    assert "Logic ID" in response.json()['message']
    assert "필수 컬럼" in response.json()['message']

def test_missing_ladder_files(client):
    """레더 파일 누락"""
    # Given: 템플릿에는 10개, ZIP에는 5개만
    ladder_zip = create_test_zip(5)  # 5개만
    template_xlsx = create_test_template(10)  # 10개 필요
    
    # When: 업로드 시도
    response = client.post("/programs/upload", ...)
    
    # Then: 검증
    assert response.status_code == 400
    data = response.json()
    assert "누락" in data['message']
    assert len(data['validation_result']['missing_files']) == 5

def test_corrupted_zip_file(client):
    """손상된 ZIP 파일"""
    # Given: 손상된 ZIP
    corrupted_zip = create_corrupted_zip()
    template_xlsx = create_test_template(10)
    
    # When: 업로드 시도
    response = client.post("/programs/upload", ...)
    
    # Then: 검증
    assert response.status_code == 400
    assert "손상" in response.json()['message']
```

---

#### 3. 트랜잭션 롤백 테스트

**test_upload_program_rollback.py**
```python
"""
트랜잭션 롤백 시나리오 테스트

테스트 케이스:
1. 파일 저장 후 DB INSERT 실패
2. 레더 CSV 저장 후 템플릿 파싱 실패
3. 템플릿 저장 후 프로그램 생성 실패
4. 중간에 DB 연결 끊김
5. 디스크 공간 부족

검증 항목:
- DB 롤백 확인 (레코드 없음)
- 저장된 파일 삭제 확인
- 적절한 에러 메시지
- 로그 기록 확인
"""

def test_rollback_on_db_error(client, db_session, monkeypatch):
    """DB 에러 발생 시 롤백"""
    # Given: 정상 파일
    ladder_zip = create_test_zip(10)
    template_xlsx = create_test_template(10)
    
    # 프로그램 생성 시 에러 발생하도록 설정
    def mock_create_program(*args, **kwargs):
        raise Exception("DB Connection Error")
    
    monkeypatch.setattr(
        "ai_backend.api.services.program_service.ProgramService.create_program",
        mock_create_program
    )
    
    # When: 업로드 시도
    response = client.post("/programs/upload", ...)
    
    # Then: 검증
    assert response.status_code == 500
    
    # DB 레코드 없음 확인
    assert db_session.query(Programs).count() == 0
    assert db_session.query(Document).count() == 0
    assert db_session.query(PgmTemplate).count() == 0
    
    # 저장된 파일 없음 확인
    assert not Path("uploads/PGM_*").exists()

def test_rollback_on_template_parsing_error(client, monkeypatch):
    """템플릿 파싱 실패 시 롤백"""
    ladder_zip = create_test_zip(10)
    template_xlsx = create_test_template(10)
    
    # 템플릿 파싱 시 에러 발생
    def mock_parse_template(*args, **kwargs):
        raise Exception("Excel Parse Error")
    
    monkeypatch.setattr(
        "ai_backend.api.services.template_service.TemplateService.parse_template_xlsx",
        mock_parse_template
    )
    
    # When: 업로드 시도
    response = client.post("/programs/upload", ...)
    
    # Then: 롤백 확인
    assert response.status_code == 500
    assert not Path("uploads/PGM_*").exists()

def test_rollback_on_disk_full(client, monkeypatch):
    """디스크 공간 부족 시 롤백"""
    ladder_zip = create_test_zip(10)
    template_xlsx = create_test_template(10)
    
    # 파일 저장 시 디스크 부족 에러
    def mock_save_file(*args, **kwargs):
        raise OSError("[Errno 28] No space left on device")
    
    monkeypatch.setattr(
        "ai_backend.api.services.file_storage_service.FileStorageService.save_and_extract_ladder_zip",
        mock_save_file
    )
    
    # When: 업로드 시도
    response = client.post("/programs/upload", ...)
    
    # Then: 에러 확인
    assert response.status_code == 500
    assert "디스크" in response.json()['message'] or "공간" in response.json()['message']
```

---

#### 4. 동시성 테스트

**test_upload_program_concurrency.py**
```python
"""
동시성 테스트

테스트 케이스:
1. 동시 업로드 5개 (순차 실행)
2. 동시 업로드 5개 (병렬 실행)
3. 같은 pgm_name으로 동시 업로드 (충돌 방지)
4. PGM_ID 자동 생성 경합 조건 (Race Condition)

검증 항목:
- 모든 업로드 성공
- PGM_ID 중복 없음
- 파일 경로 충돌 없음
- 트랜잭션 격리 수준 확인
"""

import concurrent.futures
import threading

def test_concurrent_uploads_sequential(client):
    """순차적 동시 업로드 (기준선)"""
    results = []
    
    for i in range(5):
        ladder_zip = create_test_zip(10)
        template_xlsx = create_test_template(10)
        
        response = client.post(
            "/programs/upload",
            files={...},
            data={"pgm_name": f"Program {i}", "create_user": "test"}
        )
        
        results.append(response.json())
    
    # 모든 업로드 성공 확인
    assert len(results) == 5
    for result in results:
        assert result['pgm_id'].startswith('PGM_')
    
    # PGM_ID 중복 없음 확인
    pgm_ids = [r['pgm_id'] for r in results]
    assert len(pgm_ids) == len(set(pgm_ids))

def test_concurrent_uploads_parallel(client):
    """병렬 동시 업로드"""
    def upload_program(i):
        ladder_zip = create_test_zip(10)
        template_xlsx = create_test_template(10)
        
        response = client.post(
            "/programs/upload",
            files={...},
            data={"pgm_name": f"Program {i}", "create_user": "test"}
        )
        
        return response.json()
    
    # 5개 병렬 실행
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload_program, i) for i in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # 검증
    assert len(results) == 5
    
    # PGM_ID 중복 없음 (Race Condition 테스트)
    pgm_ids = [r['pgm_id'] for r in results]
    assert len(pgm_ids) == len(set(pgm_ids))
    
    # 파일 경로 충돌 없음
    for result in results:
        pgm_id = result['pgm_id']
        upload_dir = Path(f"uploads/{pgm_id}")
        assert upload_dir.exists()

def test_same_name_concurrent_uploads(client):
    """같은 이름으로 동시 업로드 (충돌 방지)"""
    def upload_program():
        ladder_zip = create_test_zip(10)
        template_xlsx = create_test_template(10)
        
        response = client.post(
            "/programs/upload",
            files={...},
            data={
                "pgm_name": "Same Name",  # 동일한 이름
                "create_user": "test"
            }
        )
        
        return response.json()
    
    # 5개 병렬 실행 (모두 같은 이름)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload_program) for _ in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # 모두 성공 (이름은 같지만 PGM_ID는 다름)
    assert len(results) == 5
    pgm_ids = [r['pgm_id'] for r in results]
    assert len(pgm_ids) == len(set(pgm_ids))

def test_pgm_id_generation_race_condition(client, db_session):
    """PGM_ID 생성 경합 조건 테스트"""
    # PROGRAM_SEQUENCE 테이블 직접 조작
    # 동시에 generate_pgm_id() 호출
    
    def generate_id():
        from ai_backend.api.services.sequence_service import SequenceService
        service = SequenceService(db_session)
        return service.generate_pgm_id()
    
    # 100개 병렬 생성
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(generate_id) for _ in range(100)]
        pgm_ids = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # 중복 없음 확인
    assert len(pgm_ids) == 100
    assert len(set(pgm_ids)) == 100
    
    # 순차 증가 확인
    pgm_numbers = [int(id.replace('PGM_', '')) for id in pgm_ids]
    assert max(pgm_numbers) - min(pgm_numbers) == 99
```

---

### 📊 테스트 커버리지 목표

```
┌──────────────────────────────────────────────────┐
│ 모듈                        현재    목표    │
├──────────────────────────────────────────────────┤
│ ProgramUploadService       60%  →  95%       │
│ FileValidationService      70%  →  90%       │
│ FileStorageService         65%  →  90%       │
│ DocumentService            75%  →  85%       │
│ TemplateService            70%  →  85%       │
│ SequenceService            80%  →  95%       │
├──────────────────────────────────────────────────┤
│ 전체 평균                  70%  →  90%       │
└──────────────────────────────────────────────────┘
```

### 🛠️ 테스트 도구

**pytest 플러그인:**
```bash
pytest                    # 테스트 프레임워크
pytest-cov               # 커버리지 측정
pytest-asyncio           # 비동기 테스트
pytest-mock              # 모킹
pytest-benchmark         # 성능 벤치마크
pytest-xdist             # 병렬 실행
faker                    # 테스트 데이터 생성
locust                   # 부하 테스트
```

**테스트 실행 예시:**
```bash
# 전체 테스트 실행
pytest tests/integration/test_program_upload_*.py -v

# 커버리지 측정
pytest --cov=ai_backend.api.services --cov-report=html

# 병렬 실행 (8개 워커)
pytest -n 8 tests/integration/

# 특정 테스트만 실행
pytest tests/integration/test_upload_program_success.py::test_upload_program_with_100_files

# 벤치마크 실행
pytest tests/benchmark/test_performance.py --benchmark-only
```

**예상 작업 시간:** 8-10시간

---

## API 문서 보강

### 🎯 목표
API 문서 품질을 현재 → 프로덕션 수준으로 향상

### 📋 보강 항목

#### 1. Swagger 예제 추가

**현재 문제:**
```python
# program_router.py
@router.post("/programs/upload")
async def upload_program_files(
    pgm_name: str = Form(..., description="프로그램 명칭"),
    ...
):
    """프로그램 파일 업로드"""
    # 설명만 있고 예제 없음
```

**보강 방안:**
```python
@router.post(
    "/programs/upload",
    response_model=ProgramUploadResponse,
    summary="프로그램 파일 업로드",
    description="""
    PLC 프로그램 레더 파일(ZIP)과 템플릿 파일(XLSX)을 업로드하여 프로그램을 생성합니다.
    
    **주요 기능:**
    - PGM_ID 자동 생성 (예: PGM_1, PGM_2)
    - 레더 파일과 템플릿 파일 검증
    - 파일 저장 및 DB 레코드 생성
    - 트랜잭션 보장 (실패 시 롤백)
    
    **처리 시간:** 
    - 10개 파일: 약 1초
    - 100개 파일: 약 4초
    """,
    responses={
        201: {
            "description": "성공",
            "content": {
                "application/json": {
                    "example": {
                        "pgm_id": "PGM_1",
                        "pgm_name": "Test Program",
                        "pgm_version": "1.0",
                        "description": "테스트 프로그램",
                        "create_user": "admin",
                        "create_dt": "2025-11-06T10:30:00",
                        "validation_result": {
                            "validation_passed": True,
                            "matched_files": ["0000_11.csv", "0001_11.csv"],
                            "missing_files": [],
                            "unexpected_files": []
                        },
                        "saved_files": {
                            "ladder_csv_documents": [
                                {
                                    "document_id": "doc_20251106_103000_0000_11",
                                    "document_name": "0000_11.csv",
                                    "upload_path": "/uploads/PGM_1/ladder_files/0000_11.csv"
                                }
                            ],
                            "template_document": {
                                "document_id": "doc_20251106_103001_template",
                                "document_name": "template.xlsx",
                                "upload_path": "/uploads/PGM_1/template/template.xlsx"
                            }
                        },
                        "summary": {
                            "total_ladder_files": 2,
                            "template_parsed": True,
                            "template_row_count": 2
                        },
                        "message": "프로그램이 성공적으로 생성되었습니다"
                    }
                }
            }
        },
        400: {
            "description": "검증 실패",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_file_type": {
                            "summary": "잘못된 파일 타입",
                            "value": {
                                "code": "DOCUMENT_INVALID_FILE_TYPE",
                                "message": "레더 ZIP 파일은 .zip 형식이어야 합니다",
                                "timestamp": "2025-11-06T10:30:00"
                            }
                        },
                        "file_size_exceeded": {
                            "summary": "파일 크기 초과",
                            "value": {
                                "code": "DOCUMENT_FILE_TOO_LARGE",
                                "message": "파일 크기가 100.0MB를 초과했습니다",
                                "timestamp": "2025-11-06T10:30:00"
                            }
                        },
                        "missing_files": {
                            "summary": "필수 파일 누락",
                            "value": {
                                "code": "INVALID_DATA_FORMAT",
                                "message": "필수 레더 파일이 누락되었습니다: 0000_11.csv, 0001_11.csv",
                                "validation_result": {
                                    "validation_passed": False,
                                    "matched_files": [],
                                    "missing_files": ["0000_11.csv", "0001_11.csv"],
                                    "unexpected_files": []
                                },
                                "timestamp": "2025-11-06T10:30:00"
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {
                        "code": "UNDEFINED_ERROR",
                        "message": "프로그램 업로드 중 오류 발생: Database connection failed",
                        "timestamp": "2025-11-06T10:30:00"
                    }
                }
            }
        }
    }
)
async def upload_program_files(...):
    ...
```

---

#### 2. 에러 코드 문서화

**errors.md 생성**
```markdown
# API 에러 코드 가이드

## 프로그램 업로드 관련 에러

### DOCUMENT_INVALID_FILE_TYPE
**HTTP 상태:** 400  
**의미:** 지원하지 않는 파일 타입  
**발생 시점:** 파일 타입 검증 단계  
**해결 방법:** 
- 레더 파일: `.zip` 형식 사용
- 템플릿 파일: `.xlsx` 또는 `.xls` 형식 사용

**예시:**
```json
{
  "code": "DOCUMENT_INVALID_FILE_TYPE",
  "message": "레더 ZIP 파일은 .zip 형식이어야 합니다",
  "timestamp": "2025-11-06T10:30:00"
}
```

### DOCUMENT_FILE_TOO_LARGE
**HTTP 상태:** 400  
**의미:** 파일 크기 초과  
**발생 시점:** 파일 크기 검증 단계  
**최대 크기:**
- 레더 ZIP: 100MB (환경변수 설정 가능)
- 템플릿 파일: 10MB (환경변수 설정 가능)

**해결 방법:**
- 파일 크기 줄이기
- ZIP 압축률 조정
- 불필요한 파일 제거

**예시:**
```json
{
  "code": "DOCUMENT_FILE_TOO_LARGE",
  "message": "파일 크기가 100.0MB를 초과했습니다",
  "timestamp": "2025-11-06T10:30:00"
}
```

### INVALID_DATA_FORMAT
**HTTP 상태:** 400  
**의미:** 데이터 형식 오류  
**발생 시점:** 레더 파일 매칭 검증 단계  
**원인:**
1. 템플릿에 있는 Logic ID가 ZIP에 없음
2. 템플릿 필수 컬럼 누락
3. 템플릿 파일 손상

**해결 방법:**
1. 템플릿의 Logic ID와 ZIP 파일명 일치 확인
2. 템플릿에 필수 컬럼 확인: Logic ID, Folder ID, Logic Name
3. 템플릿 파일 재생성

**예시:**
```json
{
  "code": "INVALID_DATA_FORMAT",
  "message": "필수 레더 파일이 누락되었습니다: 0000_11.csv, 0001_11.csv",
  "validation_result": {
    "validation_passed": false,
    "matched_files": [],
    "missing_files": ["0000_11.csv", "0001_11.csv"],
    "unexpected_files": []
  },
  "timestamp": "2025-11-06T10:30:00"
}
```

### UNDEFINED_ERROR
**HTTP 상태:** 500  
**의미:** 서버 내부 오류  
**발생 시점:** 예상치 못한 에러  
**원인:**
- DB 연결 실패
- 디스크 공간 부족
- 네트워크 오류

**해결 방법:**
1. 에러 메시지 확인
2. 잠시 후 재시도
3. 지속 시 관리자에게 문의

**예시:**
```json
{
  "code": "UNDEFINED_ERROR",
  "message": "프로그램 업로드 중 오류 발생: Database connection failed",
  "timestamp": "2025-11-06T10:30:00"
}
```
```

---

#### 3. 사용자 가이드 작성

**user_guide.md 생성**
```markdown
# PLC 프로그램 업로드 가이드

## 빠른 시작

### 1. 파일 준비

**필요한 파일:**
1. **레더 CSV 파일들이 압축된 ZIP** (pgm_ladder_zip_file)
   - 형식: `.zip`
   - 최대 크기: 100MB
   - 파일명 패턴: `XXXX_YY.csv` (예: 0000_11.csv)

2. **템플릿 엑셀 파일** (pgm_template_file)
   - 형식: `.xlsx` 또는 `.xls`
   - 최대 크기: 10MB
   - 필수 컬럼: Logic ID, Folder ID, Logic Name

**ZIP 파일 구조 예시:**
```
ladder_files.zip
├── 0000_11.csv
├── 0001_11.csv
├── 0002_11.csv
└── ...
```

**템플릿 파일 예시:**
| Logic ID | Folder ID | Logic Name | Description | Note |
|----------|-----------|------------|-------------|------|
| 0000_11  | FOLDER_A  | Main Logic | 메인 로직   | ...  |
| 0001_11  | FOLDER_A  | Sub Logic  | 서브 로직   | ...  |

---

### 2. API 호출

**Endpoint:**
```
POST /programs/upload
```

**Request (Form Data):**
```
pgm_name: "Test Program"           (필수)
create_user: "admin"               (필수)
pgm_ladder_zip_file: [파일]        (필수)
pgm_template_file: [파일]          (필수)
pgm_version: "1.0"                 (선택)
description: "테스트 프로그램"     (선택)
notes: "비고"                      (선택)
```

**cURL 예시:**
```bash
curl -X POST "http://localhost:8000/programs/upload" \
  -F "pgm_name=Test Program" \
  -F "create_user=admin" \
  -F "pgm_ladder_zip_file=@ladder_files.zip" \
  -F "pgm_template_file=@template.xlsx" \
  -F "pgm_version=1.0" \
  -F "description=테스트 프로그램"
```

**Python 예시:**
```python
import requests

url = "http://localhost:8000/programs/upload"

files = {
    'pgm_ladder_zip_file': ('ladder_files.zip', open('ladder_files.zip', 'rb'), 'application/zip'),
    'pgm_template_file': ('template.xlsx', open('template.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
}

data = {
    'pgm_name': 'Test Program',
    'create_user': 'admin',
    'pgm_version': '1.0',
    'description': '테스트 프로그램'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

### 3. 응답 확인

**성공 응답 (201 Created):**
```json
{
  "pgm_id": "PGM_1",
  "pgm_name": "Test Program",
  "pgm_version": "1.0",
  "description": "테스트 프로그램",
  "create_user": "admin",
  "create_dt": "2025-11-06T10:30:00",
  "validation_result": {
    "validation_passed": true,
    "matched_files": ["0000_11.csv", "0001_11.csv"],
    "missing_files": [],
    "unexpected_files": []
  },
  "saved_files": {
    "ladder_csv_documents": [...],
    "template_document": {...}
  },
  "summary": {
    "total_ladder_files": 2,
    "template_parsed": true,
    "template_row_count": 2
  },
  "message": "프로그램이 성공적으로 생성되었습니다"
}
```

**실패 응답 (400 Bad Request):**
```json
{
  "code": "INVALID_DATA_FORMAT",
  "message": "필수 레더 파일이 누락되었습니다: 0000_11.csv",
  "timestamp": "2025-11-06T10:30:00"
}
```

---

## 자주 묻는 질문 (FAQ)

### Q1: PGM_ID는 어떻게 생성되나요?
A: 서버에서 자동으로 생성됩니다. PGM_1, PGM_2, PGM_3 ... 순으로 증가합니다.

### Q2: 템플릿에 없는 파일이 ZIP에 있으면 어떻게 되나요?
A: 자동으로 제거됩니다. 경고 없이 필요한 파일만 저장됩니다.

### Q3: 파일 크기 제한을 변경할 수 있나요?
A: 네, 환경변수를 통해 변경 가능합니다. 관리자에게 문의하세요.

### Q4: 업로드에 실패하면 어떻게 되나요?
A: 모든 변경사항이 롤백됩니다. 저장된 파일도 자동으로 삭제됩니다.

### Q5: 동시에 여러 프로그램을 업로드할 수 있나요?
A: 네, 최대 5개까지 동시 업로드가 가능합니다.

---

## 문제 해결

### 파일 타입 오류
**증상:** "지원하지 않는 파일 형식" 에러  
**해결:** 
- 레더 파일은 ZIP으로 압축
- 템플릿은 XLSX 또는 XLS 사용

### 파일 크기 초과
**증상:** "파일 크기 초과" 에러  
**해결:**
- ZIP 파일: 100MB 이하로 줄이기
- 템플릿: 10MB 이하로 줄이기

### 필수 파일 누락
**증상:** "필수 레더 파일이 누락되었습니다" 에러  
**해결:**
- 템플릿의 Logic ID와 ZIP 파일명 일치 확인
- 대소문자 구분 확인

### 템플릿 필수 컬럼 누락
**증상:** "필수 컬럼이 없습니다" 에러  
**해결:**
- Logic ID, Folder ID, Logic Name 컬럼 확인
- 철자 및 띄어쓰기 확인
```

---

### 📊 문서화 체크리스트

| 항목 | 현재 | 목표 | 우선순위 |
|------|------|------|----------|
| Swagger 예제 | ❌ | ✅ | 높음 |
| 에러 코드 문서 | ❌ | ✅ | 높음 |
| 사용자 가이드 | ❌ | ✅ | 중간 |
| API 아키텍처 | ❌ | ✅ | 중간 |
| 환경변수 문서 | ✅ | ✅ | 완료 |
| 코드 주석 | 70% | 90% | 낮음 |

**예상 작업 시간:** 4-5시간

---

## 추가 개선 제안

### 4. 로깅 및 모니터링 강화

**현재 문제:**
- 로그 레벨 일관성 부족
- 중요 지표 추적 미흡
- 에러 알림 없음

**개선 방안:**

**구조화된 로깅:**
```python
import structlog

logger = structlog.get_logger()

# Before
logger.info(f"✅ [Step 1] 레더 ZIP 파일 검증 완료: {filename}")

# After
logger.info(
    "ladder_zip_validation_success",
    step=1,
    filename=filename,
    file_size=file_size,
    pgm_id=pgm_id,
    elapsed_time_ms=elapsed_ms
)
```

**주요 지표 추적:**
```python
from prometheus_client import Counter, Histogram, Gauge

# 업로드 성공/실패 카운터
upload_success_counter = Counter(
    'program_upload_success_total',
    'Total successful program uploads'
)

upload_failure_counter = Counter(
    'program_upload_failure_total',
    'Total failed program uploads',
    ['error_type']  # 에러 유형별
)

# 처리 시간 히스토그램
upload_duration_histogram = Histogram(
    'program_upload_duration_seconds',
    'Program upload processing time',
    buckets=[0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
)

# 파일 크기 게이지
file_size_gauge = Gauge(
    'program_upload_file_size_bytes',
    'Uploaded file size in bytes'
)
```

**예상 작업 시간:** 3시간

---

### 5. 에러 복구 전략

**현재 문제:**
- 실패 시 재시도 없음
- 부분 실패 복구 어려움

**개선 방안:**

**자동 재시도 (Exponential Backoff):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def save_file_with_retry(self, file_path: Path, content: bytes):
    """
    파일 저장 재시도
    - 1차 실패: 2초 대기 후 재시도
    - 2차 실패: 4초 대기 후 재시도
    - 3차 실패: 최종 실패
    """
    try:
        file_path.write_bytes(content)
    except OSError as e:
        logger.warning(f"파일 저장 실패, 재시도: {e}")
        raise
```

**부분 복구:**
```python
def upload_program_with_partial_recovery(self, ...):
    """
    부분 실패 시 복구 시도
    """
    try:
        # Phase 1-3 실행
        ...
    except TemplateParsingError:
        # 템플릿 파싱만 실패 → 다른 작업은 유지
        logger.warning("템플릿 파싱 실패, 레더 파일은 저장됨")
        
        # 부분 결과 반환
        return {
            'pgm_id': pgm_id,
            'status': 'partial_success',
            'message': '레더 파일 저장 완료, 템플릿 파싱 실패',
            'saved_files': saved_files
        }
```

**예상 작업 시간:** 2시간

---

### 6. 보안 강화

**현재 문제:**
- 파일 내용 검증 미흡 (악성 파일)
- 업로드 속도 제한 없음
- 파일명 검증 미흡 (경로 순회 공격)

**개선 방안:**

**파일 내용 검증:**
```python
import magic

def validate_file_content(self, file: UploadFile):
    """
    실제 파일 내용 검증 (MIME 스니핑)
    - 확장자와 실제 내용 일치 확인
    - 악성 파일 탐지
    """
    content = file.file.read(8192)  # 처음 8KB 읽기
    file.file.seek(0)
    
    # 실제 MIME 타입 확인
    actual_mime = magic.from_buffer(content, mime=True)
    
    if file.filename.endswith('.zip'):
        if actual_mime != 'application/zip':
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="ZIP 파일이 아닙니다"
            )
```

**속도 제한 (Rate Limiting):**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/programs/upload")
@limiter.limit("5/minute")  # 1분에 5회 제한
async def upload_program_files(...):
    ...
```

**파일명 검증:**
```python
import re
from pathlib import PurePosixPath

def sanitize_filename(self, filename: str) -> str:
    """
    파일명 검증 및 정리
    - 경로 순회 공격 방지
    - 특수문자 제거
    """
    # 경로 순회 시도 차단
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HandledException(
            ResponseCode.INVALID_DATA_FORMAT,
            msg="잘못된 파일명"
        )
    
    # 안전한 파일명만 허용
    safe_filename = re.sub(r'[^\w\s.-]', '', filename)
    return safe_filename
```

**예상 작업 시간:** 3시간

---

## 우선순위 및 로드맵

### 📊 우선순위 매트릭스

```
높은 영향 ↑
│
│  [Phase 6: 성능 최적화]    [통합 테스트 작성]
│        (7시간)                  (8시간)
│         우선순위 1                우선순위 2
│
│
│  [보안 강화]              [API 문서 보강]
│    (3시간)                   (5시간)
│   우선순위 4                 우선순위 3
│
│
│  [로깅 강화]              [에러 복구]
│    (3시간)                   (2시간)
│   우선순위 5                 우선순위 6
│
└────────────────────────────────────> 높은 긴급도
```

### 📅 권장 작업 순서

#### 1차: 핵심 기능 안정화 (15시간)
```
Week 1: Phase 6 (성능 최적화) - 7시간
Week 2: 통합 테스트 작성 - 8시간
```

#### 2차: 사용성 개선 (8시간)
```
Week 3: API 문서 보강 - 5시간
Week 4: 보안 강화 - 3시간
```

#### 3차: 운영 개선 (5시간, 선택사항)
```
Week 5: 로깅 강화 - 3시간
Week 6: 에러 복구 - 2시간
```

### 💰 ROI 분석

| 작업 | 투자 시간 | 예상 효과 | ROI |
|------|----------|----------|-----|
| 성능 최적화 | 7시간 | 처리 시간 42% 감소 | 매우 높음 |
| 통합 테스트 | 8시간 | 버그 조기 발견, 안정성 향상 | 높음 |
| API 문서 | 5시간 | 사용자 문의 50% 감소 | 높음 |
| 보안 강화 | 3시간 | 보안 위험 90% 감소 | 높음 |
| 로깅 강화 | 3시간 | 문제 해결 시간 50% 감소 | 중간 |
| 에러 복구 | 2시간 | 가용성 향상 | 중간 |

---

## 📝 요약

### 즉시 시작 권장 (높은 우선순위)

1. **Phase 6: 성능 최적화** (7시간)
   - 가장 큰 임팩트
   - 사용자 경험 직접 개선
   - 확장성 확보

2. **통합 테스트 작성** (8시간)
   - 안정성 보장
   - 회귀 방지
   - 리팩토링 신뢰도 향상

3. **API 문서 보강** (5시간)
   - 사용자 편의성
   - 지원 비용 절감
   - 온보딩 시간 단축

### 점진적 개선 (중간 우선순위)

4. **보안 강화** (3시간)
   - 리스크 완화
   - 프로덕션 준비

5. **로깅 강화** (3시간)
   - 운영 효율성
   - 문제 해결 속도

6. **에러 복구** (2시간)
   - 안정성 향상
   - 사용자 경험 개선

**총 예상 시간: 28시간 (약 3.5일)**

---

궁금하신 부분이나 특정 항목에 대해 더 자세한 설명이 필요하시면 말씀해주세요! 😊