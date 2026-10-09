import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from geoalchemy2.elements import WKTElement
from forex_python.converter import CurrencyRates, RatesNotAvailableError

from core.db import get_db
from core.role_check import require_user_role
from core.redis_client import redis_client
from currency import currency
# from background_tasks import send_email_task
from models import (
    ParkingLot, User, Floor, ParkingSpot,
    ParkingBooking, UserType, BookingStatus, AvailableStatus
)
from schemas import (
    BookingSearchSchema, BookingSearchResponse,
    BookingCreateSchema, BookingCreateResponse
)

router = APIRouter(prefix="/booking", tags=["Booking"])

def get_exchange_rate(lot_currency: str, user_currency: str) -> float:
    rate_key = f"exchange:{lot_currency}:{user_currency}"
    cached = redis_client.get(rate_key)
    if cached:
        return float(cached)

    c = CurrencyRates()
    try:
        rate = c.get_rate(lot_currency, user_currency)
        redis_client.setex(rate_key, 3600, rate)
        return rate
    except RatesNotAvailableError:
        return 1.0

def get_floor_available_spots(db: Session, floor_id: int) -> int:
    floor_key = f"floor:{floor_id}:available_spots"
    cached = redis_client.get(floor_key)
    if cached is not None:
        return int(cached)

    count = db.query(func.count(ParkingSpot.id)).filter(
        ParkingSpot.floor_id == floor_id,
        ParkingSpot.status == BookingStatus.SPOT_AVAILABLE
    ).scalar()

    redis_client.setex(floor_key, 300, count)
    return count

@router.post("/search", response_model=BookingSearchResponse)
def search_nearby_parking(
    data: BookingSearchSchema,
    current_user: User = Depends(
        require_user_role(UserType.PARKING_USER)
    ),
    db: Session = Depends(get_db),
):
    radius_km = data.radius_km
    radius_m = radius_km * 1000

    user_coords = db.query(
        func.ST_Y(User.current_location),
        func.ST_X(User.current_location)
    ).filter(User.id == current_user.id).first()

    if not user_coords or not all(user_coords):
        raise HTTPException(status_code=400, detail="User location not set")

    user_lat, user_lng = user_coords
    lat, lng = round(user_lat, 3), round(user_lng, 3)
    cache_key = f"user:{current_user.id}:nearby_lots:{lat}:{lng}:{radius_km}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    user_point = WKTElement(f"POINT({user_lng} {user_lat})", srid=4326)
    distance_expr = func.ST_DistanceSphere(
        ParkingLot.location_coordinates, user_point
    ).label("distance")

    lots_with_distance = db.query(ParkingLot, distance_expr).filter(
        ParkingLot.location_coordinates.isnot(None),
        ParkingLot.available == AvailableStatus.ACTIVE,
        func.ST_DWithin(ParkingLot.location_coordinates, user_point, radius_m)
    ).all()

    if not lots_with_distance:
        raise HTTPException(status_code=404, detail="No parking found in this range")

    results = []
    conversion_applied_any = False

    for lot, distance in lots_with_distance:
        total_available_spots = sum(
            get_floor_available_spots(db, f.id)
            for f in lot.floors
            if f.available == AvailableStatus.ACTIVE
        )

        if total_available_spots == 0:
            continue

        distance_km = round(distance / 1000, 2)
        eta_minutes = max(1, round((distance_km / 30) * 60))

        lot_currency = currency.get(lot.country)
        if not lot_currency:
            continue

        converted_price = float(lot.price)
        exchange_rate = 1.0
        final_currency = lot_currency
        conversion_applied = False

        if current_user.country_code != lot.country:
            user_currency = currency.get(current_user.country_code)
            if user_currency:
                exchange_rate = get_exchange_rate(lot_currency, user_currency)
                converted_price *= exchange_rate
                final_currency = user_currency
                conversion_applied = True

        conversion_applied_any |= conversion_applied

        results.append({
            "lot_id": lot.id,
            "location_name": lot.location_name,
            "original_price": float(lot.price),
            "original_currency": lot_currency,
            "converted_price": round(converted_price, 2),
            "user_currency": final_currency,
            "exchange_rate": round(exchange_rate, 4),
            "distance_km": distance_km,
            "eta_minutes": eta_minutes,
            "available_spots": total_available_spots,
            "address": lot.full_address
        })

    if not results:
        raise HTTPException(status_code=404, detail="No available spots in this range")

    results.sort(key=lambda x: (x["converted_price"], x["distance_km"]))

    response = {
        "radius_km": radius_km,
        "total_results": len(results),
        "parking_lots": results,
        "conversion": conversion_applied_any
    }

    redis_client.setex(cache_key, 30, json.dumps(response))
    return response

@router.post("", response_model=BookingCreateResponse, status_code=status.HTTP_200_OK)
def create_booking(
    data: BookingCreateSchema,
    current_user: User = Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db)
):
    active_key = f"user:{current_user.id}:active_booking"
    if redis_client.get(active_key):
        raise HTTPException(status_code=400, detail="User already has an active booking")

    floor_key = None
    try:
        lot = db.query(ParkingLot).filter(
            ParkingLot.id == data.lot_id,
            ParkingLot.available == AvailableStatus.ACTIVE
        ).first()
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")

        floor = db.query(Floor).filter(
            Floor.parking_lot_id == data.lot_id,
            Floor.id == data.floor_id,
            Floor.available == AvailableStatus.ACTIVE
        ).first()
        if not floor:
            raise HTTPException(status_code=404, detail="Floor not found")

        floor_key = f"floor:{floor.id}:available_spots"
        available_spots = get_floor_available_spots(db, floor.id)
        if available_spots <= 0:
            raise HTTPException(status_code=400, detail="No spots available")

        spot = db.execute(
            select(ParkingSpot)
            .where(
                ParkingSpot.id == data.spot_id,
                ParkingSpot.floor_id == floor.id,
                ParkingSpot.available == AvailableStatus.ACTIVE
            )
            .with_for_update()
        ).scalar_one_or_none()

        if not spot:
            raise HTTPException(status_code=404, detail="Spot not found")

        if spot.status == BookingStatus.SPOT_BOOKED:
            raise HTTPException(status_code=400, detail="Spot already booked")

        spot.status = BookingStatus.SPOT_BOOKED

        lot_currency = currency.get(lot.country)
        final_currency = lot_currency
        cost_per_unit = float(lot.price)
        exchange_rate = 1.0

        if current_user.country_code != lot.country:
            user_currency = currency.get(current_user.country_code)
            if user_currency:
                exchange_rate = get_exchange_rate(lot_currency, user_currency)
                cost_per_unit *= exchange_rate
                final_currency = user_currency

        reservation = ParkingBooking(
            spot_id=spot.id,
            user_id=current_user.id,
            cost_per_unit=cost_per_unit,
            parking_timezone=data.timezone,
            currency=final_currency,
            exchange_rate=exchange_rate,
            parking_timestamp=data.parking_timestamp,
            leaving_timestamp=data.leaving_timestamp
        )

        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        redis_client.decr(floor_key)
        redis_client.setex(active_key, 3600, reservation.id)
        redis_client.delete(f"user:{current_user.id}:active_dashboard:v1")

        # subject = f"Booking #{reservation.id} Confirmed"
        # body = (
        #     f"Your parking booking #{reservation.id} is confirmed.\n"
        #     f"Spot: {spot.full_spot_id}\n"
        #     f"Cost: {round(reservation.cost_per_unit, 2)} {reservation.currency}\n"
        #     f"Parking time: {reservation.get_local_parking_timestamp}\n\n"
        #     "Thank you for using our parking service!"
        # )
        # send_email_task.delay(current_user.email, subject, body)

        return {
            "message": "Booking Successful",
            "booking": {
                "booking_id": reservation.id,
                "spot": spot.full_spot_id,
                "cost": round(reservation.cost_per_unit, 2),
                "parking_timestamp": reservation.get_local_parking_timestamp
            }
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        if floor_key:
            redis_client.incr(floor_key)
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")