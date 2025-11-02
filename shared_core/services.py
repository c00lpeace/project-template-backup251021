# _*_ coding: utf-8 _*_
"""
공통 문서 서비스
Backend와 Prefect 프로젝트에서 공통으로 사용하는 문서 관련 서비스들
"""

import hashlib
import logging
import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from .crud import DocumentChunkCRUD, DocumentCRUD, ProcessingJobCRUD
from .models import Document, DocumentChunk, ProcessingJob

logger = logging.getLogger(__name__)


class DocumentService:
    """공통 문서 관리 서비스"""

    def __init__(self, db: Session, upload_base_path: str = None):
        self.db = db
        self.upload_base_path = (
            Path(upload_base_path) if upload_base_path else Path("uploads")
        )
        self.upload_base_path.mkdir(parents=True, exist_ok=True)
        self.document_crud = DocumentCRUD(db)
        self.chunk_crud = DocumentChunkCRUD(db)
        self.job_crud = ProcessingJobCRUD(db)

    def _get_file_extension(self, filename: str) -> str:
        """파일 확장자 추출 (. 제거)"""
        return Path(filename).suffix.lower().lstrip(".")

    def _get_mime_type(self, filename: str) -> str:
        """MIME 타입 추출"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def _calculate_file_hash(self, file_content: bytes) -> str:
        """파일 해시값 계산 (MD5, 4096 바이트 청크 단위)"""
        hash_md5 = hashlib.md5()
        # 4096 바이트씩 청크 단위로 해시 계산
        for i in range(0, len(file_content), 4096):
            chunk = file_content[i : i + 4096]
            hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _generate_file_key(self, user_id: str, filename: str = None) -> str:
        """파일 키 생성 (저장 경로)"""
        # 폴더 구조: uploads/user_id/filename
        return f"{user_id}/{filename}"

    def _get_upload_path(self, file_key: str) -> Path:
        """실제 업로드 경로 생성"""
        return self.upload_base_path / file_key

    def create_document_from_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        document_type: str = "common",
        **additional_metadata,
    ) -> Dict:
        """파일 내용으로부터 문서 생성"""
        try:
            # 파일 정보 추출
            file_extension = self._get_file_extension(filename)
            file_type = self._get_mime_type(filename)
            file_size = len(file_content)
            file_hash = self._calculate_file_hash(file_content)

            # 중복 파일 체크
            existing_doc = self.document_crud.find_document_by_hash(file_hash)
            if existing_doc and existing_doc.status == "completed":
                logger.info(f"📋 완료된 기존 문서 발견: {existing_doc.document_id}")
                return self._document_to_dict(existing_doc, is_duplicate=True)

            # 고유한 문서 ID 생성
            if existing_doc and existing_doc.status in ["processing", "failed"]:
                document_id = existing_doc.document_id
                logger.info(f"🔄 기존 문서 재처리: {document_id}")
            else:
                document_id = (
                    f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}"
                )

            # 파일 저장
            file_key = self._generate_file_key(user_id, filename)
            upload_path = self._get_upload_path(file_key)

            # 디렉토리 생성
            upload_path.parent.mkdir(parents=True, exist_ok=True)

            # 파일 저장
            with open(upload_path, "wb") as f:
                f.write(file_content)

            # DB에 메타데이터 저장
            if existing_doc and existing_doc.status in ["failed", "processing"]:
                # 기존 문서 업데이트
                self.document_crud.update_document(
                    document_id,
                    document_name=filename,
                    original_filename=filename,
                    file_key=file_key,
                    file_size=file_size,
                    file_type=file_type,
                    file_extension=file_extension,
                    user_id=user_id,
                    upload_path=str(upload_path),
                    is_public=is_public,
                    status="completed",
                    permissions=permissions,
                    document_type=document_type,
                    **additional_metadata,
                )
                document = self.document_crud.get_document(document_id)
            else:
                # 새 문서 생성
                document = self.document_crud.create_document(
                    document_id=document_id,
                    document_name=filename,
                    original_filename=filename,
                    file_key=file_key,
                    file_size=file_size,
                    file_type=file_type,
                    file_extension=file_extension,
                    user_id=user_id,
                    upload_path=str(upload_path),
                    is_public=is_public,
                    file_hash=file_hash,
                    status="completed",
                    permissions=permissions,
                    document_type=document_type,
                    **additional_metadata,
                )

            return self._document_to_dict(document)

        except Exception as e:
            logger.error(f"문서 생성 실패: {str(e)}")
            raise

    def create_document_from_path(
        self,
        file_path: str,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        document_type: str = "common",
        **additional_metadata,
    ) -> Dict:
        """파일 경로로부터 문서 생성"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        with open(file_path, "rb") as f:
            file_content = f.read()

        return self.create_document_from_file(
            file_content=file_content,
            filename=file_path.name,
            user_id=user_id,
            is_public=is_public,
            permissions=permissions,
            document_type=document_type,
            **additional_metadata,
        )

    def get_document(self, document_id: str, user_id: str = None) -> Optional[Dict]:
        """문서 정보 조회"""
        try:
            document = self.document_crud.get_document(document_id)

            if not document or document.is_deleted:
                return None

            # 사용자 권한 체크 (user_id가 제공된 경우)
            if user_id and document.user_id != user_id and not document.is_public:
                return None

            return self._document_to_dict(document)

        except Exception as e:
            logger.error(f"문서 조회 실패: {str(e)}")
            raise

    def get_user_documents(self, user_id: str) -> List[Dict]:
        """사용자의 문서 목록 조회"""
        try:
            documents = self.document_crud.get_user_documents(user_id)
            return [self._document_to_dict(doc) for doc in documents]

        except Exception as e:
            logger.error(f"사용자 문서 목록 조회 실패: {str(e)}")
            raise

    def search_documents(self, user_id: str, search_term: str) -> List[Dict]:
        """문서 검색"""
        try:
            documents = self.document_crud.search_documents(user_id, search_term)
            return [self._document_to_dict(doc) for doc in documents]

        except Exception as e:
            logger.error(f"문서 검색 실패: {str(e)}")
            raise

    def download_document(
        self, document_id: str, user_id: str = None
    ) -> tuple[bytes, str, str]:
        """문서 다운로드"""
        try:
            document = self.document_crud.get_document(document_id)

            if not document or document.is_deleted:
                raise FileNotFoundError("문서를 찾을 수 없습니다.")

            # 사용자 권한 체크 (user_id가 제공된 경우)
            if user_id and document.user_id != user_id and not document.is_public:
                raise PermissionError("문서에 접근할 권한이 없습니다.")

            # 파일 읽기
            upload_path = Path(document.upload_path)
            if not upload_path.exists():
                raise FileNotFoundError("파일이 존재하지 않습니다.")

            with open(upload_path, "rb") as f:
                file_content = f.read()

            return file_content, document.original_filename, document.file_type

        except Exception as e:
            logger.error(f"문서 다운로드 실패: {str(e)}")
            raise

    def delete_document(self, document_id: str, user_id: str = None) -> bool:
        """문서 삭제"""
        try:
            document = self.document_crud.get_document(document_id)

            if not document:
                return False

            # 사용자 권한 체크 (user_id가 제공된 경우)
            if user_id and document.user_id != user_id:
                raise PermissionError("문서를 삭제할 권한이 없습니다.")

            # DB에서 소프트 삭제
            success = self.document_crud.delete_document(document_id)

            # 관련 청크들도 삭제
            if success:
                self.chunk_crud.delete_document_chunks(document_id)

                # 실제 파일도 삭제 (선택사항)
                upload_path = Path(document.upload_path)
                if upload_path.exists():
                    upload_path.unlink()

            return success

        except Exception as e:
            logger.error(f"문서 삭제 실패: {str(e)}")
            raise

    def update_document_processing_status(
        self, document_id: str, status: str, user_id: str = None, **processing_info
    ) -> bool:
        """문서 처리 상태 및 정보 업데이트"""
        try:
            # 권한 확인 (user_id가 제공된 경우)
            if user_id:
                document = self.document_crud.get_document(document_id)
                if not document or document.user_id != user_id:
                    raise PermissionError("문서를 수정할 권한이 없습니다.")

            # 상태 업데이트
            self.document_crud.update_document_status(document_id, status)

            # 추가 처리 정보 업데이트
            if processing_info:
                self.document_crud.update_processing_info(
                    document_id, **processing_info
                )

            return True

        except Exception as e:
            logger.error(f"문서 처리 상태 업데이트 실패: {str(e)}")
            raise

    def get_document_processing_stats(self, user_id: str) -> Dict:
        """사용자 문서 처리 통계 조회"""
        try:
            documents = self.document_crud.get_user_documents(user_id)

            stats = {
                "total_documents": len(documents),
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "total_pages": 0,
                "processed_pages": 0,
                "total_vectors": 0,
            }

            for doc in documents:
                if doc.status == "processing":
                    stats["processing"] += 1
                elif doc.status == "completed":
                    stats["completed"] += 1
                elif doc.status == "failed":
                    stats["failed"] += 1

                if doc.total_pages:
                    stats["total_pages"] += doc.total_pages
                if doc.processed_pages:
                    stats["processed_pages"] += doc.processed_pages
                if doc.vector_count:
                    stats["total_vectors"] += doc.vector_count

            # 처리 진행률 계산
            if stats["total_pages"] > 0:
                stats["processing_progress"] = round(
                    (stats["processed_pages"] / stats["total_pages"]) * 100, 2
                )
            else:
                stats["processing_progress"] = 0.0

            return stats

        except Exception as e:
            logger.error(f"문서 처리 통계 조회 실패: {str(e)}")
            raise

    def _document_to_dict(self, document: Document, is_duplicate: bool = False) -> Dict:
        """Document 객체를 딕셔너리로 변환"""
        return {
            "document_id": document.document_id,
            "document_name": document.document_name,
            "original_filename": document.original_filename,
            "file_size": document.file_size,
            "file_type": document.file_type,
            "file_extension": document.file_extension,
            "file_hash": document.file_hash,
            "upload_path": document.upload_path,
            "is_public": document.is_public,
            "status": document.status,
            "total_pages": document.total_pages,
            "processed_pages": document.processed_pages,
            "vector_count": document.vector_count,
            "milvus_collection_name": document.milvus_collection_name,
            "language": document.language,
            "author": document.author,
            "subject": document.subject,
            "metadata_json": document.metadata_json,
            "processing_config": document.processing_config,
            "permissions": document.permissions or [],
            "document_type": document.document_type or "common",
            "pgm_id": document.pgm_id,
            "create_dt": document.create_dt.isoformat(),
            "updated_at": (
                document.updated_at.isoformat() if document.updated_at else None
            ),
            "processed_at": (
                document.processed_at.isoformat() if document.processed_at else None
            ),
            "is_duplicate": is_duplicate,
        }


class DocumentChunkService:
    """문서 청크 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.chunk_crud = DocumentChunkCRUD(db)

    def create_chunk(
        self,
        doc_id: str,
        page_number: int,
        chunk_type: str,
        content: str = None,
        image_description: str = None,
        image_path: str = None,
        **additional_data,
    ) -> Dict:
        """문서 청크 생성"""
        try:
            chunk_id = (
                f"{doc_id}_page_{page_number}_{chunk_type}_{uuid.uuid4().hex[:8]}"
            )

            # 텍스트 통계 계산
            text_content = content or ""
            char_count = len(text_content) if text_content else 0
            word_count = len(text_content.split()) if text_content else 0

            chunk = self.chunk_crud.create_chunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                page_number=page_number,
                chunk_type=chunk_type,
                content=content,
                image_description=image_description,
                image_path=image_path,
                char_count=char_count,
                word_count=word_count,
                **additional_data,
            )

            return self._chunk_to_dict(chunk)

        except Exception as e:
            logger.error(f"문서 청크 생성 실패: {str(e)}")
            raise

    def get_document_chunks(self, doc_id: str) -> List[Dict]:
        """문서의 모든 청크 조회"""
        try:
            chunks = self.chunk_crud.get_document_chunks(doc_id)
            return [self._chunk_to_dict(chunk) for chunk in chunks]

        except Exception as e:
            logger.error(f"문서 청크 목록 조회 실패: {str(e)}")
            raise

    def update_chunk(self, chunk_id: str, **kwargs) -> bool:
        """청크 정보 업데이트"""
        try:
            return self.chunk_crud.update_chunk(chunk_id, **kwargs)

        except Exception as e:
            logger.error(f"청크 업데이트 실패: {str(e)}")
            raise

    def delete_chunk(self, chunk_id: str) -> bool:
        """청크 삭제"""
        try:
            return self.chunk_crud.delete_chunk(chunk_id)

        except Exception as e:
            logger.error(f"청크 삭제 실패: {str(e)}")
            raise

    def _chunk_to_dict(self, chunk: DocumentChunk) -> Dict:
        """DocumentChunk 객체를 딕셔너리로 변환"""
        return {
            "id": str(chunk.id),
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "page_number": chunk.page_number,
            "chunk_type": chunk.chunk_type,
            "content": chunk.content,
            "image_description": chunk.image_description,
            "image_path": chunk.image_path,
            "milvus_id": chunk.milvus_id,
            "embedding_model": chunk.embedding_model,
            "vector_dimension": chunk.vector_dimension,
            "char_count": chunk.char_count,
            "word_count": chunk.word_count,
            "language": chunk.language,
            "metadata_json": chunk.metadata_json,
            "created_at": chunk.created_at.isoformat(),
            "updated_at": chunk.updated_at.isoformat(),
        }


class ProcessingJobService:
    """처리 작업 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.job_crud = ProcessingJobCRUD(db)

    def create_job(
        self, doc_id: str, job_type: str, flow_run_id: str = None, total_steps: int = 0
    ) -> Dict:
        """처리 작업 생성"""
        try:
            job_id = (
                f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            )

            job = self.job_crud.create_job(
                job_id=job_id,
                doc_id=doc_id,
                job_type=job_type,
                flow_run_id=flow_run_id,
                total_steps=total_steps,
            )

            return self._job_to_dict(job)

        except Exception as e:
            logger.error(f"처리 작업 생성 실패: {str(e)}")
            raise

    def update_job_status(self, job_id: str, status: str, **kwargs) -> bool:
        """작업 상태 업데이트"""
        try:
            return self.job_crud.update_job_status(job_id, status, **kwargs)

        except Exception as e:
            logger.error(f"작업 상태 업데이트 실패: {str(e)}")
            raise

    def get_document_jobs(self, doc_id: str) -> List[Dict]:
        """문서의 모든 작업 조회"""
        try:
            jobs = self.job_crud.get_document_jobs(doc_id)
            return [self._job_to_dict(job) for job in jobs]

        except Exception as e:
            logger.error(f"문서 작업 목록 조회 실패: {str(e)}")
            raise

    def _job_to_dict(self, job: ProcessingJob) -> Dict:
        """ProcessingJob 객체를 딕셔너리로 변환"""
        return {
            "id": str(job.id),
            "job_id": job.job_id,
            "doc_id": job.doc_id,
            "job_type": job.job_type,
            "status": job.status,
            "flow_run_id": job.flow_run_id,
            "total_steps": job.total_steps,
            "completed_steps": job.completed_steps,
            "current_step": job.current_step,
            "result_data": job.result_data,
            "error_message": job.error_message,
            "started_at": job.started_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "updated_at": job.updated_at.isoformat(),
        }
