from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ProjectCreate(BaseModel):
    name: str = Field(default="未命名项目", max_length=128)
    tool: str = Field(default="parametric", max_length=32)


class ProjectOut(BaseModel):
    id: str
    name: str
    tool: str = "parametric"
    track: str = "parametric"
    created_at: datetime
    updated_at: datetime
    latest_version: int | None = None
    web_url: str | None = None


class ToolOut(BaseModel):
    id: str
    track: str
    title: str
    description: str
    available: bool
    sample_prompts: list[str] = Field(default_factory=list)


class VersionStatus(str, Enum):
    pending = "pending"
    preview_ready = "preview_ready"
    complete = "complete"


class ModelVersionOut(BaseModel):
    version: int
    status: VersionStatus = VersionStatus.complete
    stl_url: str | None = None
    scad_url: str | None = None
    preview_url: str | None = None
    three_mf_url: str | None = None
    created_at: datetime
    prompt: str | None = None


class ModelPickIn(BaseModel):
    x: float
    y: float
    z: float
    nx: float = 0.0
    ny: float = 1.0
    nz: float = 0.0
    label: str | None = None


class ChatMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    pick: ModelPickIn | None = None
    region: str | None = Field(default=None, max_length=64)


class ChatMessageOut(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime
    job_id: str | None = None


class JobOut(BaseModel):
    id: str
    project_id: str
    status: JobStatus
    prompt: str | None = None
    message: str | None = None
    version: int | None = None
    preview_url: str | None = None
    preview_ready: bool = False
    stl_ready: bool = False
    created_at: datetime
    updated_at: datetime
    web_url: str | None = None


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)


class ScadRenderIn(BaseModel):
    scad_code: str = Field(min_length=1, max_length=200_000)
    label: str = Field(default="手动编辑 SCAD", max_length=256)


class HealthOut(BaseModel):
    status: str
    openscad_available: bool
    slicer_available: bool
    bambu_connect_available: bool
    agent_via_mcp: bool = True
    mcp_server: str = "notion3d"
    web_base_url: str = "http://localhost:5173"


class ActionResult(BaseModel):
    ok: bool
    message: str
    three_mf_url: str | None = None
    bambu_connect_url: str | None = None
