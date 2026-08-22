from fastapi import FastAPI

from routers.auth import router as auth_router
from routers.tokenauth import router as tokenauth_router

app = FastAPI(title="Parking App API")

app.include_router(auth_router, prefix="/auth")
app.include_router(tokenauth_router, prefix="/tokenauth")
