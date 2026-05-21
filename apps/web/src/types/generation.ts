export type JobPhase =
  | "idle"
  | "submitting"
  | "generating"
  | "previewing"
  | "rendering"
  | "done"
  | "failed";

export type GenerationState = {
  phase: JobPhase;
  detail: string | null;
  prompt: string | null;
  busy: boolean;
  previewUrl?: string | null;
  previewReady?: boolean;
  stlReady?: boolean;
  version?: number | null;
};

type JobLike = {
  preview_ready?: boolean;
  preview_url?: string | null;
  stl_ready?: boolean;
  version?: number | null;
};

export function phaseFromJobMessage(
  status: string,
  message: string | null,
  job?: JobLike
): JobPhase {
  const msg = message ?? "";
  if (status === "failed") return "failed";
  if (status === "succeeded") return "done";
  if (job?.stl_ready || msg.includes("3D 网格已完成")) return "rendering";
  if (
    job?.preview_ready ||
    msg.includes("预览图") ||
    msg.includes("预览已") ||
    msg.includes("计算 3D")
  ) {
    return "previewing";
  }
  if (msg.includes("OpenSCAD") || msg.includes("生成")) return "generating";
  return "submitting";
}

export function phaseLabel(phase: JobPhase, detail?: string | null): string | null {
  if (detail && phase !== "idle" && phase !== "done" && phase !== "failed") return detail;
  switch (phase) {
    case "submitting":
      return "提交任务…";
    case "generating":
      return "正在生成模型…";
    case "previewing":
      return "预览已显示，正在加载 3D…";
    case "rendering":
      return "正在加载 3D 模型…";
    case "done":
      return "完成";
    case "failed":
      return detail ?? "失败";
    default:
      return null;
  }
}

export const GENERATION_STEPS = [
  { id: "generating", label: "理解并建模", hint: "根据描述生成参数化模型" },
  { id: "previewing", label: "生成预览", hint: "快速预览，确认造型是否正确" },
  { id: "rendering", label: "加载 3D", hint: "计算可旋转、可导出的 3D 模型" },
] as const;

export function stepIndex(phase: JobPhase): number {
  if (phase === "rendering" || phase === "done") return 2;
  if (phase === "previewing") return 1;
  if (phase === "generating" || phase === "submitting") return 0;
  return 0;
}

export function jobToGenerationState(
  phase: JobPhase,
  detail: string | null,
  prompt: string | null,
  busy: boolean,
  job?: JobLike & { version?: number | null }
): GenerationState {
  return {
    phase,
    detail,
    prompt,
    busy,
    previewUrl: job?.preview_url ?? null,
    previewReady: job?.preview_ready ?? false,
    stlReady: job?.stl_ready ?? false,
    version: job?.version ?? null,
  };
}
