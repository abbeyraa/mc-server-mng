import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import configure_logging
from app.api.v1.router import api_router
from app.websockets.console_ws import console_endpoint
from app.websockets.metrics_ws import metrics_endpoint
from app.services.server_controller import server_controller

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data dirs exist
    for d in [settings.worlds_dir, settings.mods_dir, settings.backups_dir, settings.server_jars_dir, settings.LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    await init_db()
    await _seed_admin()
    await server_controller.restore_state()
    logger.info("Application started")
    yield
    logger.info("Application shutting down")


async def _seed_admin() -> None:
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        existing = result.scalar_one_or_none()
        if not existing:
            admin = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            await db.commit()
            logger.info(f"Admin user '{settings.ADMIN_USERNAME}' created")


app = FastAPI(title="MC Server Manager", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.websocket("/ws/console")
async def ws_console(websocket: WebSocket, token: str = Query(...)):
    await console_endpoint(websocket, token)


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket, token: str = Query(...)):
    await metrics_endpoint(websocket, token)


@app.get("/health")
async def health():
    return {"status": "ok"}
