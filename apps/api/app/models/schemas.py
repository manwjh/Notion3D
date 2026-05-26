from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


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


class TurnImageIn(BaseModel):
    data: str = Field(min_length=1, max_length=4_000_000)
    mime_type: str = Field(default="image/png", max_length=64)
    filename: str | None = Field(default=None, max_length=128)


class AgentTurnIn(BaseModel):
    content: str = Field(default="", max_length=8000)
    pick: ModelPickIn | None = None
    region: str | None = Field(default=None, max_length=64)
    images: list[TurnImageIn] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_content_or_images(self) -> "AgentTurnIn":
        has_text = bool(self.content.strip())
        has_images = bool(self.images)
        if not has_text and not has_images:
            raise ValueError("content 与 images 不能同时为空")
        if not has_text:
            object.__setattr__(self, "content", "请查看截图并检查当前模型。")
        return self


class ChatImageOut(BaseModel):
    id: str
    url: str
    mime_type: str
    filename: str | None = None


class ChatMessageOut(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime
    turn_id: str | None = None
    job_id: str | None = None
    images: list[ChatImageOut] = Field(default_factory=list)


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
    stl_ready: bool = False
    error: str | None = None
    validation_warnings: list[str] = Field(default_factory=list)
    spatial_digest: dict | None = None
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


class PlanFidelity(str, Enum):
    layout_only = "layout_only"
    printable = "printable"
    decorative = "decorative"


class AssemblyModuleRole(str, Enum):
    shell = "shell"
    internal = "internal"
    lid = "lid"
    external = "external"
    other = "other"


class AssemblyModuleSpec(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    role: AssemblyModuleRole = AssemblyModuleRole.other
    contains: list[str] = Field(default_factory=list, max_length=32)
    anchor: str | None = Field(default=None, max_length=64)
    hinge: str | None = Field(default=None, max_length=128)


class GeometryRecipeKind(str, Enum):
    sketch_extrude = "sketch_extrude"
    sketch_extrude_shell = "sketch_extrude_shell"
    loft = "loft"
    sweep = "sweep"
    revolve = "revolve"
    union_bracket = "union_bracket"
    primitive_shell = "primitive_shell"
    primitive_layout = "primitive_layout"


class PartGeometryRecipe(BaseModel):
    part_id: str = Field(min_length=1, max_length=64)
    recipe: GeometryRecipeKind
    notes: str | None = Field(default=None, max_length=500)


class DesignPlanIn(BaseModel):
    turn_id: str | None = None
    task_class: TaskClass
    summary: str = Field(min_length=1, max_length=2000)
    strategy: PlanStrategy
    template_id: str | None = Field(default=None, max_length=64)
    params: dict[str, float] | None = None
    modules: list[str] = Field(default_factory=list, max_length=64)
    assembly_spec: list[AssemblyModuleSpec] = Field(default_factory=list, max_length=64)
    geometry_recipes: list[PartGeometryRecipe] = Field(default_factory=list, max_length=64)
    assumptions: list[str] = Field(default_factory=list)
    fidelity: PlanFidelity | None = None
    high_fidelity_requested: bool | None = None

    @model_validator(mode="after")
    def validate_geometry_recipes(self) -> "DesignPlanIn":
        if not self.geometry_recipes:
            return self
        spec_ids = {m.id for m in self.assembly_spec} if self.assembly_spec else set(self.modules)
        for entry in self.geometry_recipes:
            if spec_ids and entry.part_id not in spec_ids:
                raise ValueError(
                    f"geometry_recipes: part_id {entry.part_id} 不在 assembly_spec/modules 中"
                )
        return self

    @model_validator(mode="after")
    def validate_assembly_spec(self) -> "DesignPlanIn":
        if not self.assembly_spec:
            return self
        ids = {module.id for module in self.assembly_spec}
        for module in self.assembly_spec:
            for child_id in module.contains:
                if child_id not in ids:
                    raise ValueError(
                        f"assembly_spec: {module.id}.contains 引用未知部件 {child_id}"
                    )
            if module.anchor and module.anchor not in ids:
                raise ValueError(
                    f"assembly_spec: {module.id}.anchor 引用未知部件 {module.anchor}"
                )
            if module.hinge:
                parent_id = module.hinge.rsplit(".", 1)[0]
                if parent_id not in ids:
                    raise ValueError(
                        f"assembly_spec: {module.id}.hinge 引用未知部件 {parent_id}"
                    )
        if not self.modules:
            object.__setattr__(self, "modules", [module.id for module in self.assembly_spec])
        return self


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


class AgentActivityStepOut(BaseModel):
    id: str
    kind: str = "tool"
    label: str
    detail: str | None = None
    status: str = "running"  # running | done | error
    tool: str | None = None
    at: str | None = None


class AgentStatusOut(BaseModel):
    active: bool
    turn_id: str | None = None
    provider: str | None = None
    session_id: str | None = None
    run_id: str | None = None
    status: str | None = None
    external_url: str | None = None
    active_job_id: str | None = None
    activity: list[AgentActivityStepOut] = Field(default_factory=list)


class ProjectCapabilitiesOut(BaseModel):
    web_chat_mode: str  # agent | setup_required
    web_turn: str = "off"
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
    web_turn: str = "off"
    web_turn_ready: bool = False
    web_chat_mode: str = "setup_required"
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
