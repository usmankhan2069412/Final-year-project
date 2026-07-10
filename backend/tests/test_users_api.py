import sys
import os
import uuid
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

from app.main import app
from app.db.session import SessionLocal
from app.api.deps import get_db, get_tenant_db
from app.models.user import User
from app.models.organization import Organization, OrgMember, OrgRole
from app.services.auth import auth_service
from app.schemas.auth import UserCreate
from app.core.security import create_access_token

class AsyncSessionProxy:
    """Wraps a sync Session to be awaitable-compatible for async route handlers in tests."""
    def __init__(self, session):
        self._session = session
    
    async def execute(self, stmt):
        result = self._session.execute(stmt)
        return _AsyncResultProxy(result)
    
    async def commit(self):
        self._session.commit()
    
    async def refresh(self, instance):
        self._session.refresh(instance)
    
    async def flush(self):
        self._session.flush()
    
    def add(self, instance):
        self._session.add(instance)
    
    def add_all(self, instances):
        self._session.add_all(instances)
    
    def delete(self, instance):
        self._session.delete(instance)
    
    def __getattr__(self, name):
        return getattr(self._session, name)

class _AsyncResultProxy:
    def __init__(self, result):
        self._result = result
    def scalar_one_or_none(self):
        return self._result.scalar_one_or_none()
    def scalars(self):
        return self._result.scalars()
    def all(self):
        return self._result.all()
    def first(self):
        return self._result.first()
    def __getattr__(self, name):
        return getattr(self._result, name)

def test_users_settings_api():
    db = SessionLocal()
    db.commit = db.flush
    transaction = db.begin_nested() if db.in_transaction() else db.begin()
    async_db = AsyncSessionProxy(db)
    
    async def override_get_db():
        yield async_db

    async def override_get_tenant_db():
        yield async_db
            
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_tenant_db] = override_get_tenant_db
    client = TestClient(app)
    
    try:
        print("--- RUNNING INTEGRATION TESTS FOR USERS SETTINGS API ---")
        # Create a test user
        test_email = f"test-settings-{uuid.uuid4().hex[:6]}@example.com"
        user_in = UserCreate(email=test_email, password="password123", full_name="Test Settings User")
        import asyncio
        user = asyncio.run(auth_service.register_user(async_db, user_in))
        db.flush()
        
        # Get active organization
        membership = db.query(OrgMember).filter(OrgMember.user_id == user.id).first()
        active_org = db.query(Organization).filter(Organization.id == membership.org_id).first()
        
        # Generate token
        token = create_access_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. GET /api/v1/users/me
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == test_email
        assert data["user"]["full_name"] == "Test Settings User"
        assert data["active_organization"]["slug"] == active_org.slug
        print("Success: GET /me verified.")
        
        # 2. PUT /api/v1/users/me (update name and organization slug)
        new_slug = f"new-slug-{uuid.uuid4().hex[:6]}"
        response = client.put(
            "/api/v1/users/me",
            headers=headers,
            json={"full_name": "Updated User Name", "org_slug": new_slug}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["full_name"] == "Updated User Name"
        assert data["active_organization"]["slug"] == new_slug
        
        # Verify db is updated
        db.refresh(user)
        db.refresh(active_org)
        assert user.full_name == "Updated User Name"
        assert active_org.slug == new_slug
        print("Success: PUT /me updates verified.")
        
        # Test updating email to an already registered one (should fail with 400)
        other_email = f"other-{uuid.uuid4().hex[:6]}@example.com"
        other_user = User(email=other_email, password_hash="hash", full_name="Other")
        db.add(other_user)
        db.flush()
        
        response = client.put(
            "/api/v1/users/me",
            headers=headers,
            json={"email": other_email}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
        print("Success: PUT /me duplicate email rejection verified.")
        
        # Test password update (PUT /api/v1/users/me/password)
        # Invalid current password should fail
        response = client.put(
            "/api/v1/users/me/password",
            headers=headers,
            json={"current_password": "wrongpassword", "new_password": "newpassword123"}
        )
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]
        print("Success: PUT /me/password invalid password rejection verified.")
        
        # Valid current password should succeed
        response = client.put(
            "/api/v1/users/me/password",
            headers=headers,
            json={"current_password": "password123", "new_password": "newpassword123"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        print("Success: PUT /me/password update verified.")
        
        print("\nAll users settings API integration tests passed successfully!")
        
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        db.close()

if __name__ == "__main__":
    test_users_settings_api()
