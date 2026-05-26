<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import type { ModelVersion } from "../api/client";
import ExportMenu from "./ExportMenu.vue";

withDefaults(
  defineProps<{
    activeVersion: ModelVersion | null | undefined;
    projectName?: string | null;
    versionIncomplete: boolean;
    jobBusy: boolean;
    resumingStl: boolean;
    viewingLatest: boolean;
    hasExport: boolean;
  }>(),
  {
    projectName: null,
  },
);

const emit = defineEmits<{
  resumeStl: [];
}>();

const menuOpen = ref(false);
const menuRef = ref<HTMLElement | null>(null);

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
</style>
