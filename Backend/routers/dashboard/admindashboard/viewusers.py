import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from extensions import redis_client
from models import User, UserType
from rolecheck.role_required import role_required
from schemas import User as UserOutput

router = APIRouter()

users_schema = UserOutput(many=True)  # existing marshmallow schema reused
CACHE_KEY = "all_users"
CACHE_TTL = 120


@router.get("/users", dependencies=[Depends(role_required(UserType.ADMIN))])
def get_all_users(db: Session = Depends(get_db)):
    try:
        cached_data = redis_client.get(CACHE_KEY)
    except Exception:
        cached_data = None

    if cached_data:
        user_details = json.loads(cached_data)
    else:
        records = db.query(User).all()
        user_details = users_schema.dump(records)

        try:
            redis_client.setex(CACHE_KEY, CACHE_TTL, json.dumps(user_details))
        except Exception:
            pass

    return {
        "message": "Admin Login Approved",
        "user_details": user_details,
    }
