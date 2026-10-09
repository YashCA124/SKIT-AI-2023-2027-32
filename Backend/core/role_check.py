from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import get_current_claims
from models import User, UserType


def require_role(required_role: UserType):
    def role_checker(claims: dict = Depends(get_current_claims)):
        if claims.get("role") != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden",
            )
        return claims

    return role_checker


def get_current_user(
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identity",
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_user_role(required_role: UserType):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.user_type != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden",
            )
        return current_user

    return role_checker