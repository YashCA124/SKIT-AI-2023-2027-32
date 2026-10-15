from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from core.db import get_db
from models import ParkingLot, Booking, AvailableStatus, BookingStatus
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/booking", tags=["Booking Extension"])

@router.post("/parking/scan/{qr_token}")
def verify_parking_booking(
    qr_token: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    lot = db.query(ParkingLot).filter(
        ParkingLot.qr_token == qr_token,
    ).first()

    if not lot:
        raise HTTPException(
            status_code=404,
            detail="Invalid parking lot QR code",
        )

    if lot.available != AvailableStatus.ACTIVE:
        raise HTTPException(
            status_code=409,
            detail="This parking lot is not available",
        )

    now = datetime.now(timezone.utc)

    booking = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.parking_lot_id == lot.id,
        Booking.status == BookingStatus.CONFIRMED,
        Booking.start_time <= now,
        Booking.end_time > now,
    ).with_for_update().first()

    if not booking:
        raise HTTPException(
            status_code=403,
            detail="No valid booking found for this parking lot",
        )

    # Update to the checked-in state in your transaction.
    booking.status = BookingStatus.CHECKED_IN
    booking.checked_in_at = now

    db.commit()

    return {
        "success": True,
        "message": "Booking verified. Welcome!",
        "parking_lot": lot.location_name,
        "booking_id": booking.id,
        "checked_in_at": now.isoformat(),
    }