import { computed, type ComputedRef, type Ref } from "vue";
import type { DesignTurn, ModelVersion } from "../api/client";
import type { GenerationState } from "../types/generation";
import { phaseLabel } from "../types/generation";
import { mergeDesignContext } from "../utils/designContext";

type SessionRefs = {
  projectId: Ref<string | null>;
  versions: Ref<ModelVersion[]>;
  selectedVersion: Ref<number | null>;
  followLatestVersion: Ref<boolean>;
  active: ComputedRef<ModelVersion | undefined>;
  generation: Ref<GenerationState | null>;
  jobBusy: Ref<boolean>;
  jobVersion: Ref<number | null>;
  viewingLatest: Ref<boolean>;
  activeTurn: Ref<DesignTurn | null>;
};

export function useWorkbenchDisplay(session: SessionRefs) {
  const {
    projectId,
    versions,
    selectedVersion,
    followLatestVersion,
    active,
    generation,
    jobBusy,
    jobVersion,
    viewingLatest,
    activeTurn,
  } = session;

  /** Version being rendered now (includes stlReady before versions list refreshes). */
  const inFlightVersion = computed(() => {
    if (!followLatestVersion.value || jobVersion.value == null) return null;
    const g = generation.value;
    if (!g) return null;
    if (jobBusy.value || g.stlReady) return jobVersion.value;
    return null;
  });

  function versionApiBase(version: number): string | null {
    if (!projectId.value) return null;
    return `/api/projects/${projectId.value}/versions/${version}`;
  }

  function versionAssetUrl(
    version: number | null | undefined,
    asset: "model.stl" | "parts.json",
  ): string | null {
    if (!projectId.value || version == null) return null;
    const row = versions.value.find((item) => item.version === version);
    const base =
      asset === "model.stl" ? row?.stl_url : row?.parts_url;
    if (!base) return null;
    return `${base}?v=${version}`;
  }

  const displayPartsUrl = computed(() => {
    const inFlight = inFlightVersion.value;
    if (inFlight != null) {
      if (generation.value?.stlReady) {
        return `${versionApiBase(inFlight)}/parts.json?v=${inFlight}`;
      }
      return versionAssetUrl(inFlight, "parts.json");
    }
    return active.value?.parts_url
      ? `${active.value.parts_url}?v=${active.value.version}`
      : null;
  });

  const displayStlUrl = computed(() => {
    const inFlight = inFlightVersion.value;
    if (inFlight != null) {
      if (generation.value?.stlReady) {
        return `${versionApiBase(inFlight)}/model.stl?v=${inFlight}`;
      }
      return versionAssetUrl(inFlight, "model.stl");
    }
    return active.value?.stl_url
      ? `${active.value.stl_url}?v=${active.value.version}`
      : null;
  });

  const sourceUrl = computed(() => {
    const inFlight = inFlightVersion.value;
    const ver = inFlight ?? active.value?.version;
    if (!projectId.value || ver == null) return null;

    if (inFlight != null) {
      return `${versionApiBase(inFlight)}/model.forge.js?v=${inFlight}`;
    }

    if (active.value?.forge_url) {
      return `${active.value.forge_url}?v=${active.value.version}`;
    }
    return null;
  });

  const forgeSourcesUrl = computed(() => {
    const inFlight = inFlightVersion.value;
    const ver = inFlight ?? active.value?.version;
    if (!projectId.value || ver == null) return null;
    if (inFlight != null) {
      return `${versionApiBase(inFlight)}/forge-sources?v=${inFlight}`;
    }
    return active.value?.forge_sources_url
      ? `${active.value.forge_sources_url}?v=${active.value.version}`
      : null;
  });

  const hasModel = computed(
    () =>
      versions.value.some((v) => v.status === "complete") ||
      Boolean(displayStlUrl.value),
  );

  const viewerLoading = computed(() => {
    if (generation.value?.stlReady || displayStlUrl.value) return false;
    if (!jobBusy.value || !followLatestVersion.value) return false;
    const phase = generation.value?.phase;
    return phase !== "done" && phase !== "failed";
  });

  const viewerLoadingLabel = computed(
    () =>
      phaseLabel(generation.value?.phase ?? "rendering", generation.value?.detail) ??
      "正在生成 3D 模型…",
  );

  const showBlockingOverlay = computed(
    () => viewerLoading.value && !hasModel.value,
  );

  const hasExportable = computed(
    () =>
      Boolean(active.value?.stl_url) ||
      Boolean(displayStlUrl.value) ||
      Boolean(generation.value?.stlReady && jobVersion.value != null),
  );

  const activeValidationWarnings = computed(() => {
    const fromVersion = active.value?.validation_warnings ?? [];
    if (
      followLatestVersion.value &&
      (jobBusy.value || generation.value?.stlReady)
    ) {
      const fromJob = generation.value?.validationWarnings ?? [];
      if (fromJob.length) return fromJob;
    }
    return fromVersion;
  });

  const designContext = computed(() =>
    mergeDesignContext(
      activeTurn.value,
      active.value,
      Boolean(
        activeTurn.value &&
          (jobBusy.value || generation.value?.stlReady || viewingLatest.value),
      ),
    ),
  );

  const editorVersion = computed(
    () => inFlightVersion.value ?? selectedVersion.value,
  );

  return {
    displayPartsUrl,
    displayStlUrl,
    sourceUrl,
    forgeSourcesUrl,
    hasModel,
    viewerLoading,
    viewerLoadingLabel,
    showBlockingOverlay,
    hasExportable,
    activeValidationWarnings,
    designContext,
    editorVersion,
  };
}
