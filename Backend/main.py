import logging
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from core.db import engine
from core.redis_client import redis_client
from routers.auth import router as auth_router
from routers.tokenauth import router as tokenauth_router

# User (driver) routers
from routers.dashboard.userdashboard.userdashboard import router as user_dashboard_router
from routers.dashboard.userdashboard.booking import router as booking_router
from routers.dashboard.userdashboard.extension import router as booking_extension_router
from routers.dashboard.userdashboard.release import router as booking_release_router
from routers.dashboard.userdashboard.release_record import router as released_records_router

# Merchant routers
from routers.dashboard.merchantdashboard.merchantdashboard import router as merchant_dashboard_router
from routers.dashboard.merchantdashboard.createlot import router as create_lot_router
from routers.dashboard.merchantdashboard.addfloor import router as add_floor_router
from routers.dashboard.merchantdashboard.addspots import router as add_spots_router
from routers.dashboard.merchantdashboard.blocklot import router as block_lot_router
from routers.dashboard.merchantdashboard.blockfloor import router as block_floor_router
from routers.dashboard.merchantdashboard.blockspot import router as block_spot_router
from routers.dashboard.merchantdashboard.deletelot import router as delete_lot_router
from routers.dashboard.merchantdashboard.deletefloor import router as delete_floor_router
from routers.dashboard.merchantdashboard.deletespot import router as delete_spot_router
from routers.dashboard.merchantdashboard.updateprice import router as update_price_router

# Admin routers
from routers.dashboard.admindashboard.admindashboard import router as admin_dashboard_router
from routers.dashboard.admindashboard.viewusers import router as view_users_router
from routers.dashboard.admindashboard.viewlots import router as view_lots_router
from routers.dashboard.admindashboard.searchuser import router as search_user_router
from routers.dashboard.admindashboard.searchlot import router as search_lot_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Parking App API")

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

# --- User (driver): /user/dashboard, /user/booking/..., /user/records/released
app.include_router(user_dashboard_router, prefix="/user")
app.include_router(booking_router, prefix="/user")
app.include_router(booking_extension_router, prefix="/user")
app.include_router(booking_release_router, prefix="/user")
app.include_router(released_records_router, prefix="/user")

# --- Merchant: /merchant/...
for _merchant_router in (
    merchant_dashboard_router,
    create_lot_router,
    add_floor_router,
    add_spots_router,
    block_lot_router,
    block_floor_router,
    block_spot_router,
    delete_lot_router,
    delete_floor_router,
    delete_spot_router,
    update_price_router,
):
    app.include_router(_merchant_router, prefix="/merchant")

# --- Admin: paths already start with /admin for these three
app.include_router(admin_dashboard_router)
app.include_router(search_user_router)
app.include_router(search_lot_router)
# ...and these two don't, so they get the prefix: /admin/users, /admin/parking-lots
app.include_router(view_users_router, prefix="/admin")
app.include_router(view_lots_router, prefix="/admin")