<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import type { ModelVersion } from "../api/client";
import ExportMenu from "./ExportMenu.vue";

const props = withDefaults(
  defineProps<{
    activeVersion: ModelVersion | null | undefined;
    projectName?: string | null;
    versionIncomplete: boolean;
    jobBusy: boolean;
    resumingStl: boolean;
    pickMode: boolean;
    canPick: boolean;
    viewingLatest: boolean;
    hasExport: boolean;
    sourceBackend?: "forge" | "scad";
    viewMode?: "assembly" | "forge";
    canForgePreview?: boolean;
  }>(),
  {
    viewMode: "assembly",
    canForgePreview: false,
    sourceBackend: "forge",
    projectName: null,
  },
);

const emit = defineEmits<{
  resumeStl: [];
  togglePick: [];
  setViewMode: [mode: "assembly" | "forge"];
}>();

const menuOpen = ref(false);
const menuRef = ref<HTMLElement | null>(null);

const showViewToggle = computed(
  () => props.canForgePreview && props.sourceBackend !== "scad" && Boolean(props.activeVersion?.forge_url),
);

function onDocClick(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) menuOpen.value = false;
}

onMounted(() => document.addEventListener("mousedown", onDocClick));
onUnmounted(() => document.removeEventListener("mousedown", onDocClick));
</script>

<template>
  <div class="workbench-context-bar">
    <div class="workbench-context-main">
      <span v-if="projectName" class="workbench-project-name">{{ projectName }}</span>
      <template v-if="activeVersion">
        <span class="workbench-version">v{{ activeVersion.version }}</span>
        <span
          class="workbench-version-tag"
          :class="{ ok: activeVersion.status === 'complete' }"
        >
          {{ activeVersion.status === "complete" ? "可导出" : "待补全" }}
        </span>
        <span v-if="!viewingLatest" class="workbench-version-note">历史方案</span>
      </template>
    </div>

    <div class="workbench-context-actions">
      <div v-if="showViewToggle" class="preview-view-toggle" role="tablist">
        <button
          type="button"
          role="tab"
          class="action-btn action-btn--ghost"
          :class="{ active: viewMode !== 'forge' }"
          @click="emit('setViewMode', 'assembly')"
        >
          装配
        </button>
        <button
          type="button"
          role="tab"
          class="action-btn action-btn--ghost"
          :class="{ active: viewMode === 'forge' }"
          @click="emit('setViewMode', 'forge')"
        >
          Forge 实时
        </button>
      </div>

      <button
        type="button"
        class="action-btn action-btn--pick"
        :class="{ active: pickMode }"
        :disabled="!canPick"
        :aria-pressed="pickMode"
        @click="emit('togglePick')"
      >
        {{ pickMode ? "点选中" : "点选" }}
      </button>

      <ExportMenu v-if="hasExport" :version="activeVersion" />

      <div ref="menuRef" class="preview-menu">
        <button
          type="button"
          class="action-btn action-btn--ghost preview-menu-trigger"
          :aria-expanded="menuOpen"
          aria-label="更多"
          @click="menuOpen = !menuOpen"
        >
          ⋯
        </button>
        <div v-if="menuOpen" class="preview-menu-dropdown">
          <button
            v-if="versionIncomplete && !jobBusy"
            type="button"
            :disabled="resumingStl"
            @click="
              emit('resumeStl');
              menuOpen = false;
            "
          >
            {{ resumingStl ? "生成中…" : "生成可打印模型" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workbench-context-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  flex-wrap: wrap;
  padding: 0.4rem 0.85rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-surface);
  flex-shrink: 0;
}

.workbench-context-main {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
  font-size: 0.8rem;
}

.workbench-project-name {
  font-weight: 600;
  color: var(--text);
  max-width: 14rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workbench-version {
  color: var(--text-muted);
}

.workbench-version-tag {
  font-size: 0.68rem;
  color: var(--warn);
}

.workbench-version-tag.ok {
  color: var(--success);
}

.workbench-version-note {
  font-size: 0.68rem;
  color: var(--text-subtle);
}

.workbench-context-actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
}

.preview-view-toggle {
  display: inline-flex;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  overflow: hidden;
}

.preview-view-toggle .action-btn {
  border: none;
  border-radius: 0;
  font-size: 0.72rem;
  padding: 0.28rem 0.5rem;
}

.preview-view-toggle .action-btn.active {
  background: #2a3550;
  color: #dbe4ff;
}
</style>
