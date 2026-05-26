import type { DesignTurn } from "../api/client";
import type { GenerationState, JobPhase } from "../types/generation";

export function mergeSessionPhase(
  generation: GenerationState | null,
  agentBusy: boolean,
  activeTurn: DesignTurn | null,
  agentActive = false,
): {
  phase: JobPhase;
  detail: string | null;
  busy: boolean;
  lane: "idle" | "agent" | "render";
  designPhase: string | null;
} {
  const designPhase = activeTurn?.design_phase ?? null;
  if (generation?.busy) {
    const terminal =
      generation.phase === "done" || generation.phase === "failed";
    return {
      phase: generation.phase,
      detail: generation.detail,
      busy: !terminal,
      lane: terminal ? "idle" : "render",
      designPhase,
    };
  }
  if (agentBusy || agentActive) {
    return {
      phase: "generating",
      detail: "正在建模…",
      busy: true,
      lane: "agent",
      designPhase: designPhase ?? "author",
    };
  }
  return {
    phase: generation?.phase ?? "idle",
    detail: generation?.detail ?? null,
    busy: false,
    lane: "idle",
    designPhase,
  };
}

export function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
