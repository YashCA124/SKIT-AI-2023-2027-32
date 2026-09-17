from fastapi import APIRouter

from dependencies import MerchantId

router = APIRouter(tags=["merchant"])


@router.get("/merchantdashboard")
def merchant_dashboard(user_id: MerchantId):
    return {
        "message": "Merchant Login Approved",
        "user id": user_id,
    }
