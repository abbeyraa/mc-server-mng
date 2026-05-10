from datetime import datetime, timedelta, timezone
import base64
import hashlib
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
BCRYPT_PASSWORD_MAX_BYTES = 72


def hash_password(password: str) -> str:
    return pwd_context.hash(_normalize_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(_normalize_password(plain), hashed)
    except ValueError:
        # Invalid/unsupported hash payload should be treated as auth failure.
        return False


def _normalize_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) <= BCRYPT_PASSWORD_MAX_BYTES:
        return password
    # Bcrypt truncates at 72 bytes; pre-hash long inputs to keep full entropy.
    digest = hashlib.sha256(raw).digest()
    return base64.b64encode(digest).decode("ascii")


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise ValueError("Invalid token")
