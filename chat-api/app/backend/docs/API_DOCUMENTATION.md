# API 문서

## 목차
- [개요](#개요)
- [인증 및 권한](#인증-및-권한)
- [공통 응답 형식](#공통-응답-형식)
- [PLC 관리 API](#plc-관리-api)
- [프로그램 관리 API](#프로그램-관리-api)
- [템플릿 관리 API](#템플릿-관리-api)
- [문서 관리 API](#문서-관리-api)
- [매핑 이력 관리 API](#매핑-이력-관리-api)
- [캐시 관리 API](#캐시-관리-api)
- [에러 코드](#에러-코드)

---

## 개요

### Base URL
```
http://localhost:8000/v1
```

### API 버전
- **현재 버전**: v1
- **프로토콜**: HTTP/HTTPS
- **응답 형식**: JSON
- **인코딩**: UTF-8

### Swagger UI
- **URL**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 인증 및 권한

### 현재 구현 상태
- **인증 방식**: 미구현 (개발 중)
- **향후 계획**: JWT Token 기반 인증 도입

### 권한 체계
- **향후 계획**: 사용자 레벨, 그룹 레벨 권한 구현 예정

---

## 공통 응답 형식

### 성공 응답
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "plant": "PLT1",
  "process": "PRC1",
  ...
}
```

### 에러 응답
```json
{
  "detail": "에러 메시지",
  "error_code": "ERROR_CODE"
}
```

---

## PLC 관리 API

### 1. PLC 생성
**POST** `/plcs`

**Request Body:**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "plant": "PLT1",
  "process": "PRC1",
  "line": "LN1",
  "equipment_group": "EQ1",
  "unit": "U1",
  "plc_name": "테스트 PLC",
  "create_user": "admin"
}
```

**Response (201 Created):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "plant": "PLT1",
  "process": "PRC1",
  "line": "LN1",
  "equipment_group": "EQ1",
  "unit": "U1",
  "plc_name": "테스트 PLC"
}
```

---

### 2. PLC 조회 (단일)
**GET** `/plc/{plc_id}`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Query Parameters:**
- `include_deleted` (optional): 삭제된 PLC도 포함 여부 (default: false)

**Response (200 OK):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "plant": "PLT1",
  "process": "PRC1",
  "line": "LN1",
  "equipment_group": "EQ1",
  "unit": "U1",
  "plc_name": "테스트 PLC",
  "pgm_id": "PGM_1",
  "is_active": true,
  "create_user": "admin",
  "create_dt": "2025-11-12T10:00:00",
  "update_user": null,
  "update_dt": null,
  "pgm_mapping_dt": "2025-11-12T11:00:00",
  "pgm_mapping_user": "admin"
}
```

---

### 3. PLC 목록 조회
**GET** `/plcs`

**Query Parameters:**
- `skip` (optional): 건너뛸 개수 (default: 0, min: 0)
- `limit` (optional): 조회할 개수 (default: 100, min: 1, max: 1000)
- `is_active` (optional): 활성 상태 필터 (true/false, null=전체)
- `plant` (optional): Plant 필터
- `process` (optional): 공정 필터
- `line` (optional): Line 필터
- `equipment_group` (optional): 장비그룹 필터
- `unit` (optional): 호기 필터

**Response (200 OK):**
```json
{
  "total": 25,
  "items": [
    {
      "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
      "plant": "PLT1",
      "process": "PRC1",
      "line": "LN1",
      "equipment_group": "EQ1",
      "unit": "U1",
      "plc_name": "테스트 PLC",
      "pgm_id": "PGM_1",
      "is_active": true,
      "create_user": "admin",
      "create_dt": "2025-11-12T10:00:00"
    }
  ]
}
```

---

### 4. PLC 수정
**PUT** `/plc/{plc_id}`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Request Body:**
```json
{
  "plant": "PLT1",
  "process": "PRC1",
  "line": "LN1",
  "equipment_group": "EQ1",
  "unit": "U1",
  "plc_name": "수정된 PLC 이름",
  "update_user": "admin"
}
```

**Response (200 OK):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "plant": "PLT1",
  "process": "PRC1",
  "line": "LN1",
  "equipment_group": "EQ1",
  "unit": "U1",
  "plc_name": "수정된 PLC 이름",
  "update_dt": "2025-11-12T12:00:00"
}
```

---

### 5. PLC 삭제 (소프트 삭제)
**DELETE** `/plc/{plc_id}`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Response (200 OK):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "message": "PLC가 성공적으로 삭제되었습니다."
}
```

---

### 6. PLC 복원
**POST** `/plc/{plc_id}/restore`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Response (200 OK):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "message": "PLC가 성공적으로 복원되었습니다."
}
```

---

### 7. PLC 검색
**GET** `/plcs/search/keyword`

**Query Parameters:**
- `keyword` (required): 검색 키워드 (PLC ID 또는 PLC 이름, min: 1자)
- `skip` (optional): 건너뛸 개수 (default: 0, min: 0)
- `limit` (optional): 조회할 개수 (default: 100, min: 1, max: 1000)
- `is_active` (optional): 활성 상태 필터 (default: true)

**Response (200 OK):**
```json
{
  "total": 3,
  "items": [
    {
      "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
      "plc_name": "테스트 PLC",
      "plant": "PLT1",
      "is_active": true
    }
  ]
}
```

---

### 8. PLC 개수 조회
**GET** `/plcs/count/summary`

**Response (200 OK):**
```json
{
  "active_count": 150,
  "inactive_count": 10,
  "total_count": 160
}
```

---

### 9. PLC 존재 여부 확인
**GET** `/plc/{plc_id}/exists`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Response (200 OK):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "exists": true
}
```

---

### 10. 계층별 고유 값 조회
**GET** `/plcs/hierarchy/values`

**Query Parameters:**
- `level` (required): 조회할 레벨 (plant/process/line/equipment_group/unit 중 하나)
- `plant` (optional): Plant 필터
- `process` (optional): 공정 필터
- `line` (optional): Line 필터
- `equipment_group` (optional): 장비그룹 필터

**Response (200 OK):**
```json
{
  "level": "process",
  "values": ["PRC1", "PRC2", "PRC3"]
}
```

---

### 11. PLC 계층 구조 트리 조회
**GET** `/plcs/tree`

**Query Parameters:**
- `is_active` (optional): 활성 PLC만 조회 (default: true)

**Response (200 OK):**
```json
{
  "data": [
    {
      "plt": "PLT1",
      "procList": [
        {
          "proc": "PRC1",
          "lineList": [
            {
              "line": "LN1",
              "eqGrpList": [
                {
                  "eqGrp": "EQ1",
                  "unitList": [
                    {
                      "unit": "U1",
                      "info": [
                        {
                          "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
                          "create_dt": "2025-11-12T10:00:00",
                          "user": "admin"
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

### 12. 프로그램 매핑
**POST** `/plc/{plc_id}/mapping`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Request Body:**
```json
{
  "pgm_id": "PGM_1",
  "user": "admin",
  "notes": "신규 매핑"
}
```

**Response (200 OK):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "pgm_id": "PGM_1",
  "pgm_mapping_dt": "2025-11-12T13:00:00",
  "pgm_mapping_user": "admin",
  "message": "PLC 'PLT1-PRC1-LN1-EQ1-U1-PLC01'에 프로그램 'PGM_1'가 성공적으로 매핑되었습니다."
}
```

---

### 13. 프로그램 매핑 해제
**DELETE** `/plc/{plc_id}/mapping`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Request Body:**
```json
{
  "user": "admin",
  "notes": "매핑 해제"
}
```

**Response (200 OK):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "message": "PLC 'PLT1-PRC1-LN1-EQ1-U1-PLC01'의 프로그램 매핑이 성공적으로 해제되었습니다."
}
```

---

### 14. 매핑되지 않은 PLC 목록 조회
**GET** `/plcs/unmapped/list`

**Query Parameters:**
- `skip` (optional): 건너뛸 개수 (default: 0, min: 0)
- `limit` (optional): 조회할 개수 (default: 100, min: 1, max: 1000)

**Response (200 OK):**
```json
{
  "total": 5,
  "items": [
    {
      "plc_id": "PLT1-PRC1-LN1-EQ1-U2-PLC01",
      "plc_name": "매핑 안된 PLC",
      "pgm_id": null,
      "is_active": true
    }
  ]
}
```

---

### 15. 프로그램 일괄 매핑
**POST** `/plcs/mapping/bulk`

**Request Body:**
```json
{
  "plc_ids": ["PLC01", "PLC02", "PLC03"],
  "pgm_id": "PGM_1",
  "user": "admin",
  "notes": "일괄 매핑",
  "rollback_on_error": false
}
```

**Request Parameters:**
- `plc_ids` (required): 매핑할 PLC ID 목록 (최대 100개)
- `pgm_id` (required): 매핑할 프로그램 ID
- `user` (required): 작업자
- `notes` (optional): 비고
- `rollback_on_error` (optional): 에러 시 전체 롤백 여부 (default: false)
  - true: 하나라도 실패하면 전체 롤백
  - false: 성공한 것만 커밋 (부분 성공)

**Response (200 OK):**
```json
{
  "total": 3,
  "success_count": 2,
  "failure_count": 1,
  "pgm_id": "PGM_1",
  "results": [
    {
      "plc_id": "PLC01",
      "success": true,
      "message": "프로그램 'PGM_1' 매핑 성공",
      "pgm_id": "PGM_1",
      "prev_pgm_id": null
    },
    {
      "plc_id": "PLC02",
      "success": false,
      "message": "PLC 'PLC02'를 찾을 수 없습니다.",
      "pgm_id": null,
      "prev_pgm_id": null
    },
    {
      "plc_id": "PLC03",
      "success": true,
      "message": "프로그램 'PGM_1' 매핑 성공",
      "pgm_id": "PGM_1",
      "prev_pgm_id": "PGM_OLD"
    }
  ],
  "message": "3개 중 2개 성공, 1개 실패",
  "rolled_back": false
}
```

---

### 16. 프로그램 일괄 매핑 해제
**DELETE** `/plcs/mapping/bulk`

**Request Body:**
```json
{
  "plc_ids": ["PLC01", "PLC02", "PLC03"],
  "user": "admin",
  "notes": "일괄 매핑 해제",
  "rollback_on_error": false
}
```

**Request Parameters:**
- `plc_ids` (required): 매핑 해제할 PLC ID 목록 (최대 100개)
- `user` (required): 작업자
- `notes` (optional): 비고
- `rollback_on_error` (optional): 에러 시 전체 롤백 여부 (default: false)

**Response (200 OK):**
```json
{
  "total": 3,
  "success_count": 3,
  "failure_count": 0,
  "results": [
    {
      "plc_id": "PLC01",
      "success": true,
      "message": "매핑 해제 성공",
      "pgm_id": "PGM_1",
      "prev_pgm_id": "PGM_1"
    }
  ],
  "message": "모두 성공적으로 매핑 해제되었습니다. (성공: 3개)",
  "rolled_back": false
}
```

---

### 17. 프로그램 일괄 변경
**PUT** `/plcs/mapping/bulk`

**Request Body:**
```json
{
  "plc_ids": ["PLC01", "PLC02", "PLC03"],
  "new_pgm_id": "PGM_2",
  "user": "admin",
  "notes": "프로그램 일괄 변경",
  "rollback_on_error": false
}
```

**Request Parameters:**
- `plc_ids` (required): 프로그램을 변경할 PLC ID 목록 (최대 100개)
- `new_pgm_id` (required): 새로운 프로그램 ID
- `user` (required): 작업자
- `notes` (optional): 비고
- `rollback_on_error` (optional): 에러 시 전체 롤백 여부 (default: false)

**Response (200 OK):**
```json
{
  "total": 3,
  "success_count": 3,
  "failure_count": 0,
  "new_pgm_id": "PGM_2",
  "results": [
    {
      "plc_id": "PLC01",
      "success": true,
      "message": "프로그램이 'PGM_1'에서 'PGM_2'로 변경되었습니다.",
      "pgm_id": "PGM_2",
      "prev_pgm_id": "PGM_1"
    }
  ],
  "message": "모두 성공적으로 프로그램이 변경되었습니다. (성공: 3개)",
  "rolled_back": false
}
```

---

## 프로그램 관리 API

### 1. 프로그램 생성
**POST** `/programs`

**Request Body:**
```json
{
  "pgm_id": "PGM_1",
  "pgm_name": "테스트 프로그램",
  "pgm_version": "1.0",
  "description": "프로그램 설명",
  "create_user": "admin",
  "notes": "비고"
}
```

**Response (201 Created):**
```json
{
  "pgm_id": "PGM_1",
  "pgm_name": "테스트 프로그램",
  "pgm_version": "1.0",
  "description": "프로그램 설명",
  "is_active": true,
  "create_user": "admin",
  "create_dt": "2025-11-12T10:00:00",
  "update_user": null,
  "update_dt": null
}
```

---

### 2. 프로그램 조회 (단일)
**GET** `/programs/{pgm_id}`

**Path Parameters:**
- `pgm_id` (required): 프로그램 ID

**Response (200 OK):**
```json
{
  "pgm_id": "PGM_1",
  "pgm_name": "테스트 프로그램",
  "pgm_version": "1.0",
  "description": "프로그램 설명",
  "is_active": true,
  "create_user": "admin",
  "create_dt": "2025-11-12T10:00:00"
}
```

---

### 3. 프로그램 목록 조회
**GET** `/programs`

**Query Parameters:**
- `page` (optional): 페이지 번호 (default: 1, min: 1)
- `page_size` (optional): 페이지당 개수 (default: 50, min: 1, max: 100)
- `search` (optional): 검색어 (ID 또는 명칭)
- `pgm_version` (optional): 프로그램 버전 필터

**Response (200 OK):**
```json
{
  "items": [
    {
      "pgm_id": "PGM_1",
      "pgm_name": "테스트 프로그램",
      "pgm_version": "1.0",
      "is_active": true,
      "create_dt": "2025-11-12T10:00:00"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 10
}
```

---

### 4. 프로그램 수정
**PUT** `/programs/{pgm_id}`

**Path Parameters:**
- `pgm_id` (required): 프로그램 ID

**Request Body:**
```json
{
  "pgm_name": "수정된 프로그램명",
  "pgm_version": "1.1",
  "description": "수정된 설명",
  "notes": "수정 비고",
  "update_user": "admin"
}
```

**Response (200 OK):**
```json
{
  "pgm_id": "PGM_1",
  "pgm_name": "수정된 프로그램명",
  "pgm_version": "1.1",
  "description": "수정된 설명",
  "update_user": "admin",
  "update_dt": "2025-11-12T14:00:00"
}
```

---

### 5. 프로그램 삭제
**DELETE** `/programs/{pgm_id}`

**Path Parameters:**
- `pgm_id` (required): 프로그램 ID

**Response (200 OK):**
```json
{
  "pgm_id": "PGM_1",
  "message": "프로그램이 성공적으로 삭제되었습니다."
}
```

---

### 6. 프로그램별 매핑된 PLC 목록 조회
**GET** `/programs/{pgm_id}/plcs`

**Path Parameters:**
- `pgm_id` (required): 프로그램 ID

**Query Parameters:**
- `skip` (optional): 건너뛸 개수 (default: 0, min: 0)
- `limit` (optional): 조회할 개수 (default: 100, min: 1, max: 100)

**Response (200 OK):**
```json
{
  "pgm_id": "PGM_1",
  "total": 25,
  "items": [
    {
      "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
      "plc_name": "테스트 PLC",
      "pgm_id": "PGM_1",
      "pgm_mapping_dt": "2025-11-12T13:00:00",
      "pgm_mapping_user": "admin"
    }
  ]
}
```

---

### 7. 프로그램 파일 업로드
**POST** `/programs/upload`

**Content-Type:** `multipart/form-data`

**Form Parameters:**
- `pgm_name` (required): 프로그램 명칭
- `create_user` (required): 생성자
- `ladder_zip` (required): 레더 CSV 파일들이 압축된 ZIP
- `template_xlsx` (required): 필수 파일 목록이 기재된 템플릿 파일
- `pgm_version` (optional): 프로그램 버전
- `description` (optional): 프로그램 설명
- `notes` (optional): 비고

**Response (201 Created):**
```json
{
  "pgm_id": "PGM_1",
  "pgm_name": "신규 프로그램",
  "pgm_version": "1.0",
  "description": "프로그램 설명",
  "create_user": "admin",
  "create_dt": "2025-11-12T10:00:00",
  "validation_result": {
    "is_valid": true,
    "missing_files": [],
    "extra_files": ["불필요파일.csv"],
    "matched_files": ["로직1.csv", "로직2.csv"],
    "total_required": 2,
    "total_matched": 2
  },
  "saved_files": {
    "zip_files": [
      {
        "document_id": "doc_20251112_100000_abc123",
        "file_name": "로직1.csv",
        "file_path": "/uploads/PGM_1/로직1.csv"
      }
    ],
    "template_file": {
      "document_id": "doc_20251112_100001_def456",
      "file_name": "template.xlsx",
      "file_path": "/uploads/PGM_1/template.xlsx"
    }
  },
  "summary": {
    "total_saved_files": 3,
    "zip_extracted_files": 2,
    "removed_extra_files": 1
  },
  "message": "프로그램 'PGM_1'이 성공적으로 생성되었습니다."
}
```

---

## 템플릿 관리 API

### 1. 템플릿 트리 구조 조회
**GET** `/templates/{pgm_id}`

**Path Parameters:**
- `pgm_id` (required): 프로그램 ID

**Response (200 OK):**
```json
{
  "pgm_id": "PGM_1",
  "tree": [
    {
      "folder_id": "FLD001",
      "folder_name": "메인폴더",
      "sub_folders": [
        {
          "sub_folder_id": "SUB001",
          "sub_folder_name": "서브폴더1",
          "logics": [
            {
              "logic_id": "LOGIC001",
              "logic_name": "로직1",
              "description": "로직 설명"
            }
          ]
        }
      ]
    }
  ]
}
```

---

### 2. 템플릿 목록 조회
**GET** `/templates`

**Query Parameters:**
- `pgm_id` (optional): 프로그램 ID 필터
- `folder_id` (optional): 폴더 ID 필터
- `logic_name` (optional): 로직명 검색어
- `page` (optional): 페이지 번호 (default: 1, min: 1)
- `page_size` (optional): 페이지 크기 (default: 100, min: 1, max: 1000)

**Response (200 OK):**
```json
{
  "items": [
    {
      "template_id": "TMPL001",
      "pgm_id": "PGM_1",
      "folder_id": "FLD001",
      "folder_name": "메인폴더",
      "sub_folder_id": "SUB001",
      "sub_folder_name": "서브폴더1",
      "logic_id": "LOGIC001",
      "logic_name": "로직1",
      "description": "로직 설명"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### 3. 템플릿 삭제
**DELETE** `/templates/{pgm_id}`

**Path Parameters:**
- `pgm_id` (required): 프로그램 ID

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "프로그램 PGM_1의 템플릿이 삭제되었습니다.",
  "data": {
    "deleted_count": 50
  }
}
```

---

### 4. 템플릿 요약 정보 조회
**GET** `/templates-summary`

**Response (200 OK):**
```json
{
  "total_programs": 10,
  "total_templates": 500,
  "programs": [
    {
      "pgm_id": "PGM_1",
      "pgm_name": "테스트 프로그램",
      "template_count": 50
    },
    {
      "pgm_id": "PGM_2",
      "pgm_name": "프로그램2",
      "template_count": 75
    }
  ]
}
```

---

### 5. 프로그램별 템플릿 개수 조회
**GET** `/templates/count/{pgm_id}`

**Path Parameters:**
- `pgm_id` (required): 프로그램 ID

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "pgm_id": "PGM_1",
    "template_count": 50
  }
}
```

---

## 문서 관리 API

### 1. 문서 업로드
**POST** `/v1/upload`

**Content-Type:** `multipart/form-data`

**Form Parameters:**
- `file` (required): 업로드할 파일
- `user_id` (optional): 사용자 ID (default: "user")
- `is_public` (optional): 공개 여부 (default: false)
- `permissions` (optional): 권한 리스트 (JSON 문자열)
- `document_type` (optional): 문서 타입 (default: "common")
- `metadata` (optional): 메타데이터 (JSON 문자열)

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "문서가 업로드되었습니다.",
  "data": {
    "document_id": "doc_20251112_100000_abc123",
    "document_name": "테스트파일.pdf",
    "upload_path": "/uploads/user/테스트파일.pdf",
    "file_size": 1024000,
    "file_extension": "pdf"
  }
}
```

---

### 2. 문서 목록 조회
**GET** `/v1/documents`

**Query Parameters:**
- `user_id` (optional): 사용자 ID
- `document_type` (optional): 문서 타입 필터
- `pgm_id` (optional): 프로그램 ID 필터
- `skip` (optional): 건너뛸 개수 (default: 0)
- `limit` (optional): 조회할 개수 (default: 100)

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "document_id": "doc_20251112_100000_abc123",
        "document_name": "로직1.csv",
        "pgm_id": "PGM_1",
        "file_extension": "csv",
        "file_size": 2048,
        "upload_path": "/uploads/PGM_1/로직1.csv",
        "create_dt": "2025-11-12T10:00:00"
      }
    ],
    "total": 25
  }
}
```

---

### 3. 문서 조회 (단일)
**GET** `/v1/documents/{document_id}`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "document_id": "doc_20251112_100000_abc123",
    "document_name": "로직1.csv",
    "original_filename": "로직1.csv",
    "file_key": "PGM_1/로직1.csv",
    "upload_path": "/uploads/PGM_1/로직1.csv",
    "file_type": "text/csv",
    "file_extension": "csv",
    "document_type": "PGM_LADDER_CSV",
    "pgm_id": "PGM_1",
    "file_size": 2048,
    "create_dt": "2025-11-12T10:00:00"
  }
}
```

---

### 4. 문서 다운로드
**GET** `/v1/documents/{document_id}/download`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Response (200 OK):**
- Binary file with proper headers
- `Content-Type: application/octet-stream`
- `Content-Disposition: attachment; filename="로직1.csv"`

---

### 5. 문서 삭제
**DELETE** `/v1/documents/{document_id}`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "문서가 삭제되었습니다.",
  "data": {
    "document_id": "doc_20251112_100000_abc123"
  }
}
```

---

### 6. ZIP 파일 업로드
**POST** `/v1/upload-zip`

**Content-Type:** `multipart/form-data`

**Form Parameters:**
- `file` (required): ZIP 파일
- `pgm_id` (required): 프로그램 ID
- `user_id` (optional): 사용자 ID (default: "user")
- `is_public` (optional): 공개 여부 (default: false)
- `keep_zip_file` (optional): 원본 ZIP 저장 여부 (default: true)

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "zip 파일이 성공적으로 업로드되었습니다",
  "data": {
    "extracted_files": [
      {
        "document_id": "doc_20251112_100000_abc123",
        "file_name": "로직1.csv",
        "file_path": "/uploads/PGM_1/로직1.csv",
        "file_size": 2048
      },
      {
        "document_id": "doc_20251112_100001_def456",
        "file_name": "로직2.csv",
        "file_path": "/uploads/PGM_1/로직2.csv",
        "file_size": 3072
      }
    ],
    "zip_file": {
      "document_id": "doc_20251112_100002_ghi789",
      "file_name": "archive.zip",
      "file_path": "/uploads/PGM_1/zip/archive.zip"
    },
    "summary": {
      "total_extracted": 2,
      "total_size": 5120
    }
  }
}
```

---

### 7. ZIP 내부 파일 목록 조회
**GET** `/v1/zip/{document_id}/contents`

**Path Parameters:**
- `document_id` (required): ZIP 문서 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")
- `search_term` (optional): 파일명 또는 경로 검색어
- `extension` (optional): 확장자 필터 (예: .txt, .csv)
- `page` (optional): 페이지 번호 (default: 1)
- `page_size` (optional): 페이지 크기 (default: 100, min: 1, max: 1000)

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "file_path": "로직1.csv",
        "file_size": 2048,
        "is_directory": false
      },
      {
        "file_path": "로직2.csv",
        "file_size": 3072,
        "is_directory": false
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 100
  }
}
```

---

### 8. ZIP 내부 파일 추출
**GET** `/v1/zip/{document_id}/extract/{file_path}`

**Path Parameters:**
- `document_id` (required): ZIP 문서 ID
- `file_path` (required): 추출할 파일 경로

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response (200 OK):**
- Binary file with proper headers
- `Content-Type: application/octet-stream`
- `Content-Disposition: attachment; filename="로직1.csv"`

---

## 매핑 이력 관리 API

### 1. PLC별 매핑 이력 조회
**GET** `/pgm-history/plc/{plc_id}`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Query Parameters:**
- `skip` (optional): 건너뛸 개수 (default: 0, min: 0)
- `limit` (optional): 조회할 개수 (default: 50, min: 1, max: 100)

**Response (200 OK):**
```json
{
  "total": 15,
  "items": [
    {
      "history_id": 1001,
      "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
      "pgm_id": "PGM_1",
      "prev_pgm_id": null,
      "action": "CREATE",
      "action_user": "admin",
      "action_dt": "2025-11-12T10:00:00",
      "notes": "신규 매핑"
    },
    {
      "history_id": 1002,
      "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
      "pgm_id": "PGM_2",
      "prev_pgm_id": "PGM_1",
      "action": "UPDATE",
      "action_user": "admin",
      "action_dt": "2025-11-12T14:00:00",
      "notes": "프로그램 변경"
    }
  ]
}
```

---

### 2. 프로그램별 매핑 이력 조회
**GET** `/pgm-history/program/{pgm_id}`

**Path Parameters:**
- `pgm_id` (required): 프로그램 ID

**Query Parameters:**
- `skip` (optional): 건너뛸 개수 (default: 0, min: 0)
- `limit` (optional): 조회할 개수 (default: 50, min: 1, max: 100)

**Response (200 OK):**
```json
{
  "total": 25,
  "items": [
    {
      "history_id": 1001,
      "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
      "pgm_id": "PGM_1",
      "prev_pgm_id": null,
      "action": "CREATE",
      "action_user": "admin",
      "action_dt": "2025-11-12T10:00:00"
    }
  ]
}
```

---

### 3. 사용자별 매핑 이력 조회
**GET** `/pgm-history/user/{action_user}`

**Path Parameters:**
- `action_user` (required): 사용자 ID

**Query Parameters:**
- `skip` (optional): 건너뛸 개수 (default: 0, min: 0)
- `limit` (optional): 조회할 개수 (default: 50, min: 1, max: 100)

**Response (200 OK):**
```json
{
  "total": 100,
  "items": [
    {
      "history_id": 1001,
      "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
      "pgm_id": "PGM_1",
      "action": "CREATE",
      "action_user": "admin",
      "action_dt": "2025-11-12T10:00:00"
    }
  ]
}
```

---

### 4. 최근 매핑 이력 조회
**GET** `/pgm-history/recent`

**Query Parameters:**
- `skip` (optional): 건너뛸 개수 (default: 0, min: 0)
- `limit` (optional): 조회할 개수 (default: 100, min: 1, max: 200)
- `action` (optional): 액션 필터 (CREATE/UPDATE/DELETE/RESTORE)

**Response (200 OK):**
```json
{
  "total": 50,
  "items": [
    {
      "history_id": 1050,
      "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC05",
      "pgm_id": "PGM_3",
      "action": "CREATE",
      "action_user": "admin",
      "action_dt": "2025-11-12T15:30:00"
    }
  ]
}
```

---

### 5. PLC 이력 통계 조회
**GET** `/pgm-history/plc/{plc_id}/stats`

**Path Parameters:**
- `plc_id` (required): PLC ID

**Response (200 OK):**
```json
{
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "total_changes": 15,
  "action_counts": {
    "CREATE": 1,
    "UPDATE": 10,
    "DELETE": 2,
    "RESTORE": 2
  },
  "last_action_dt": "2025-11-12T14:00:00",
  "first_action_dt": "2025-11-10T09:00:00"
}
```

---

### 6. 이력 조회 (단일)
**GET** `/pgm-history/{history_id}`

**Path Parameters:**
- `history_id` (required): 이력 ID

**Response (200 OK):**
```json
{
  "history_id": 1001,
  "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
  "pgm_id": "PGM_1",
  "prev_pgm_id": null,
  "action": "CREATE",
  "action_user": "admin",
  "action_dt": "2025-11-12T10:00:00",
  "notes": "신규 매핑"
}
```

---

## 캐시 관리 API

### 1. 캐시 상태 조회
**GET** `/cache/status`

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "enabled": true,
    "redis_version": "7.0.5",
    "used_memory": "2.5M",
    "total_keys": 150,
    "cache_config": {
      "enabled": true,
      "ttl_chat_messages": 3600,
      "ttl_user_chats": 1800,
      "redis_host": "localhost",
      "redis_port": 6379,
      "redis_db": 0
    }
  }
}
```

**Redis 비활성 상태:**
```json
{
  "status": "success",
  "data": {
    "enabled": false,
    "message": "Redis not available"
  }
}
```

---

### 2. 캐시 초기화
**POST** `/cache/clear`

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "캐시가 초기화되었습니다.",
  "data": {
    "cleared_keys": 150
  }
}
```

---

## 에러 코드

### HTTP 상태 코드
- `200`: 성공
- `201`: 생성 성공
- `400`: 잘못된 요청
- `404`: 리소스를 찾을 수 없음
- `409`: 충돌 (이미 존재하는 리소스)
- `500`: 서버 내부 오류

### 커스텀 에러 응답
```json
{
  "detail": "에러 메시지",
  "error_code": "ERROR_CODE"
}
```

---

## 예제 코드

### Python (requests)
```python
import requests

# PLC 생성
response = requests.post(
    "http://localhost:8000/v1/plcs",
    json={
        "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
        "plant": "PLT1",
        "process": "PRC1",
        "line": "LN1",
        "equipment_group": "EQ1",
        "unit": "U1",
        "plc_name": "테스트 PLC",
        "create_user": "admin"
    }
)
plc = response.json()

# 프로그램 매핑
response = requests.post(
    f"http://localhost:8000/v1/plc/{plc['plc_id']}/mapping",
    json={
        "pgm_id": "PGM_1",
        "user": "admin",
        "notes": "신규 매핑"
    }
)
```

### JavaScript (fetch)
```javascript
// PLC 목록 조회
const response = await fetch('http://localhost:8000/v1/plcs?skip=0&limit=10', {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
});
const { total, items } = await response.json();

// 프로그램 일괄 매핑
const bulkResponse = await fetch('http://localhost:8000/v1/plcs/mapping/bulk', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    plc_ids: ['PLC01', 'PLC02', 'PLC03'],
    pgm_id: 'PGM_1',
    user: 'admin',
    notes: '일괄 매핑',
    rollback_on_error: false
  })
});
```

### cURL
```bash
# PLC 생성
curl -X POST http://localhost:8000/v1/plcs \
  -H "Content-Type: application/json" \
  -d '{
    "plc_id": "PLT1-PRC1-LN1-EQ1-U1-PLC01",
    "plant": "PLT1",
    "process": "PRC1",
    "line": "LN1",
    "equipment_group": "EQ1",
    "unit": "U1",
    "plc_name": "테스트 PLC",
    "create_user": "admin"
  }'

# 프로그램 파일 업로드
curl -X POST http://localhost:8000/v1/programs/upload \
  -F "pgm_name=신규 프로그램" \
  -F "create_user=admin" \
  -F "ladder_zip=@/path/to/ladder.zip" \
  -F "template_xlsx=@/path/to/template.xlsx" \
  -F "pgm_version=1.0"

# ZIP 파일 업로드
curl -X POST http://localhost:8000/v1/upload-zip \
  -F "file=@/path/to/archive.zip" \
  -F "pgm_id=PGM_1" \
  -F "user_id=admin" \
  -F "keep_zip_file=true"
```

---

## 변경 이력

### v1.0.0 (2025-11-12)
- PLC 관리 API (17개 엔드포인트)
- 프로그램 관리 API (7개 엔드포인트)
- 템플릿 관리 API (5개 엔드포인트)
- 문서 관리 API (8개 엔드포인트)
- 매핑 이력 관리 API (6개 엔드포인트)
- 캐시 관리 API (2개 엔드포인트)
- 일괄 매핑 기능 (최대 100개 PLC 동시 처리)
- 프로그램 파일 업로드 (PGM_ID 자동 생성)

---

**최종 업데이트**: 2025-11-12  
**문서 버전**: 1.0.0
