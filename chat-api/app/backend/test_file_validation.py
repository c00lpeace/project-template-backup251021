# -*- coding: utf-8 -*-
"""
FileValidationUtils 테스트 스크립트 (DB 불필요 버전)

사용법:
  python test_file_validation.py

테스트 전 준비사항:
  1. test_data 폴더에 파일 준비
     - ladder.zip (레더 CSV 파일들 압축)
     - template.xlsx (템플릿 파일)
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from ai_backend.utils.files_validation_utils import FileValidationUtils
from ai_backend.types.response.exceptions import HandledException


def print_section(title: str):
    """섹션 제목 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_result(result: dict):
    """검증 결과 출력"""
    print("\n📊 검증 결과 상세:")
    print("-" * 70)
    print(f"✅ 검증 통과 여부: {result['validation_passed']}")
    print(f"📁 총 레더 파일 수: {result['summary']['total_ladder_files']}")
    print(f"📦 필터링된 ZIP: {result['summary']['filtered_ladder_zip_file'].filename}")
    print(f"💬 메시지: {result['message']}")
    print("-" * 70)


def test_file_validation():
    """FileValidationUtils 통합 테스트 (DB 불필요)"""
    
    print_section("🧪 FileValidationUtils 테스트 시작")
    
    # 테스트 파일 경로 설정
    test_data_dir = Path(__file__).parent / "test_data"
    
    # ladder_zip_path = str(test_data_dir / "test_data.zip")
    ladder_zip_path = str(test_data_dir / "test_data_strct_fail.zip")
    # ladder_zip_path = str(test_data_dir / "test_data_less_fail.zip")
    # ladder_zip_path = str(test_data_dir / "test_data_more_pass.zip")
    template_xlsx_path = str(test_data_dir / "test_template.xlsx")

    # comment_csv_path = str(test_data_dir / "test_comment.csv")
    comment_csv_path = str(test_data_dir / "test_comment_fail.csv")
    
    # 파일 존재 여부 확인
    print("📂 테스트 파일 확인:")
    for file_path, name in [(ladder_zip_path, "ladder_less_fail.zip"), 
                            (template_xlsx_path, "template.xlsx")]:
        if Path(file_path).exists():
            print(f"   ✅ {name} 발견: {file_path}")
        else:
            print(f"   ❌ {name} 없음: {file_path}")
            print(f"\n⚠️  test_data 폴더에 {name} 파일을 준비해주세요!\n")
            return 1
    
    try:
        # FileValidationUtils 생성 (DB 불필요!)
        validator = FileValidationUtils()
        print("\n✅ FileValidationUtils 초기화 성공!")
        
        print_section("🔄 파일 검증 프로세스 시작")
        
        # 검증 실행
        result = validator.test_validation_program_files(
            ladder_zip_path=ladder_zip_path,
            template_xlsx_path=template_xlsx_path,
            comment_csv_path=comment_csv_path)
        
        # 결과 출력
        print_section("✅ 검증 완료!")
        print_result(result)
        
        # 필터링된 ZIP 파일 정보
        filtered_zip = result['summary']['filtered_ladder_zip_file']
        print("\n🎯 필터링된 ZIP 파일 상세:")
        print(f"   - 파일명: {filtered_zip.filename}")
        print(f"   - Content-Type: {filtered_zip.content_type}")
        print(f"   - 포함된 파일 수: {result['summary']['total_ladder_files']}개")
        
        # 필터링된 ZIP 파일 저장 (선택사항)
        output_path = test_data_dir / "filtered_output.zip"
        filtered_zip.file.seek(0)  # 포인터 리셋
        with open(output_path, "wb") as f:
            f.write(filtered_zip.file.read())
        print(f"\n💾 필터링된 ZIP 저장: {output_path}")
        
        print_section("🎉 모든 테스트 완료!")
        print("✅ 파일 타입 검증 통과")
        print("✅ 템플릿 구조 검증 통과")
        print("✅ 레더 ZIP 구조 검증 통과")
        print("✅ 파일 매칭 검증 통과")
        print("✅ ZIP 필터링 완료")
        print()
        
        return 0
        
    except HandledException as e:
        print_section("❌ 검증 실패 (HandledException)")
        print(f"코드: {e.code}")
        print(f"메시지: {e}")
        print()
        return 1
        
    except Exception as e:
        print_section("❌ 예상치 못한 오류")
        print(f"오류: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return 1


def create_test_data_structure():
    """테스트 데이터 폴더 구조 생성 (선택사항)"""
    test_data_dir = Path(__file__).parent / "test_data"
    
    if not test_data_dir.exists():
        test_data_dir.mkdir()
        print(f"✅ test_data 폴더 생성: {test_data_dir}")
        print("\n다음 파일들을 test_data 폴더에 준비해주세요:")
        print("  1. ladder.zip - 레더 CSV 파일들이 압축된 ZIP")
        print("  2. template.xlsx - 템플릿 Excel 파일")
    else:
        print(f"✅ test_data 폴더 존재: {test_data_dir}")


if __name__ == "__main__":
    print("=" * 70)
    print("  FileValidationUtils 독립 실행 테스트 (DB 불필요 ✨)")
    print("=" * 70)
    
    # 테스트 데이터 폴더 확인/생성
    create_test_data_structure()
    
    # 테스트 실행
    exit_code = test_file_validation()
    sys.exit(exit_code)
