# _*_ coding: utf-8 _*_
"""프로그램 파일 검증 유틸리티"""
import csv
import logging
import io
import os
import zipfile
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import pandas as pd
from fastapi import UploadFile
from starlette.datastructures import Headers
from ai_backend.config.simple_settings import settings
from ai_backend.types.response.exceptions import HandledException
from ai_backend.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)

class FileValidationUtils:
    """
    파일 검증 유틸리티
    """
    def __init__(self):
        self.settings = settings
 
    def test_validation_program_files(
        self,
        ladder_zip_path: str,
        template_xlsx_path: str,
        comment_csv_path: str,
    ) -> Dict:
        """
        (테스트)프로그램 파일 검증
        
        Args:
            ladder_zip_path: 레더 CSV 파일들이 압축된 ZIP파일 경로
            template_xlsx_path: template.xlsx 파일 경로
            comment_csv_path: COMMENT.CSV 파일 경로 (선택사항)
            
        Returns:
            {
                'program': Program,
                'pgm_id': str,
                'validation_result': Dict,
                'saved_files': Dict,
                'message': str
            }
        """
        try:
            # 0. UploadFile 객체 생성
            ladder_zip = self.file_path_to_upload_file(ladder_zip_path)
            template_xlsx = self.file_path_to_upload_file(template_xlsx_path)
            comment_csv = self.file_path_to_upload_file(comment_csv_path)
            
            logger.info(f"[Step 0] UploadFile 객체 생성")
            
            # 1. 파일 타입 검증
            validation_errors = {}
            logger.info(f"[Step 1] 파일 타입 검증 시작")
            ladder_zip_file_validation = self.validate_ladder_zip_file_type(ladder_zip)
            if ladder_zip_file_validation["is_valid"] is False:
                validation_errors['ladder_zip'] = ladder_zip_file_validation["error_message"]
            template_file_validation = self.validate_template_file_type(template_xlsx)
            if template_file_validation["is_valid"] is False:
                validation_errors['template_file'] = template_file_validation["error_message"]
            comment_file_validation = self.validate_comment_file_type(comment_csv)
            if template_file_validation["is_valid"] is False:
                validation_errors['comment_file'] = comment_file_validation["error_message"]
            if validation_errors:
                print(validation_errors)
                raise HandledException(
                    ResponseCode.DOCUMENT_UPLOAD_FAILED,
                    msg=f"업로드 파일 타입 검증 실패: {validation_errors}"
                )
            
            # 2. 템플릿 파일 구조 검증
            validation_errors = {}
            logger.info(f"[Step 2] 템플릿 파일 검증 시작")
            template_file_validation_result = self.validate_template_file_structure(template_xlsx)
            
            # 3. 레더 ZIP 파일 검증
            logger.info(f"[Step 3] 레더 ZIP 파일 검증 시작")
            ladder_zip_validation_result = self.validate_ladder_zip_structure(ladder_zip)

            # 4. 레더 파일 목록 매칭 (Logic ID vs ZIP 내부 파일 목록)
            logger.info(f"[Step 4] 레더 파일 매칭 검증 시작")
            validation_result = self.validate_ladder_files_match(
                required_files=template_file_validation_result['logic_ids'],
                actual_files=ladder_zip_validation_result['file_list']
            )

            # 5. 매칭된 레더 CSV 파일들 구조 검증 (메모리)
            validation_errors = self.validate_matched_ladder_csv_structures_in_memory(ladder_zip, validation_result['matched_files'])
            print(validation_errors)

            
            # 6. 커멘트 파일 구조 검증
            validation_errors = {}
            comment_csv_bytes = comment_csv.file.read()  # 커멘트 파일 내용 읽기
            comment_csv.file.seek(0) # 파일 포인터 복귀
            comment_csv_required_cols = self.settings.get_pgm_comment_csv_required_columns()
            comment_csv_header_row = self.settings.pgm_comment_csv_header_row
            validation_errors = self.validate_csv_structure_from_bytes(comment_csv_bytes, comment_csv.filename, comment_csv_required_cols, comment_csv_header_row)
            print(validation_errors)




            # # 5. 불필요한 파일 제거 (검증 통과 시)
            # logger.info(f"[Step 5] 불필요한 파일 제거 시작")
            # filtered_ladder_zip_file = self._filter_ladder_zip(
            #     ladder_zip,
            #     validation_result['matched_files']
            # )
            
            # 결과 반환
            return {
                'validation_passed': validation_result['validation_passed'],
                'summary': {
                    'total_ladder_files': len(validation_result['matched_files'])
                },
                'message': '프로그램 파일 검증 작업이 성공적으로 완료되었습니다'
            }
            
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"프로그램 검증 작업 실패: {str(e)}", exc_info=True)
    
    
    def file_path_to_upload_file(self, file_path: str) -> UploadFile:
        """로컬 파일 경로를 FastAPI UploadFile 객체로 변환"""
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # BytesIO로 파일 콘텐츠 래핑
        file_like = io.BytesIO(file_content)
        
        # UploadFile 객체 생성
        upload_file = UploadFile(
            file=file_like,
            filename=os.path.basename(file_path),
            size=len(file_content)
        ) 
        return upload_file

    def validate_ladder_zip_file_type(self, ladder_zip: UploadFile) -> Dict[str, Any]:
        """레더 ZIP 파일 타입 검증"""
        if not ladder_zip or not ladder_zip.filename:
            return {
                "is_valid": False,
                "error_message": "레더 ZIP 파일이 업로드되지 않았습니다"
        }
        allowed_extensions = self.settings.pgm_ladder_zip_allowed_extensions.split(',')
        if not any(ladder_zip.filename.lower().endswith(ext) for ext in allowed_extensions):
            return {
                "is_valid": False,
                "error_message": f"레더 ZIP 파일은 압축파일 형식이어야 합니다({', '.join(allowed_extensions)})"
            }
        return {"is_valid": True, "error_message": None}

    def validate_template_file_type(self, template_file: UploadFile) -> Dict[str, Any]:
        """템플릿 파일 타입 검증"""
        if not template_file or not template_file.filename:
            return {
                "is_valid": False,
                "error_message": "템플릿 파일이 업로드되지 않았습니다"
            }
        allowed_extensions = self.settings.pgm_template_allowed_extensions.split(',')
        if not any(template_file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return {
                "is_valid": False,
                "error_message": f"템플릿 파일은 Excel파일 형식이어야 합니다({', '.join(allowed_extensions)})"
            }
        return {"is_valid": True, "error_message": None}

    def validate_comment_file_type(self, comment_file: UploadFile) -> Dict[str, Any]:
        """커멘트 파일 타입 검증"""
        if not comment_file or not comment_file.filename:
            return {
                "is_valid": False,
                "error_message": "커멘트 파일이 업로드되지 않았습니다"
            }
        allowed_extensions = self.settings.pgm_comment_csv_allowed_extensions.split(',')
        if not any(comment_file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return {
                "is_valid": False,
                "error_message": f"커멘트 파일은 csv파일 형식이어야 합니다({', '.join(allowed_extensions)})"
            }
        return {"is_valid": True, "error_message": None}
    
    def validate_ladder_zip_structure(self, zip_file: UploadFile) -> Dict:
        """
        레더 ZIP 구조 검증 (손상 여부, 내부 파일 목록)
        
        Args:
            zip_file: 레더 ZIP 파일
            
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
                
                logger.info(f"레더 ZIP 파일 구조 검증 통과: {len(file_list)}개 파일")
                
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
            logger.error(f"ZIP 구조 검증 실패: {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"레더 ZIP 파일 구조 검증 중 오류가 발생했습니다: {str(e)}"
            )

    def validate_template_file_structure(self, xlsx_file: UploadFile) -> Dict[str, Any]:
        """
        템플릿 파일 구조 검증 (필수 컬럼 존재 여부, 환경변수 기반)
        
        Args:
            xlsx_file: 템플릿 Excel 파일
            
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
            
            # Logic ID 추출 1
            logic_ids_raw = df['Logic ID'].dropna().astype(str).tolist()

            # Logic ID 추출 2 (중복 제거)
            logic_ids = df['Logic ID'].dropna().astype(str).unique().tolist()
            
            if not logic_ids:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg="템플릿에 Logic ID가 없습니다"
                )
            diff_list = list(set(logic_ids_raw) - set(logic_ids))
            if diff_list != []:
                raise HandledException(
                    ResponseCode.INVALID_DATA_FORMAT,
                    msg=f"템플릿에 중복된 Logic ID가 있습니다. 중복된 Logic ID {len(diff_list)}개({', '.join(diff_list)})"
                )
            
            logger.info(f"템플릿 구조 검증 통과: {len(logic_ids)}개 Logic ID, {len(df)}개 행")
            
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
            logger.error(f"템플릿 구조 검증 실패: {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"템플릿 파일 구조 검증 중 오류가 발생했습니다: {str(e)}"
            )
    
    def validate_ladder_files_match(
        self,
        required_files: List[str],
        actual_files: List[str]
    ) -> Dict[str, Any]:
        """
        템플릿 Logic ID vs ZIP 파일 목록 비교
        
        Args:
            required_files: 템플릿에 명시된 필수 Logic ID 리스트
            actual_files: ZIP 내부 파일명 리스트 (확장자 제외)
            
        Returns:
            {
                'matched_files': List[str],
                'missing_files': List[str],
                'extra_files': List[str],
                'validation_passed': bool
            }
        """
        # 집합 연산
        required_set = set(required_files)
        actual_set = set(actual_files)
        
        matched_files = list(required_set & actual_set)  # 교집합
        missing_files = list(required_set - actual_set)  # 필수이지만 누락된 파일
        extra_files = list(actual_set - required_set)    # 불필요한 파일
        # 매칭 검증 통과 여부
        validation_passed = len(missing_files) == 0
        
        result = {
            'matched_files': sorted(matched_files),
            'missing_files': sorted(missing_files),
            'extra_files': sorted(extra_files),
            'validation_passed': validation_passed
        }
        
        if validation_passed:
            logger.info(
                f"레더 파일 매칭 검증 통과: "
                f"{len(matched_files)}개 일치, {len(extra_files)}개 불필요"
            )
        else:
            raise HandledException(
                ResponseCode.DOCUMENT_INVALID_FILE_TYPE,
                msg=(
                    f"레더 파일 매칭 검증 실패: "
                    f"- {len(missing_files)}개 파일이 누락되었습니다: {', '.join(missing_files)}"
                    f" - 누락된 파일: {', '.join(missing_files)}"
                )
            )
        
        return result

    def filter_ladder_zip(
        self,
        ladder_zip_file: UploadFile,
        keep_files: List[str]
    ) -> UploadFile:
        """
        레더 ZIP에서 필요한 파일만 남기고 새로운 ZIP 생성
        
        Args:
            ladder_zip_file: 원본 레더 ZIP 파일
            keep_files: 유지할 파일 목록 (예: ["0000_11.csv", "0001_11.csv"])
            
        Returns:
            UploadFile: 필터링된 ZIP 파일 객체
        """
        try:
            # 원본 ZIP 읽기
            original_content = ladder_zip_file.file.read()
            ladder_zip_file.file.seek(0)  # 포인터 복원
            
            # 새로운 ZIP 생성
            filtered_buffer = io.BytesIO()
            
            try:
                with zipfile.ZipFile(io.BytesIO(original_content), 'r') as original_zip:
                    with zipfile.ZipFile(filtered_buffer, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                        for info in original_zip.infolist():
                            if not info.is_dir():
                                filename = Path(info.filename).stem
                                if filename in keep_files:
                                    # 필요한 파일만 복사
                                    new_zip.writestr(info, original_zip.read(info.filename))
                logger.info(f"필터링된 레더 ZIP 파일 생성완료 (내부 파일 갯수: {len(keep_files)})")
            except Exception as e:
                raise HandledException(
                    ResponseCode.DOCUMENT_UPLOAD_ERROR,
                    msg=f"ZIP 파일 필터링 중 오류가 발생했습니다: {str(e)}",
                    e=e
                )
            # BytesIO 포인터를 처음으로 되돌림
            filtered_buffer.seek(0)
            
            # UploadFile 객체 생성
            filtered_ladder_zip_file = UploadFile(
                file=filtered_buffer,
                filename=f"filtered_{ladder_zip_file.filename}",
                headers=Headers({"content-type": "application/zip"})
            )
            
            logger.info(
                f"레더 ZIP 필터링 완료: "
                f"{len(keep_files)}개 파일 유지"
            )
            
            return filtered_ladder_zip_file
            
        except Exception as e:
            logger.error(f"ZIP 파일 필터링 실패: {str(e)}")
            raise HandledException(
                ResponseCode.DOCUMENT_UPLOAD_ERROR,
                msg=f"ZIP 파일 필터링 실패: {str(e)}",
                e=e
            )
    
    def validate_matched_ladder_csv_structures_in_memory(
        self,
        ladder_zip_file: UploadFile,
        matched_files: List[str]
    ) -> Dict:
        """
        매칭된 레더 CSV 파일들만 메모리에서 구조 검증
        
        Args:
            ladder_zip_file: 레더 ZIP 파일 (UploadFile)
            matched_files: 매칭된 파일명 리스트 (확장자 제외)
            
        Returns:
            'is_valid': bool
            
        Raises:
            HandledException: 하나라도 검증 실패 시
        """

        try:
            # ZIP 파일 읽기 (메모리)
            zip_bytes = ladder_zip_file.file.read()
            ladder_zip_file.file.seek(0)  # 필수: 파일 포인터 복계
            
            # validation_csv_result = {}
            # failed_msg = []
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
                        logger.warning(f"ZIP 내부에서 파일을 찾을 수 없음: {csv_filename}")
                        continue
                    
                    # 첫 번째 매칭 파일 사용
                    csv_path_in_zip = matching_paths[0]
                    
                    try:
                        # CSV 파일 내용 읽기
                        csv_bytes = zip_ref.read(csv_path_in_zip)
                        
                        # 구조 검증
                        validation_result = self.validate_csv_structure_from_bytes(
                            csv_bytes=csv_bytes,
                            filename=csv_filename,
                            required_columns=self.settings.get_pgm_ladder_csv_required_columns(),
                            header_row_index=self.settings.pgm_ladder_csv_header_row
                        )
                        
                        validated_count += 1
                        # 검증 실패 시 정보 수집
                        if not validation_result['is_valid']:
                            failed_files.append({
                                'filename': validation_result['filename'],
                                'missing_columns': validation_result['missing_columns']
                            })
                            logger.error(
                                f"매칭된 CSV 구조 검증 실패: {csv_filename} - "
                                f"필수 컬럼 누락: {', '.join(validation_result['missing_columns'])}"
                            )

                    except Exception as e:
                        failed_files.append({
                            'filename': csv_filename,
                            'error': str(e)
                        })
                        logger.error(f"CSV 구조 검증 실패: {csv_filename} - {str(e)}")
                
            # 결과 확인
            is_valid = len(failed_files) == 0
            
            if is_valid:
                logger.info(
                    f"매칭된 레더 CSV 구조 검증 작업 완료(Pass): "
                    f"{validated_count}개 파일 통과"
                )
                return {
                    'is_valid': True
                }
            else:
                logger.error("매칭된 레더 CSV 구조 검증 작업 완료(Fail)")
                return {
                    'is_valid': False,
                    'failed_files': failed_files
                }        
            return is_valid
        
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"레더 CSV 구조 검증 중 오류 발생: {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"레더 CSV 구조 검증 중 오류 발생: {str(e)}"
            )
    
    def validate_csv_structure_from_bytes(
            self,
            csv_bytes: bytes,
            filename: str,
            required_columns: List[str],
            header_row_index: int = 0,
        ) -> Dict[str, Any]:
        """ 
        단일 CSV파일 구조 검증 (메모리 상에서)

        Args:
            csv_bytes: CSV 파일 bytes,
            filename: 파일명 (오류 메시지용)
        Returns:
            Dict: {
                'is_valid': bool,
                'header_columns': List[str],
                'data_row_count': int
            }
        """
        try:
            # 디코딩
            encoding = self.settings.pgm_ladder_csv_encoding
            csv_text = csv_bytes.decode(encoding)
            
            # CSV reader로 필요한 줄만 읽기
            reader = csv.reader(io.StringIO(csv_text))

            lines = []
            for i, row in enumerate(reader):
                # 헤더가 위치한 행까지 읽기
                if i > header_row_index:
                    break
                lines.append(row)
            
            # 헤더 컬럼 추출
            header_columns = lines[header_row_index]
            
            # 필수 컬럼 확인
            missing_cols = [col for col in required_columns if col not in header_columns]
            
            if missing_cols:                
                return {
                    # 사용자 요청에 따라 예외 대신 결과 반환
                    'is_valid': False,
                    'filename': filename,
                    'missing_columns': missing_cols
                }
                        
            return {
                'is_valid': True,
                'filename': filename
            }
        
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"CSV 파일 구조 검증 작업 실패: {filename} - {str(e)}")
            raise HandledException(
                ResponseCode.INVALID_DATA_FORMAT,
                msg=f"CSV 파일 구조 검증 작업 중 오류: {filename} ({str(e)})"
            )

