# -*- coding: utf-8 -*-
"""
Excel 파일의 Logic ID로 CSV 파일 생성

사용법:
    python create_csv_from_logic_ids.py
"""

import os
import pandas as pd
from pathlib import Path


def create_csv_files_from_excel(excel_path: str, output_dir: str = "./csv_files"):
    """
    Excel 파일의 Logic ID를 읽어서 각 Logic ID 이름의 CSV 파일 생성
    
    Args:
        excel_path: Excel 파일 경로
        output_dir: CSV 파일을 저장할 디렉토리
    """
    # Excel 파일 읽기
    df = pd.read_excel(excel_path)
    
    # Logic ID 컬럼 확인
    if 'Logic ID' not in df.columns:
        raise ValueError("'Logic ID' 컬럼이 없습니다!")
    
    # Logic ID 추출 (중복 제거)
    logic_ids = df['Logic ID'].dropna().unique().tolist()
    
    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"📁 출력 디렉토리: {output_path.absolute()}")
    print(f"📊 총 {len(logic_ids)}개의 CSV 파일 생성 예정\n")
    
    # 각 Logic ID로 CSV 파일 생성
    for i, logic_id in enumerate(logic_ids, 1):
        # CSV 파일명 (확장자 포함)
        csv_filename = f"{logic_id}.csv"
        csv_path = output_path / csv_filename
        
        # sample_ladder.csv와 동일한 형태의 더미 데이터 생성
        dummy_data = pd.DataFrame([
            # 첫 번째 줄: 파일명/날짜
            [f"KV_{logic_id}_20231104", None, None, None, None, None, None],
            # 두 번째 줄: Module Type Information
            ["Module Type Information:", "RCPU R08", None, None, None, None, None],
            # 세 번째 줄: 컬럼 헤더
            ["Step No.", "Line Statement", "Instruction", "I/O (Device)", "Blank", "P/I Statement", "Note"],
            # 네 번째 줄: Title
            [0, f"[Title]{logic_id}", None, None, None, None, None],
            # 더미 데이터 행들
            [10, None, "LD", "M1001", None, None, None],
            [11, None, "AND<=", "K1500", None, None, None],
            [None, None, None, "D0", None, None, None],
            [14, None, "OUT", "M1600", None, None, None],
            [15, None, "LD", "SM400", None, None, None],
            [16, None, "MPS", None, None, None, None],
            [17, None, "AND", "D1614.0", None, None, None],
            [18, None, "MOV", "K1", None, None, None],
            [None, None, None, "ZR1600", None, None, None],
            [20, None, "MPP", None, None, None, None],
        ])
        
        # CSV 파일 저장 (헤더 없이, 인덱스 없이)
        dummy_data.to_csv(csv_path, index=False, header=False, encoding='utf-8-sig')
        
        print(f"✅ {i:2d}. {csv_filename} 생성 완료")
    
    print(f"\n🎉 총 {len(logic_ids)}개 CSV 파일 생성 완료!")
    print(f"📂 저장 위치: {output_path.absolute()}")
    
    return output_path


if __name__ == "__main__":
    # Excel 파일 경로
    
    # 현재 파일이 있는 디렉토리 경로
    current_dir = Path(__file__).parent.resolve()
    print(f"디렉토리 경로: {current_dir}")
    test_path = current_dir / "backend" / "test_data"
    excel_file = test_path/ "sample_template.xlsx"
    

    # CSV 파일 생성
    output_dir = create_csv_files_from_excel(
        excel_path=str(excel_file),
        output_dir=str(test_path)
    )
    
    # 생성된 파일 목록 확인
    csv_files = sorted(output_dir.glob("*.csv"))
    print(f"\n📋 생성된 파일 목록 (처음 10개):")
    for i, csv_file in enumerate(csv_files[:10], 1):
        print(f"   {i}. {csv_file.name}")
    
    if len(csv_files) > 10:
        print(f"   ... 외 {len(csv_files) - 10}개")