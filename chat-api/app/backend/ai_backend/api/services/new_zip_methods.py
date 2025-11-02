# -*- coding: utf-8 -*-
"""
새로운 ZIP 업로드 메서드들
document_service.py의 DocumentService 클래스에 추가할 메서드들입니다.
"""

def _extract_and_save_to_db(
    self,
    zip_path: str,
    pgm_id: str,
    user_id: str,
    is_public: bool = False,
    permissions: list = None
):
    """ZIP 파일 압축 해제 및 각 파일을 DOCUMENTS 테이블에 저장
    
    Args:
        zip_path: ZIP 파일 경로
        pgm_id: 프로그램 ID
        user_id: 사용자 ID
        is_public: 공개 여부
        permissions: 권한 리스트
        
    Returns:
        {
            'extracted_files': [...],
            'total_files': 100,
            'success_count': 98,
            'failed_count': 2,
            'failed_files': [...],
            'extraction_path': '/uploads/user/{pgm_id}'
        }
    """
    import os
    import zipfile
    from pathlib import Path
    from collections import defaultdict
    
    try:
        # 1. 압축 해제 대상 디렉토리 설정
        extraction_base = Path(self.upload_base_path) / user_id / pgm_id
        extraction_base.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        failed_files = []
        success_count = 0
        failed_count = 0
        
        # 2. ZIP 파일 열기
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.infolist()
            
            for info in file_list:
                try:
                    # 디렉토리는 스킵
                    if info.is_dir():
                        continue
                    
                    # 파일 경로 및 이름 추출
                    file_relative_path = info.filename
                    file_name = Path(file_relative_path).name
                    
                    # 압축 해제된 파일 경로
                    extracted_file_path = extraction_base / file_relative_path
                    extracted_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 파일 압축 해제
                    with zip_ref.open(info.filename) as source:
                        file_content = source.read()
                        with open(extracted_file_path, 'wb') as target:
                            target.write(file_content)
                    
                    # 3. DOCUMENTS 테이블에 저장
                    file_extension = Path(file_name).suffix.lower() or '.unknown'
                    file_size = len(file_content)
                    
                    # create_document_from_file 호출
                    doc_result = self.create_document_from_file(
                        file_content=file_content,
                        filename=file_name,
                        user_id=user_id,
                        is_public=is_public,
                        permissions=permissions,
                        document_type='common',  # ZIP에서 추출된 일반 파일
                        metadata_json={
                            'pgm_id': pgm_id,
                            'original_zip_path': file_relative_path,
                            'extracted_from_zip': True
                        },
                        pgm_id=pgm_id  # ⭐ PGM_ID 전달
                    )
                    
                    extracted_files.append({
                        'document_id': doc_result['document_id'],
                        'file_name': file_name,
                        'relative_path': file_relative_path,
                        'file_size': file_size,
                        'file_extension': file_extension
                    })
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"파일 저장 실패: {info.filename}, 오류: {str(e)}")
                    failed_files.append({
                        'file_name': info.filename,
                        'error': str(e)
                    })
                    failed_count += 1
        
        return {
            'extracted_files': extracted_files,
            'total_files': len(file_list) - sum(1 for f in file_list if f.is_dir()),
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_files': failed_files,
            'extraction_path': str(extraction_base)
        }
        
    except zipfile.BadZipFile:
        raise HandledException(
            ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
            msg="손상된 ZIP 파일입니다"
        )
    except Exception as e:
        logger.error(f"ZIP 파일 압축 해제 실패: {str(e)}")
        raise


def _save_original_zip(
    self,
    file,
    pgm_id: str,
    user_id: str,
    is_public: bool = False,
    permissions: list = None,
    extracted_file_count: int = 0
):
    """원본 ZIP 파일을 zipfiles 폴더에 저장
    
    Args:
        file: ZIP 파일 (UploadFile)
        pgm_id: 프로그램 ID
        user_id: 사용자 ID
        is_public: 공개 여부
        permissions: 권한 리스트
        extracted_file_count: 추출된 파일 개수
        
    Returns:
        ZIP 파일의 document 정보
    """
    from pathlib import Path
    import os
    import uuid
    from datetime import datetime
    
    try:
        # 1. zipfiles 폴더 생성
        zipfiles_dir = Path(self.upload_base_path) / user_id / 'zipfiles'
        zipfiles_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 파일 저장 경로 생성 (안전한 파일명)
        file_name = file.filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{file_name}"
        zip_file_path = zipfiles_dir / safe_filename
        
        # 3. 파일 저장
        file_content = file.file.read()
        with open(zip_file_path, 'wb') as f:
            f.write(file_content)
        
        # 4. DOCUMENTS 테이블에 저장
        doc_result = self.create_document_from_file(
            file_content=file_content,
            filename=file_name,
            user_id=user_id,
            is_public=is_public,
            permissions=permissions,
            document_type='zip',  # ZIP 원본
            metadata_json={
                'pgm_id': pgm_id,
                'is_original_zip': True,
                'extracted_file_count': extracted_file_count,
                'stored_in_zipfiles': True
            },
            pgm_id=pgm_id  # ⭐ PGM_ID 전달
        )
        
        logger.info(f"원본 ZIP 파일 저장 완료: {file_name}, document_id={doc_result['document_id']}")
        
        return doc_result
        
    except Exception as e:
        logger.error(f"원본 ZIP 파일 저장 실패: {str(e)}")
        raise
