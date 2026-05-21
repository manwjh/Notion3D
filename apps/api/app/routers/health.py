from fastapi import APIRouter

from app.models.schemas import HealthOut
from app.services import cad_service, print_service, slicer_service
from app.services.links import web_base

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(
        status="ok",
        openscad_available=cad_service.openscad_available(),
        slicer_available=slicer_service.slicer_available(),
        bambu_connect_available=print_service.bambu_connect_available(),
        agent_via_mcp=True,
        mcp_server="notion3d",
        web_base_url=web_base(),
    )
