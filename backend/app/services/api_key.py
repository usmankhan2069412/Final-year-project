import secrets
import hashlib
from datetime import datetime, timezone
import uuid
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyResponse, ApiKeyCreateResponse

class ApiKeyService:
    @staticmethod
    def list_keys(db: Session, org_id: uuid.UUID) -> List[ApiKeyResponse]:
        """List all API keys (masked) for the organization."""
        keys = db.query(ApiKey).filter(ApiKey.org_id == org_id).order_by(ApiKey.created_at.desc()).all()
        
        response = []
        for k in keys:
            status_str = "revoked" if k.revoked_at is not None else "active"
            response.append(
                ApiKeyResponse(
                    id=k.id,
                    name=k.name,
                    prefix=k.key_prefix,
                    created_at=k.created_at,
                    last_used=k.last_used_at,
                    status=status_str
                )
            )
        return response

    @staticmethod
    def create_key(db: Session, org_id: uuid.UUID, name: str) -> ApiKeyCreateResponse:
        """Generate a new secure API key, store its hash, and return it once."""
        # 1. Generate secure random key
        token = secrets.token_urlsafe(32)
        raw_key = f"ak_prod_{token}"
        
        # 2. Mask it for the user prefix (e.g., ak_prod_abcd...)
        prefix = f"ak_prod_{token[:6]}..."
        
        # 3. Hash the key for secure DB storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # 4. Save to DB
        db_key = ApiKey(
            org_id=org_id,
            name=name,
            key_hash=key_hash,
            key_prefix=prefix
        )
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        
        return ApiKeyCreateResponse(
            id=db_key.id,
            name=db_key.name,
            key=raw_key,
            prefix=prefix,
            created_at=db_key.created_at
        )

    @staticmethod
    def revoke_key(db: Session, org_id: uuid.UUID, key_id: uuid.UUID) -> bool:
        """Revoke an API key by setting its revoked_at timestamp."""
        db_key = db.query(ApiKey).filter(
            ApiKey.id == key_id,
            ApiKey.org_id == org_id
        ).first()
        
        if not db_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API Key not found or access denied"
            )
            
        if db_key.revoked_at is None:
            db_key.revoked_at = datetime.now(timezone.utc)
            db.commit()
            
        return True
