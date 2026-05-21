import { onUnmounted, ref, watch } from "vue";
import { getJob, listActiveJobs, type Job } from "../api/client";
import {
  jobToGenerationState,
  phaseFromJob,
  type GenerationState,
} from "../types/generation";

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useActiveJob(
  projectId: () => string | null,
  onDone: () => void | Promise<void>,
) {
  const generation = ref<GenerationState | null>(null);
  let trackingId: string | null = null;
  let cancelled = false;

  async function trackJob(job: Job, prompt: string) {
    const pid = projectId();
    if (!pid || trackingId === job.id) return;
    trackingId = job.id;

    let current = job;
    while (current.status === "pending" || current.status === "running") {
      if (cancelled) return;
      const phase = phaseFromJob(current);
      generation.value = jobToGenerationState(
        phase,
        current.message,
        prompt,
        true,
        current,
      );
      await sleep(800);
      current = await getJob(pid, current.id);
    }

    const finalPhase = current.status === "succeeded" ? "done" : "failed";
    generation.value = jobToGenerationState(
      finalPhase,
      current.error ?? current.message,
      prompt,
      true,
      current,
    );
    await onDone();

    const delay = current.status === "succeeded" ? 1500 : 3000;
    setTimeout(() => {
      if (trackingId === job.id) {
        generation.value = null;
        trackingId = null;
      }
    }, delay);
  }

  watch(
    projectId,
    (pid) => {
      if (!pid) {
        generation.value = null;
        trackingId = null;
        return;
      }
      listActiveJobs(pid)
        .then((jobs) => {
          if (jobs.length === 0) return;
          const job = jobs[0];
          if (trackingId === job.id) return;
          trackJob(job, job.prompt ?? "继续任务…");
        })
        .catch(console.error);
    },
    { immediate: true },
  );

  onUnmounted(() => {
    cancelled = true;
  });

  return { generation, trackJob };
}
