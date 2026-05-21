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


class ProjectOut(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    latest_version: int | None = None
    web_url: str | None = None


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


class AgentTurnIn(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    pick: ModelPickIn | None = None
    region: str | None = Field(default=None, max_length=64)


class TemplateJobIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
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
    kind: str | None = None
    status: JobStatus
    phase: str | None = None
    prompt: str | None = None
    message: str | None = None
    version: int | None = None
    preview_url: str | None = None
    preview_ready: bool = False
    stl_ready: bool = False
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    web_url: str | None = None


class AgentRunOut(BaseModel):
    provider: str
    session_id: str
    run_id: str
    status: str = "RUNNING"
    external_url: str | None = None


class TurnOut(BaseModel):
    """Unified design turn — agent or blocked."""

    routing: str  # agent | blocked
    reason: str | None = None
    agent: AgentRunOut | None = None
    assistant_message_id: str | None = None


class ScadRenderIn(BaseModel):
    scad_code: str = Field(min_length=1, max_length=200_000)
    label: str = Field(default="手动编辑 SCAD", max_length=256)


class AgentProviderOut(BaseModel):
    id: str
    title: str
    kind: str
    configured: bool
    ready: bool
    note: str = ""


class AgentStatusOut(BaseModel):
    active: bool
    provider: str | None = None
    session_id: str | None = None
    run_id: str | None = None
    status: str | None = None
    external_url: str | None = None
    active_job_id: str | None = None


class ProjectCapabilitiesOut(BaseModel):
    web_chat_mode: str  # agent | setup_required
    assistant_label: str | None = None
    assistant_ready: bool = False


class ProjectStateOut(BaseModel):
    project: ProjectOut
    messages: list[ChatMessageOut]
    active_job: JobOut | None = None
    agent: AgentStatusOut
    capabilities: ProjectCapabilitiesOut


class HealthOut(BaseModel):
    status: str
    openscad_available: bool
    web_base_url: str = "http://localhost:5173"
    agent_provider: str = "auto"
    agent_active: str | None = None
    agent_bridge_ready: bool = False
    agent_providers: list[AgentProviderOut] = Field(default_factory=list)
    web_chat_mode: str = "setup_required"
    assistant_label: str | None = None
