import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db
from app.services.document import KnowledgeService
from app.schemas.document import KnowledgeSourceCreate, KnowledgeSourceResponse, KnowledgeSourceDetailResponse
from app.models.document import KnowledgeSource, SourceType, SourceStatus

router = APIRouter()

def _get_org_id(db: Session) -> uuid.UUID:
    """Helper to retrieve the resolved organization ID from the db session context."""
    org_id_str = db.execute(text("SELECT current_setting('app.current_org_id', true)")).scalar()
    if not org_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is missing."
        )
    try:
        return uuid.UUID(org_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format in tenant context."
        )

@router.post("/upload", response_model=KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    chatbot_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_tenant_db)
):
    """Upload a file as a knowledge source (PDF, DOCX, TXT, CSV) and trigger background embedding."""
    org_id = _get_org_id(db)
    try:
        source = KnowledgeService.upload_file(db=db, org_id=org_id, chatbot_id=chatbot_id, file=file)
        background_tasks.add_task(KnowledgeService.process_source_background, source.id)
        return source
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("", response_model=KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_source(
    source_in: KnowledgeSourceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db)
):
    """Create a text, website, phone, email, or app knowledge source."""
    org_id = _get_org_id(db)
    
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
        background_tasks.add_task(KnowledgeService.process_source_background, source.id, source_in.value)
        return source
        
    if source_in.source_type == SourceType.WEBSITE:
        source = KnowledgeService.create_website_source(
            db=db,
            org_id=org_id,
            chatbot_id=source_in.chatbot_id,
            url=source_in.value
        )
        background_tasks.add_task(KnowledgeService.process_source_background, source.id)
        return source

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported source type")

@router.get("/chatbots/{chatbot_id}", response_model=List[KnowledgeSourceResponse])
def list_knowledge_sources(
    chatbot_id: uuid.UUID,
    db: Session = Depends(get_tenant_db)
):
    """List all knowledge sources for a chatbot."""
    org_id = _get_org_id(db)
    sources = db.query(KnowledgeSource).filter(
        KnowledgeSource.chatbot_id == chatbot_id,
        KnowledgeSource.org_id == org_id
    ).all()
    return sources

@router.get("/{source_id}", response_model=KnowledgeSourceDetailResponse)
def get_knowledge_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_tenant_db)
):
    """Retrieve details and chunks of a knowledge source."""
    org_id = _get_org_id(db)
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
    db: Session = Depends(get_tenant_db)
):
    """Delete a knowledge source and clean up files/vectors."""
    org_id = _get_org_id(db)
    success = KnowledgeService.delete_source(db=db, org_id=org_id, source_id=source_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found")
    return None
