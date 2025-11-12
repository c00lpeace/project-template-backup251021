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
        (테스트)프로그램 파일 검증 - 모든 단계를 실행하고 결과를 수집
        
        Args:
            ladder_zip_path: 레더 CSV 파일들이 압축된 ZIP파일 경로
            template_xlsx_path: template.xlsx 파일 경로
            comment_csv_path: COMMENT.CSV 파일 경로 (선택사항)
            
        Returns:
            {
                'validation_passed': bool,
                'validation_results': [  # 각 단계별 결과
                    {
                        'title': str,
                        'is_valid': bool,
                        'errors': List[str]
                    }
                ]
            }
        """
        validation_results = []
        
        # 각 단계의 데이터를 저장할 변수들
        template_data = None
        ladder_zip_data = None
        matched_files_data = None
        
        try:
            # 0. UploadFile 객체 생성
            logger.info("[Step 0] UploadFile 객체 생성")
            ladder_zip = self.file_path_to_upload_file(ladder_zip_path)
            template_xlsx = self.file_path_to_upload_file(template_xlsx_path)
            comment_csv = self.file_path_to_upload_file(comment_csv_path)
            
            # Step 1: 파일 타입 검증
            logger.info("[Step 1] 파일 타입 검증 시작")
            
            result = self.validate_ladder_zip_file_type(ladder_zip)
            validation_results.append({
                'title': '레더 ZIP 파일 타입 검증',
                'is_valid': result['is_valid'],
                'errors': result['errors']
            })
            
            result = self.validate_template_file_type(template_xlsx)
            validation_results.append({
                'title': '템플릿 파일 타입 검증',
                'is_valid': result['is_valid'],
                'errors': result['errors']
            })
            
            result = self.validate_comment_file_type(comment_csv)
            validation_results.append({
                'title': '커멘트 파일 타입 검증',
                'is_valid': result['is_valid'],
                'errors': result['errors']
            })
            
            # Step 2: 템플릿 파일 구조 검증
            logger.info("[Step 2] 템플릿 파일 구조 검증 시작")
            result = self.validate_template_file_structure(template_xlsx)
            validation_results.append({
                'title': '템플릿 파일 구조 검증',
                'is_valid': result['is_valid'],
                'errors': result['errors']
            })
            if result['is_valid']:
                template_data = result['data']
                logger.info(f"템플릿 구조 검증 통과: {len(template_data['logic_ids'])}개 Logic ID")
            
            # Step 3: 레더 ZIP 파일 구조 검증
            logger.info("[Step 3] 레더 ZIP 파일 구조 검증 시작")
            result = self.validate_ladder_zip_structure(ladder_zip)
            validation_results.append({
                'title': '레더 ZIP 파일 구조 검증',
                'is_valid': result['is_valid'],
                'errors': result['errors']
            })
            if result['is_valid']:
                ladder_zip_data = result['data']
                logger.info(f"레더 ZIP 구조 검증 통과: {ladder_zip_data['file_count']}개 파일")
            
            # Step 4: 레더 파일 목록 매칭 (의존성 체크)
            logger.info("[Step 4] 레더 파일 매칭 검증 시작")
            if template_data and ladder_zip_data:
                matched_files_data, result = self.validate_ladder_files_match(
                    required_files=template_data['logic_ids'],
                    actual_files=ladder_zip_data['file_list']
                )
                validation_results.append({
                    'title': '레더 파일 목록 매칭',
                    'is_valid': result['is_valid'],
                    'errors': result['errors']
                })
                if matched_files_data:
                    logger.info(f"파일 매칭 검증 통과: {len(matched_files_data)}개 매칭")
            else:
                validation_results.append({
                    'title': '레더 파일 목록 매칭',
                    'is_valid': False,
                    'errors': ['이전 단계(템플릿 또는 ZIP 구조) 실패로 인해 실행 불가']
                })
            
            # Step 5: 매칭된 레더 CSV 파일들 구조 검증 (의존성 체크)
            logger.info("[Step 5] 매칭된 레더 CSV 구조 검증 시작")
            if matched_files_data:
                result = self.validate_matched_ladder_csv_structures_in_memory(
                    ladder_zip,
                    matched_files_data
                )
                validation_results.append({
                    'title': '매칭된 레더 CSV 구조 검증',
                    'is_valid': result['is_valid'],
                    'errors': result['errors']
                })
                if result['is_valid']:
                    logger.info("레더 CSV 구조 검증 통과")
            else:
                validation_results.append({
                    'title': '매칭된 레더 CSV 구조 검증',
                    'is_valid': False,
                    'errors': ['이전 단계(파일 매칭) 실패로 인해 실행 불가']
                })
            
            # Step 6: 커멘트 파일 구조 검증
            logger.info("[Step 6] 커멘트 파일 구조 검증 시작")
            comment_csv_bytes = comment_csv.file.read()
            comment_csv.file.seek(0)  # 파일 포인터 복귀
            
            result = self.validate_csv_structure_from_bytes(
                comment_csv_bytes,
                comment_csv.filename,
                self.settings.get_pgm_comment_csv_required_columns(),
                self.settings.pgm_comment_csv_header_row
            )
            validation_results.append({
                'title': '커멘트 파일 구조 검증',
                'is_valid': result['is_valid'],
                'errors': [f"필수 컬럼 누락: {', '.join(result['missing_columns'])}"] if not result['is_valid'] else []
            })
            if result['is_valid']:
                logger.info("커멘트 CSV 구조 검증 통과")
            
            # 최종 결과 판정
            all_passed = all(step['is_valid'] for step in validation_results)
            
            if all_passed:
                logger.info("모든 검증 단계 통과")
                return {
                    'validation_passed': True,
                    'validation_results': validation_results
                }
            else:
                failed_count = sum(1 for s in validation_results if not s['is_valid'])
                logger.error(f"검증 실패: {failed_count}개 단계 실패")
                
                # 실패한 단계들 로그 출력
                for step in validation_results:
                    if not step['is_valid']:
                        logger.error(f"  [{step['title']}] " + "; ".join(step['errors']))
                
                # 예외 발생 대신 결과 반환
                return {
                    'validation_passed': False,
                    'validation_results': validation_results
                }
                
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"프로그램 검증 작업 실패: {str(e)}", exc_info=True)
            raise HandledException(
                ResponseCode.DOCUMENT_UPLOAD_ERROR,
                msg=f"프로그램 검증 작업 중 예상치 못한 오류 발생: {str(e)}",
                e=e
            )
    
    
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
                "errors": ["레더 ZIP 파일이 업로드되지 않았습니다"],
                "data": None
            }
        allowed_extensions = self.settings.pgm_ladder_zip_allowed_extensions.split(',')
        if not any(ladder_zip.filename.lower().endswith(ext) for ext in allowed_extensions):
            return {
                "is_valid": False,
                "errors": [f"레더 ZIP 파일은 압축파일 형식이어야 합니다({', '.join(allowed_extensions)})"],
                "data": None
            }
        return {
            "is_valid": True,
            "errors": [],
            "data": None
        }

    def validate_template_file_type(self, template_file: UploadFile) -> Dict[str, Any]:
        """템플릿 파일 타입 검증"""
        if not template_file or not template_file.filename:
            return {
                "is_valid": False,
                "errors": ["템플릿 파일이 업로드되지 않았습니다"],
                "data": None
            }
        allowed_extensions = self.settings.pgm_template_allowed_extensions.split(',')
        if not any(template_file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return {
                "is_valid": False,
                "errors": [f"템플릿 파일은 Excel파일 형식이어야 합니다({', '.join(allowed_extensions)})"],
                "data": None
            }
        return {
            "is_valid": True,
            "errors": [],
            "data": None
        }

    def validate_comment_file_type(self, comment_file: UploadFile) -> Dict[str, Any]:
        """커멘트 파일 타입 검증"""
        if not comment_file or not comment_file.filename:
            return {
                "is_valid": False,
                "errors": ["커멘트 파일이 업로드되지 않았습니다"],
                "data": None
            }
        allowed_extensions = self.settings.pgm_comment_csv_allowed_extensions.split(',')
        if not any(comment_file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return {
                "is_valid": False,
                "errors": [f"커멘트 파일은 csv파일 형식이어야 합니다({', '.join(allowed_extensions)})"],
                "data": None
            }
        return {
            "is_valid": True,
            "errors": [],
            "data": None
        }
    
    def validate_ladder_zip_structure(self, zip_file: UploadFile) -> Dict:
        """
        레더 ZIP 구조 검증 (손상 여부, 내부 파일 목록)
        
        Args:
            zip_file: 레더 ZIP 파일
            
        Returns:
            Dict: {
                'is_valid': bool,
                'errors': List[str],
                'data': {
                    'file_list': List[str],  # ZIP 내부 파일명 리스트 (확장자 제외)
                    'file_count': int
                }
            }
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
                    return {
                        'is_valid': False,
                        'errors': [f"손상된 파일이 포함되어 있습니다: {bad_file}"],
                        'data': None
                    }
                
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
                    'is_valid': True,
                    'errors': [],
                    'data': {
                        'file_list': file_list,
                        'file_count': len(file_list)
                    }
                }
        
        except zipfile.BadZipFile as e:
            return {
                'is_valid': False,
                'errors': [f"잘못된 ZIP 파일 형식입니다: {str(e)}"],
                'data': None
            }
        except Exception as e:
            logger.error(f"ZIP 구조 검증 실패: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"레더 ZIP 파일 구조 검증 중 오류가 발생했습니다: {str(e)}"],
                'data': None
            }

    def validate_template_file_structure(self, xlsx_file: UploadFile) -> Dict[str, Any]:
        """
        템플릿 파일 구조 검증 (필수 컬럼 존재 여부, 환경변수 기반)
        
        Args:
            xlsx_file: 템플릿 Excel 파일
            
        Returns:
            Dict: {
                'is_valid': bool,
                'errors': List[str],
                'data': {
                    'logic_ids': List[str],
                    'row_count': int
                }
            }
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
                return {
                    'is_valid': False,
                    'errors': [f"템플릿에 필수 컬럼이 없습니다: {', '.join(missing_cols)}"],
                    'data': None
                }
            
            # Logic ID 추출 1
            logic_ids_raw = df['Logic ID'].dropna().astype(str).tolist()

            # Logic ID 추출 2 (중복 제거)
            logic_ids = df['Logic ID'].dropna().astype(str).unique().tolist()
            
            if not logic_ids:
                return {
                    'is_valid': False,
                    'errors': ["템플릿에 Logic ID가 없습니다"],
                    'data': None
                }
            
            diff_list = list(set(logic_ids_raw) - set(logic_ids))
            if diff_list != []:
                return {
                    'is_valid': False,
                    'errors': [f"템플릿에 중복된 Logic ID가 있습니다. 중복된 Logic ID {len(diff_list)}개({', '.join(diff_list)})"],
                    'data': None
                }
            
            logger.info(f"템플릿 구조 검증 통과: {len(logic_ids)}개 Logic ID, {len(df)}개 행")
            
            return {
                'is_valid': True,
                'errors': [],
                'data': {
                    'logic_ids': logic_ids,
                    'row_count': len(df)
                }
            }
        
        except pd.errors.EmptyDataError:
            return {
                'is_valid': False,
                'errors': ["템플릿 파일이 비어 있습니다"],
                'data': None
            }
        except Exception as e:
            logger.error(f"템플릿 구조 검증 실패: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"템플릿 파일 구조 검증 중 오류가 발생했습니다: {str(e)}"],
                'data': None
            }
    
    def validate_ladder_files_match(
        self,
        required_files: List[str],
        actual_files: List[str]
    ) -> tuple[Optional[List[str]], Dict[str, Any]]:
        """
        템플릿 Logic ID vs ZIP 파일 목록 비교
        
        Args:
            required_files: 템플릿에 명시된 필수 Logic ID 리스트
            actual_files: ZIP 내부 파일명 리스트 (확장자 제외)
            
        Returns:
            Tuple[matched_files, result]:
                - matched_files: 매칭된 파일 리스트 (실패 시 None)
                - result: {
                    'is_valid': bool,
                    'errors': List[str]
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
        
        if validation_passed:
            logger.info(
                f"레더 파일 매칭 검증 통과: "
                f"{len(matched_files)}개 일치, {len(extra_files)}개 불필요"
            )
            return sorted(matched_files), {
                'is_valid': True,
                'errors': []
            }
        else:
            # 누락된 파일 목록을 보기 좋게 포맷 (최대 10개까지만 표시)
            missing_with_ext = [f"{f}.csv" for f in sorted(missing_files)[:10]]
            missing_display = ', '.join(missing_with_ext)
            if len(missing_files) > 10:
                missing_display += f" 외 {len(missing_files) - 10}개"
            
            return None, {
                'is_valid': False,
                'errors': [f"{len(missing_files)}개 파일이 누락되었습니다 ({missing_display})"]
            }

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
            {
                'is_valid': bool,
                'errors': List[str],
                'data': {
                    'validated_count': int,
                    'failed_files': List[Dict]
                }
            }
        """
        try:
            # ZIP 파일 읽기 (메모리)
            zip_bytes = ladder_zip_file.file.read()
            ladder_zip_file.file.seek(0)  # 필수: 파일 포인터 복귀
            
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
                    'is_valid': True,
                    'errors': [],
                    'data': {
                        'validated_count': validated_count,
                        'failed_files': []
                    }
                }
            else:
                logger.error("매칭된 레더 CSV 구조 검증 작업 완료(Fail)")
                # 실패 파일 목록을 에러 메시지로 변환
                error_messages = []
                for failed in failed_files:
                    if 'missing_columns' in failed:
                        error_messages.append(
                            f"{failed['filename']}: 필수 컬럼 누락 ({', '.join(failed['missing_columns'])})"
                        )
                    else:
                        error_messages.append(f"{failed['filename']}: {failed.get('error', '알 수 없는 오류')}")
                
                return {
                    'is_valid': False,
                    'errors': error_messages,
                    'data': {
                        'validated_count': validated_count,
                        'failed_files': failed_files
                    }
                }
        
        except Exception as e:
            logger.error(f"레더 CSV 구조 검증 중 오류 발생: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"레더 CSV 구조 검증 중 오류 발생: {str(e)}"],
                'data': None
            }
    
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

