from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, projects, tools
from app.services import job_service


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    job_service.load_jobs_from_disk()
    await job_service.resume_interrupted_jobs()
    yield


app = FastAPI(
    title="Notion3D API",
    description="文本 → OpenSCAD 建模 → 预览 → 导出；Agent 通过 MCP Server 集成",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tools.router)
app.include_router(projects.router)
