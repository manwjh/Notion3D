<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import {
  createProject,
  getProjectState,
  health,
  listProjects,
  listVersions,
  resumeVersionStl,
  type DesignTurn,
  type Health,
  type Job,
  type ModelVersion,
  type Project,
} from "../api/client";
import AdvancedPanel from "../components/AdvancedPanel.vue";
import AgentStatusBar from "../components/AgentStatusBar.vue";
import AssistantSetupPanel from "../components/AssistantSetupPanel.vue";
import ChatPanel from "../components/ChatPanel.vue";
import GenerationOverlay from "../components/GenerationOverlay.vue";
import ModelViewer from "../components/ModelViewer.vue";
import NewProjectModal from "../components/NewProjectModal.vue";
import PreviewHeader from "../components/PreviewHeader.vue";
import ProjectLinkButton from "../components/ProjectLinkButton.vue";
import SystemStatusButton from "../components/SystemStatusButton.vue";
import { useActiveJob } from "../composables/useActiveJob";
import { useProjectRoute } from "../composables/useProjectRoute";
import { phaseLabel } from "../types/generation";
import type { ModelPick } from "../types/pick";

const projects = ref<Project[]>([]);
const projectId = ref<string | null>(null);
const versions = ref<ModelVersion[]>([]);
const selectedVersion = ref<number | null>(null);
const followLatestVersion = ref(true);
const sysHealth = ref<Health | null>(null);
const showNewProject = ref(false);
const showSetup = ref(false);
const showAdvanced = ref(false);
const creatingProject = ref(false);
const pickMode = ref(false);
const modelPick = ref<ModelPick | null>(null);
const resumingStl = ref(false);
const pendingPrompt = ref<string | null>(null);
const pendingAutoSubmit = ref(false);
const projectsLoaded = ref(false);
const unknownProject = ref(false);
const mobilePanel = ref<"studio" | "chat">("chat");
const narrowLayout = ref(false);
const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null);
const activeTurn = ref<DesignTurn | null>(null);

useProjectRoute(projectId);

async function refreshHealth() {
  try {
    sysHealth.value = await health();
  } catch {
    sysHealth.value = null;
  }
}

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
  const v = await listVersions(projectId.value);
  versions.value = v;
  if (v.length === 0) {
    selectedVersion.value = null;
    return;
  }
  if (followLatestVersion.value) {
    selectedVersion.value = v[v.length - 1].version;
    return;
  }
  if (
    selectedVersion.value != null &&
    v.some((item) => item.version === selectedVersion.value)
  ) {
    return;
  }
  selectedVersion.value = v[v.length - 1].version;
}

async function refreshAfterJob() {
  await Promise.all([refreshVersionsList(), refreshProjectState()]);
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

onMounted(() => {
  const mq = window.matchMedia("(max-width: 1024px)");
  const syncLayout = () => {
    narrowLayout.value = mq.matches;
  };
  syncLayout();
  mq.addEventListener("change", syncLayout);
  refreshProjects().catch(console.error);
  refreshHealth();
  const healthTimer = setInterval(refreshHealth, 30000);
  const projectTimer = setInterval(() => refreshProjects().catch(console.error), 15000);
  const onFocus = () => refreshProjects().catch(console.error);
  window.addEventListener("focus", onFocus);
  onUnmounted(() => {
    mq.removeEventListener("change", syncLayout);
    clearInterval(healthTimer);
    clearInterval(projectTimer);
    window.removeEventListener("focus", onFocus);
  });
});

watch(projectId, () => {
  followLatestVersion.value = true;
  refreshVersionsList().catch(console.error);
  refreshProjectState().catch(console.error);
}, { immediate: true });

watch(
  () => generation.value?.busy,
  (busy) => {
    if (busy) refreshProjectState().catch(console.error);
  },
);

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
    followLatestVersion.value = true;
    showNewProject.value = false;
    mobilePanel.value = "chat";
  } finally {
    creatingProject.value = false;
  }
}

function onTrackJob(job: Job, prompt: string) {
  followLatestVersion.value = true;
  return trackJob(job, prompt);
}

function onTurnComplete() {
  followLatestVersion.value = true;
  refreshAfterJob().catch(console.error);
}

function onSelectVersion(version: number) {
  followLatestVersion.value = false;
  selectedVersion.value = version;
  if (narrowLayout.value) mobilePanel.value = "studio";
}

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
const jobBusy = computed(() => generation.value?.busy ?? false);

const versionIncomplete = computed(
  () =>
    Boolean(
      active.value?.status === "preview_ready" &&
        !active.value.stl_url,
    ),
);

const displayStlUrl = computed(() => {
  if (jobBusy.value && followLatestVersion.value) {
    if (generation.value?.stlReady && projectId.value && jobVersion.value != null) {
      return `/api/projects/${projectId.value}/versions/${jobVersion.value}/model.stl?v=${jobVersion.value}`;
    }
    return null;
  }
  return active.value?.stl_url ? `${active.value.stl_url}?v=${active.value.version}` : null;
});

const scadUrl = computed(() => {
  if (jobBusy.value && followLatestVersion.value && projectId.value && jobVersion.value != null) {
    return `/api/projects/${projectId.value}/versions/${jobVersion.value}/model.scad`;
  }
  return active.value?.scad_url ?? null;
});

const hasModel = computed(
  () =>
    versions.value.some((v) => v.status === "complete") ||
    Boolean(displayStlUrl.value),
);

const viewerLoading = computed(
  () => jobBusy.value && followLatestVersion.value && !displayStlUrl.value,
);

const viewerLoadingLabel = computed(
  () =>
    phaseLabel(generation.value?.phase ?? "rendering", generation.value?.detail) ??
    "正在生成 3D 模型…",
);

const showBlockingOverlay = computed(
  () => viewerLoading.value && !hasModel.value,
);

const canPick = computed(() => Boolean(displayStlUrl.value));

watch(hasModel, (val, old) => {
  if (val && !old && narrowLayout.value) mobilePanel.value = "studio";
});

watch(
  () => generation.value?.stlReady,
  (ready, wasReady) => {
    if (ready && !wasReady && followLatestVersion.value && narrowLayout.value) {
      mobilePanel.value = "studio";
    }
  },
);

const hasExportable = computed(() => Boolean(active.value?.stl_url));

const currentProject = computed(() => projects.value.find((p) => p.id === projectId.value));

const agentReady = computed(() => sysHealth.value?.web_chat_mode === "agent");

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
    await trackJob(job, job.prompt ?? `生成 3D v${active.value.version}`);
    await refreshAfterJob();
  } catch (err) {
    console.error(err);
  } finally {
    resumingStl.value = false;
  }
}

function togglePickMode() {
  if (!canPick.value) return;
  pickMode.value = !pickMode.value;
  if (!pickMode.value) modelPick.value = null;
}

function onModelPick(p: ModelPick) {
  modelPick.value = p;
  pickMode.value = false;
  mobilePanel.value = "chat";
  void nextTick(() => chatPanelRef.value?.focusInput());
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"><span /><span /><span /></div>
        <div class="brand-text">
          <strong class="brand-title">Notion3D</strong>
          <span class="brand-subtitle">对话建模</span>
        </div>
        <AgentStatusBar :agent-ready="agentReady" />
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
        <button type="button" class="btn-ghost btn-ghost--compact" @click="showSetup = true">
          助手
        </button>
        <ProjectLinkButton
          :project-id="projectId"
          :web-url="currentProject?.web_url"
          :compact="narrowLayout"
        />
        <SystemStatusButton :health="sysHealth" />
      </div>
    </header>

    <nav v-if="narrowLayout" class="mobile-panel-tabs" aria-label="工作区切换">
      <button
        type="button"
        class="mobile-panel-tab"
        :class="{ active: mobilePanel === 'chat' }"
        @click="mobilePanel = 'chat'"
      >
        设计助手
      </button>
      <button
        type="button"
        class="mobile-panel-tab"
        :class="{ active: mobilePanel === 'studio' }"
        @click="mobilePanel = 'studio'"
      >
        图纸预览
      </button>
    </nav>

    <main
      class="workspace workspace--agent-first"
      :class="{
        'workspace--narrow': narrowLayout,
        'workspace--show-studio': !narrowLayout || mobilePanel === 'studio',
        'workspace--show-chat': !narrowLayout || mobilePanel === 'chat',
      }"
    >
      <aside class="chat-pane" :class="{ 'chat-pane--linked': modelPick }">
        <ChatPanel
          ref="chatPanelRef"
          :project-id="projectId"
          :has-model="hasModel"
          :initial-prompt="pendingPrompt"
          :auto-submit-initial="pendingAutoSubmit"
          :pick="modelPick"
          :generation="generation"
          :active-turn="activeTurn"
          :health="sysHealth"
          :narrow="narrowLayout"
          :versions="versions"
          :selected-version="selectedVersion"
          @consume-initial-prompt="
            pendingPrompt = null;
            pendingAutoSubmit = false;
          "
          @request-project="showNewProject = true"
          @clear-pick="modelPick = null"
          @turn-complete="onTurnComplete"
          @track-job="onTrackJob"
          @open-setup="showSetup = true"
          @select-version="onSelectVersion"
        />
      </aside>

      <section class="studio-pane viewport-pane">
        <template v-if="!projectId">
          <div class="viewer-root viewer-empty">
            <div class="viewer-empty-icon" aria-hidden="true"><span /><span /><span /></div>
            <p>图纸预览</p>
            <span>新建项目并在对话区描述需求，方案会显示在这里</span>
          </div>
        </template>

        <template v-else>
          <div v-if="unknownProject" class="unknown-project-banner" role="alert">
            找不到这个项目。若刚创建，请稍等片刻后刷新。
            <button type="button" class="btn-secondary btn-secondary--compact" @click="refreshProjects(projectId)">
              刷新
            </button>
          </div>

          <PreviewHeader
            :active-version="active"
            :version-incomplete="versionIncomplete"
            :job-busy="jobBusy"
            :resuming-stl="resumingStl"
            :pick-mode="pickMode"
            :can-pick="canPick"
            :viewing-latest="viewingLatest"
            :has-export="hasExportable"
            @resume-stl="handleResumeStl"
            @toggle-pick="togglePickMode"
            @open-advanced="showAdvanced = true"
          />

          <div class="viewer-wrap viewer-wrap--full">
            <ModelViewer
              :stl-url="displayStlUrl"
              :loading="viewerLoading"
              :loading-label="viewerLoadingLabel"
              :legacy-incomplete="versionIncomplete && !jobBusy"
              :pick-mode="pickMode"
              :pick="modelPick"
              @pick="onModelPick"
            />
            <GenerationOverlay
              v-if="showBlockingOverlay && generation"
              :state="generation"
              :has-model="false"
            />
          </div>
        </template>
      </section>
    </main>

    <AdvancedPanel
      :open="showAdvanced"
      :project-id="projectId"
      :scad-url="scadUrl"
      :version="jobBusy && followLatestVersion && jobVersion != null ? jobVersion : selectedVersion"
      :generating="jobBusy && followLatestVersion"
      :generation-phase="generation?.phase"
      :track-job="onTrackJob"
      @close="showAdvanced = false"
    />

    <NewProjectModal
      :open="showNewProject"
      :busy="creatingProject"
      @close="showNewProject = false"
      @submit="handleCreateProject"
    />

    <AssistantSetupPanel :open="showSetup" :health="sysHealth" @close="showSetup = false" />
  </div>
</template>
