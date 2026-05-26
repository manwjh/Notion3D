import { onUnmounted, ref, watch } from "vue";
import { listActiveJobs, waitJob, type Job } from "../api/client";
import {
  jobToGenerationState,
  phaseFromJob,
  type GenerationState,
} from "../types/generation";

export function useActiveJob(
  projectId: () => string | null,
  onDone: () => void | Promise<void>,
) {
  const generation = ref<GenerationState | null>(null);
  let trackingId: string | null = null;
  let cancelled = false;

  function applyJobState(current: Job, prompt: string) {
    const phase = phaseFromJob(current);
    generation.value = jobToGenerationState(
      phase,
      current.message,
      prompt,
      true,
      current,
    );
  }

  async function finalizeJob(current: Job, prompt: string) {
    const finalPhase = current.status === "succeeded" ? "done" : "failed";
    generation.value = jobToGenerationState(
      finalPhase,
      current.error ?? current.message,
      prompt,
      true,
      current,
    );
    try {
      await onDone();
    } catch (err) {
      console.error(err);
    } finally {
      const delay = current.status === "succeeded" ? 1500 : 3000;
      setTimeout(() => {
        if (trackingId === current.id) {
          generation.value = null;
          trackingId = null;
        }
      }, delay);
    }
  }

  async function trackJob(job: Job, prompt: string) {
    const pid = projectId();
    if (!pid || trackingId === job.id) return;
    trackingId = job.id;

    if (cancelled) return;

    const current = await waitJob(pid, job, (updated) => {
      if (cancelled) return;
      applyJobState(updated, prompt);
    });

    if (cancelled) return;
    await finalizeJob(current, prompt);
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
