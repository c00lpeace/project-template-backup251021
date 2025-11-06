# _*_ coding: utf-8 _*_
"""
물리 파일 저장 전담 서비스

프로그램 업로드 시 파일 시스템 작업을 담당:
- 파일 저장 (환경변수 기반 경로)
- ZIP 압축 해제 (환경변수 기반 타임아웃)
- 파일 삭제 (롤백 시)

Phase 1 작업: 리팩토링 - 책임 분리
"""

import logging
import zipfile
import io
import hashlib
import shutil
from typing import List, Dict
from pathlib import Path
from datetime import datetime

from fastapi import UploadFile

from ai_backend.config.simple_settings import settings
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode


logger = logging.getLogger(__name__)


class FileStorageService:
    """
    물리 파일 저장 전담 서비스
    
    환경변수 기반 경로를 사용하여 파일을 저장/삭제합니다.
    파일 시스템 작업만 수행하며, DB 저장은 하지 않습니다.
    """
    
    def __init__(self):
        """
        환경변수 설정 주입
        """
        self.settings = settings
    
    # ==========================================
    # 레더 ZIP 저장 및 압축 해제
    # ==========================================
    
    def save_and_extract_ladder_zip(
        self,
        ladder_zip_file: UploadFile,
        pgm_id: str
    ) -> Dict:
        """
        레더 ZIP 저장 및 압축 해제
        
        Args:
            ladder_zip_file: 레더 ZIP 파일 (UploadFile 또는 bytes)
            pgm_id: 프로그램 ID
            
        Returns:
            Dict: {
                'extracted_ladder_files': List[Dict],  # 압축 해제된 파일 정보
                'original_zip': Dict or None           # 원본 ZIP 정보 (keep_original_zip=True 시)
            }
            
        Raises:
            HandledException: 파일 저장 또는 압축 해제 실패
        """
        try:
            # 저장 디렉토리 생성 (환경변수 기반)
            ladder_dir = Path(self.settings.get_ladder_files_dir(pgm_id))
            ladder_dir.mkdir(parents=True, exist_ok=True)
            
            # ZIP 파일 읽기
            if isinstance(ladder_zip_file, UploadFile):
                zip_bytes = ladder_zip_file.file.read()
                ladder_zip_file.file.seek(0)  # 파일 포인터 복귀
                original_filename = ladder_zip_file.filename
            else:
                zip_bytes = ladder_zip_file
                original_filename = f"ladder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            # ZIP 압축 해제
            extracted_files = self._extract_zip_files(
                zip_bytes=zip_bytes,
                extract_dir=ladder_dir,
                timeout=self.settings.pgm_zip_extract_timeout
            )
            
            logger.info(f"✅ 레더 파일 압축 해제 완료: {len(extracted_files)}개 파일")
            
            # 원본 ZIP 보관 (환경변수 설정)
            zip_info = None
            if self.settings.pgm_keep_original_zip:
                zip_info = self._save_original_zip(
                    zip_bytes=zip_bytes,
                    pgm_id=pgm_id,
                    original_filename=original_filename
                )
                logger.info(f"✅ 원본 ZIP 보관 완료: {zip_info['path']}")
            
            return {
                'extracted_ladder_files': extracted_files,
                'original_zip': zip_info
            }
        
        except Exception as e:
            logger.error(f"❌ 레더 ZIP 저장 및 압축 해제 실패: {str(e)}")
            raise HandledException(
                ResponseCode.DOCUMENT_UPLOAD_ERROR,
                msg=f"레더 ZIP 저장 및 압축 해제 중 오류가 발생했습니다: {str(e)}"
            )
    
    def _extract_zip_files(
        self,
        zip_bytes: bytes,
        extract_dir: Path,
        timeout: int = 300
    ) -> List[Dict]:
        """
        ZIP 파일 압축 해제 (메모리에서 직접)
        
        Args:
            zip_bytes: ZIP 파일 바이트
            extract_dir: 압축 해제 디렉토리
            timeout: 타임아웃 (초) - 현재는 사용하지 않음
            
        Returns:
            List[Dict]: 압축 해제된 파일 정보 리스트
        """
        extracted_files = []
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                # 디렉토리는 건너뛰기
                if file_info.is_dir():
                    continue
                
                # __MACOSX 폴더 제외
                if file_info.filename.startswith('__MACOSX'):
                    continue
                
                # 파일 이름만 추출 (경로 제거)
                filename = Path(file_info.filename).name
                
                # 파일 저장 경로
                save_path = extract_dir / filename
                
                # 파일 추출 및 저장
                with zip_ref.open(file_info) as source, open(save_path, 'wb') as target:
                    file_content = source.read()
                    target.write(file_content)
                    
                    # 파일 해시 계산
                    file_hash = hashlib.sha256(file_content).hexdigest()
                
                # 파일 정보 저장
                extracted_files.append({
                    'filename': filename,
                    'path': str(save_path),
                    'size': save_path.stat().st_size,
                    'hash': file_hash
                })
        
        return extracted_files
    
    def _save_original_zip(
        self,
        zip_bytes: bytes,
        pgm_id: str,
        original_filename: str
    ) -> Dict:
        """
        원본 ZIP 파일 저장
        
        Args:
            zip_bytes: ZIP 파일 바이트
            pgm_id: 프로그램 ID
            original_filename: 원본 파일명
            
        Returns:
            Dict: 저장된 ZIP 파일 정보
        """
        # ZIP 저장 디렉토리 생성 (환경변수 기반)
        zip_dir = Path(self.settings.get_zip_file_dir(pgm_id))
        zip_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (타임스탬프 추가)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{Path(original_filename).stem}_{timestamp}.zip"
        save_path = zip_dir / filename
        
        # ZIP 파일 저장
        with open(save_path, 'wb') as f:
            f.write(zip_bytes)
        
        # 파일 해시 계산
        file_hash = hashlib.sha256(zip_bytes).hexdigest()
        
        return {
            'filename': filename,
            'path': str(save_path),
            'size': len(zip_bytes),
            'hash': file_hash
        }
    
    # ==========================================
    # 템플릿 파일 저장
    # ==========================================
    
    def save_template_file(
        self,
        template_file: UploadFile,
        pgm_id: str
    ) -> Dict:
        """
        템플릿 파일 저장
        
        Args:
            template_file: 템플릿 파일
            pgm_id: 프로그램 ID
            
        Returns:
            Dict: 저장된 파일 정보
            
        Raises:
            HandledException: 파일 저장 실패
        """
        try:
            # 저장 디렉토리 생성 (환경변수 기반)
            template_dir = Path(self.settings.get_template_file_dir(pgm_id))
            template_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일명 생성 (타임스탬프 추가)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_name = Path(template_file.filename).stem
            extension = Path(template_file.filename).suffix
            filename = f"{original_name}_{timestamp}{extension}"
            save_path = template_dir / filename
            
            # 파일 읽기
            file_bytes = template_file.file.read()
            template_file.file.seek(0)  # 파일 포인터 복귀
            
            # 파일 저장
            with open(save_path, 'wb') as f:
                f.write(file_bytes)
            
            # 파일 해시 계산
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            
            logger.info(f"✅ 템플릿 파일 저장 완료: {save_path}")
            
            return {
                'filename': filename,
                'file_path': str(save_path),
                'path': str(save_path),  # 호환성 유지
                'size': len(file_bytes),
                'hash': file_hash
            }
        
        except Exception as e:
            logger.error(f"❌ 템플릿 파일 저장 실패: {str(e)}")
            raise HandledException(
                ResponseCode.DOCUMENT_UPLOAD_ERROR,
                msg=f"템플릿 파일 저장 중 오류가 발생했습니다: {str(e)}"
            )
    
    # ==========================================
    # 파일 삭제 (롤백 시)
    # ==========================================
    
    def delete_program_files(self, pgm_id: str) -> None:
        """
        프로그램 전체 파일 삭제 (롤백 시 사용)
        
        Args:
            pgm_id: 프로그램 ID
        """
        try:
            # 프로그램 디렉토리 경로 (환경변수 기반)
            program_dir = Path(self.settings.get_program_upload_dir(pgm_id))
            
            if program_dir.exists():
                shutil.rmtree(program_dir)
                logger.info(f"✅ 프로그램 파일 삭제 완료: {program_dir}")
            else:
                logger.warning(f"⚠️ 삭제할 프로그램 디렉토리가 없습니다: {program_dir}")
        
        except Exception as e:
            logger.error(f"❌ 프로그램 파일 삭제 실패: {str(e)}")
            # 롤백 시 에러가 발생해도 계속 진행
    
    def delete_files(self, file_paths: List[str]) -> None:
        """
        특정 파일들 삭제 (롤백 시 사용)
        
        Args:
            file_paths: 삭제할 파일 경로 리스트
        """
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    logger.info(f"✅ 파일 삭제 완료: {file_path}")
                else:
                    logger.warning(f"⚠️ 삭제할 파일이 없습니다: {file_path}")
            
            except Exception as e:
                logger.error(f"❌ 파일 삭제 실패 ({file_path}): {str(e)}")
                # 롤백 시 에러가 발생해도 계속 진행
    
    # ==========================================
    # 유틸리티 메서드
    # ==========================================
    
    def calculate_file_hash(self, file_bytes: bytes) -> str:
        """
        파일 해시 계산 (SHA-256)
        
        Args:
            file_bytes: 파일 바이트
            
        Returns:
            str: SHA-256 해시값
        """
        return hashlib.sha256(file_bytes).hexdigest()
    
    def get_file_size_mb(self, file_size_bytes: int) -> float:
        """
        파일 크기를 MB 단위로 변환
        
        Args:
            file_size_bytes: 파일 크기 (바이트)
            
        Returns:
            float: 파일 크기 (MB)
        """
        return file_size_bytes / (1024 * 1024)
