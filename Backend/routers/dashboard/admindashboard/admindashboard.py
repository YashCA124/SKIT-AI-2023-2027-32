from fastapi import APIRouter, Depends
from core.role_check import require_role
from models import UserType

router = APIRouter(tags=["Admin"])

@router.get(
    "/admin/dashboard",
    dependencies=[Depends(require_role(UserType.ADMIN))],
)
def admin_dashboard():
    return {"message": "Admin Login Approved"}
