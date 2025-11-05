# -*- coding: utf-8 -*-
"""
마이그레이션 실행 스크립트
사용법: python run_migration.py
"""

import os
import sys
from pathlib import Path

# psycopg2 설치 필요: pip install psycopg2-binary
try:
    import psycopg2
except ImportError:
    print("❌ psycopg2가 설치되어 있지 않습니다.")
    print("다음 명령어로 설치하세요: pip install psycopg2-binary")
    sys.exit(1)

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).parent

# 데이터베이스 설정 (.env 파일에서 읽거나 직접 입력)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'chat_db',
    'user': 'postgres',
    'password': input("PostgreSQL 비밀번호를 입력하세요: ")  # 보안을 위해 입력받음
}


def run_migration(sql_file: str):
    """PostgreSQL 마이그레이션 실행"""
    
    # SQL 파일 경로
    sql_path = BASE_DIR / 'migrations' / sql_file
    
    if not sql_path.exists():
        print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_path}")
        return False
    
    print(f"📁 SQL 파일: {sql_path}")
    print(f"🔗 데이터베이스 연결 중: {DB_CONFIG['database']}@{DB_CONFIG['host']}...")
    
    try:
        # PostgreSQL 연결
        connection = psycopg2.connect(**DB_CONFIG)
        connection.autocommit = True  # 각 문장마다 자동 커밋
        
        print("✅ 데이터베이스 연결 성공!")
        
        with connection.cursor() as cursor:
            # SQL 파일 읽기
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            print(f"📝 마이그레이션 실행 중...")
            
            # SQL 실행
            cursor.execute(sql)
            
            print(f"✅ 마이그레이션 '{sql_file}' 실행 완료!")
            
            # 결과 확인
            print("\n📊 PROGRAM_SEQUENCE 테이블 확인:")
            cursor.execute("SELECT * FROM PROGRAM_SEQUENCE;")
            result = cursor.fetchone()
            if result:
                print(f"   ID: {result[0]}, LAST_NUMBER: {result[1]}, UPDATE_DT: {result[2]}")
            else:
                print("   (데이터 없음)")
            
            return True
    
    except psycopg2.Error as e:
        print(f"❌ 마이그레이션 실패: {e}")
        print(f"상세 정보: {e.pgerror if hasattr(e, 'pgerror') else str(e)}")
        return False
    
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return False
    
    finally:
        if 'connection' in locals():
            connection.close()
            print("🔌 데이터베이스 연결 종료")


def main():
    """메인 함수"""
    print("=" * 70)
    print("🚀 PostgreSQL 마이그레이션 실행 스크립트")
    print("=" * 70)
    print()
    
    # 실행할 마이그레이션 파일
    migration_file = '001_add_program_sequence_table_postgresql.sql'
    
    # 마이그레이션 실행
    success = run_migration(migration_file)
    
    print()
    print("=" * 70)
    if success:
        print("✅ 마이그레이션 완료!")
        print()
        print("다음 단계:")
        print("1. Python에서 테스트:")
        print("   from ai_backend.api.services.sequence_service import SequenceService")
        print("   sequence_service = SequenceService(db)")
        print("   pgm_id = sequence_service.generate_pgm_id()")
        print()
        print("2. Phase 2로 진행: ProgramUploadService 구현")
    else:
        print("❌ 마이그레이션 실패. 위 오류를 확인해주세요.")
    print("=" * 70)


if __name__ == "__main__":
    main()
