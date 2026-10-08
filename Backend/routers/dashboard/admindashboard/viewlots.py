import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from core.db import get_db
from core.redis_client import redis_client
from models import ParkingLot, Floor, UserType
from core.role_check import require_role
from schemas import Lot

router = APIRouter()

lots_schema = Lot(many=True)  # existing marshmallow schema reused for output
CACHE_TTL = 120


class LotFilters(BaseModel):
    """Replaces LotFilterSchema. Adjust constraints to match the old schema."""
    country_code: str = Field(..., min_length=2, max_length=3)
    state: Optional[str] = None
    city: Optional[str] = None


def lot_filters(
    country_code: str = Query(..., min_length=2, max_length=3),
    state: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
) -> LotFilters:
    return LotFilters(country_code=country_code, state=state, city=city)


@router.get("/parking-lots", dependencies=[Depends(require_role(UserType.ADMIN))])
def get_all_parking_lots(
    filters: LotFilters = Depends(lot_filters),
    db: Session = Depends(get_db),
):
    country_code = filters.country_code
    state = filters.state
    city = filters.city

    cache_key = f"lots:{country_code}:{(state or 'any').lower()}:{(city or 'any').lower()}"

    try:
        cache_data = redis_client.get(cache_key)
    except Exception:
        cache_data = None

    if cache_data:
        return json.loads(cache_data)

    query = db.query(ParkingLot).options(
        selectinload(ParkingLot.floors).selectinload(Floor.spots),
        selectinload(ParkingLot.owner),
    )

    query = query.filter(ParkingLot.country == country_code)

    if state:
        query = query.filter(ParkingLot.state == state.lower())

    if city:
        query = query.filter(ParkingLot.city == city.lower())

    parking_lots = query.all()

    if not parking_lots:
        return JSONResponse(
            status_code=404,
            content={"message": "No parking lots found for given filters"},
        )

    result = {
        "message": "Parking lots retrieved successfully",
        "parking_lots": lots_schema.dump(parking_lots),
    }

    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    except Exception:
        pass

    return result
