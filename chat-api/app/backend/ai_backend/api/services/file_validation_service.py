# _*_ coding: utf-8 _*_
"""
파일 검증 전담 서비스

프로그램 업로드 시 필요한 모든 파일 검증 로직을 담당:
- 파일 타입 검증 (환경변수 기반)
- 파일 크기 검증 (환경변수 기반)
- 파일 구조 검증 (ZIP 내부 구조, 템플릿 컬럼)
- 파일 매칭 검증 (템플릿 Logic ID vs ZIP 파일 목록)

Phase 1 작업: 리팩토링 - 책임 분리
"""

import re
import zipfile
import io
import logging
from typing import List, Dict
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

from ai_backend.config.simple_settings import settings
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode
from ai_backend.types.response.program_response import ValidationResult


logger = logging.getLogger(__name__)


class FileValidationService:
    """
    파일 검증 전담 서비스
    
    환경변수 기반 설정을 사용하여 파일을 검증합니다.
    검증만 수행하며, 파일 저장이나 DB 저장은 하지 않습니다.
    """
    
    def __init__(self):
        """
        환경변수 설정 주입
        """
        self.settings = settings
    
    # ==========================================
    # 레더 ZIP 파일 검증
    # ==========================================
    
    def validate_ladder_zip_file_type(self, file: UploadFile) -> None:
        """
        레더 ZIP 파일 타입 검증 (환경변수 기반)
        
        Args:
            file: 업로드된 파일
            
        Raises:
            HandledException: 잘못된 파일 타입
        """
        if not file or not file.filename:
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="파일이 업로드되지 않았습니다"
            )
        
        # ZIP 확장자만 허용
        allowed_extensions = ['.zip']
        
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg=f"레더 파일은 ZIP 형식이어야 합니다. 허용: {', '.join(allowed_extensions)}"
            )
        
        logger.info(f"✅ 레더 ZIP 파일 타입 검증 통과: {file.filename}")
    
    def validate_ladder_zip_file_size(self, file: UploadFile) -> None:
        """
        레더 ZIP 파일 크기 검증 (환경변수 기반)
        
        Args:
            file: 업로드된 파일
            
        Raises:
            HandledException: 파일 크기 초과
        """
        max_size = self.settings.pgm_ladder_zip_max_size
        max_size_mb = self.settings.get_pgm_ladder_zip_max_size_mb()
        
        # 파일 크기 확인
        file.file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.file.tell()
        file.file.seek(0)  # 파일 처음으로 복귀
        
        if file_size > max_size:
            raise HandledException(
                ResponseCode.DOCUMENT_FILE_TOO_LARGE,
                msg=f"레더 ZIP 파일 크기가 {max_size_mb:.0f}MB를 초과했습니다 (현재: {file_size / 1024 / 1024:.2f}MB)"
            )
        
        logger.info(f"✅ 레더 ZIP 파일 크기 검증 통과: {file_size / 1024 / 1024:.2f}MB (최대: {max_size_mb:.0f}MB)")
    
    def validate_ladder_zip_structure(self, zip_file: UploadFile) -> Dict:
        """
        ZIP 구조 검증 (손상 여부, 내부 파일 목록)
        
        Args:
            zip_file: ZIP 파일
            
        Returns:
            Dict: {
                'file_list': List[str],  # ZIP 내부 파일명 리스트 (확장자 제외)
                'file_count': int,
                'is_valid': bool
            }
            
        Raises:
            HandledException: ZIP 파일 손상 또는 구조 오류
        """
        try:
            # 파일 내용 읽기
            zip_bytes = zip_file.file.read()
            zip_file.file.seek(0)  # 파일 포인터 복귀
            
            # ZIP 파일 열기 (메모리)
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
                # ZIP 파일 무결성 검증
                bad_file = zip_ref.testzip()
                if bad_file:
                    raise HandledException(
                        ResponseCode.INVALID_DATA_FORMAT,
                        msg=f"손상된 파일이 포함되어 있습니다: {bad_file}"
                    )
                
                # 파일 목록 추출 (디렉토리 제외)
                all_files = [
                    name for name in zip_ref.namelist()
                    if not name.endswith('/') and not name.startswith('__MACOSX')
                ]
                
                # 파일명만 추출 (경로 및 확장자 제외)
                file_list = []
                for file_path in all_files:
                    # 경로에서 파일명만 추출
                    filename = Path(file_path).name
                    # 확장자 제거
                    name_without_ext = Path(filename).stem
                    file_list.append(name_without_ext)
                
                logger.info(f"✅ ZIP 구조 검증 통과: {len(file_list)}개 파일")
                
                return {
                    'file_list': file_list,
                    'file_count': len(file_list),
                    'is_valid': True
                }
        
        except zipfile.BadZipFile as e:
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"잘못된 ZIP 파일 형식입니다: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ ZIP 구조 검증 실패: {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"ZIP 파일 구조 검증 중 오류가 발생했습니다: {str(e)}"
            )
    
    # ==========================================
    # 템플릿 파일 검증
    # ==========================================
    
    def validate_template_file_type(self, file: UploadFile) -> None:
        """
        템플릿 파일 타입 검증
        
        Args:
            file: 업로드된 파일
            
        Raises:
            HandledException: 잘못된 파일 타입
        """
        if not file or not file.filename:
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg="파일이 업로드되지 않았습니다"
            )
        
        # XLSX, XLS 확장자만 허용
        allowed_extensions = ['.xlsx', '.xls']
        
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg=f"템플릿 파일은 Excel 형식이어야 합니다. 허용: {', '.join(allowed_extensions)}"
            )
        
        logger.info(f"✅ 템플릿 파일 타입 검증 통과: {file.filename}")
    
    def validate_template_file_size(self, file: UploadFile) -> None:
        """
        템플릿 파일 크기 검증 (환경변수 기반)
        
        Args:
            file: 업로드된 파일
            
        Raises:
            HandledException: 파일 크기 초과
        """
        max_size = self.settings.pgm_template_max_size
        max_size_mb = self.settings.get_pgm_template_max_size_mb()
        
        # 파일 크기 확인
        file.file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.file.tell()
        file.file.seek(0)  # 파일 처음으로 복귀
        
        if file_size > max_size:
            raise HandledException(
                ResponseCode.DOCUMENT_FILE_TOO_LARGE,
                msg=f"템플릿 파일 크기가 {max_size_mb:.0f}MB를 초과했습니다 (현재: {file_size / 1024 / 1024:.2f}MB)"
            )
        
        logger.info(f"✅ 템플릿 파일 크기 검증 통과: {file_size / 1024 / 1024:.2f}MB (최대: {max_size_mb:.0f}MB)")
    
    def validate_template_file_structure(self, xlsx_file: UploadFile) -> Dict:
        """
        템플릿 구조 검증 (필수 컬럼 존재 여부, 환경변수 기반)
        
        Args:
            xlsx_file: Excel 파일
            
        Returns:
            Dict: {
                'logic_ids': List[str],  # Logic ID 리스트
                'row_count': int,
                'is_valid': bool
            }
            
        Raises:
            HandledException: 필수 컬럼 누락 또는 구조 오류
        """
        try:
            # Excel 파일 읽기 (메모리)
            xlsx_bytes = xlsx_file.file.read()
            xlsx_file.file.seek(0)  # 파일 포인터 복귀
            
            df = pd.read_excel(io.BytesIO(xlsx_bytes))
            
            # 필수 컬럼 확인 (환경변수)
            required_cols = self.settings.get_pgm_template_required_columns()
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise HandledException(
                    ResponseCode.REQUIRED_FIELD_MISSING,
                    msg=f"템플릿에 필수 컬럼이 없습니다: {', '.join(missing_cols)}"
                )
            
            # Logic ID 추출 (중복 제거)
            logic_ids = df['Logic ID'].dropna().astype(str).unique().tolist()
            
            if not logic_ids:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg="템플릿에 Logic ID가 없습니다"
                )
            
            logger.info(f"✅ 템플릿 구조 검증 통과: {len(logic_ids)}개 Logic ID, {len(df)}개 행")
            
            return {
                'logic_ids': logic_ids,
                'row_count': len(df),
                'is_valid': True
            }
        
        except pd.errors.EmptyDataError:
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg="템플릿 파일이 비어 있습니다"
            )
        except Exception as e:
            logger.error(f"❌ 템플릿 구조 검증 실패: {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"템플릿 파일 구조 검증 중 오류가 발생했습니다: {str(e)}"
            )
    
    # ==========================================
    # 레더 파일 매칭 검증
    # ==========================================
    
    def validate_ladder_files_match(
        self,
        required_files: List[str],
        actual_files: List[str]
    ) -> ValidationResult:
        """
        템플릿 Logic ID vs ZIP 파일 목록 비교
        
        Args:
            required_files: 템플릿에 명시된 필수 Logic ID 리스트
            actual_files: ZIP 내부 파일명 리스트 (확장자 제외)
            
        Returns:
            ValidationResult: 검증 결과
        """
        # 집합 연산
        required_set = set(required_files)
        actual_set = set(actual_files)
        
        matched_files = list(required_set & actual_set)  # 교집합
        missing_files = list(required_set - actual_set)  # 필수이지만 없는 파일
        extra_files = list(actual_set - required_set)    # 불필요한 파일
        
        validation_passed = len(missing_files) == 0
        
        result = ValidationResult(
            required_files=required_files,
            zip_files=actual_files,
            matched_files=sorted(matched_files),
            missing_files=sorted(missing_files),
            extra_files=sorted(extra_files),
            validation_passed=validation_passed
        )
        
        if validation_passed:
            logger.info(
                f"✅ 레더 파일 매칭 검증 통과: "
                f"{len(matched_files)}개 일치, {len(extra_files)}개 불필요"
            )
        else:
            logger.warning(
                f"⚠️ 레더 파일 매칭 검증 실패: "
                f"{len(missing_files)}개 누락, {len(matched_files)}개 일치, {len(extra_files)}개 불필요"
            )
        
        return result
    
    # ==========================================
    # 레더 파일명 패턴 검증 (선택사항)
    # ==========================================
    
    def validate_ladder_filename_pattern(self, filename: str) -> bool:
        """
        레더 파일명 패턴 검증 (환경변수 기반)
        
        현재는 모든 파일명을 허용합니다.
        필요 시 환경변수에 정규표현식 패턴을 추가하여 검증할 수 있습니다.
        
        Args:
            filename: 파일명 (확장자 제외)
            
        Returns:
            bool: 패턴 일치 여부
        """
        # 환경변수에 패턴이 있으면 사용, 없으면 모두 허용
        pattern = getattr(self.settings, 'pgm_ladder_filename_pattern', None)
        
        if not pattern:
            return True  # 패턴 없으면 모두 허용
        
        return bool(re.match(pattern, filename))
    
    # ==========================================
    # 레더 CSV 구조 검증 (Phase 1.5)
    # ==========================================
    
    def validate_ladder_csv_structure_from_bytes(
        self,
        csv_bytes: bytes,
        filename: str
    ) -> Dict:
        """
        레더 CSV 파일 구조 검증 (메모리 상에서)
        
        검증 항목:
        1. 파일 식별자 (1줄) - 선택적
        2. 모듈 정보 (2줄) - 선택적
        3. 필수 컬럼 (3줄) - 필수
        4. 최소 데이터 행 수 - 필수
        
        환경변수로 검증 규칙 제어 가능:
        - pgm_ladder_csv_structure_validation_enabled: 검증 on/off
        - pgm_ladder_csv_validate_file_identifier: 파일 식별자 검증 on/off
        - pgm_ladder_csv_validate_module_info: 모듈 정보 검증 on/off
        - pgm_ladder_csv_required_columns: 필수 컬럼
        - pgm_ladder_csv_header_row: 헤더 행 위치 (0-based)
        - pgm_ladder_csv_min_data_rows: 최소 데이터 행 수
        - pgm_ladder_csv_encoding: 인코딩
        
        Args:
            csv_bytes: CSV 파일 bytes
            filename: 파일명 (오류 메시지용)
            
        Returns:
            Dict: {
                'is_valid': bool,
                'file_identifier': str,
                'module_info': str,
                'header_columns': List[str],
                'data_row_count': int
            }
            
        Raises:
            HandledException: 구조 검증 실패
        """
        # 검증 비활성화 시 바로 통과
        if not self.settings.pgm_ladder_csv_structure_validation_enabled:
            logger.info(f"⏭️ 레더 CSV 구조 검증 비활성화: {filename}")
            return {'is_valid': True, 'skipped': True}
        
        try:
            # 1. bytes → 문자열 디코딩
            encoding = self.settings.pgm_ladder_csv_encoding
            
            try:
                csv_text = csv_bytes.decode(encoding)
            except UnicodeDecodeError:
                # 인코딩 실패 시 chardet로 자동 감지 (선택사항)
                try:
                    import chardet
                    detected = chardet.detect(csv_bytes)
                    detected_encoding = detected['encoding']
                    csv_text = csv_bytes.decode(detected_encoding)
                    logger.warning(
                        f"⚠️ 인코딩 자동 감지: {filename} ({encoding} → {detected_encoding})"
                    )
                except (ImportError, Exception):
                    raise HandledException(
                        ResponseCode.INVALID_DATA_FORMAT,
                        msg=f"파일 인코딩 오류: {filename} ({encoding})"
                    )
            
            # 2. StringIO로 메모리 파일 객체 생성
            lines = csv_text.strip().split('\n')
            
            # 3. 최소 줄 수 검증 (3줄 + 데이터 1줄 = 4줄)
            min_lines = self.settings.pgm_ladder_csv_header_row + 1 + self.settings.pgm_ladder_csv_min_data_rows
            if len(lines) < min_lines:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"파일 구조 오류: {filename} (최소 {min_lines}줄 필요, 현재 {len(lines)}줄)"
                )
            
            # 4. 파일 식별자 검증 (1줄) - 선택적
            file_identifier = lines[0].strip() if len(lines) > 0 else ""
            if self.settings.pgm_ladder_csv_validate_file_identifier:
                if not file_identifier:
                    raise HandledException(
                        ResponseCode.INVALID_DATA_FORMAT,
                        msg=f"파일 식별자 누락: {filename} (1줄)"
                    )
                logger.info(f"✅ 파일 식별자 확인: {filename} ({file_identifier})")
            
            # 5. 모듈 정보 검증 (2줄) - 선택적
            module_info = lines[1].strip() if len(lines) > 1 else ""
            if self.settings.pgm_ladder_csv_validate_module_info:
                prefix = self.settings.pgm_ladder_csv_module_info_prefix
                if not module_info.startswith(prefix):
                    raise HandledException(
                        ResponseCode.INVALID_DATA_FORMAT,
                        msg=f"모듈 정보 형식 오류: {filename} (2줄, '{prefix}'로 시작해야 함)"
                    )
                logger.info(f"✅ 모듈 정보 확인: {filename} ({module_info})")
            
            # 6. 필수 컬럼 검증 (3줄) - 필수
            header_row_index = self.settings.pgm_ladder_csv_header_row
            header_line = lines[header_row_index].strip() if len(lines) > header_row_index else ""
            
            if not header_line:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"헤더 행 누락: {filename} ({header_row_index + 1}줄)"
                )
            
            # 컬럼 분리
            header_columns = [col.strip() for col in header_line.split(',')]
            
            # 필수 컬럼 확인 (환경변수)
            required_cols = self.settings.get_pgm_ladder_csv_required_columns()
            missing_cols = [col for col in required_cols if col not in header_columns]
            
            if missing_cols:
                raise HandledException(
                    ResponseCode.REQUIRED_FIELD_MISSING,
                    msg=f"필수 컬럼 누락: {filename} ({', '.join(missing_cols)})"
                )
            
            logger.info(
                f"✅ 헤더 컬럼 확인: {filename} "
                f"({len(header_columns)}개 컬럼, 필수 {len(required_cols)}개 포함)"
            )
            
            # 7. 최소 데이터 행 수 검증
            data_start_row = header_row_index + 1
            data_row_count = len(lines) - data_start_row
            min_data_rows = self.settings.pgm_ladder_csv_min_data_rows
            
            if data_row_count < min_data_rows:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"데이터 행 부족: {filename} (최소 {min_data_rows}행 필요, 현재 {data_row_count}행)"
                )
            
            logger.info(f"✅ 레더 CSV 구조 검증 통과: {filename} ({data_row_count}행 데이터)")
            
            return {
                'is_valid': True,
                'file_identifier': file_identifier,
                'module_info': module_info,
                'header_columns': header_columns,
                'data_row_count': data_row_count
            }
        
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"❌ 레더 CSV 구조 검증 실패: {filename} - {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"레더 CSV 구조 검증 중 오류: {filename} ({str(e)})"
            )
    
    def validate_matched_ladder_csv_structures_in_memory(
        self,
        ladder_zip_file: UploadFile,
        matched_files: List[str]
    ) -> Dict:
        """
        매칭된 레더 CSV 파일들만 메모리에서 구조 검증
        
        해결방안 C:
        - ZIP을 두 번 열기 (Step 3: 구조만, Step 8: CSV 내용)
        - 메모리에서만 처리, 디스크 저장 전에 오류 발견
        
        Args:
            ladder_zip_file: 레더 ZIP 파일 (UploadFile)
            matched_files: 매칭된 파일명 리스트 (확장자 제외)
            
        Returns:
            Dict: {
                'validated_count': int,
                'failed_files': List[Dict],  # [{'filename': str, 'error': str}, ...]
                'is_valid': bool
            }
            
        Raises:
            HandledException: 하나라도 검증 실패 시
        """
        # 검증 비활성화 시 바로 통과
        if not self.settings.pgm_ladder_csv_structure_validation_enabled:
            logger.info("⏭️ 레더 CSV 구조 검증 비활성화")
            return {'validated_count': 0, 'failed_files': [], 'is_valid': True, 'skipped': True}
        
        try:
            # ZIP 파일 읽기 (메모리)
            zip_bytes = ladder_zip_file.file.read()
            ladder_zip_file.file.seek(0)  # 필수: 파일 포인터 복계
            
            failed_files = []
            validated_count = 0
            
            # ZIP 파일 열기
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
                # 매칭된 파일만 검증
                for filename_without_ext in matched_files:
                    csv_filename = f"{filename_without_ext}.csv"
                    
                    # ZIP 내부에서 파일 찾기 (경로 고려)
                    matching_paths = [
                        name for name in zip_ref.namelist()
                        if name.endswith(csv_filename) and not name.startswith('__MACOSX')
                    ]
                    
                    if not matching_paths:
                        logger.warning(f"⚠️ ZIP 내부에서 파일을 찾을 수 없음: {csv_filename}")
                        continue
                    
                    # 첫 번째 매칭 파일 사용
                    csv_path_in_zip = matching_paths[0]
                    
                    try:
                        # CSV 파일 내용 읽기
                        csv_bytes = zip_ref.read(csv_path_in_zip)
                        
                        # 구조 검증
                        self.validate_ladder_csv_structure_from_bytes(
                            csv_bytes=csv_bytes,
                            filename=csv_filename
                        )
                        
                        validated_count += 1
                        
                    except HandledException as e:
                        # 검증 실패 기록
                        failed_files.append({
                            'filename': csv_filename,
                            'error': str(e.msg)
                        })
                        logger.error(f"❌ CSV 구조 검증 실패: {csv_filename} - {e.msg}")
                    
                    except Exception as e:
                        failed_files.append({
                            'filename': csv_filename,
                            'error': str(e)
                        })
                        logger.error(f"❌ CSV 구조 검증 오류: {csv_filename} - {str(e)}")
            
            # 결과 확인
            is_valid = len(failed_files) == 0
            
            if is_valid:
                logger.info(
                    f"✅ 매칭된 레더 CSV 구조 검증 완료: "
                    f"{validated_count}개 파일 통과"
                )
            else:
                # 하나라도 실패하면 예외 발생
                failed_names = [f['filename'] for f in failed_files]
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=(
                        f"레더 CSV 구조 검증 실패: {len(failed_files)}개 파일 "
                        f"({', '.join(failed_names[:3])}{'...' if len(failed_names) > 3 else ''})"
                    ),
                    data={'failed_files': failed_files}
                )
            
            return {
                'validated_count': validated_count,
                'failed_files': failed_files,
                'is_valid': is_valid
            }
        
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"❌ 레더 CSV 구조 검증 중 오류: {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"레더 CSV 구조 검증 중 오류 발생: {str(e)}"
            )
