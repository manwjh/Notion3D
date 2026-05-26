import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exceptions import register_exception_handlers
from app.routers import (
    design,
    health,
    job_events,
    project_agent,
    project_state_events,
    projects,
    templates,
)
from app.services import job_service
from app.services.agents import refresh_provider_cache

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info(
        "Notion3D Engine: file-backed storage, single-process mode "
        "(do not run uvicorn with --workers > 1)"
    )
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    job_service.load_jobs_from_disk()
    await refresh_provider_cache()
    await job_service.resume_interrupted_jobs()
    yield


app = FastAPI(
    title="Notion3D API",
    description="ForgeCAD 装配渲染引擎；Web 对话与 MCP 均经外部 Agent",
    version="0.3.0",
    lifespan=lifespan,
)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(job_events.router)
app.include_router(project_state_events.router)
app.include_router(design.router)
app.include_router(project_agent.router)
app.include_router(templates.router)
