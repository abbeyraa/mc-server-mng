from fastapi import APIRouter

from app.api.v1 import auth, server, profiles, worlds, mods, monitoring, console, backup

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(server.router)
api_router.include_router(profiles.router)
api_router.include_router(worlds.router)
api_router.include_router(mods.router)
api_router.include_router(monitoring.router)
api_router.include_router(console.router)
api_router.include_router(backup.router)
