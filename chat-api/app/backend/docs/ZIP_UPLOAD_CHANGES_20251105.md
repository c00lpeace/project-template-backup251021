# 📦 ZIP 파일 업로드 최신 변경사항

> **작성일:** 2025-11-05  
> **목적:** ZIP 업로드 관련 필드명 표준화 및 구조 개편 내역 문서화

---

## 📊 변경사항 요약

### 주요 변경 목표
1. **shared_core Document 모델과 필드명 통일**
2. **메서드명 명확화** (`_extract_and_save_to_db` → `_extract_and_save_each_files`)
3. **폴더 구조 개선** (프로그램별 ZIP 관리)
4. **document_type 고정값 사용** (CSV/ZIP 명확히 구분)
5. **document_id 생성 방식 변경** (timestamp + hash 기반)

---

## 🔄 메서드명 변경

### 1. _extract_and_save_to_db() → _extract_and_save_each_files()

```python
# ❌ 변경 전
def _extract_and_save_to_db(self, zip_path: str, pgm_id: str, ...):
    """ZIP 파일 압축 해제 및 저장"""
    pass

# ✅ 변경 후
def _extract_and_save_each_files(self, zip_bytes: bytes, pgm_id: str, ...):
    """ZIP 파일 압축 해제 및 각 파일을 DOCUMENTS 테이블에 저장"""
    pass
```

**변경 이유:**
- 더 명확한 메서드명 (각 파일을 개별적으로 저장한다는 의미 강조)
- 파라미터 타입 변경 (파일 경로 → 바이트 데이터)

---

## 📝 필드명 표준화 (shared_core 호환)

### save_extracted_file_to_db() 메서드

**Document 생성 시 필드명 변경:**

| 항목 | 변경 전 | 변경 후 | 비고 |
|------|---------|---------|------|
| 파일명 | `file_name` | `document_name` | shared_core 표준 |
| 원본 파일명 | - | `original_filename` | 신규 추가 |
| 파일 키 | - | `file_key` | 신규 추가 |
| 파일 경로 | `file_path` | `upload_path` | shared_core 표준 |
| MIME 타입 | - | `file_type` | 신규 추가 |
| 문서 타입 | 동적 판단 | `PGM_LADDER_CSV` | 고정값 사용 |

**코드 비교:**

```python
# ❌ 변경 전
document_crud.create_document(
    file_name=filename,
    file_path=actual_file_path,
    document_type=self._determine_document_type(filename),  # 동적 판단
    ...
)

# ✅ 변경 후
document_crud.create_document(
    document_name=filename,           # ⭐ 필드명 변경
    original_filename=filename,       # ⭐ 신규 추가
    file_key=file_key,               # ⭐ 신규 추가
    upload_path=actual_file_path,    # ⭐ 필드명 변경
    file_type=file_type,             # ⭐ 신규 추가 (MIME type)
    document_type='PGM_LADDER_CSV',  # ⭐ 고정값
    ...
)
```

### _save_original_zip() 메서드

**동일한 필드명 변경 적용:**

```python
# ✅ 변경 후
document_crud.create_document(
    document_name=filename,
    original_filename=filename,
    file_key=file_key,
    upload_path=actual_file_path,
    file_type=file_type,
    document_type='PGM_LADDER_ZIP',  # ⭐ ZIP용 고정값
    ...
)
```

---

## 📂 폴더 구조 변경

### ZIP 저장 경로 변경

```python
# ❌ 변경 전
zipfiles_dir = Path(self.upload_base_path) / 'zipfiles'
파일명: {timestamp}_{user_id}_{filename}

# ✅ 변경 후  
zipfiles_dir = Path(self.upload_base_path) / pgm_id / 'zip'
파일명: filename (원본 파일명 그대로)
```

**폴더 구조 비교:**

```
# ❌ 변경 전
/uploads/
  ├─ {pgm_id}/           # 추출 파일
  │   ├─ file1.txt
  │   └─ file2.py
  └─ zipfiles/           # 원본 ZIP (전체 통합)
      └─ 20251105_user_archive.zip

# ✅ 변경 후
/uploads/
  └─ {pgm_id}/
      ├─ folder/         # 추출 파일
      │   ├─ file1.txt
      │   └─ file2.py
      └─ zip/            # ⭐ 원본 ZIP (프로그램별로 관리)
          └─ archive.zip
```

**변경 이유:**
- 프로그램별 파일 관리의 일관성
- pgm_id로 모든 관련 파일을 그룹화
- 원본 ZIP 파일명 유지 (timestamp 제거)

---

## 🔖 document_type 고정값 사용

### 타입 구분 명확화

```python
# ❌ 변경 전 (동적 판단)
def _determine_document_type(self, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == '.csv':
        return 'pgm_ladder_csv'
    elif ext == '.zip':
        return 'zip'
    else:
        return 'common'

# ✅ 변경 후 (고정값 사용)
# 추출 파일
document_type = 'PGM_LADDER_CSV'  # 모든 추출 파일

# 원본 ZIP
document_type = 'PGM_LADDER_ZIP'  # 원본 ZIP 파일
```

**변경 이유:**
- 타입 구분 명확화
- 조회 쿼리 최적화 (`WHERE document_type = 'PGM_LADDER_CSV'`)
- 유지보수 편의성

---

## 🆔 document_id 생성 방식 변경

### UUID → timestamp + hash

```python
# ❌ 변경 전
import uuid
document_id = str(uuid.uuid4())
# 예: "550e8400-e29b-41d4-a716-446655440000"

# ✅ 변경 후
document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}"
# 예: "doc_20251105_143022_a1b2c3d4"
```

**변경 이유:**
- 시간 정보 포함으로 디버깅 용이
- 파일 해시로 중복 방지
- 더 짧고 읽기 쉬운 ID

---

## 🔧 헬퍼 메서드 추가

### save_extracted_file_to_db() 내부에서 사용

```python
# 파일 정보 추출 로직 추가
file_extension = self._get_file_extension(filename)
file_type = self._get_mime_type(filename)
file_size = len(file_content)
file_hash = self._calculate_file_hash(file_content)
```

**필요한 헬퍼 메서드:**
- `_get_file_extension(filename)` → `.csv`, `.txt` 등
- `_get_mime_type(filename)` → `text/csv`, `application/zip` 등
- `_calculate_file_hash(content)` → MD5 해시값

**NOTE:** 이 메서드들은 BaseDocumentService에서 상속받음

---

## 📊 변경사항 상세 비교표

| 구분 | 항목 | 변경 전 | 변경 후 |
|------|------|---------|---------|
| **메서드명** | 압축 해제 | `_extract_and_save_to_db` | `_extract_and_save_each_files` |
| **필드명** | 파일명 | `file_name` | `document_name` |
| **필드명** | 파일 경로 | `file_path` | `upload_path` |
| **필드** | 원본 파일명 | - | `original_filename` (신규) |
| **필드** | 파일 키 | - | `file_key` (신규) |
| **필드** | MIME 타입 | - | `file_type` (신규) |
| **폴더 구조** | ZIP 저장 | `/uploads/zipfiles/` | `/uploads/{pgm_id}/zip/` |
| **파일명** | ZIP 파일 | `{timestamp}_{user_id}_{filename}` | `{filename}` (원본 유지) |
| **document_type** | 추출 파일 | 동적 판단 | `PGM_LADDER_CSV` (고정) |
| **document_type** | 원본 ZIP | 동적 판단 | `PGM_LADDER_ZIP` (고정) |
| **document_id** | 생성 방식 | UUID 기반 | timestamp + hash 기반 |

---

## 🎯 기대 효과

### 1. 코드 일관성 향상
- shared_core Document 모델과 완벽히 호환
- 필드명 통일로 혼란 최소화

### 2. 파일 관리 개선
- 프로그램별 폴더 구조로 관리 용이
- 원본 ZIP 파일명 유지로 추적 편의

### 3. 타입 안정성 강화
- document_type 고정값으로 쿼리 최적화
- 타입 구분 명확화

### 4. 디버깅 편의성
- document_id에 시간 정보 포함
- 더 읽기 쉬운 ID 형식

### 5. 확장성 향상
- file_key 추가로 파일 식별 강화
- MIME 타입 지원으로 파일 타입 정보 보강

---

## ⚠️ 주의사항

### 1. 기존 데이터 마이그레이션
```sql
-- 기존 데이터의 document_type 업데이트 필요 (선택사항)
UPDATE DOCUMENTS 
SET document_type = 'PGM_LADDER_CSV'
WHERE document_type IN ('pgm_ladder_csv', 'common')
  AND file_extension IN ('csv', 'txt');

UPDATE DOCUMENTS 
SET document_type = 'PGM_LADDER_ZIP'
WHERE document_type = 'zip';
```

### 2. API 클라이언트 영향 없음
- 외부 API 변경 없음
- 내부 구현만 변경
- 기존 업로드 API 그대로 사용 가능

### 3. 폴더 구조 변경 대응
- 기존 `/uploads/zipfiles/`의 파일들은 그대로 유지
- 새로 업로드되는 파일만 새 구조 적용
- 필요시 기존 파일 이동 스크립트 작성

---

## 🔍 테스트 체크리스트

### 기능 테스트
- [ ] ZIP 파일 업로드 (정상 케이스)
- [ ] ZIP 파일 업로드 (대용량 파일)
- [ ] ZIP 파일 업로드 (다중 폴더 구조)
- [ ] 추출된 파일 개별 다운로드
- [ ] 원본 ZIP 파일 다운로드
- [ ] pgm_id로 문서 목록 조회

### 데이터 검증
- [ ] DOCUMENTS 테이블 필드 확인
  - document_name 저장 확인
  - original_filename 저장 확인
  - file_key 저장 확인
  - upload_path 저장 확인
  - file_type (MIME) 저장 확인
  - document_type 고정값 확인
- [ ] 폴더 구조 확인
  - `/uploads/{pgm_id}/zip/` 생성 확인
  - 원본 파일명 유지 확인
- [ ] document_id 형식 확인
  - `doc_YYYYMMDD_HHMMSS_xxxxxxxx` 형식

### 성능 테스트
- [ ] 대용량 ZIP (100MB+) 업로드
- [ ] 다수의 파일 (1000개+) 포함 ZIP 업로드
- [ ] 메모리 사용량 모니터링

---

## 📚 관련 문서

1. **PROJECT_REFERENCE_GUIDE.md**
   - 프로젝트 전체 구조
   - 최근 변경사항 섹션 참조

2. **DATABASE_SCHEMA_REFERENCE.md**
   - DOCUMENTS 테이블 스키마
   - shared_core 필드 목록

3. **shared_core/models.py**
   - Document 모델 전체 정의
   - 필드 타입 및 제약조건

4. **shared_core/crud.py**
   - DocumentCRUD.create_document() 메서드
   - 파라미터 목록 및 사용법

---

## 💡 추가 고려사항

### 향후 개선 가능 사항

1. **파일 중복 제거**
   - file_hash를 이용한 중복 파일 감지
   - 동일 파일 재업로드 시 기존 파일 참조

2. **압축 해제 진행률 표시**
   - WebSocket을 통한 실시간 진행률
   - 대용량 ZIP 처리 시 사용자 경험 개선

3. **파일 타입별 처리**
   - CSV 파일: 자동 파싱 및 미리보기
   - 이미지 파일: 썸네일 생성
   - 문서 파일: 텍스트 추출

4. **배치 업로드**
   - 여러 ZIP 파일 동시 업로드
   - 비동기 처리 최적화

---

**작성일:** 2025-11-05  
**작성자:** Claude  
**문서 버전:** 1.0

**다음 업데이트:**
- 실제 테스트 결과 반영
- 성능 벤치마크 데이터 추가
- 마이그레이션 스크립트 제공
