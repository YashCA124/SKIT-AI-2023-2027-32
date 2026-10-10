from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db import get_db
from core.role_check import require_user_role
from models import ParkingLot, User, UserType
from schemas import UpdatePriceSchema

router = APIRouter(tags=["merchant"])


@router.post("/updateprice")
def update_price(
    payload: UpdatePriceSchema,
    current_user: User = Depends(
        require_user_role(UserType.MERCHANT)
    ),
    db: Session = Depends(get_db),
):
    lot = db.get(ParkingLot, payload.lot_id)

    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking lot not found",
        )

    if lot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access",
        )

    if lot.price == payload.new_price:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Price already set to this value",
        )

    try:
        lot.price = payload.new_price
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while updating price",
        )

    return {"message": "Price updated successfully"}