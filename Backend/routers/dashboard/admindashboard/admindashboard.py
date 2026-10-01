from fastapi import APIRouter, Depends
from rolecheck.role_required import require_role
from models import UserType

router = APIRouter(tags=["Admin"])


@router.get(
    "/admin/dashboard",
    dependencies=[Depends(require_role(UserType.ADMIN))],
)
def admin_dashboard():
    return {"message": "Admin Login Approved"}
