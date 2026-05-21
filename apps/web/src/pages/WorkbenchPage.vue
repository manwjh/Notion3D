<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import {
  createProject,
  health,
  listProjects,
  listVersions,
  resumeVersionStl,
  type Health,
  type ModelVersion,
  type Project,
} from "../api/client";
import ChatPanel from "../components/ChatPanel.vue";
import ExportMenu from "../components/ExportMenu.vue";
import GenerationOverlay from "../components/GenerationOverlay.vue";
import ModelToolsPanel from "../components/ModelToolsPanel.vue";
import ModelViewer from "../components/ModelViewer.vue";
import NewProjectModal from "../components/NewProjectModal.vue";
import ProjectLinkButton from "../components/ProjectLinkButton.vue";
import SystemStatusButton from "../components/SystemStatusButton.vue";
import WelcomeScreen from "../components/WelcomeScreen.vue";
import WorkflowBar from "../components/WorkflowBar.vue";
import { useActiveJob } from "../composables/useActiveJob";
import { useProjectRoute } from "../composables/useProjectRoute";
import type { ModelPick } from "../types/pick";

const SAMPLE_PROMPTS = [
  "20mm 立方体",
  "40×30×20mm 带孔盒子",
  "直径 30mm 的球",
  "手机支架，倾角 15°",
];

type WorkflowStep = "describe" | "preview" | "adjust" | "export";

const projects = ref<Project[]>([]);
const projectId = ref<string | null>(null);
const versions = ref<ModelVersion[]>([]);
const selectedVersion = ref<number | null>(null);
const sysHealth = ref<Health | null>(null);
const showNewProject = ref(false);
const creatingProject = ref(false);
const showAdvancedPick = ref(false);
const pickMode = ref(false);
const modelPick = ref<ModelPick | null>(null);
const resumingStl = ref(false);
const pendingPrompt = ref<string | null>(null);
const projectsLoaded = ref(false);
const unknownProject = ref(false);

useProjectRoute(projectId);

async function refreshHealth() {
  try {
    sysHealth.value = await health();
  } catch {
    sysHealth.value = null;
  }
}

async function refreshAfterJob() {
  if (!projectId.value) return;
  const v = await listVersions(projectId.value);
  versions.value = v;
  if (v.length > 0) {
    selectedVersion.value =
      selectedVersion.value != null && v.some((item) => item.version === selectedVersion.value)
        ? selectedVersion.value
        : v[v.length - 1].version;
  }
}

const { generation, trackJob } = useActiveJob(() => projectId.value, refreshAfterJob);

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

async function refreshVersions() {
  if (!projectId.value) {
    versions.value = [];
    selectedVersion.value = null;
    return;
  }
  const v = await listVersions(projectId.value);
  versions.value = v;
  if (v.length > 0) {
    selectedVersion.value =
      selectedVersion.value != null && v.some((item) => item.version === selectedVersion.value)
        ? selectedVersion.value
        : v[v.length - 1].version;
  } else {
    selectedVersion.value = null;
  }
}

onMounted(() => {
  refreshProjects().catch(console.error);
  refreshHealth();
  const healthTimer = setInterval(refreshHealth, 30000);
  const projectTimer = setInterval(() => refreshProjects().catch(console.error), 15000);
  const onFocus = () => refreshProjects().catch(console.error);
  window.addEventListener("focus", onFocus);
  onUnmounted(() => {
    clearInterval(healthTimer);
    clearInterval(projectTimer);
    window.removeEventListener("focus", onFocus);
  });
});

watch(projectId, () => refreshVersions().catch(console.error), { immediate: true });

watch([projectsLoaded, () => projects.value.length], () => {
  if (projectsLoaded.value && projects.value.length === 0) showNewProject.value = true;
});

watch(selectedVersion, () => {
  modelPick.value = null;
  pickMode.value = false;
});

async function handleCreateProject(name: string) {
  creatingProject.value = true;
  try {
    const p = await createProject(name);
    await refreshProjects(p.id);
    projectId.value = p.id;
    showNewProject.value = false;
  } finally {
    creatingProject.value = false;
  }
}

const active = computed(() => {
  if (selectedVersion.value != null) {
    return versions.value.find((v) => v.version === selectedVersion.value);
  }
  return versions.value[versions.value.length - 1];
});

const jobVersion = computed(() => generation.value?.version ?? null);
const jobBusy = computed(() => generation.value?.busy ?? false);

const versionIncomplete = computed(
  () =>
    active.value?.status === "preview_ready" &&
    active.value.preview_url &&
    !active.value.stl_url,
);

const displayStlUrl = computed(() => {
  if (jobBusy.value) {
    if (generation.value?.stlReady && projectId.value && jobVersion.value != null) {
      return `/api/projects/${projectId.value}/versions/${jobVersion.value}/model.stl?v=${jobVersion.value}`;
    }
    return null;
  }
  return active.value?.stl_url ? `${active.value.stl_url}?v=${active.value.version}` : null;
});

const displayPreviewUrl = computed(() => {
  if (jobBusy.value && generation.value?.previewReady && generation.value.previewUrl) {
    return `${generation.value.previewUrl}?v=${jobVersion.value ?? "preview"}`;
  }
  if (versionIncomplete.value && active.value?.preview_url) {
    return `${active.value.preview_url}?v=${active.value.version}`;
  }
  return active.value?.preview_url ?? null;
});

const previewPending = computed(() =>
  Boolean(
    (jobBusy.value && generation.value?.previewReady && !generation.value?.stlReady) ||
      versionIncomplete.value,
  ),
);

const scadUrl = computed(() => {
  if (jobBusy.value && projectId.value && jobVersion.value != null) {
    return `/api/projects/${projectId.value}/versions/${jobVersion.value}/model.scad`;
  }
  return active.value?.scad_url ?? null;
});

const hasModel = computed(
  () =>
    versions.value.some((v) => v.status === "complete") ||
    Boolean(displayStlUrl.value || previewPending.value || displayPreviewUrl.value),
);

const hasExportable = computed(() => Boolean(active.value?.stl_url));

const workflowStep = computed<WorkflowStep>(() => {
  if (hasExportable.value) return "export";
  if (hasModel.value || previewPending.value) return "adjust";
  if (jobBusy.value) return "preview";
  return "describe";
});

const currentProject = computed(() => projects.value.find((p) => p.id === projectId.value));

const selectedProjectId = computed({
  get: () => projectId.value ?? "",
  set: (v: string) => {
    projectId.value = v || null;
  },
});

async function handleResumeStl() {
  if (!projectId.value || !active.value || resumingStl.value || jobBusy.value) return;
  resumingStl.value = true;
  try {
    const job = await resumeVersionStl(projectId.value, active.value.version);
    await trackJob(job, job.prompt ?? `恢复 v${active.value.version}`);
    await refreshAfterJob();
  } catch (err) {
    console.error(err);
  } finally {
    resumingStl.value = false;
  }
}

function toggleAdvanced() {
  showAdvancedPick.value = !showAdvancedPick.value;
  if (!showAdvancedPick.value) {
    pickMode.value = false;
    modelPick.value = null;
  }
}

function onModelPick(p: ModelPick) {
  modelPick.value = p;
  pickMode.value = false;
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"><span /><span /><span /></div>
        <div class="brand-text">
          <strong class="brand-title">Notion3D</strong>
          <span class="brand-subtitle">OpenSCAD 工作台</span>
        </div>
        <WorkflowBar :step="workflowStep" :busy="jobBusy" />
      </div>
      <div class="topbar-actions">
        <div class="project-picker">
          <label class="sr-only" for="project-select">选择项目</label>
          <select id="project-select" v-model="selectedProjectId">
            <option value="">选择项目…</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <button type="button" class="btn-secondary" @click="showNewProject = true">新建</button>
        <ProjectLinkButton :project-id="projectId" :web-url="currentProject?.web_url" />
        <ExportMenu v-if="hasExportable" :version="active" prominent />
        <SystemStatusButton :health="sysHealth" />
      </div>
    </header>

    <main class="workspace workspace--studio">
      <section class="studio-pane">
        <WelcomeScreen
          v-if="!projectId"
          :sample-prompts="SAMPLE_PROMPTS"
          @create-project="showNewProject = true"
          @pick-prompt="
            (text) => {
              pendingPrompt = text;
              showNewProject = true;
            }
          "
        />

        <template v-else>
          <div v-if="unknownProject" class="unknown-project-banner" role="alert">
            找不到该项目。若 Agent 刚创建，请稍等刷新；或确认 API 已启动且 project id 正确。
            <button type="button" class="btn-secondary btn-secondary--compact" @click="refreshProjects(projectId)">
              刷新列表
            </button>
          </div>
          <div class="version-bar">
            <div class="version-bar-row">
              <div class="version-list">
                <span class="version-label">{{ currentProject?.name ?? "项目" }}</span>
                <em v-if="versions.length === 0 && !jobBusy" class="version-empty">
                  等待第一次生成
                </em>
                <button
                  v-for="v in versions"
                  :key="v.version"
                  type="button"
                  class="version-btn"
                  :class="{
                    active: selectedVersion === v.version,
                    'version-btn--partial': v.status !== 'complete',
                  }"
                  :title="v.prompt ?? undefined"
                  @click="selectedVersion = v.version"
                >
                  版本 {{ v.version }}
                  <span
                    v-if="v.status === 'preview_ready'"
                    class="version-dot"
                    aria-label="仅预览"
                  />
                </button>
              </div>
              <div class="version-actions">
                <button
                  v-if="versionIncomplete && !jobBusy"
                  type="button"
                  class="btn-primary action-btn--compact"
                  :disabled="resumingStl"
                  @click="handleResumeStl"
                >
                  {{ resumingStl ? "加载中…" : "加载 3D 模型" }}
                </button>
                <button
                  type="button"
                  class="action-btn action-btn--ghost"
                  :class="{ active: showAdvancedPick }"
                  :aria-pressed="showAdvancedPick"
                  @click="toggleAdvanced"
                >
                  高级
                </button>
                <button
                  v-if="showAdvancedPick"
                  type="button"
                  class="action-btn action-btn--pick"
                  :class="{ active: pickMode }"
                  :disabled="!hasModel"
                  :aria-pressed="pickMode"
                  @click="pickMode = !pickMode"
                >
                  {{ pickMode ? "点选中…" : "3D 点选" }}
                </button>
                <ExportMenu v-if="hasExportable" :version="active" />
              </div>
            </div>
            <p v-if="active?.prompt" class="version-prompt" :title="active.prompt">
              {{ active.prompt }}
            </p>
          </div>

          <div class="studio-stack studio-stack--with-tools">
            <div class="viewer-wrap">
              <ModelViewer
                :stl-url="displayStlUrl"
                :preview-url="displayPreviewUrl"
                :preview-pending="previewPending"
                :pick-mode="pickMode"
                :pick="modelPick"
                @pick="onModelPick"
              />
              <GenerationOverlay
                v-if="generation?.busy && !generation.previewReady"
                :state="generation"
                :has-model="hasModel"
              />
            </div>
            <ModelToolsPanel
              v-if="scadUrl || jobBusy"
              :project-id="projectId"
              :scad-url="scadUrl"
              :version="jobBusy && jobVersion != null ? jobVersion : selectedVersion"
              :generating="jobBusy"
              :generation-phase="generation?.phase"
              :track-job="trackJob"
            />
          </div>
        </template>
      </section>

      <aside class="chat-pane" :class="{ 'chat-pane--linked': modelPick }">
        <ChatPanel
          :project-id="projectId"
          :sample-prompts="SAMPLE_PROMPTS"
          :has-model="hasModel"
          :initial-prompt="pendingPrompt"
          :pick="modelPick"
          :generation="generation"
          :track-job="trackJob"
          @consume-initial-prompt="pendingPrompt = null"
          @request-project="showNewProject = true"
          @clear-pick="modelPick = null"
        />
      </aside>
    </main>

    <NewProjectModal
      :open="showNewProject"
      :busy="creatingProject"
      :sample-prompts="SAMPLE_PROMPTS"
      @close="showNewProject = false"
      @submit="handleCreateProject"
    />
  </div>
</template>
