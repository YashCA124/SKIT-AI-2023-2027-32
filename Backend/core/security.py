import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from .redis_client import redis_client

# --- Config (mirrors Flask-JWT-Extended defaults) -------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRES = timedelta(days=30)

bearer_scheme = HTTPBearer()


def _create_token(
    identity: str,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: Optional[dict] = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": identity,
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + expires_delta,
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(identity: str, additional_claims: Optional[dict] = None) -> str:
    return _create_token(identity, "access", ACCESS_TOKEN_EXPIRES, additional_claims)


def create_refresh_token(identity: str, additional_claims: Optional[dict] = None) -> str:
    return _create_token(identity, "refresh", REFRESH_TOKEN_EXPIRES, additional_claims)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def blacklist_token(jti: str, expires_seconds: int = 3600) -> None:
    """Equivalent of redis_client.setex(f"blacklist:{jti}", 3600, "true")"""
    redis_client.setex(f"blacklist:{jti}", expires_seconds, "true")


def _is_blacklisted(jti: str) -> bool:
    return redis_client.get(f"blacklist:{jti}") is not None


def _get_claims(
    credentials: HTTPAuthorizationCredentials, expected_type: str
) -> dict:
    claims = decode_token(credentials.credentials)

    if claims.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{expected_type.capitalize()} token required",
        )

    if _is_blacklisted(claims.get("jti", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    return claims


def get_current_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Equivalent of @jwt_required() -> use with get_jwt() / get_jwt_identity()."""
    return _get_claims(credentials, expected_type="access")


def get_current_refresh_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Equivalent of @jwt_required(refresh=True)."""
    return _get_claims(credentials, expected_type="refresh")
