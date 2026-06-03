import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, get_current_org_id
from app.services.document import KnowledgeService
from app.schemas.document import KnowledgeSourceCreate, KnowledgeSourceResponse, KnowledgeSourceDetailResponse, KnowledgeJobResponse
from app.models.document import KnowledgeSource, KnowledgeJob, SourceType

logger = logging.getLogger(__name__)

router = APIRouter()

def run_knowledge_jobs_task():
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        # Process jobs sequentially until there are none left
        while KnowledgeService.process_next_job(db):
            pass
    except Exception as e:
        logger.exception("Error in run_knowledge_jobs_task background task: %s", e)
    finally:
        db.close()

@router.post("/upload", response_model=KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    chatbot_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Upload a file as a knowledge source (PDF, DOCX, TXT, CSV) and enqueue indexing."""
    try:
        source = KnowledgeService.upload_file(db=db, org_id=org_id, chatbot_id=chatbot_id, file=file)
        background_tasks.add_task(run_knowledge_jobs_task)
        return source
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("", response_model=KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_source(
    source_in: KnowledgeSourceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Create a text, website, phone, email, or app knowledge source."""
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
        background_tasks.add_task(run_knowledge_jobs_task)
        return source
        
    if source_in.source_type == SourceType.WEBSITE:
        source = KnowledgeService.create_website_source(
            db=db,
            org_id=org_id,
            chatbot_id=source_in.chatbot_id,
            url=source_in.value
        )
        background_tasks.add_task(run_knowledge_jobs_task)
        return source

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported source type")

@router.get("/chatbots/{chatbot_id}", response_model=List[KnowledgeSourceResponse])
def list_knowledge_sources(
    chatbot_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """List all knowledge sources for a chatbot."""
    try:
        KnowledgeService.ensure_chatbot_access(db=db, org_id=org_id, chatbot_id=chatbot_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    sources = db.query(KnowledgeSource).filter(
        KnowledgeSource.chatbot_id == chatbot_id,
        KnowledgeSource.org_id == org_id
    ).all()
    return sources

@router.get("/jobs/{chatbot_id}", response_model=List[KnowledgeJobResponse])
def list_knowledge_jobs(
    chatbot_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """List indexing jobs for a chatbot so clients can poll durable processing state."""
    try:
        KnowledgeService.ensure_chatbot_access(db=db, org_id=org_id, chatbot_id=chatbot_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return db.query(KnowledgeJob).filter(
        KnowledgeJob.chatbot_id == chatbot_id,
        KnowledgeJob.org_id == org_id
    ).order_by(KnowledgeJob.created_at.desc()).all()

@router.get("/{source_id}", response_model=KnowledgeSourceDetailResponse)
def get_knowledge_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Retrieve details and chunks of a knowledge source."""
    source = db.query(KnowledgeSource).filter(
        KnowledgeSource.id == source_id,
        KnowledgeSource.org_id == org_id
    ).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found")
    return source

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Delete a knowledge source and clean up files/vectors."""
    success = KnowledgeService.delete_source(db=db, org_id=org_id, source_id=source_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found")
    return None
