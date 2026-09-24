from fastapi import APIRouter, HTTPException

from dependencies import DbSession, MerchantId
from errors import api_error
from models import ParkingLot
from schemas import UpdatePriceSchema

router = APIRouter(tags=["merchant"])


@router.post("/updateprice")
def update_price(payload: UpdatePriceSchema, db: DbSession, user_id: MerchantId):
    """
    The manual type/range checks from the Flask version now live in
    UpdatePriceSchema, so malformed input returns 422 instead of 400.
    Everything else behaves identically.
    """

    lot = db.get(ParkingLot, payload.lot_id)

    if not lot:
        raise api_error(404, "Parking lot not found")

    if lot.user_id != user_id:
        raise api_error(403, "Unauthorized access")

    if lot.price == payload.new_price:
        raise api_error(409, "Price already set to this value")

    try:
        lot.price = payload.new_price
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"message": "Error occurred", "error": str(e)},
        )

    return {"message": "Price updated successfully"}
