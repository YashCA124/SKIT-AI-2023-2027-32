import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.db import get_db
from core.redis_client import redis_client
from models import User, UserType
from core.role_check import require_role
from schemas import User as UserOutput

router = APIRouter()

users_schema = UserOutput(many=True) 
CACHE_KEY = "all_users"
CACHE_TTL = 120


@router.get("/users", dependencies=[Depends(require_role(UserType.ADMIN))])
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
