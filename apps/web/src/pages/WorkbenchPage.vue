<script setup lang="ts">
import { computed, ref } from "vue";
import { resumeVersionStl } from "../api/client";
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
import { phaseLabel } from "../types/generation";
import { useProjectRoute } from "../composables/useProjectRoute";
import { useWorkbenchHealth } from "../composables/useWorkbenchHealth";
import { useWorkbenchProjects } from "../composables/useWorkbenchProjects";
import { useWorkbenchSession } from "../composables/useWorkbenchSession";
import { useWorkbenchDisplay } from "../composables/useWorkbenchDisplay";
import {
  useWorkbenchLayout,
  useWorkbenchViewport,
} from "../composables/useWorkbenchViewport";

const projectId = ref<string | null>(null);
useProjectRoute(projectId);

const { sysHealth } = useWorkbenchHealth();
const {
  projects,
  unknownProject,
  showNewProject,
  creatingProject,
  currentProject,
  selectedProjectId,
  refreshProjects,
  handleCreateProject: createProjectAndSelect,
} = useWorkbenchProjects(projectId);

const {
  versions,
  selectedVersion,
  followLatestVersion,
  activeTurn,
  generation,
  active,
  viewingLatest,
  jobVersion,
  jobBusy,
  versionIncomplete,
  refreshAfterJob,
  syncActiveTurn,
  onTrackJob,
  onTurnComplete,
  onSelectVersion: selectVersion,
} = useWorkbenchSession(projectId);

const {
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
} = useWorkbenchDisplay({
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
});

const pendingPrompt = ref<string | null>(null);
const pendingAutoSubmit = ref(false);
const resumingStl = ref(false);

const { narrowLayout, mobilePanel, focusMobilePanel } = useWorkbenchLayout({
  hasModel,
  stlReady: computed(() => generation.value?.stlReady),
  followLatestVersion,
});

const {
  modelPick,
  viewportParts,
  partHidden,
  partOpacities,
  viewportRef,
  chatPanelRef,
  onPartsLoaded,
  onModelPick,
  onPartPick,
  onClearPartPick,
  onTogglePart,
  onPartOpacity,
  onFocusPart,
  onShowAllParts,
  onFitAllParts,
  onShellMode,
} = useWorkbenchViewport({
  selectedVersion,
  narrowLayout,
  mobilePanel,
});

const jobStatusLabel = computed(() => {
  if (resumingStl.value) return "正在生成可打印模型…";
  if (!jobBusy.value) return null;
  return (
    phaseLabel(generation.value?.phase ?? "generating", generation.value?.detail) ??
    "正在处理…"
  );
});

const selectedPartLabel = computed(
  () => modelPick.value?.label ?? modelPick.value?.element ?? null,
);

async function submitNewProject(name: string) {
  const id = await createProjectAndSelect(name);
  if (id) {
    followLatestVersion.value = true;
    focusMobilePanel("chat");
  }
}

function handleSelectVersion(version: number) {
  selectVersion(version);
  if (narrowLayout.value) focusMobilePanel("viewport");
}

async function handleResumeStl() {
  if (!projectId.value || !active.value || resumingStl.value || jobBusy.value) return;
  resumingStl.value = true;
  try {
    const job = await resumeVersionStl(projectId.value, active.value.version);
    await onTrackJob(job, job.prompt ?? `生成 3D v${active.value.version}`);
    await refreshAfterJob();
  } catch (err) {
    console.error(err);
  } finally {
    resumingStl.value = false;
  }
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"><span /><span /><span /></div>
        <div class="brand-text">
          <strong class="brand-title">Notion3D</strong>
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
      :viewing-latest="viewingLatest"
      :has-export="hasExportable"
      @resume-stl="handleResumeStl"
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
              :pick="modelPick"
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
          @clear-pick="onClearPartPick"
          @turn-complete="onTurnComplete"
          @track-job="onTrackJob"
          @active-turn-change="syncActiveTurn"
          @select-version="handleSelectVersion"
        />
      </aside>
    </main>

    <WorkbenchStatusBar
      :health="sysHealth"
      :validation-warnings="activeValidationWarnings"
      :project-selected="Boolean(projectId)"
      :job-status-label="jobStatusLabel"
      :part-count="viewportParts.length"
      :version-incomplete="versionIncomplete"
      :has-model="hasModel"
      :selected-part-label="selectedPartLabel"
    />

    <NewProjectModal
      :open="showNewProject"
      :busy="creatingProject"
      @close="showNewProject = false"
      @submit="submitNewProject"
    />
  </div>
</template>
