import sys
import os
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

import app.db.base
from app.db.session import SessionLocal
from app.api.deps import get_current_user_or_api_key
from app.models.user import User
from app.models.organization import Organization, OrgMember, OrgRole
from app.models.subscription import SubscriptionPlan, Subscription
from app.services.auth import auth_service
from app.services.billing import BillingService, QuotaGuard
from app.services.team import TeamService
from app.services.api_key import ApiKeyService
from app.schemas.auth import UserCreate

class MockRequest:
    def __init__(self, headers):
        self.headers = headers

async def run_tests():
    db = SessionLocal()
    # Mock commit so we don't commit to DB during tests
    db.commit = db.flush
    
    # Start a transaction
    transaction = db.begin_nested() if db.in_transaction() else db.begin()
    
    try:
        print("--- RUNNING INTEGRATION TESTS FOR PHASE 6 SERVICES ---")
        
        # 1. Test normal registration assigns Starter Plan
        test_email = f"test-register-{uuid.uuid4().hex[:6]}@example.com"
        user_in = UserCreate(email=test_email, password="password123", full_name="Test User")
        
        user = auth_service.register_user(db, user_in)
        assert user.id is not None
        print(f"Created user: {user.email}")
        
        # Retrieve org for the user
        membership = db.query(OrgMember).filter(OrgMember.user_id == user.id).first()
        assert membership is not None
        assert membership.role == OrgRole.OWNER
        
        org = db.query(Organization).filter(Organization.id == membership.org_id).first()
        assert org is not None
        print(f"Created organization: {org.slug}")
        
        # Verify active subscription to Starter plan
        sub = db.query(Subscription).filter(
            Subscription.org_id == org.id,
            Subscription.status == "active"
        ).first()
        assert sub is not None
        assert sub.plan.name == "Starter"
        print("Success: Auto-assigned Starter plan on registration verified.")

        # Set tenant context for RLS
        db.execute(
            text("SELECT set_config('app.current_org_id', :org_id, true)"),
            {"org_id": str(org.id)}
        )

        # 2. Test Billing Service
        # List plans
        plans = BillingService.get_plans(db)
        assert len(plans) >= 3
        prof_plan = next(p for p in plans if p.name == "Professional")
        print(f"Found plans: {[p.name for p in plans]}")

        # Get subscription
        sub_resp = BillingService.get_subscription(db, org.id)
        assert sub_resp.plan.name == "Starter"
        assert sub_resp.status == "active"
        print("Success: get_subscription returned active Starter plan.")

        # Subscribe to Professional
        sub_resp = BillingService.subscribe(db, org.id, prof_plan.id)
        assert sub_resp.plan.name == "Professional"
        assert sub_resp.status == "active"
        print("Success: subscribe upgraded organization to Professional.")

        # Quota checks
        assert QuotaGuard.check_quota(db, org.id, "bots") is True
        assert QuotaGuard.check_quota(db, org.id, "members") is True
        print("Success: QuotaGuard checks passed.")

        # Billing history
        history = BillingService.get_billing_history(db, org.id)
        assert len(history) >= 2
        print(f"Success: Billing history returned {len(history)} items.")

        # Cancel subscription
        sub_resp = BillingService.cancel_subscription(db, org.id)
        assert sub_resp.status == "cancelled"
        print("Success: cancel_subscription cancelled the active plan.")

        # 3. Test Team Service
        # Invite a member (existing user)
        other_user = User(email=f"other-{uuid.uuid4().hex[:6]}@example.com", full_name="Other User", password_hash="fake")
        db.add(other_user)
        db.flush()

        member_resp = await TeamService.invite_member(db, org.id, other_user.email, "member")
        assert member_resp is not None
        assert member_resp.email == other_user.email
        assert member_resp.role == "member"
        print("Success: invite_member added existing user to org.")

        # Get members
        members = TeamService.get_members(db, org.id)
        assert len(members) == 2
        print(f"Success: get_members returned {len(members)} members.")

        # Update role to admin
        updated_member = TeamService.update_role(db, org.id, member_resp.id, "admin")
        assert updated_member.role == "admin"
        print("Success: update_role changed member role to admin.")

        # Remove member
        success = TeamService.remove_member(db, org.id, member_resp.id)
        assert success is True
        print("Success: remove_member removed member from org.")

        # 4. Test API Key Service
        # Create key
        key_resp = ApiKeyService.create_key(db, org.id, "Test Key")
        assert key_resp.name == "Test Key"
        assert key_resp.key.startswith("ak_prod_")
        print("Success: create_key generated API key.")

        # List keys
        keys = ApiKeyService.list_keys(db, org.id)
        assert len(keys) == 1
        assert keys[0].status == "active"
        print("Success: list_keys returned active keys.")

        # Test API Key Authentication
        # Test with valid key
        req = MockRequest({"X-API-Key": key_resp.key})
        auth_user = get_current_user_or_api_key(req, db)
        assert auth_user.id == user.id
        print("Success: get_current_user_or_api_key authenticated valid API key.")

        # Revoke key
        ApiKeyService.revoke_key(db, org.id, key_resp.id)
        print("Success: revoke_key set revoked_at on the key.")

        # Test with revoked key (should raise HTTPException 401)
        try:
            get_current_user_or_api_key(req, db)
            assert False, "Should have raised 401 for revoked key"
        except Exception as e:
            assert hasattr(e, "status_code") and e.status_code == 401
            print("Success: get_current_user_or_api_key rejected revoked key.")

        print("\nAll Phase 6 service integration tests passed successfully!")

    finally:
        transaction.rollback()
        db.close()

if __name__ == "__main__":
    asyncio.run(run_tests())
