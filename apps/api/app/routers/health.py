from fastapi import APIRouter

from app.config import settings
from app.models.schemas import AgentProviderOut, HealthOut
from app.services import forgecad_service, forge_preview_service
from app.services.agents import active_provider_id, bridge_ready, list_provider_info, refresh_provider_cache
from app.services.capabilities import capabilities, web_chat_mode
from app.services.links import web_base

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    await refresh_provider_cache()
    providers = [AgentProviderOut(**p.__dict__) for p in list_provider_info()]
    caps = capabilities()
    return HealthOut(
        status="ok",
        forgecad_available=forgecad_service.forgecad_available(),
        cad_backend=settings.cad_backend,
        web_base_url=web_base(),
        agent_provider=settings.agent_provider,
        agent_active=active_provider_id(),
        agent_bridge_ready=bridge_ready(),
        agent_providers=providers,
        web_chat_mode=web_chat_mode(),
        assistant_label=caps["assistant_label"],
        forge_preview_available=forgecad_service.forgecad_available(),
        forge_preview_running=forge_preview_service.preview_running(),
    )
