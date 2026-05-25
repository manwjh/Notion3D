import type { DesignTurn, ModelVersion } from "../api/client";
import type { DesignContextView } from "../components/DesignContextBanner.vue";

export function designContextFromTurn(turn: DesignTurn | null | undefined): DesignContextView | null {
  if (!turn) return null;
  return {
    phase: turn.design_phase ?? null,
    revision: turn.revision ?? null,
    planSummary: turn.plan_summary ?? null,
    planStrategy: turn.plan_strategy ?? null,
    planTemplateId: turn.plan_template_id ?? null,
    planAssumptions: turn.plan_assumptions ?? [],
    planModules: turn.plan_modules ?? [],
    reviewStatus: turn.review_status ?? null,
    reviewNotes: turn.review_notes ?? [],
  };
}

export function designContextFromVersion(version: ModelVersion | null | undefined): DesignContextView | null {
  if (!version) return null;
  return {
    phase: null,
    revision: version.design_revision ?? null,
    planSummary: version.plan_summary ?? null,
    planStrategy: version.plan_strategy ?? null,
    planTemplateId: version.plan_template_id ?? null,
    planAssumptions: version.plan_assumptions ?? [],
    planModules: version.plan_modules ?? [],
    reviewStatus: version.review_status ?? null,
    reviewNotes: version.review_notes ?? [],
  };
}

export function mergeDesignContext(
  turn: DesignTurn | null | undefined,
  version: ModelVersion | null | undefined,
  preferTurn: boolean,
): DesignContextView | null {
  const fromTurn = designContextFromTurn(turn);
  const fromVersion = designContextFromVersion(version);
  if (preferTurn && fromTurn && (fromTurn.planSummary || (fromTurn.reviewNotes?.length ?? 0) > 0)) {
    return {
      ...fromVersion,
      ...fromTurn,
      revision: fromTurn.revision ?? fromVersion?.revision ?? null,
    };
  }
  if (fromVersion?.planSummary || (fromVersion?.reviewNotes?.length ?? 0) > 0) {
    return fromVersion;
  }
  return fromTurn;
}
