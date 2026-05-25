export type JobPhase =
  | "idle"
  | "submitting"
  | "generating"
  | "rendering"
  | "done"
  | "failed";

export type GenerationState = {
  phase: JobPhase;
  detail: string | null;
  prompt: string | null;
  busy: boolean;
  stlReady?: boolean;
  version?: number | null;
  validationWarnings?: string[];
};

type JobLike = {
  status?: string;
  phase?: string | null;
  preview_ready?: boolean;
  stl_ready?: boolean;
  version?: number | null;
  message?: string | null;
  validation_warnings?: string[];
};

const PHASE_MAP: Record<string, JobPhase> = {
  pending: "generating",
  scad: "generating",
  preview: "rendering",
  stl: "rendering",
  done: "done",
  failed: "failed",
};

export function phaseFromJob(job: JobLike): JobPhase {
  if (job.status === "failed" || job.phase === "failed") return "failed";
  if (job.status === "succeeded" || job.phase === "done") return "done";
  if (job.phase && PHASE_MAP[job.phase]) return PHASE_MAP[job.phase];
  if (job.stl_ready) return "rendering";
  if (job.preview_ready) return "rendering";
  return "generating";
}

export function phaseLabel(phase: JobPhase, detail?: string | null): string | null {
  if (detail && phase !== "idle" && phase !== "done" && phase !== "failed") return detail;
  switch (phase) {
    case "submitting":
      return "收到需求…";
    case "generating":
      return "准备模型…";
    case "rendering":
      return "正在生成 3D 模型…";
    case "done":
      return "完成";
    case "failed":
      return detail ?? "未能完成，请重试";
    default:
      return null;
  }
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
    stlReady: job?.stl_ready ?? false,
    version: job?.version ?? null,
    validationWarnings: job?.validation_warnings ?? [],
  };
}
