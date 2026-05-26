import { computed, ref, watch, type Ref } from "vue";
import {
  getProjectState,
  listActiveJobs,
  listVersions,
  type DesignTurn,
  type Job,
  type ModelVersion,
} from "../api/client";
import { useActiveJob } from "./useActiveJob";

export function useWorkbenchSession(projectId: Ref<string | null>) {
  const versions = ref<ModelVersion[]>([]);
  const selectedVersion = ref<number | null>(null);
  const followLatestVersion = ref(true);
  const activeTurn = ref<DesignTurn | null>(null);

  async function refreshProjectState() {
    if (!projectId.value) {
      activeTurn.value = null;
      return;
    }
    try {
      const state = await getProjectState(projectId.value);
      activeTurn.value = state.active_turn;
    } catch {
      activeTurn.value = null;
    }
  }

  async function refreshVersionsList() {
    if (!projectId.value) {
      versions.value = [];
      selectedVersion.value = null;
      return;
    }
    const list = await listVersions(projectId.value);
    versions.value = list;
    if (list.length === 0) {
      selectedVersion.value = null;
      return;
    }
    if (followLatestVersion.value) {
      selectedVersion.value = list[list.length - 1].version;
      return;
    }
    if (
      selectedVersion.value != null &&
      list.some((item) => item.version === selectedVersion.value)
    ) {
      return;
    }
    selectedVersion.value = list[list.length - 1].version;
  }

  async function refreshAfterJob() {
    await Promise.all([refreshVersionsList(), refreshProjectState()]);
  }

  const { generation, trackJob } = useActiveJob(
    () => projectId.value,
    refreshAfterJob,
  );

  watch(
    projectId,
    () => {
      followLatestVersion.value = true;
      refreshVersionsList().catch(console.error);
      refreshProjectState().catch(console.error);
    },
    { immediate: true },
  );

  watch(
    () => generation.value?.busy,
    (busy, wasBusy) => {
      if (busy) {
        refreshProjectState().catch(console.error);
        return;
      }
      if (wasBusy) refreshAfterJob().catch(console.error);
    },
  );

  const active = computed(() => {
    if (selectedVersion.value != null) {
      return versions.value.find((v) => v.version === selectedVersion.value);
    }
    return versions.value[versions.value.length - 1];
  });

  const latestVersionNum = computed(() => versions.value.at(-1)?.version ?? null);

  const viewingLatest = computed(
    () =>
      latestVersionNum.value != null &&
      selectedVersion.value === latestVersionNum.value,
  );

  const jobVersion = computed(() => generation.value?.version ?? null);
  const jobBusy = computed(() => {
    const g = generation.value;
    if (!g?.busy) return false;
    if (g.phase === "done" || g.phase === "failed") return false;
    if (g.stlReady) return false;
    return true;
  });

  const versionIncomplete = computed(
    () =>
      Boolean(
        active.value?.status === "pending" &&
          active.value.forge_url &&
          !active.value.stl_url,
      ),
  );

  function onTrackJob(job: Job, prompt: string) {
    followLatestVersion.value = true;
    return trackJob(job, prompt);
  }

  watch(
    () =>
      [
        projectId.value,
        activeTurn.value?.render_phase,
        activeTurn.value?.job_id,
        generation.value?.busy,
      ] as const,
    ([pid, renderPhase, jobId, tracking]) => {
      if (!pid || renderPhase !== "running" || tracking) return;
      listActiveJobs(pid)
        .then((jobs) => {
          if (jobs.length === 0) {
            refreshProjectState().catch(console.error);
            return;
          }
          const job =
            (jobId ? jobs.find((item) => item.id === jobId) : undefined) ??
            jobs[0];
          if (job) onTrackJob(job, job.prompt ?? "继续任务…");
        })
        .catch(console.error);
    },
  );

  function syncActiveTurn(turn: DesignTurn | null) {
    activeTurn.value = turn;
  }

  function onTurnComplete() {
    followLatestVersion.value = true;
    refreshAfterJob().catch(console.error);
  }

  function onSelectVersion(version: number) {
    followLatestVersion.value = false;
    selectedVersion.value = version;
  }

  return {
    versions,
    selectedVersion,
    followLatestVersion,
    activeTurn,
    generation,
    active,
    latestVersionNum,
    viewingLatest,
    jobVersion,
    jobBusy,
    versionIncomplete,
    refreshProjectState,
    refreshAfterJob,
    syncActiveTurn,
    onTrackJob,
    onTurnComplete,
    onSelectVersion,
  };
}
