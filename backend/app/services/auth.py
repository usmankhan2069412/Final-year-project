import re
import logging
import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.models.user import User, AuthProvider
from app.models.organization import Organization, OrgMember, OrgRole
from app.models.subscription import SubscriptionPlan, Subscription
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash, verify_password, create_reset_token, verify_reset_token
from app.core.config import settings

logger = logging.getLogger(__name__)

_SLUG_CLEANUP = re.compile(r"[^a-z0-9\s-]")
_SLUG_SPACES  = re.compile(r"[\s_-]+")


def generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = _SLUG_CLEANUP.sub("", slug)
    slug = _SLUG_SPACES.sub("-", slug)
    return slug.strip("-")


class AuthService:

    @staticmethod
    async def _create_user_organization(db: AsyncSession, db_user: User, base_name: str) -> None:
        from app.services.notification import NotificationService

        base = generate_slug(base_name)
        slug = f"{base}-org"
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        if result.scalar_one_or_none():
            slug = f"{slug}-{str(uuid.uuid4())[:8]}"

        db_org = Organization(owner_id=db_user.id, slug=slug)
        db.add(db_org)
        await db.flush()

        db.add(OrgMember(org_id=db_org.id, user_id=db_user.id, role=OrgRole.OWNER))

        result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.name == "Starter"))
        starter_plan = result.scalar_one_or_none()
        if starter_plan:
            subscription = Subscription(
                org_id=db_org.id,
                plan_id=starter_plan.id,
                status="active",
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc) + timedelta(days=30),
            )
            db.add(subscription)
        else:
            logger.warning("Starter plan not found in database; subscription auto-assignment skipped.")

        await NotificationService.create_notification(
            db,
            user_id=db_user.id,
            title="Welcome to Aina AI",
            details="Your workspace has been successfully created."
        )
        await NotificationService.create_notification(
            db,
            user_id=db_user.id,
            title="Billing Activated",
            details="Free trial plan active with 10,000 complimentary credits."
        )

    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
        result = await db.execute(
            select(User).where(User.email == user_in.email, User.deleted_at == None)
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        db_user = User(
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name,
        )
        db.add(db_user)
        await db.flush()

        base_name = user_in.full_name or user_in.email.split("@")[0]
        await AuthService._create_user_organization(db, db_user, base_name)

        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.email == email, User.deleted_at == None)
        )
        db_user = result.scalar_one_or_none()
        if not db_user or not db_user.password_hash:
            return None
        if not verify_password(password, db_user.password_hash):
            return None
        return db_user

    @staticmethod
    async def request_password_reset(db: AsyncSession, email: str) -> Optional[str]:
        result = await db.execute(
            select(User).where(User.email == email, User.deleted_at == None)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        token = create_reset_token(email)
        logger.info("Password reset token generated for user id=%s", db_user.id)
        return token

    @staticmethod
    async def process_password_reset(db: AsyncSession, token: str, new_password: str) -> User:
        email = verify_reset_token(token)
        if not email:
            raise ValueError("Invalid or expired password reset token")

        result = await db.execute(
            select(User).where(User.email == email, User.deleted_at == None)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise ValueError("Invalid or expired password reset token")

        db_user.password_hash = get_password_hash(new_password)
        await db.commit()
        await db.refresh(db_user)
        logger.info("Password reset completed for user id=%s", db_user.id)
        return db_user

    @staticmethod
    async def google_login(db: AsyncSession, token: str) -> User:
        try:
            tokeninfo_resp = httpx.get(
                f"https://oauth2.googleapis.com/tokeninfo?access_token={token}",
                timeout=10.0
            )
            if tokeninfo_resp.status_code != 200:
                raise ValueError("Invalid Google token")

            token_info = tokeninfo_resp.json()
            logger = logging.getLogger("app.services.auth")
            logger.info(f"Tokeninfo response: {token_info}")
            logger.info(f"Configured GOOGLE_CLIENT_ID: {settings.GOOGLE_CLIENT_ID}")

            aud = token_info.get("aud") or token_info.get("issued_to") or token_info.get("azp")

            if aud != settings.GOOGLE_CLIENT_ID:
                clean_aud = str(aud).strip()
                clean_config = str(settings.GOOGLE_CLIENT_ID).strip()
                if clean_aud != clean_config:
                    raise ValueError(f"Token audience mismatch. Expected: {clean_config}, Got: {clean_aud}")

            userinfo_resp = httpx.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            if userinfo_resp.status_code != 200:
                raise ValueError("Failed to retrieve user info")

            idinfo = userinfo_resp.json()
            email = idinfo['email']
            full_name = idinfo.get('name', '')

            result = await db.execute(
                select(User).where(User.email == email, User.deleted_at == None)
            )
            db_user = result.scalar_one_or_none()

            if db_user:
                return db_user

            db_user = User(
                email=email,
                full_name=full_name,
                auth_provider=AuthProvider.GOOGLE,
            )
            db.add(db_user)
            await db.flush()

            base_name = full_name or email.split("@")[0]
            await AuthService._create_user_organization(db, db_user, base_name)

            await db.commit()
            await db.refresh(db_user)
            logger.info("New user created via Google login id=%s", db_user.id)
            return db_user

        except Exception as e:
            logger.error(f"Google login failed: {e}")
            raise ValueError(f"Invalid Google token: {str(e)}")


auth_service = AuthService()
