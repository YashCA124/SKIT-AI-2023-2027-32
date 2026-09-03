from fastapi import APIRouter, Depends

from core.security import (
    create_access_token,
    get_current_claims,
    get_current_refresh_claims,
)
from schemas.auth import TokenResponse

router = APIRouter(tags=["tokenauth"])


# ---------------------------------------------------------------------------
# GET /tokenauth/protected
# ---------------------------------------------------------------------------
@router.get("/protected")
def protected_route(claims: dict = Depends(get_current_claims)):
    return {
        "message": "Access granted",
        "user_id": claims.get("sub"),
        "role": claims.get("role"),
    }


# ---------------------------------------------------------------------------
# POST /tokenauth/refresh
# ---------------------------------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
def token_refresh(claims: dict = Depends(get_current_refresh_claims)):
    new_access_token = create_access_token(
        identity=claims.get("sub"),
        additional_claims={"role": claims.get("role")},
    )
    return {"access_token": new_access_token}
