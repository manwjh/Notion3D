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
  status?: string;
  phase?: string | null;
  preview_ready?: boolean;
  preview_url?: string | null;
  stl_ready?: boolean;
  version?: number | null;
  message?: string | null;
};

const PHASE_MAP: Record<string, JobPhase> = {
  pending: "generating",
  scad: "generating",
  preview: "previewing",
  stl: "rendering",
  done: "done",
  failed: "failed",
};

export function phaseFromJob(job: JobLike): JobPhase {
  if (job.status === "failed" || job.phase === "failed") return "failed";
  if (job.status === "succeeded" || job.phase === "done") return "done";
  if (job.phase && PHASE_MAP[job.phase]) return PHASE_MAP[job.phase];
  if (job.stl_ready) return "rendering";
  if (job.preview_ready) return "previewing";
  return "generating";
}

export function phaseLabel(phase: JobPhase, detail?: string | null): string | null {
  if (detail && phase !== "idle" && phase !== "done" && phase !== "failed") return detail;
  switch (phase) {
    case "submitting":
      return "收到需求…";
    case "generating":
      return "正在生成方案…";
    case "previewing":
      return "初稿预览好了，正在加载 3D…";
    case "rendering":
      return "正在完善可打印模型…";
    case "done":
      return "完成";
    case "failed":
      return detail ?? "未能完成，请重试";
    default:
      return null;
  }
}

export const SESSION_STEPS = [
  { id: "generating", label: "理解需求", hint: "根据描述生成方案" },
  { id: "previewing", label: "出初稿", hint: "快速预览造型方向" },
  { id: "rendering", label: "可打印模型", hint: "生成可旋转、可导出的 3D" },
] as const;

export function stepIndex(phase: JobPhase): number {
  if (phase === "rendering" || phase === "done") return 2;
  if (phase === "previewing") return 1;
  if (phase === "generating" || phase === "submitting") return 0;
  return -1;
}

export function jobToGenerationState(
  phase: JobPhase,
  detail: string | null,
  prompt: string | null,
  busy: boolean,
  job?: JobLike,
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
