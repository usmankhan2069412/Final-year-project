import os
import uuid
import logging
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import settings
from app.models.chatbot import Chatbot
from app.models.document import (
    KnowledgeSource,
    Document,
    KnowledgeChunk,
    KnowledgeJob,
    SourceType,
    SourceStatus,
    FileType,
    ChunkStatus,
    KnowledgeJobStatus,
)
from app.services.text_extractor import TextExtractor
from app.services.chunker import TextChunker
from app.services.embedding import embedding_service
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class KnowledgeService:
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv"}

    @staticmethod
    def ensure_chatbot_access(db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID) -> Chatbot:
        chatbot = db.query(Chatbot).filter(
            Chatbot.id == chatbot_id,
            Chatbot.org_id == org_id,
            Chatbot.deleted_at == None,
        ).first()
        if not chatbot:
            raise ValueError("Chatbot not found or inaccessible")
        return chatbot

    @staticmethod
    def _clean_label(label: str | None, fallback: str) -> str:
        cleaned = (label or fallback).strip()
        return cleaned[:120] or fallback

    @classmethod
    def _enqueue_job(cls, db: Session, source: KnowledgeSource) -> KnowledgeJob:
        job = KnowledgeJob(
            source_id=source.id,
            chatbot_id=source.chatbot_id,
            org_id=source.org_id,
            status=KnowledgeJobStatus.QUEUED,
        )
        db.add(job)
        source.status = SourceStatus.QUEUED
        return job

    @staticmethod
    def _validate_public_url(url: str) -> str:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Website URL must start with http:// or https://")
        try:
            addresses = socket.getaddrinfo(parsed.hostname, None)
            for result in addresses:
                ip = ipaddress.ip_address(result[4][0])
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise ValueError("Website URL must resolve to a public address")
        except socket.gaierror:
            raise ValueError("Website URL could not be resolved")
        return url.strip()

    @staticmethod
    def create_metadata_source(db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, source_type: SourceType, value: str, label: str) -> KnowledgeSource:
        KnowledgeService.ensure_chatbot_access(db, org_id, chatbot_id)
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Knowledge source value cannot be empty")
        source = KnowledgeSource(
            org_id=org_id,
            chatbot_id=chatbot_id,
            source_type=source_type,
            label=KnowledgeService._clean_label(label, source_type.value.title()),
            value=cleaned_value,
            status=SourceStatus.INDEXED
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def upload_file(cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, file: UploadFile) -> KnowledgeSource:
        cls.ensure_chatbot_access(db, org_id, chatbot_id)
        filename = Path(file.filename or "").name
        if not filename or "." not in filename:
            raise ValueError("Uploaded file must have a supported extension")
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError("Unsupported file type")
        if file.content_type and file.content_type not in {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/csv",
            "application/csv",
            "application/octet-stream",
        }:
            raise ValueError("Unsupported file content type")
            
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_id = uuid.uuid4()
        storage_filename = f"{file_id}.{ext}"
        upload_root = os.path.abspath(settings.UPLOAD_DIR)
        storage_path = os.path.abspath(os.path.join(upload_root, storage_filename))
        if not storage_path.startswith(upload_root):
            raise ValueError("Invalid upload path")
        
        size = 0
        content = file.file.read(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
        size = len(content)
        if size == 0:
            raise ValueError("Uploaded file is empty")
        if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise ValueError("File exceeds maximum allowed size")
        with open(storage_path, "wb") as f:
            f.write(content)

        source = KnowledgeSource(
            org_id=org_id,
            chatbot_id=chatbot_id,
            source_type=SourceType.FILE,
            label="Documents",
            value=filename,
            status=SourceStatus.QUEUED
        )
        db.add(source)
        db.flush()

        doc = Document(
            source_id=source.id,
            chatbot_id=chatbot_id,
            org_id=org_id,
            filename=filename,
            storage_path=storage_path,
            file_type=FileType(ext),
            file_size_bytes=size,
            uploaded_at=datetime.now(timezone.utc)
        )
        db.add(doc)
        cls._enqueue_job(db, source)
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def create_text_source(cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, text: str, label: str) -> KnowledgeSource:
        cls.ensure_chatbot_access(db, org_id, chatbot_id)
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Text knowledge source cannot be empty")
        source = KnowledgeSource(
            org_id=org_id,
            chatbot_id=chatbot_id,
            source_type=SourceType.TEXT,
            label=cls._clean_label(label, "Text"),
            value=cleaned_text,
            status=SourceStatus.QUEUED
        )
        db.add(source)
        db.flush()
        cls._enqueue_job(db, source)
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def create_website_source(cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, url: str) -> KnowledgeSource:
        cls.ensure_chatbot_access(db, org_id, chatbot_id)
        url = cls._validate_public_url(url)
        source = KnowledgeSource(
            org_id=org_id,
            chatbot_id=chatbot_id,
            source_type=SourceType.WEBSITE,
            label="Website URL",
            value=url,
            status=SourceStatus.QUEUED
        )
        db.add(source)
        db.flush()
        cls._enqueue_job(db, source)
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def process_source_background(cls, source_id: uuid.UUID):
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            source = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
            if not source:
                return
            cls.process_source(db, source)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Error processing knowledge source %s", source_id)
        finally:
            db.close()

    @classmethod
    def process_source(cls, db: Session, source: KnowledgeSource) -> None:
        source.status = SourceStatus.PROCESSING
        source.error_message = None
        db.flush()

        text = ""
        if source.source_type == SourceType.FILE:
            doc = source.document
            if not doc:
                raise ValueError("Document metadata is missing")
            if doc.file_type == FileType.PDF:
                text = TextExtractor.extract_pdf(doc.storage_path)
            elif doc.file_type == FileType.DOCX:
                text = TextExtractor.extract_docx(doc.storage_path)
            elif doc.file_type == FileType.TXT:
                text = TextExtractor.extract_txt(doc.storage_path)
            elif doc.file_type == FileType.CSV:
                text = TextExtractor.extract_csv(doc.storage_path)
        elif source.source_type == SourceType.TEXT:
            text = source.value
        elif source.source_type == SourceType.WEBSITE:
            text = TextExtractor.extract_url_sync(source.value)

        chunks = TextChunker.split_text(text)
        db.query(KnowledgeChunk).filter(KnowledgeChunk.source_id == source.id).delete()
        try:
            VectorStoreService.remove_by_source(str(source.chatbot_id), str(source.id))
        except Exception:
            logger.warning("Unable to remove previous vectors for source %s", source.id, exc_info=True)

        if not chunks:
            source.status = SourceStatus.INDEXED
            return

        chunk_records = []
        for i, chunk_text in enumerate(chunks):
            record = KnowledgeChunk(
                source_id=source.id,
                chatbot_id=source.chatbot_id,
                chunk_text=chunk_text,
                chunk_index=i,
                index_status=ChunkStatus.PROCESSING
            )
            db.add(record)
            chunk_records.append(record)
        db.flush()

        embeddings = embedding_service.encode(chunks)
        chunk_ids = [str(r.id) for r in chunk_records]
        VectorStoreService.add_vectors(str(source.chatbot_id), embeddings, chunk_ids, str(source.id), chunks)

        for r in chunk_records:
            r.index_status = ChunkStatus.COMPLETED
        source.status = SourceStatus.INDEXED

    @classmethod
    def _notify_job_update(cls, db: Session, job: KnowledgeJob):
        from app.models.organization import OrgMember
        from app.services.websocket import manager
        import asyncio

        try:
            members = db.query(OrgMember).filter(OrgMember.org_id == job.org_id).all()
            if not members:
                return
            
            payload = {
                "type": "knowledge_update",
                "chatbot_id": str(job.chatbot_id)
            }
            
            async def send_updates():
                for member in members:
                    await manager.send_personal_message(payload, member.user_id)
            
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(send_updates())
            except RuntimeError:
                asyncio.run(send_updates())
                
        except Exception as e:
            logger.error(f"Failed to notify users of knowledge update: {e}")

    @classmethod
    def process_next_job(cls, db: Session) -> bool:
        job = db.query(KnowledgeJob).filter(
            KnowledgeJob.status == KnowledgeJobStatus.QUEUED,
            KnowledgeJob.attempts < KnowledgeJob.max_attempts,
        ).order_by(KnowledgeJob.created_at.asc()).first()
        if not job:
            return False

        job.status = KnowledgeJobStatus.PROCESSING
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        job.error_message = None
        db.commit()

        try:
            source = db.query(KnowledgeSource).filter(KnowledgeSource.id == job.source_id).first()
            if not source:
                raise ValueError("Knowledge source not found")
            cls.process_source(db, source)
            job.status = KnowledgeJobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            cls._notify_job_update(db, job)
            return True
        except Exception as exc:
            db.rollback()
            job = db.query(KnowledgeJob).filter(KnowledgeJob.id == job.id).first()
            source = db.query(KnowledgeSource).filter(KnowledgeSource.id == job.source_id).first() if job else None
            if job:
                job.error_message = str(exc)
                job.status = KnowledgeJobStatus.FAILED if job.attempts >= job.max_attempts else KnowledgeJobStatus.QUEUED
            if source:
                source.status = SourceStatus.FAILED if job and job.status == KnowledgeJobStatus.FAILED else SourceStatus.QUEUED
                source.error_message = str(exc)
            db.commit()
            if job and job.status == KnowledgeJobStatus.FAILED:
                cls._notify_job_update(db, job)
            logger.exception("Knowledge job failed: %s", job.id if job else "unknown")
            return True

    @classmethod
    def delete_source(cls, db: Session, org_id: uuid.UUID, source_id: uuid.UUID) -> bool:
        source = db.query(KnowledgeSource).filter(
            KnowledgeSource.id == source_id,
            KnowledgeSource.org_id == org_id
        ).first()
        if not source:
            return False

        if source.source_type == SourceType.FILE and source.document:
            path = source.document.storage_path
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        if source.source_type in [SourceType.FILE, SourceType.TEXT, SourceType.WEBSITE]:
            try:
                VectorStoreService.remove_by_source(str(source.chatbot_id), str(source.id))
            except Exception:
                pass

        db.delete(source)
        db.commit()
        return True
