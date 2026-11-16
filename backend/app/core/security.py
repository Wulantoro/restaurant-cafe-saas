import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import jwt, JWTError
from fastapi import status

from app.core.config import settings
from app.core.exceptions import DomainException


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(
    subject: str,
    claims: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        **claims,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str,
    claims: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    # Refresh token defaults to 7 days
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=7)
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        **claims,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise DomainException(
            code="INVALID_TOKEN",
            message="Token is invalid or expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
