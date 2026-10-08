from fastapi import APIRouter, Depends

from core.role_check import require_role
from models.user_type import UserType

router = APIRouter(tags=["merchant"])

@router.get(
    "/merchantdashboard", 
    dependencies=[Depends(require_role(UserType.MERCHANT))]
)
def merchant_dashboard():
    return {
        "message": "Merchant Dashboard"
    }