from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthOut
from app.services import forgecad_service, forge_preview_service
from app.services.agents import bridge_ready, refresh_provider_cache
from app.services.capabilities import web_chat_mode
from app.services.links import web_base

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    await refresh_provider_cache()
    return HealthOut(
        status="ok",
        forgecad_available=forgecad_service.forgecad_available(),
        cad_backend=settings.cad_backend,
        web_base_url=web_base(),
        web_turn=settings.normalized_web_turn,
        web_turn_ready=bridge_ready(),
        web_chat_mode=web_chat_mode(),
        forge_preview_available=forge_preview_service.preview_studio_available(),
        forge_preview_running=forge_preview_service.preview_running(),
    )
