import os
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import settings
from app.models.document import KnowledgeSource, Document, KnowledgeChunk, SourceType, SourceStatus, FileType, ChunkStatus
from app.services.text_extractor import TextExtractor
from app.services.chunker import TextChunker
from app.services.embedding import embedding_service
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class KnowledgeService:
    @staticmethod
    def create_metadata_source(db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, source_type: SourceType, value: str, label: str) -> KnowledgeSource:
        source = KnowledgeSource(
            org_id=org_id,
            chatbot_id=chatbot_id,
            source_type=source_type,
            label=label,
            value=value,
            status=SourceStatus.INDEXED
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def upload_file(cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, file: UploadFile) -> KnowledgeSource:
        filename = file.filename
        ext = filename.split(".")[-1].lower()
        if ext not in ["pdf", "docx", "txt", "csv"]:
            raise ValueError("Unsupported file type")
            
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_id = uuid.uuid4()
        storage_filename = f"{file_id}.{ext}"
        storage_path = os.path.join(settings.UPLOAD_DIR, storage_filename)
        
        size = 0
        with open(storage_path, "wb") as f:
            content = file.file.read()
            size = len(content)
            if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                os.remove(storage_path)
                raise ValueError("File exceeds maximum allowed size")
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
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def create_text_source(cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, text: str, label: str) -> KnowledgeSource:
        source = KnowledgeSource(
            org_id=org_id,
            chatbot_id=chatbot_id,
            source_type=SourceType.TEXT,
            label=label,
            value=text[:100] + ("..." if len(text) > 100 else ""),
            status=SourceStatus.QUEUED
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def create_website_source(cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, url: str) -> KnowledgeSource:
        source = KnowledgeSource(
            org_id=org_id,
            chatbot_id=chatbot_id,
            source_type=SourceType.WEBSITE,
            label="Website URL",
            value=url,
            status=SourceStatus.QUEUED
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @classmethod
    def process_source_background(cls, source_id: uuid.UUID, raw_text: str = None):
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            source = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
            if not source:
                return

            source.status = SourceStatus.PROCESSING
            db.commit()

            text = ""
            if source.source_type == SourceType.FILE:
                doc = source.document
                if doc.file_type == FileType.PDF:
                    text = TextExtractor.extract_pdf(doc.storage_path)
                elif doc.file_type == FileType.DOCX:
                    text = TextExtractor.extract_docx(doc.storage_path)
                elif doc.file_type == FileType.TXT:
                    text = TextExtractor.extract_txt(doc.storage_path)
                elif doc.file_type == FileType.CSV:
                    text = TextExtractor.extract_csv(doc.storage_path)
            elif source.source_type == SourceType.TEXT:
                text = raw_text or source.value
            elif source.source_type == SourceType.WEBSITE:
                import asyncio
                text = asyncio.run(TextExtractor.extract_url(source.value))

            chunks = TextChunker.split_text(text)
            if not chunks:
                source.status = SourceStatus.INDEXED
                db.commit()
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
            db.commit()

        except Exception as e:
            logger.exception("Error processing knowledge source %s", source_id)
            db.rollback()
            source = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
            if source:
                source.status = SourceStatus.FAILED
                source.error_message = str(e)
                db.commit()
        finally:
            db.close()

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
