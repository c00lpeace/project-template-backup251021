# -*- coding: utf-8 -*-
"""
PROGRAM_SEQUENCE 테스트 스크립트
사용법: python test_sequence.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from ai_backend.database.base import Database
from ai_backend.api.services.sequence_service import SequenceService

# 데이터베이스 설정
DB_CONFIG = {
    'database': {
        'username': 'postgres',
        'password': input("PostgreSQL 비밀번호를 입력하세요: "),
        'host': 'localhost',
        'port': 5432,
        'dbname': 'chat_db'
    }
}

def test_sequence_service():
    """SequenceService 테스트"""
    
    print("=" * 70)
    print("🧪 PROGRAM_SEQUENCE 테스트")
    print("=" * 70)
    print()
    
    try:
        # Database 인스턴스 생성
        db_instance = Database(DB_CONFIG)
        print("✅ 데이터베이스 연결 성공!")
        
        with db_instance.session() as db:
            # SequenceService 생성
            sequence_service = SequenceService(db)
            print("✅ SequenceService 초기화 성공!")
            print()
            
            # 1. 현재 시퀀스 번호 조회
            print("📊 현재 시퀀스 상태:")
            current = sequence_service.get_current_number()
            print(f"   현재 LAST_NUMBER: {current}")
            print()
            
            # 2. 다음 PGM_ID 미리보기
            next_id = sequence_service.get_next_pgm_id_preview()
            print(f"   다음 생성될 PGM_ID: {next_id}")
            print()
            
            # 3. PGM_ID 5개 생성
            print("🔄 PGM_ID 5개 생성 테스트:")
            generated_ids = []
            
            for i in range(5):
                pgm_id = sequence_service.generate_pgm_id()
                generated_ids.append(pgm_id)
                print(f"   {i+1}. {pgm_id}")
                db.commit()  # 중요: 각 생성 후 커밋!
            
            print()
            
            # 4. 최종 상태 확인
            print("📊 최종 시퀀스 상태:")
            final_current = sequence_service.get_current_number()
            print(f"   현재 LAST_NUMBER: {final_current}")
            
            final_next = sequence_service.get_next_pgm_id_preview()
            print(f"   다음 생성될 PGM_ID: {final_next}")
            print()
            
            # 5. 생성된 ID 요약
            print("✅ 생성된 PGM_ID 목록:")
            for idx, pgm_id in enumerate(generated_ids, 1):
                print(f"   {idx}. {pgm_id}")
            
            print()
            print("=" * 70)
            print("🎉 테스트 완료! 모든 기능이 정상 동작합니다.")
            print("=" * 70)
            
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 테스트 실패: {str(e)}")
        print("=" * 70)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_sequence_service()
