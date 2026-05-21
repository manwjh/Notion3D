import type { Ref } from "vue";
import { watch } from "vue";
import { useRoute, useRouter } from "vue-router";

/** Sync selected project with /p/:projectId deep links (Agent → Web handoff). */
export function useProjectRoute(projectId: Ref<string | null>) {
  const route = useRoute();
  const router = useRouter();

  function routeProjectId(): string | null {
    const param = route.params.projectId;
    if (typeof param === "string" && param) return param;
    const query = route.query.project;
    if (typeof query === "string" && query) return query;
    return null;
  }

  watch(
    () => routeProjectId(),
    (id) => {
      if (id && id !== projectId.value) projectId.value = id;
    },
    { immediate: true },
  );

  watch(projectId, (id) => {
    const onProjectRoute = route.name === "project";
    if (!id) {
      if (onProjectRoute) router.replace({ name: "home" });
      return;
    }
    if (!onProjectRoute || route.params.projectId !== id) {
      router.replace({ name: "project", params: { projectId: id } });
    }
  });
}

export function projectWebPath(projectId: string): string {
  return `/p/${projectId}`;
}

export function projectWebUrl(projectId: string): string {
  return `${window.location.origin}${projectWebPath(projectId)}`;
}
