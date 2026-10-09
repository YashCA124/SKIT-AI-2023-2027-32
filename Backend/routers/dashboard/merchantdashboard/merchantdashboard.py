from fastapi import APIRouter, Depends

from core.role_check import require_user_role
from models import User, UserType

router = APIRouter(tags=["merchant"])


@router.get("/merchantdashboard")
def merchant_dashboard(
    current_user: User = Depends(
        require_user_role(UserType.MERCHANT)
    ),
):
    return {
        "message": "Merchant Dashboard",
        "user_id": current_user.id,
        "name": current_user.name,
        "role": current_user.user_type.value,
    }