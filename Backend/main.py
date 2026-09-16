import os
from datetime import datetime, timezone

from fastapi import FastAPI

from routers.auth import router as auth_router
from routers.tokenauth import router as tokenauth_router

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
    database_configured = bool(os.getenv("DATABASE_URL"))
    return {
        "status": "ready" if database_configured else "degraded",
        "service": "parking-app-api",
        "database_configured": database_configured,
        "environment": os.getenv("APP_ENV", "development"),
    }


app.include_router(auth_router, prefix="/auth")
app.include_router(tokenauth_router, prefix="/tokenauth")
