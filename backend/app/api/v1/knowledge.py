import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from pydantic import BaseModel
from app.api.deps import get_tenant_db, get_current_org_id
from app.services.document import KnowledgeService
from app.schemas.document import KnowledgeSourceCreate, KnowledgeSourceResponse, KnowledgeSourceDetailResponse, KnowledgeJobResponse
from app.models.document import KnowledgeSource, KnowledgeJob, SourceType
from app.services.text_extractor import TextExtractor

logger = logging.getLogger(__name__)

router = APIRouter()

class UrlValidationRequest(BaseModel):
    url: str



@router.post("/upload", response_model=KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    chatbot_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Upload a file as a knowledge source (PDF, DOCX, TXT, CSV) and enqueue indexing."""
    try:
        source = KnowledgeService.upload_file(db=db, org_id=org_id, chatbot_id=chatbot_id, file=file)
        return source
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/validate-url")
def validate_url(
    payload: UrlValidationRequest,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Pre-flight check to see if a URL can be crawled."""
    try:
        url = KnowledgeService._validate_public_url(payload.url)
        meta = TextExtractor.validate_url_sync(url)
        return {"status": "ok", "links_found": meta["links_found"]}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Error validating url: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot crawl this website.")


@router.post("", response_model=KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_source(
    source_in: KnowledgeSourceCreate,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Create a text, website, phone, email, or app knowledge source."""
    try:
        if source_in.source_type == SourceType.FILE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="For files, use the /upload endpoint."
            )
            
        # Metadata types don't require processing
        if source_in.source_type in [SourceType.EMAIL, SourceType.PHONE, SourceType.APP]:
            return KnowledgeService.create_metadata_source(
                db=db,
                org_id=org_id,
                chatbot_id=source_in.chatbot_id,
                source_type=source_in.source_type,
                value=source_in.value,
                label=source_in.label
            )
            
        if source_in.source_type == SourceType.TEXT:
            source = KnowledgeService.create_text_source(
                db=db,
                org_id=org_id,
                chatbot_id=source_in.chatbot_id,
                text=source_in.value,
                label=source_in.label
            )
            return source
            
        if source_in.source_type == SourceType.WEBSITE:
            source = KnowledgeService.create_website_source(
                db=db,
                org_id=org_id,
                chatbot_id=source_in.chatbot_id,
                url=source_in.value
            )
            return source

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported source type")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Error creating knowledge source: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating knowledge source."
        )

@router.get("/chatbots/{chatbot_id}", response_model=List[KnowledgeSourceResponse])
def list_knowledge_sources(
    chatbot_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """List all knowledge sources for a chatbot."""
    try:
        KnowledgeService.ensure_chatbot_access(db=db, org_id=org_id, chatbot_id=chatbot_id)
        sources = db.query(KnowledgeSource).filter(
            KnowledgeSource.chatbot_id == chatbot_id,
            KnowledgeSource.org_id == org_id
        ).all()
        return sources
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Error listing knowledge sources: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving knowledge sources."
        )

@router.get("/jobs/{chatbot_id}", response_model=List[KnowledgeJobResponse])
def list_knowledge_jobs(
    chatbot_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """List indexing jobs for a chatbot so clients can poll durable processing state."""
    try:
        KnowledgeService.ensure_chatbot_access(db=db, org_id=org_id, chatbot_id=chatbot_id)
        return db.query(KnowledgeJob).filter(
            KnowledgeJob.chatbot_id == chatbot_id,
            KnowledgeJob.org_id == org_id
        ).order_by(KnowledgeJob.created_at.desc()).all()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Error listing knowledge jobs: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving knowledge jobs."
        )

@router.get("/{source_id}", response_model=KnowledgeSourceDetailResponse)
def get_knowledge_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Retrieve details and chunks of a knowledge source."""
    try:
        source = db.query(KnowledgeSource).filter(
            KnowledgeSource.id == source_id,
            KnowledgeSource.org_id == org_id
        ).first()
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found")
        return source
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving knowledge source: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving knowledge source details."
        )

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Delete a knowledge source and clean up files/vectors."""
    try:
        success = KnowledgeService.delete_source(db=db, org_id=org_id, source_id=source_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting knowledge source: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting knowledge source."
        )
