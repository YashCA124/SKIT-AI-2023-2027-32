from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.elements import WKTElement
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from core.db import get_db
from core.security import get_current_claims
from models import (
    Admin,
    AvailableStatus,
    BookingStatus,
    Floor,
    ParkingBooking,
    ParkingLot,
    ParkingSpot,
    User,
    UserType,
)
from schemas.parking import BookingCreate, LotCreate, LotStatusUpdate, LotUpdate, UserRoleUpdate

router = APIRouter(prefix="/api")


def _role_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def current_principal(
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db),
) -> dict:
    role = claims.get("role")
    identity = claims.get("sub")

    if role == UserType.ADMIN.value:
        admin = db.query(Admin).filter_by(username=identity).first()
        if admin is None:
            raise HTTPException(status_code=401, detail="Administrator account no longer exists")
        return {"id": admin.id, "name": admin.username, "role": role, "admin": admin}

    try:
        user_id = int(identity)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid account identity") from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return {
        "id": user.id,
        "name": user.name,
        "role": _role_value(user.user_type),
        "user": user,
    }


def require_role(required_role: UserType):
    def dependency(principal: dict = Depends(current_principal)) -> dict:
        if principal["role"] != required_role.value:
            raise HTTPException(status_code=403, detail="This account is not permitted to access this feature")
        return principal

    return dependency


def _spot_available(spot: ParkingSpot) -> bool:
    return (
        _role_value(spot.available) == AvailableStatus.ACTIVE.value
        and _role_value(spot.status) == BookingStatus.SPOT_AVAILABLE.value
    )


def _lot_payload(lot: ParkingLot, include_owner: bool = False) -> dict:
    floors = sorted(lot.floors, key=lambda item: item.floor_id)
    all_spots = [spot for floor in floors for spot in floor.spots]
    available_spaces = [
        {"id": spot.id, "label": spot.full_spot_id}
        for floor in floors
        if _role_value(floor.available) == AvailableStatus.ACTIVE.value
        for spot in floor.spots
        if _spot_available(spot)
    ]
    payload = {
        "id": lot.id,
        "location_name": lot.location_name,
        "price": float(lot.price),
        "currency": lot.currency,
        "country": lot.country,
        "city": lot.city,
        "state": lot.state,
        "address": lot.address,
        "pincode": lot.pincode,
        "available": _role_value(lot.available),
        "floor_count": len(floors),
        "total_spots": len(all_spots),
        "available_spots": len(available_spaces),
        "available_spaces": available_spaces,
        "floors": [
            {
                "id": floor.id,
                "floor_id": floor.floor_id,
                "label": floor.label,
                "total_spots": len(floor.spots),
                "available_spots": (
                    sum(1 for spot in floor.spots if _spot_available(spot))
                    if _role_value(floor.available) == AvailableStatus.ACTIVE.value
                    else 0
                ),
                "available_spaces": (
                    [
                        {"id": spot.id, "label": spot.full_spot_id}
                        for spot in floor.spots
                        if _spot_available(spot)
                    ]
                    if _role_value(floor.available) == AvailableStatus.ACTIVE.value
                    else []
                ),
            }
            for floor in floors
        ],
    }
    if include_owner:
        payload["owner_id"] = lot.user_id
        payload["owner_name"] = lot.owner.name if lot.owner else None
    return payload


def _booking_payload(booking: ParkingBooking) -> dict:
    spot = booking.spot
    floor = spot.floor
    lot = floor.parking_lot
    return {
        "id": booking.id,
        "spot_id": spot.id,
        "spot_label": spot.full_spot_id,
        "parking_timestamp": booking.parking_timestamp.isoformat(),
        "leaving_timestamp": (
            booking.leaving_timestamp.isoformat() if booking.leaving_timestamp else None
        ),
        "parking_timezone": booking.parking_timezone,
        "status": _role_value(booking.status),
        "lot": {
            "id": lot.id,
            "name": lot.location_name,
            "address": lot.full_address,
        },
        "cost_per_unit": float(booking.cost_per_unit),
        "currency": booking.currency,
        "total_cost": (
            float(booking.get_total_cost) if booking.get_total_cost is not None else None
        ),
    }


def _loaded_lots(db: Session):
    return db.query(ParkingLot).options(
        selectinload(ParkingLot.floors).selectinload(Floor.spots),
        selectinload(ParkingLot.owner),
    )


@router.get("/account")
def get_account(principal: dict = Depends(current_principal)):
    if principal["role"] == UserType.ADMIN.value:
        return {"id": principal["id"], "name": principal["name"], "role": principal["role"]}

    user = principal["user"]
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone_no": user.phone_no,
        "address": user.address,
        "pincode": user.pincode,
        "city": user.city,
        "state": user.state,
        "country": user.country,
        "role": principal["role"],
    }


@router.get("/parking/lots")
def search_parking_lots(
    city: str | None = Query(default=None, max_length=100),
    _principal: dict = Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db),
):
    query = _loaded_lots(db).filter(ParkingLot.available == AvailableStatus.ACTIVE)
    if city and city.strip():
        query = query.filter(ParkingLot.city.ilike(f"%{city.strip()}%"))
    lots = query.order_by(ParkingLot.location_name).all()
    return {"parking_lots": [_lot_payload(lot) for lot in lots]}


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    principal: dict = Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db),
):
    spot = (
        db.query(ParkingSpot)
        .filter_by(id=payload.spot_id)
        .with_for_update()
        .first()
    )
    if spot is None:
        raise HTTPException(status_code=404, detail="Parking space was not found")
    lot = spot.floor.parking_lot
    if (
        _role_value(lot.available) != AvailableStatus.ACTIVE.value
        or _role_value(spot.floor.available) != AvailableStatus.ACTIVE.value
        or not _spot_available(spot)
    ):
        raise HTTPException(status_code=409, detail="This parking space is no longer available")

    booking = ParkingBooking(
        spot_id=spot.id,
        user_id=principal["id"],
        parking_timestamp=datetime.now(timezone.utc),
        parking_timezone=payload.parking_timezone,
        cost_per_unit=lot.price,
        status=BookingStatus.BOOKING_ACTIVE,
        currency=lot.currency,
        exchange_rate=Decimal("1.0000"),
    )
    spot.status = BookingStatus.SPOT_BOOKED
    db.add(booking)
    try:
        db.commit()
        db.refresh(booking)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This parking space was booked by another driver") from exc
    return _booking_payload(booking)


@router.get("/bookings")
def get_bookings(
    principal: dict = Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db),
):
    bookings = (
        db.query(ParkingBooking)
        .options(
            selectinload(ParkingBooking.spot)
            .selectinload(ParkingSpot.floor)
            .selectinload(Floor.parking_lot)
        )
        .filter_by(user_id=principal["id"])
        .order_by(ParkingBooking.parking_timestamp.desc())
        .all()
    )
    return {"bookings": [_booking_payload(booking) for booking in bookings]}


@router.post("/bookings/{booking_id}/end")
def end_booking(
    booking_id: int,
    principal: dict = Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(ParkingBooking)
        .filter_by(
            id=booking_id,
            user_id=principal["id"],
            status=BookingStatus.BOOKING_ACTIVE,
        )
        .with_for_update()
        .first()
    )
    if booking is None:
        raise HTTPException(status_code=404, detail="Active booking was not found")

    booking.leaving_timestamp = datetime.now(timezone.utc)
    booking.status = BookingStatus.BOOKING_COMPLETED
    booking.spot.status = BookingStatus.SPOT_AVAILABLE
    db.commit()
    db.refresh(booking)
    return _booking_payload(booking)


@router.get("/merchant/lots")
def get_merchant_lots(
    principal: dict = Depends(require_role(UserType.PARKING_MERCHANT)),
    db: Session = Depends(get_db),
):
    lots = (
        _loaded_lots(db)
        .filter(ParkingLot.user_id == principal["id"])
        .order_by(ParkingLot.location_name)
        .all()
    )
    return {"parking_lots": [_lot_payload(lot) for lot in lots]}


@router.post("/merchant/lots", status_code=status.HTTP_201_CREATED)
def create_merchant_lot(
    payload: LotCreate,
    principal: dict = Depends(require_role(UserType.PARKING_MERCHANT)),
    db: Session = Depends(get_db),
):
    point = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
    lot = ParkingLot(
        location_name=payload.location_name,
        price=payload.price,
        currency=payload.currency,
        country=payload.country,
        city=payload.city,
        state=payload.state,
        address=payload.address,
        pincode=payload.pincode,
        location_coordinates=point,
        user_id=principal["id"],
        available=AvailableStatus.ACTIVE,
    )
    for floor_input in payload.floors:
        floor = Floor(floor_id=floor_input.floor_id, available=AvailableStatus.ACTIVE)
        floor.spots = [
            ParkingSpot(
                spot_id=number,
                status=BookingStatus.SPOT_AVAILABLE,
                available=AvailableStatus.ACTIVE,
            )
            for number in range(1, floor_input.total_spots + 1)
        ]
        lot.floors.append(floor)

    db.add(lot)
    try:
        db.commit()
        db.refresh(lot)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A lot with conflicting floor or space data already exists") from exc
    return _lot_payload(lot)


@router.patch("/merchant/lots/{lot_id}")
def update_merchant_lot(
    lot_id: int,
    payload: LotUpdate,
    principal: dict = Depends(require_role(UserType.PARKING_MERCHANT)),
    db: Session = Depends(get_db),
):
    lot = (
        db.query(ParkingLot)
        .filter_by(id=lot_id, user_id=principal["id"])
        .first()
    )
    if lot is None:
        raise HTTPException(status_code=404, detail="Parking location was not found")
    if payload.price is not None:
        lot.price = payload.price
    if payload.available is not None:
        lot.available = AvailableStatus(payload.available)
    db.commit()
    db.refresh(lot)
    return {"id": lot.id, "price": float(lot.price), "available": _role_value(lot.available)}


@router.get("/admin/users")
def list_users(
    _principal: dict = Depends(require_role(UserType.ADMIN)),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).all()
    return {
        "users": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": _role_value(user.user_type),
                "city": user.city,
                "country": user.country,
            }
            for user in users
        ]
    }


@router.patch("/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    _principal: dict = Depends(require_role(UserType.ADMIN)),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User account was not found")
    user.user_type = UserType.PARKING_MERCHANT
    db.commit()
    return {"id": user.id, "role": _role_value(user.user_type)}


@router.get("/admin/parking-lots")
def list_all_lots(
    _principal: dict = Depends(require_role(UserType.ADMIN)),
    db: Session = Depends(get_db),
):
    lots = _loaded_lots(db).order_by(ParkingLot.id).all()
    return {"parking_lots": [_lot_payload(lot, include_owner=True) for lot in lots]}


@router.patch("/admin/parking-lots/{lot_id}")
def update_admin_lot_status(
    lot_id: int,
    payload: LotStatusUpdate,
    _principal: dict = Depends(require_role(UserType.ADMIN)),
    db: Session = Depends(get_db),
):
    lot = db.get(ParkingLot, lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail="Parking location was not found")
    lot.available = AvailableStatus(payload.available)
    db.commit()
    return {"id": lot.id, "available": _role_value(lot.available)}
