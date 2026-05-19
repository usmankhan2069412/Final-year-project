from datetime import datetime, timedelta, timezone
from typing import Union
from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, VerifyMismatchError
from app.core.config import settings

# Initialize Argon2 Password Hasher
pwd_hasher = PasswordHasher()

def get_password_hash(password: str) -> str:
    return pwd_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against the hashed password.
    Handles all Argon2 failure modes (mismatch, malformed hash).
    """
    try:
        return pwd_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError, Exception):
        return False

def create_access_token(subject: Union[str, object], expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> str | None:
    """
    Decode and verify a JWT access token.
    Returns the subject (user_id) if valid, otherwise None.
    """
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded.get("type") != "access":
            return None
        return decoded.get("sub")
    except jwt.JWTError:
        return None

def create_reset_token(email: str) -> str:
    """
    Create a short-lived JWT reset token valid for 15 minutes.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "reset"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_reset_token(token: str) -> str | None:
    """
    Verify a password reset token and return the email if valid.
    """
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded.get("type") != "reset":
            return None
        return decoded.get("sub")
    except jwt.JWTError:
        return None
