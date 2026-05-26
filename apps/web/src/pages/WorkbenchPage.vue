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
import StructurePanel from "../components/StructurePanel.vue";
import ViewportHost from "../components/ViewportHost.vue";
import WorkbenchContextBar from "../components/WorkbenchContextBar.vue";
import WorkbenchStatusBar from "../components/WorkbenchStatusBar.vue";
import ChatPanel from "../components/ChatPanel.vue";
import GenerationOverlay from "../components/GenerationOverlay.vue";
import NewProjectModal from "../components/NewProjectModal.vue";
import ProjectLinkButton from "../components/ProjectLinkButton.vue";
import SystemStatusButton from "../components/SystemStatusButton.vue";
import { WORKBENCH } from "../strings/zh";
import type { ModelPart } from "../types/parts";
import { useActiveJob } from "../composables/useActiveJob";
import { useProjectRoute } from "../composables/useProjectRoute";
import { phaseLabel } from "../types/generation";
import { mergeDesignContext } from "../utils/designContext";
import type { ModelPick } from "../types/pick";

const projects = ref<Project[]>([]);
const projectId = ref<string | null>(null);
const versions = ref<ModelVersion[]>([]);
const selectedVersion = ref<number | null>(null);
const followLatestVersion = ref(true);
const sysHealth = ref<Health | null>(null);
const showNewProject = ref(false);
const creatingProject = ref(false);
const pickMode = ref(false);
const modelPick = ref<ModelPick | null>(null);
const previewViewMode = ref<"assembly" | "forge">("assembly");
const viewportParts = ref<ModelPart[]>([]);
const partHidden = ref<Record<string, boolean>>({});
const partOpacities = ref<Record<string, number>>({});
const viewportRef = ref<InstanceType<typeof ViewportHost> | null>(null);
const resumingStl = ref(false);
const pendingPrompt = ref<string | null>(null);
const pendingAutoSubmit = ref(false);
const projectsLoaded = ref(false);
const unknownProject = ref(false);
const mobilePanel = ref<"structure" | "viewport" | "chat">("chat");
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
  viewportParts.value = [];
  partHidden.value = {};
  partOpacities.value = {};
});

function onPartsLoaded(parts: ModelPart[]) {
  viewportParts.value = parts;
  partHidden.value = {};
  partOpacities.value = {};
  for (const part of parts) {
    partOpacities.value[part.id] = part.opacity ?? 1;
  }
  viewportRef.value?.applyPartDefaults(parts);
  if (modelPick.value?.element) {
    viewportRef.value?.highlightPart(modelPick.value.element);
  }
}

function onPartPick(part: ModelPart) {
  if (modelPick.value?.element === part.id) {
    onClearPartPick();
    return;
  }
  onModelPick({
    x: 0,
    y: 0,
    z: 0,
    nx: 0,
    ny: 1,
    nz: 0,
    element: part.id,
    label: part.label,
  });
}

function onClearPartPick() {
  modelPick.value = null;
  viewportRef.value?.highlightPart(null);
}

function onTogglePart(partId: string) {
  partHidden.value[partId] = !partHidden.value[partId];
  viewportRef.value?.setPartVisible(partId, !partHidden.value[partId]);
}

function onPartOpacity(partId: string, value: number) {
  partOpacities.value[partId] = value;
  viewportRef.value?.setPartOpacity(partId, value);
}

function onFocusPart(partId: string) {
  viewportRef.value?.fitPart(partId);
}

function onShowAllParts() {
  for (const part of viewportParts.value) {
    partHidden.value[part.id] = false;
    viewportRef.value?.setPartVisible(part.id, true);
  }
}

function onFitAllParts() {
  viewportRef.value?.fitAll();
}

function onShellMode() {
  for (const part of viewportParts.value) {
    const isShell = /shell|外壳|壳/i.test(part.label);
    const opacity = isShell ? 0.25 : 1;
    partOpacities.value[part.id] = opacity;
    viewportRef.value?.setPartOpacity(part.id, opacity);
    partHidden.value[part.id] = false;
    viewportRef.value?.setPartVisible(part.id, true);
  }
}

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
  if (narrowLayout.value) mobilePanel.value = "viewport";
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
      active.value?.status === "pending" &&
        active.value.forge_url &&
        !active.value.stl_url,
    ),
);

const displayPartsUrl = computed(() => {
  if (jobBusy.value && followLatestVersion.value) {
    if (generation.value?.stlReady && projectId.value && jobVersion.value != null) {
      return `/api/projects/${projectId.value}/versions/${jobVersion.value}/parts.json?v=${jobVersion.value}`;
    }
    return null;
  }
  return active.value?.parts_url
    ? `${active.value.parts_url}?v=${active.value.version}`
    : null;
});

const displayStlUrl = computed(() => {
  if (jobBusy.value && followLatestVersion.value) {
    if (generation.value?.stlReady && projectId.value && jobVersion.value != null) {
      return `/api/projects/${projectId.value}/versions/${jobVersion.value}/model.stl?v=${jobVersion.value}`;
    }
    return null;
  }
  return active.value?.stl_url ? `${active.value.stl_url}?v=${active.value.version}` : null;
});

const sourceUrl = computed(() => {
  const ver = jobBusy.value && followLatestVersion.value ? jobVersion.value : active.value?.version;
  if (!projectId.value || ver == null) return null;

  const base = `/api/projects/${projectId.value}/versions/${ver}`;

  if (jobBusy.value && followLatestVersion.value) {
    return `${base}/model.forge.js?v=${ver}`;
  }

  if (active.value?.forge_url) {
    return `${active.value.forge_url}?v=${active.value.version}`;
  }
  return null;
});

const forgeSourcesUrl = computed(() => {
  const ver = jobBusy.value && followLatestVersion.value ? jobVersion.value : active.value?.version;
  if (!projectId.value || ver == null) return null;
  if (jobBusy.value && followLatestVersion.value) {
    return `/api/projects/${projectId.value}/versions/${ver}/forge-sources?v=${ver}`;
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

const canPick = computed(() => Boolean(displayStlUrl.value || displayPartsUrl.value));

const canForgePreview = computed(
  () =>
    Boolean(sysHealth.value?.forge_preview_available ?? sysHealth.value?.forgecad_available) &&
    Boolean(active.value?.forge_url),
);

const activePreviewVersion = computed(() =>
  jobBusy.value && followLatestVersion.value && jobVersion.value != null
    ? jobVersion.value
    : selectedVersion.value,
);

watch(previewViewMode, (mode) => {
  if (mode === "forge") pickMode.value = false;
});

watch(
  () => [active.value?.version, active.value?.forge_url] as const,
  () => {
    if (!canForgePreview.value && previewViewMode.value === "forge") {
      previewViewMode.value = "assembly";
    }
  },
);

watch(hasModel, (val, old) => {
  if (val && !old && narrowLayout.value) mobilePanel.value = "viewport";
});

watch(
  () => generation.value?.stlReady,
  (ready, wasReady) => {
    if (ready && !wasReady && followLatestVersion.value && narrowLayout.value) {
      mobilePanel.value = "viewport";
    }
  },
);

const hasExportable = computed(() => Boolean(active.value?.stl_url));

const activeValidationWarnings = computed(() => {
  const fromVersion = active.value?.validation_warnings ?? [];
  if (jobBusy.value && followLatestVersion.value) {
    const fromJob = generation.value?.validationWarnings ?? [];
    if (fromJob.length) return fromJob;
  }
  return fromVersion;
});

const designContext = computed(() =>
  mergeDesignContext(
    activeTurn.value,
    active.value,
    Boolean(activeTurn.value && (jobBusy.value || viewingLatest.value)),
  ),
);

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
  previewViewMode.value = "assembly";
  mobilePanel.value = "chat";
  viewportRef.value?.highlightPart(p.element ?? null);
  void nextTick(() => {
    chatPanelRef.value?.prefillFromPick?.(p);
    chatPanelRef.value?.focusInput();
  });
}

const editorVersion = computed(() =>
  jobBusy.value && followLatestVersion.value && jobVersion.value != null
    ? jobVersion.value
    : selectedVersion.value,
);
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"><span /><span /><span /></div>
        <div class="brand-text">
          <strong class="brand-title">Notion3D</strong>
          <span class="brand-subtitle">{{ WORKBENCH.subtitle }}</span>
        </div>
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
        :class="{ active: mobilePanel === 'structure' }"
        @click="mobilePanel = 'structure'"
      >
        结构
      </button>
      <button
        type="button"
        class="mobile-panel-tab"
        :class="{ active: mobilePanel === 'viewport' }"
        @click="mobilePanel = 'viewport'"
      >
        视口
      </button>
      <button
        type="button"
        class="mobile-panel-tab"
        :class="{ active: mobilePanel === 'chat' }"
        @click="mobilePanel = 'chat'"
      >
        {{ WORKBENCH.mobileChatTab }}
      </button>
    </nav>

    <WorkbenchContextBar
      v-if="projectId"
      :active-version="active"
      :project-name="currentProject?.name"
      :version-incomplete="versionIncomplete"
      :job-busy="jobBusy"
      :resuming-stl="resumingStl"
      :pick-mode="pickMode"
      :can-pick="canPick"
      :viewing-latest="viewingLatest"
      :has-export="hasExportable"
      :view-mode="previewViewMode"
      :can-forge-preview="canForgePreview"
      @resume-stl="handleResumeStl"
      @toggle-pick="togglePickMode"
      @set-view-mode="previewViewMode = $event"
    />

    <main
      class="workspace workspace--workbench"
      :class="{
        'workspace--narrow': narrowLayout,
        'workspace--show-structure': !narrowLayout || mobilePanel === 'structure',
        'workspace--show-viewport': !narrowLayout || mobilePanel === 'viewport',
        'workspace--show-chat': !narrowLayout || mobilePanel === 'chat',
      }"
    >
      <aside class="structure-pane">
        <div v-if="!projectId" class="structure-empty">
          <p>部件树与参数</p>
          <span>创建项目并开始建模后，结构面板会显示在这里。</span>
        </div>
        <StructurePanel
          v-else
          :parts="viewportParts"
          :pick="modelPick"
          :src-files="active?.src_files"
          :has-forge-source="Boolean(active?.forge_url)"
          :project-id="projectId"
          :source-url="sourceUrl"
          :forge-sources-url="forgeSourcesUrl"
          :version="editorVersion"
          :generating="jobBusy && followLatestVersion"
          :generation-phase="generation?.phase"
          :track-job="onTrackJob"
          :hidden="partHidden"
          :opacities="partOpacities"
          @pick="onPartPick"
          @clear-pick="onClearPartPick"
          @toggle="onTogglePart"
          @opacity="onPartOpacity"
          @focus="onFocusPart"
          @show-all="onShowAllParts"
          @fit-all="onFitAllParts"
          @shell-mode="onShellMode"
        />
      </aside>

      <section class="studio-pane viewport-pane">
        <template v-if="!projectId">
          <div class="viewer-root viewer-empty">
            <div class="viewer-empty-icon" aria-hidden="true"><span /><span /><span /></div>
            <p>3D 视口</p>
            <span>{{ WORKBENCH.viewportEmpty }}</span>
          </div>
        </template>

        <template v-else>
          <div v-if="unknownProject" class="unknown-project-banner" role="alert">
            找不到这个项目。若刚创建，请稍等片刻后刷新。
            <button type="button" class="btn-secondary btn-secondary--compact" @click="refreshProjects(projectId)">
              刷新
            </button>
          </div>

          <div class="viewer-wrap viewer-wrap--full">
            <ViewportHost
              ref="viewportRef"
              :stl-url="displayStlUrl"
              :parts-url="displayPartsUrl"
              :loading="viewerLoading"
              :loading-label="viewerLoadingLabel"
              :version-pending="versionIncomplete && !jobBusy"
              :pick-mode="pickMode"
              :pick="modelPick"
              :view-mode="previewViewMode"
              :project-id="projectId"
              :preview-version="activePreviewVersion"
              :forge-preview-enabled="canForgePreview"
              @pick="onModelPick"
              @parts-loaded="onPartsLoaded"
            />
            <GenerationOverlay
              v-if="showBlockingOverlay && generation"
              :state="generation"
              :has-model="false"
            />
          </div>
        </template>
      </section>

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
          :design-context="designContext"
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
          @select-version="onSelectVersion"
        />
      </aside>
    </main>

    <WorkbenchStatusBar
      :health="sysHealth"
      :validation-warnings="activeValidationWarnings"
    />

    <NewProjectModal
      :open="showNewProject"
      :busy="creatingProject"
      @close="showNewProject = false"
      @submit="handleCreateProject"
    />
  </div>
</template>
