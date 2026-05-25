import type { DesignTurn } from "../api/client";
import type { GenerationState, JobPhase } from "../types/generation";

export function mergeSessionPhase(
  generation: GenerationState | null,
  agentBusy: boolean,
  activeTurn: DesignTurn | null,
): {
  phase: JobPhase;
  detail: string | null;
  busy: boolean;
  lane: "idle" | "agent" | "render";
  designPhase: string | null;
} {
  const designPhase = activeTurn?.design_phase ?? null;
  if (generation?.busy) {
    return {
      phase: generation.phase,
      detail: generation.detail,
      busy: true,
      lane: "render",
      designPhase,
    };
  }
  if (activeTurn?.render_phase === "running") {
    return {
      phase: "rendering",
      detail: "正在生成 3D 模型…",
      busy: true,
      lane: "render",
      designPhase: designPhase ?? "render",
    };
  }
  if (agentBusy || activeTurn?.agent_phase === "running") {
    return {
      phase: "generating",
      detail: "助手处理中…",
      busy: true,
      lane: "agent",
      designPhase: designPhase ?? "intake",
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
