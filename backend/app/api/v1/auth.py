import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token, ForgotPasswordRequest, ResetPasswordRequest, GoogleLoginRequest
from app.services.auth import auth_service
from app.core.security import create_access_token
from app.core.config import settings
from app.core.email import send_reset_password_email

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(*, db: Session = Depends(get_db), user_in: UserCreate):
    """Register a new user and create a default organization."""
    try:
        user = auth_service.register_user(db, user_in=user_in)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
def login(*, db: Session = Depends(get_db), user_in: UserLogin):
    """Authenticate user and return a JWT access token."""
    user = auth_service.authenticate(db, email=user_in.email, password=user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    *, 
    db: Session = Depends(get_db), 
    request_in: ForgotPasswordRequest,
    background_tasks: BackgroundTasks
):
    """Request a password reset link."""
    token = auth_service.request_password_reset(db, email=request_in.email)
    if token:
        reset_link = f"http://localhost:3002/reset-password?token={token}"
        
        # 🟢 Send real email in the background if enabled
        if settings.SEND_REAL_EMAILS:
            background_tasks.add_task(send_reset_password_email, request_in.email, reset_link)
            logger.info("Enqueued password reset email transmission for: %s", request_in.email)
        else:
            # Fallback to dev console logging
            logger.warning("[DEV ONLY] Reset Password Link: %s", reset_link)
            logger.warning("[DEV ONLY] (If your Vite server is running on another port, please change 3002 to your active port)")

    # Always return the same response — prevents user enumeration
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(*, db: Session = Depends(get_db), request_in: ResetPasswordRequest):
    """Reset user password using a valid reset token."""
    try:
        auth_service.process_password_reset(
            db, token=request_in.token, new_password=request_in.new_password
        )
        return {"message": "Password reset successfully."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/google-login", response_model=Token)
def google_login(*, db: Session = Depends(get_db), request_in: GoogleLoginRequest):
    """Authenticate user using Google OAuth token and return a JWT access token."""
    try:
        user = auth_service.google_login(db, token=request_in.token)
        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
