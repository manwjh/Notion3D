from fastapi import APIRouter

from app.models.schemas import ToolOut
from app.services.tracks.registry import list_tools

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("", response_model=list[ToolOut])
async def get_tools() -> list[ToolOut]:
    return [ToolOut(**t) for t in list_tools()]
