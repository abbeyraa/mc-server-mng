from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.services.monitoring_service import get_metrics
from app.services.server_controller import server_controller

router = APIRouter(prefix="/metrics", tags=["monitoring"])


@router.get("")
async def metrics(_: User = Depends(get_current_user)):
    status_info = server_controller.get_status()
    return {**get_metrics(status_info["pid"]), **status_info}
