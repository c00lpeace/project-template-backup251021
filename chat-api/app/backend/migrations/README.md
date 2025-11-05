# 📋 Database Migrations

이 디렉토리는 데이터베이스 마이그레이션 SQL 스크립트를 포함합니다.

## 🗄️ 데이터베이스 종류

프로젝트가 **MySQL**과 **PostgreSQL** 두 가지를 지원합니다.

| 파일명 패턴 | 데이터베이스 |
|------------|-------------|
| `*_mysql.sql` 또는 `*.sql` (suffix 없음) | MySQL / MariaDB |
| `*_postgresql.sql` | PostgreSQL |

---

## 🚀 마이그레이션 실행 방법

### 1️⃣ PostgreSQL 실행

```bash
# psql 접속
psql -U [username] -d [database_name]

# SQL 파일 실행
\i /path/to/migrations/001_add_program_sequence_table_postgresql.sql

# 또는 커맨드라인에서 직접 실행
psql -U [username] -d [database_name] -f migrations/001_add_program_sequence_table_postgresql.sql
```

### 2️⃣ MySQL 실행

```bash
# MySQL 접속
mysql -u [username] -p [database_name]

# SQL 파일 실행
source /path/to/migrations/001_add_program_sequence_table.sql;

# 또는 커맨드라인에서 직접 실행
mysql -u [username] -p [database_name] < migrations/001_add_program_sequence_table.sql
```

### 3️⃣ Python 스크립트로 실행

#### PostgreSQL
```python
import psycopg2
from pathlib import Path

def run_postgresql_migration(sql_file: str):
    """PostgreSQL 마이그레이션 실행"""
    connection = psycopg2.connect(
        host='localhost',
        user='your_username',
        password='your_password',
        database='your_database'
    )
    
    try:
        with connection.cursor() as cursor:
            # SQL 파일 읽기
            sql_path = Path(__file__).parent / sql_file
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # SQL 실행
            cursor.execute(sql)
            connection.commit()
            print(f"✅ Migration '{sql_file}' executed successfully!")
    
    except Exception as e:
        connection.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    
    finally:
        connection.close()

# 실행
if __name__ == "__main__":
    run_postgresql_migration('001_add_program_sequence_table_postgresql.sql')
```

#### MySQL
```python
import pymysql
from pathlib import Path

def run_mysql_migration(sql_file: str):
    """MySQL 마이그레이션 실행"""
    connection = pymysql.connect(
        host='localhost',
        user='your_username',
        password='your_password',
        database='your_database',
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # SQL 파일 읽기
            sql_path = Path(__file__).parent / sql_file
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # SQL 실행 (여러 문장 분리)
            for statement in sql.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            
            connection.commit()
            print(f"✅ Migration '{sql_file}' executed successfully!")
    
    except Exception as e:
        connection.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    
    finally:
        connection.close()

# 실행
if __name__ == "__main__":
    run_mysql_migration('001_add_program_sequence_table.sql')
```

### 4️⃣ DBeaver 또는 pgAdmin / MySQL Workbench

1. 적절한 마이그레이션 파일 열기
2. SQL 스크립트 전체 선택
3. 실행 (Ctrl + Enter)

---

## 📂 마이그레이션 파일 목록

| 파일명 | DB | 설명 | 생성일 |
|--------|----|----- |--------|
| `001_add_program_sequence_table_postgresql.sql` | PostgreSQL | PROGRAM_SEQUENCE 테이블 추가 | 2025-11-05 |
| `001_add_program_sequence_table_postgresql_rollback.sql` | PostgreSQL | PROGRAM_SEQUENCE 테이블 제거 (롤백) | 2025-11-05 |
| `001_add_program_sequence_table.sql` | MySQL | PROGRAM_SEQUENCE 테이블 추가 | 2025-11-05 |
| `001_add_program_sequence_table_rollback.sql` | MySQL | PROGRAM_SEQUENCE 테이블 제거 (롤백) | 2025-11-05 |

---

## ⚠️ 주의사항

### 운영 환경 (Production)
- ✅ 반드시 백업을 먼저 수행하세요
- ✅ 마이그레이션 전 테스트 환경에서 검증하세요
- ✅ 롤백 스크립트를 미리 준비하세요
- ❌ 운영 중인 시스템에서 직접 실행하지 마세요

### 개발 환경 (Development)
- ✅ 마이그레이션 실행 전후 데이터 확인
- ✅ 롤백 스크립트 테스트
- ✅ 마이그레이션 순서 준수

---

## 🔄 롤백 방법

마이그레이션을 되돌려야 할 경우:

### PostgreSQL
```bash
psql -U [username] -d [database] -f migrations/001_add_program_sequence_table_postgresql_rollback.sql
```

### MySQL
```bash
mysql -u [username] -p [database] < migrations/001_add_program_sequence_table_rollback.sql
```

---

## 📊 마이그레이션 이후 확인

### PostgreSQL
```sql
-- 테이블 존재 확인
SELECT tablename FROM pg_tables WHERE tablename = 'program_sequence';

-- 테이블 구조 확인
\d program_sequence

-- 초기 데이터 확인
SELECT * FROM PROGRAM_SEQUENCE;

-- 다음 PGM_ID 확인
SELECT CONCAT('PGM_', LAST_NUMBER + 1) AS NEXT_PGM_ID 
FROM PROGRAM_SEQUENCE 
WHERE ID = 1;

-- 트리거 확인
SELECT tgname FROM pg_trigger WHERE tgrelid = 'program_sequence'::regclass;
```

### MySQL
```sql
-- 테이블 존재 확인
SHOW TABLES LIKE 'PROGRAM_SEQUENCE';

-- 테이블 구조 확인
DESC PROGRAM_SEQUENCE;

-- 초기 데이터 확인
SELECT * FROM PROGRAM_SEQUENCE;

-- 다음 PGM_ID 확인
SELECT CONCAT('PGM_', LAST_NUMBER + 1) AS NEXT_PGM_ID 
FROM PROGRAM_SEQUENCE 
WHERE ID = 1;
```

---

## 🔧 Python에서 시퀀스 사용

```python
from ai_backend.api.services.sequence_service import SequenceService
from ai_backend.database.base import Database

# 데이터베이스 설정 로드
from ai_backend.config import settings
db_config = {
    'database': {
        'username': settings.database_user,
        'password': settings.database_password,
        'host': settings.database_host,
        'port': settings.database_port,
        'dbname': settings.database_name
    }
}

# Database 인스턴스 생성
db_instance = Database(db_config)

# 세션 사용
with db_instance.session() as db:
    # SequenceService 초기화
    sequence_service = SequenceService(db)
    
    # 시퀀스 테이블 초기화 (처음 한 번만)
    result = sequence_service.initialize_sequence()
    print(f"초기화 결과: {result}")
    
    # PGM_ID 생성 테스트
    for i in range(5):
        pgm_id = sequence_service.generate_pgm_id()
        print(f"생성된 PGM_ID: {pgm_id}")
        db.commit()  # 중요: 커밋 필수!
    
    # 현재 번호 확인
    current = sequence_service.get_current_number()
    print(f"현재 시퀀스 번호: {current}")
    
    # 다음 ID 미리보기
    next_id = sequence_service.get_next_pgm_id_preview()
    print(f"다음 PGM_ID: {next_id}")

# 출력 예상:
# 초기화 결과: True
# 생성된 PGM_ID: PGM_1
# 생성된 PGM_ID: PGM_2
# 생성된 PGM_ID: PGM_3
# 생성된 PGM_ID: PGM_4
# 생성된 PGM_ID: PGM_5
# 현재 시퀀스 번호: 5
# 다음 PGM_ID: PGM_6
```

---

## 📝 마이그레이션 작성 규칙

1. **파일명**: `{번호}_{설명}_{db}.sql`
   - PostgreSQL: `001_add_program_sequence_table_postgresql.sql`
   - MySQL: `001_add_program_sequence_table.sql` (suffix 없음)

2. **롤백 파일**: `{번호}_{설명}_{db}_rollback.sql`
   - PostgreSQL: `001_add_program_sequence_table_postgresql_rollback.sql`
   - MySQL: `001_add_program_sequence_table_rollback.sql`

3. **주석**:
   - 파일 상단에 목적과 생성일 명시
   - 주요 단계마다 주석 추가

4. **트랜잭션**:
   - 가능한 한 트랜잭션으로 묶기
   - 에러 발생 시 자동 롤백되도록 설정

---

## 🔍 PostgreSQL vs MySQL 차이점

| 항목 | PostgreSQL | MySQL |
|------|-----------|-------|
| 날짜 타입 | `TIMESTAMP` | `DATETIME` |
| 자동 업데이트 | 트리거 필요 | `ON UPDATE CURRENT_TIMESTAMP` |
| 주석 | `COMMENT ON ...` | `COMMENT '...'` |
| 문자열 결합 | `CONCAT()` 또는 `\|\|` | `CONCAT()` |
| 충돌 처리 | `ON CONFLICT` | `ON DUPLICATE KEY` |
| 엔진/문자셋 | 불필요 | `ENGINE=InnoDB CHARSET=utf8mb4` |

---

## 🚀 다음 단계

마이그레이션 실행 후:
1. ✅ `SequenceService.initialize_sequence()` 호출 (선택사항)
2. ✅ `SequenceService.generate_pgm_id()` 테스트
3. ✅ Phase 2로 진행 (ProgramUploadService 구현)

---

**문의사항이 있으시면 개발팀에 연락해주세요!** 🚀
