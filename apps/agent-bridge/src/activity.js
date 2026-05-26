/**
 * Human-readable labels for Notion3D MCP tool calls (Web activity feed).
 */

const TOOL_LABELS = {
  notion3d_health: "检查建模引擎",
  notion3d_render_forge: "提交 ForgeCAD 渲染",
  notion3d_wait_job: "等待渲染完成",
  notion3d_get_forge_sources: "读取 Forge 源码",
  notion3d_get_job: "查询渲染任务",
  notion3d_list_active_jobs: "查看进行中的任务",
  notion3d_list_versions: "列出历史方案",
  notion3d_apply_template: "应用模板",
  notion3d_get_template: "读取模板",
  notion3d_list_templates: "浏览模板库",
  notion3d_report_design_plan: "记录建模计划",
  notion3d_report_design_review: "记录验收结果",
  notion3d_get_design_state: "读取设计状态",
  notion3d_get_project_state: "读取项目快照",
  notion3d_create_project: "创建项目",
  notion3d_list_projects: "列出项目",
  notion3d_list_messages: "读取对话历史",
  notion3d_save_template: "保存为模板",
  notion3d_wait_agent: "等待 Agent 完成",
};

export function resolveMcpToolName(name, args) {
  if (name && name !== "mcp" && !name.startsWith("Mcp")) return name;
  if (!args || typeof args !== "object") return name || "mcp";
  const direct =
    args.toolName ||
    args.tool_name ||
    args.name ||
    args.tool ||
    args.serverToolName;
  if (typeof direct === "string" && direct) return direct;
  if (typeof args.tool === "string") return args.tool;
  return name || "mcp";
}

export function toolActivityLabel(name, args) {
  const resolved = resolveMcpToolName(name, args);
  if (!resolved) return "执行工具";
  if (TOOL_LABELS[resolved]) return TOOL_LABELS[resolved];
  if (resolved.startsWith("notion3d_")) {
    return resolved.slice("notion3d_".length).split("_").join(" ");
  }
  return resolved;
}

export function toolActivityDetail(name, args) {
  if (!args || typeof args !== "object") return null;
  if (name === "notion3d_render_forge") {
    const label = args.label || args.prompt;
    if (label) return String(label).slice(0, 120);
  }
  if (name === "notion3d_wait_job" && args.job_id) {
    return `job ${String(args.job_id).slice(0, 8)}…`;
  }
  if (name === "notion3d_get_forge_sources" && args.version != null) {
    return `v${args.version}`;
  }
  if (name === "notion3d_apply_template" && args.template_id) {
    return String(args.template_id);
  }
  if (name === "notion3d_report_design_plan" && args.summary) {
    return String(args.summary).slice(0, 100);
  }
  return null;
}

export function mapToolStatus(status) {
  if (status === "completed") return "done";
  if (status === "error") return "error";
  return "running";
}

export function createActivityCollector() {
  const steps = [];
  const byId = new Map();

  function upsert(step) {
    const existing = byId.get(step.id);
    if (existing) {
      Object.assign(existing, step);
      return existing;
    }
    steps.push(step);
    byId.set(step.id, step);
    return step;
  }

  function pushStatus(label) {
    upsert({
      id: `status-${steps.length}`,
      kind: "status",
      label,
      detail: null,
      status: "done",
      at: new Date().toISOString(),
    });
  }

  function ingest(event) {
    if (!event || typeof event !== "object") return;

    if (event.type === "tool_call") {
      const toolName = resolveMcpToolName(event.name, event.args);
      upsert({
        id: event.call_id || `tool-${steps.length}`,
        kind: "tool",
        tool: toolName || null,
        label: toolActivityLabel(event.name, event.args),
        detail: toolActivityDetail(toolName, event.args),
        status: mapToolStatus(event.status),
        at: new Date().toISOString(),
      });
      return;
    }

    if (event.type === "status" && event.message) {
      pushStatus(event.message);
      return;
    }

    if (event.type === "status" && event.status) {
      const st = String(event.status).toUpperCase();
      if (st === "FINISHED" || st === "RUNNING" || st === "CREATING") return;
      pushStatus(String(event.status));
      return;
    }

    if (event.type === "thinking" && event.text) {
      const text = String(event.text).trim();
      if (!text) return;
      upsert({
        id: `think-${steps.length}`,
        kind: "thinking",
        label: text.length > 72 ? `${text.slice(0, 72)}…` : text,
        detail: null,
        status: "done",
        at: new Date().toISOString(),
      });
    }
  }

  return {
    ingest,
    snapshot() {
      return steps.map((s) => ({ ...s }));
    },
  };
}
