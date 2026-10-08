from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.db import get_db
from core.role_check import require_role
# from background_tasks import send_email_task
from models import (
    ParkingBooking, ParkingLot, Floor, ParkingSpot,
    BookingStatus, UserType, AvailableStatus, User
)
from schemas import ExtendBookingSchema, ExtendBookingResponse

router = APIRouter(prefix="/booking", tags=["Booking Extension"])

@router.post("/extend", response_model=ExtendBookingResponse)
def extend_booking(
    data: ExtendBookingSchema,
    current_user: User = Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db)
):
    try:
        lot = db.query(ParkingLot).filter(
            ParkingLot.id == data.lot_id,
            ParkingLot.available.in_([AvailableStatus.ACTIVE, AvailableStatus.PENDING])
        ).first()
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")

        floor = db.query(Floor).filter(
            Floor.parking_lot_id == data.lot_id,
            Floor.floor_id == data.floor_id,
            Floor.available.in_([AvailableStatus.ACTIVE, AvailableStatus.PENDING])
        ).first()
        if not floor:
            raise HTTPException(status_code=404, detail="Floor not found")

        spot = db.query(ParkingSpot).filter(
            ParkingSpot.floor_id == floor.id,
            ParkingSpot.spot_id == data.spot_id,
            ParkingSpot.available.in_([AvailableStatus.ACTIVE, AvailableStatus.PENDING])
        ).first()
        if not spot:
            raise HTTPException(status_code=404, detail="Spot not found")

        booking = db.query(ParkingBooking).filter(
            ParkingBooking.user_id == current_user.id,
            ParkingBooking.spot_id == spot.id,
            ParkingBooking.status == BookingStatus.BOOKING_ACTIVE
        ).with_for_update().first()

        if not booking:
            raise HTTPException(status_code=404, detail="No active booking found")

        current_leaving = booking.leaving_timestamp
        current_parking = booking.parking_timestamp

        if data.new_leaving_timestamp <= current_leaving:
            raise HTTPException(
                status_code=400,
                detail="New leaving must be after current leaving"
            )

        overlapping = db.query(ParkingBooking).filter(
            ParkingBooking.spot_id == spot.id,
            ParkingBooking.id != booking.id,
            ParkingBooking.status == BookingStatus.BOOKING_ACTIVE,
            ParkingBooking.parking_timestamp < data.new_leaving_timestamp,
            ParkingBooking.leaving_timestamp > current_parking
        ).first()

        if overlapping:
            raise HTTPException(status_code=400, detail="Conflicting booking exists")

        booking.leaving_timestamp = data.new_leaving_timestamp
        db.commit()

        # send_email_task.delay(
        #     current_user.email,
        #     f"Booking #{booking.id} Extended",
        #     f"New leaving time: {data.new_leaving_timestamp.isoformat()}"
        # )

        return {
            "message": "Booking extended successfully",
            "booking_id": booking.id,
            "previous_leaving_timestamp": current_leaving.isoformat(),
            "new_leaving_timestamp": data.new_leaving_timestamp.isoformat()
        }

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extend booking: {str(e)}"
        )