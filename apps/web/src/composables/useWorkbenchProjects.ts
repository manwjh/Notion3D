import { computed, onMounted, onUnmounted, ref, watch, type Ref } from "vue";
import { createProject, listProjects, type Project } from "../api/client";

export function useWorkbenchProjects(projectId: Ref<string | null>) {
  const projects = ref<Project[]>([]);
  const projectsLoaded = ref(false);
  const unknownProject = ref(false);
  const showNewProject = ref(false);
  const creatingProject = ref(false);

  const currentProject = computed(() =>
    projects.value.find((p) => p.id === projectId.value),
  );

  const selectedProjectId = computed({
    get: () => projectId.value ?? "",
    set: (value: string) => {
      projectId.value = value || null;
    },
  });

  async function refreshProjects(preferredId?: string | null) {
    const list = await listProjects();
    projects.value = list;
    const target = preferredId ?? projectId.value;
    if (target && list.some((p) => p.id === target)) {
      projectId.value = target;
      unknownProject.value = false;
    } else if (target) {
      unknownProject.value = !list.some((p) => p.id === target);
      projectId.value = target;
    } else if (projectId.value && list.some((p) => p.id === projectId.value)) {
      unknownProject.value = false;
    } else {
      unknownProject.value = false;
      projectId.value = list[0]?.id ?? null;
    }
    projectsLoaded.value = true;
  }

  async function handleCreateProject(name: string) {
    creatingProject.value = true;
    try {
      const project = await createProject(name);
      await refreshProjects(project.id);
      projectId.value = project.id;
      showNewProject.value = false;
      return project.id;
    } finally {
      creatingProject.value = false;
    }
  }

  watch([projectsLoaded, () => projects.value.length], () => {
    if (projectsLoaded.value && projects.value.length === 0) {
      showNewProject.value = true;
    }
  });

  onMounted(() => {
    refreshProjects().catch(console.error);
    const projectTimer = setInterval(
      () => refreshProjects().catch(console.error),
      15000,
    );
    const onFocus = () => refreshProjects().catch(console.error);
    window.addEventListener("focus", onFocus);
    onUnmounted(() => {
      clearInterval(projectTimer);
      window.removeEventListener("focus", onFocus);
    });
  });

  return {
    projects,
    projectsLoaded,
    unknownProject,
    showNewProject,
    creatingProject,
    currentProject,
    selectedProjectId,
    refreshProjects,
    handleCreateProject,
  };
}
