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


class DesignPhase(str, Enum):
    intake = "intake"
    plan = "plan"
    author = "author"
    render = "render"
    review = "review"
    done = "done"
    blocked = "blocked"


class ReviewStatus(str, Enum):
    pass_ = "pass"
    retry = "retry"
    accept_warnings = "accept_warnings"


class PlanStrategy(str, Enum):
    template_apply = "template_apply"
    template_edit = "template_edit"
    from_scratch = "from_scratch"
    chat_only = "chat_only"


class TaskClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class ModelVersionOut(BaseModel):
    version: int
    status: VersionStatus = VersionStatus.complete
    stl_url: str | None = None
    parts_url: str | None = None
    forge_url: str | None = None
    preview_url: str | None = None
    cad_backend: str | None = "forgecad"
    created_at: datetime
    prompt: str | None = None
    turn_id: str | None = None
    job_id: str | None = None
    validation_warnings: list[str] = Field(default_factory=list)
    plan_summary: str | None = None
    plan_strategy: str | None = None
    plan_template_id: str | None = None
    plan_assumptions: list[str] = Field(default_factory=list)
    plan_modules: list[str] = Field(default_factory=list)
    review_status: str | None = None
    review_notes: list[str] = Field(default_factory=list)
    design_revision: int | None = None
    src_files: list[str] = Field(default_factory=list)
    forge_sources_url: str | None = None


class ForgeSourcesOut(BaseModel):
    version: int
    forge_code: str
    files: dict[str, str] = Field(default_factory=dict)
    cad_backend: str = "forgecad"


class ForgePreviewOut(BaseModel):
    ready: bool
    url: str | None = None
    embed_url: str | None = None
    error: str | None = None
    mode: str | None = None
    port: int | None = None


class ModelPickIn(BaseModel):
    x: float
    y: float
    z: float
    nx: float = 0.0
    ny: float = 1.0
    nz: float = 0.0
    label: str | None = None
    element: str | None = None


class AgentTurnIn(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    pick: ModelPickIn | None = None
    region: str | None = Field(default=None, max_length=64)


class ChatMessageOut(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime
    turn_id: str | None = None
    job_id: str | None = None


class JobSource(str, Enum):
    agent = "agent"
    manual = "manual"
    template = "template"
    system = "system"


class JobOut(BaseModel):
    id: str
    project_id: str
    kind: str | None = None
    source: JobSource | None = None
    turn_id: str | None = None
    status: JobStatus
    phase: str | None = None
    prompt: str | None = None
    message: str | None = None
    version: int | None = None
    preview_url: str | None = None
    preview_ready: bool = False
    stl_ready: bool = False
    error: str | None = None
    validation_warnings: list[str] = Field(default_factory=list)
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

    turn_id: str | None = None
    routing: str  # agent | blocked
    reason: str | None = None
    agent: AgentRunOut | None = None
    assistant_message_id: str | None = None


class DesignTurnOut(BaseModel):
    id: str
    agent_phase: str  # running | replied | failed
    render_phase: str  # idle | running | done | failed
    design_phase: DesignPhase = DesignPhase.intake
    user_message_id: str
    assistant_message_id: str | None = None
    job_id: str | None = None
    version: int | None = None
    revision: int = 0
    plan_summary: str | None = None
    plan_strategy: str | None = None
    plan_template_id: str | None = None
    plan_assumptions: list[str] = Field(default_factory=list)
    plan_modules: list[str] = Field(default_factory=list)
    review_status: str | None = None
    review_notes: list[str] = Field(default_factory=list)


class DesignPlanIn(BaseModel):
    turn_id: str | None = None
    task_class: TaskClass
    summary: str = Field(min_length=1, max_length=2000)
    strategy: PlanStrategy
    template_id: str | None = Field(default=None, max_length=64)
    params: dict[str, float] | None = None
    modules: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class DesignReviewIn(BaseModel):
    turn_id: str | None = None
    status: ReviewStatus
    notes: list[str] = Field(default_factory=list)
    retry_phase: DesignPhase | None = None


class DesignArtifactOut(BaseModel):
    turn_id: str
    design_phase: DesignPhase
    plan: dict | None = None
    review: dict | None = None
    revision: int = 0


class ForgeRenderIn(BaseModel):
    forge_code: str = Field(min_length=1, max_length=400_000)
    label: str = Field(default="ForgeCAD 建模", max_length=256)
    source: JobSource = Field(default=JobSource.manual)
    files: dict[str, str] | None = Field(
        default=None,
        description="Optional sub-files relative to src/, e.g. {\"motor.forge.js\": \"...\"}",
    )


class AgentProviderOut(BaseModel):
    id: str
    title: str
    kind: str
    configured: bool
    ready: bool
    note: str = ""


class AgentStatusOut(BaseModel):
    active: bool
    turn_id: str | None = None
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
    active_turn: DesignTurnOut | None = None
    active_job: JobOut | None = None
    agent: AgentStatusOut
    capabilities: ProjectCapabilitiesOut


class HealthOut(BaseModel):
    status: str
    forgecad_available: bool = False
    cad_backend: str = "forgecad"
    web_base_url: str = "http://localhost:5173"
    agent_provider: str = "cursor_sdk"
    agent_active: str | None = None
    agent_bridge_ready: bool = False
    agent_providers: list[AgentProviderOut] = Field(default_factory=list)
    web_chat_mode: str = "setup_required"
    assistant_label: str | None = None
    forge_preview_available: bool = False
    forge_preview_running: bool = False


class TemplateParamOut(BaseModel):
    name: str
    label: str | None = None
    default: float | None = None
    unit: str | None = None


class TemplateOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    license: str | None = None
    source: str | None = None
    scope: str
    params: list[TemplateParamOut] = Field(default_factory=list)


class TemplateDetailOut(TemplateOut):
    forge_code: str | None = None
    format: str = "forge"


class TemplateApplyIn(BaseModel):
    project_id: str | None = None
    name: str | None = Field(default=None, max_length=128)
    params: dict[str, float] | None = None
    label: str | None = Field(default=None, max_length=256)


class TemplateApplyOut(BaseModel):
    project: ProjectOut
    job: JobOut
    template_id: str


class SaveTemplateIn(BaseModel):
    id: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    tags: list[str] = Field(default_factory=list)
    category: str | None = Field(default=None, max_length=32)
