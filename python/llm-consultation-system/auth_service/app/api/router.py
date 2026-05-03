from fastapi import APIRouter

from app.api.routes_auth import router as auth_routes_router

api_router = APIRouter()
api_router.include_router(auth_routes_router, tags=["auth"])
