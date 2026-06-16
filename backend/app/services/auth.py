import re
import logging
import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
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
    """Generate a clean, URL-safe lowercase slug (ASCII only)."""
    slug = name.lower().strip()
    slug = _SLUG_CLEANUP.sub("", slug)   # only a-z, 0-9, spaces, hyphens
    slug = _SLUG_SPACES.sub("-", slug)   # collapse spaces/underscores/hyphens
    return slug.strip("-")


class AuthService:

    @staticmethod
    def _create_user_organization(db: Session, db_user: User, base_name: str) -> None:
        """Helper to provision default org, subscription, and notifications for a new user."""
        from app.services.notification import NotificationService

        # Generate unique org slug
        base = generate_slug(base_name)
        slug = f"{base}-org"
        if db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{slug}-{str(uuid.uuid4())[:8]}"

        # Create organization + owner membership
        db_org = Organization(owner_id=db_user.id, slug=slug)
        db.add(db_org)
        db.flush()

        db.add(OrgMember(org_id=db_org.id, user_id=db_user.id, role=OrgRole.OWNER))

        # Auto-assign Starter plan
        starter_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == "Starter").first()
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

        # Seed welcome notifications in DB
        NotificationService.create_notification(
            db,
            user_id=db_user.id,
            title="Welcome to Aina AI",
            details="Your workspace has been successfully created."
        )
        NotificationService.create_notification(
            db,
            user_id=db_user.id,
            title="Billing Activated",
            details="Free trial plan active with 10,000 complimentary credits."
        )


    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """
        Register a new user, create a default organization, and assign them as OWNER.
        """
        # Check if email is already in use by an active (non-deleted) account
        existing = db.query(User).filter(
            User.email == user_in.email,
            User.deleted_at == None  # noqa: E711
        ).first()
        if existing:
            raise ValueError("Email already registered")

        # Create user
        db_user = User(
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name,
        )
        db.add(db_user)
        db.flush()  # Populates db_user.id

        base_name = user_in.full_name or user_in.email.split("@")[0]
        AuthService._create_user_organization(db, db_user, base_name)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        Returns None for both 'user not found' and 'wrong password' to prevent enumeration.
        """
        db_user = db.query(User).filter(
            User.email == email,
            User.deleted_at == None  # noqa: E711
        ).first()
        if not db_user or not db_user.password_hash:
            return None
        if not verify_password(password, db_user.password_hash):
            return None
        return db_user

    @staticmethod
    def request_password_reset(db: Session, email: str) -> Optional[str]:
        """
        Generate a short-lived reset token if the email belongs to an active user.
        Caller must NOT reveal whether the email exists.
        """
        db_user = db.query(User).filter(
            User.email == email,
            User.deleted_at == None  # noqa: E711
        ).first()
        if not db_user:
            return None
        token = create_reset_token(email)
        logger.info("Password reset token generated for user id=%s", db_user.id)
        return token

    @staticmethod
    def process_password_reset(db: Session, token: str, new_password: str) -> User:
        """
        Verify the reset token and update the user's password securely.
        Raises ValueError for any invalid/expired token or missing user.
        """
        email = verify_reset_token(token)
        if not email:
            raise ValueError("Invalid or expired password reset token")

        db_user = db.query(User).filter(
            User.email == email,
            User.deleted_at == None  # noqa: E711
        ).first()
        if not db_user:
            raise ValueError("Invalid or expired password reset token")  # don't reveal 'user not found'

        db_user.password_hash = get_password_hash(new_password)
        db.commit()
        db.refresh(db_user)
        logger.info("Password reset completed for user id=%s", db_user.id)
        return db_user

    @staticmethod
    def google_login(db: Session, token: str) -> User:
        """
        Verify Google access token and log the user in.
        Creates a new user and default organization if they don't exist.
        """
        try:
            # 1. Verify token audience to prevent Confused Deputy attacks
            tokeninfo_resp = httpx.get(
                f"https://oauth2.googleapis.com/tokeninfo?access_token={token}",
                timeout=10.0
            )
            if tokeninfo_resp.status_code != 200:
                raise ValueError("Invalid Google token")
            
            token_info = tokeninfo_resp.json()
            import logging
            logger = logging.getLogger("app.services.auth")
            logger.info(f"Tokeninfo response: {token_info}")
            logger.info(f"Configured GOOGLE_CLIENT_ID: {settings.GOOGLE_CLIENT_ID}")
            
            # Check multiple potential client ID fields in tokeninfo
            aud = token_info.get("aud") or token_info.get("issued_to") or token_info.get("azp")
            
            if aud != settings.GOOGLE_CLIENT_ID:
                # Fallback check: sometimes one has a suffix or prefix, or is missing.
                # Let's check if the client IDs match when stripped/cleaned
                clean_aud = str(aud).strip()
                clean_config = str(settings.GOOGLE_CLIENT_ID).strip()
                if clean_aud != clean_config:
                    raise ValueError(f"Token audience mismatch. Expected: {clean_config}, Got: {clean_aud}")
            
            # 2. Retrieve user profile info securely
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

            db_user = db.query(User).filter(
                User.email == email,
                User.deleted_at == None  # noqa: E711
            ).first()

            if db_user:
                return db_user

            # Create user
            db_user = User(
                email=email,
                full_name=full_name,
                auth_provider=AuthProvider.GOOGLE,
            )
            db.add(db_user)
            db.flush()

            base_name = full_name or email.split("@")[0]
            AuthService._create_user_organization(db, db_user, base_name)

            db.commit()
            db.refresh(db_user)
            logger.info("New user created via Google login id=%s", db_user.id)
            return db_user

        except Exception as e:
            logger.error(f"Google login failed: {e}")
            raise ValueError(f"Invalid Google token: {str(e)}")


auth_service = AuthService()
