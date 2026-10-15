from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from core.db import get_db
from models import ParkingLot
from core.qrcode import generate_parking_qr

router = APIRouter()

@router.get("/parking-lots/{lot_id}/qr")
def get_parking_lot_qr(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    lot = db.query(ParkingLot).filter(
        ParkingLot.id == lot_id,
        ParkingLot.user_id == current_user.id,
    ).first()

    if not lot:
        raise HTTPException(
            status_code=404,
            detail="Parking lot not found",
        )

    png = generate_parking_qr(lot.qr_token)

    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Content-Disposition":
                f'inline; filename="parking-lot-{lot.id}-qr.png"'
        },
    )