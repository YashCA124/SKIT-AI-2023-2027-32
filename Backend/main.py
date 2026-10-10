import logging
import os
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from sqlalchemy import func

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from core.db import SessionLocal, engine
from core.redis_client import redis_client
from models import Admin
from routers.auth import router as auth_router
from routers.parking_api import router as parking_router
from routers.tokenauth import router as tokenauth_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Parking App API")


@app.on_event("startup")
def bootstrap_initial_admin():
    username = os.getenv("INITIAL_ADMIN_USERNAME", "").strip()
    password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    if bool(username) != bool(password):
        raise RuntimeError(
            "Set both INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD, or leave both empty."
        )
    if not username:
        return

    db = SessionLocal()
    try:
        if db.query(Admin).filter_by(username=username).first():
            return
        next_id = (db.query(func.max(Admin.id)).scalar() or 0) + 1
        db.add(
            Admin(
                id=next_id,
                username=username,
                password=generate_password_hash(password),
            )
        )
        db.commit()
        logger.info("Bootstrapped initial administrator account %s.", username)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "parking-app-api",
        "environment": os.getenv("APP_ENV", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def readiness_check():
    database_connected = False
    redis_connected = False

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_connected = True
    except SQLAlchemyError:
        logger.warning("Database readiness check failed.", exc_info=True)

    try:
        redis_connected = bool(redis_client.ping())
    except RedisError:
        logger.warning("Redis readiness check failed.", exc_info=True)

    ready = database_connected and redis_connected
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "degraded",
            "service": "parking-app-api",
            "database_connected": database_connected,
            "redis_connected": redis_connected,
            "environment": os.getenv("APP_ENV", "development"),
        },
    )


app.include_router(auth_router, prefix="/auth")
app.include_router(tokenauth_router, prefix="/tokenauth")
app.include_router(parking_router)
