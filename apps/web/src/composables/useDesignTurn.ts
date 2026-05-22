import type { DesignTurn } from "../api/client";
import type { GenerationState, JobPhase } from "../types/generation";

export function mergeSessionPhase(
  generation: GenerationState | null,
  agentBusy: boolean,
  activeTurn: DesignTurn | null,
): { phase: JobPhase; detail: string | null; busy: boolean; lane: "idle" | "agent" | "render" } {
  if (generation?.busy) {
    return {
      phase: generation.phase,
      detail: generation.detail,
      busy: true,
      lane: "render",
    };
  }
  if (activeTurn?.render_phase === "running") {
    return {
      phase: "rendering",
      detail: "正在生成 3D 模型…",
      busy: true,
      lane: "render",
    };
  }
  if (agentBusy || activeTurn?.agent_phase === "running") {
    return {
      phase: "generating",
      detail: "助手处理中…",
      busy: true,
      lane: "agent",
    };
  }
  return {
    phase: generation?.phase ?? "idle",
    detail: generation?.detail ?? null,
    busy: false,
    lane: "idle",
  };
}

export function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
