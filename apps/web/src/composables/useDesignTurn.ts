import type { GenerationState, JobPhase } from "../types/generation";

export function mergeSessionPhase(
  generation: GenerationState | null,
  agentBusy: boolean,
): { phase: JobPhase; detail: string | null; busy: boolean } {
  if (agentBusy && (!generation || !generation.busy)) {
    return { phase: "generating", detail: "设计助手正在建模…", busy: true };
  }
  if (generation?.busy) {
    return {
      phase: generation.phase,
      detail: generation.detail,
      busy: true,
    };
  }
  return { phase: generation?.phase ?? "idle", detail: generation?.detail ?? null, busy: false };
}

export function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
