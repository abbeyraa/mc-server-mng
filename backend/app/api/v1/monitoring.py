from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.services.monitoring_service import get_metrics

router = APIRouter(prefix="/metrics", tags=["monitoring"])


@router.get("")
async def metrics(_: User = Depends(get_current_user)):
    return get_metrics()
