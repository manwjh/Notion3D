<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import type { ModelVersion } from "../api/client";
import ExportMenu from "./ExportMenu.vue";

defineProps<{
  activeVersion: ModelVersion | null | undefined;
  versionIncomplete: boolean;
  jobBusy: boolean;
  resumingStl: boolean;
  pickMode: boolean;
  canPick: boolean;
  viewingLatest: boolean;
  hasExport: boolean;
}>();

const emit = defineEmits<{
  resumeStl: [];
  togglePick: [];
  openAdvanced: [];
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
  <header class="preview-header">
    <div class="preview-header-main">
      <h2 class="preview-title">图纸预览</h2>
      <p v-if="activeVersion" class="preview-meta">
        正在查看 v{{ activeVersion.version }}
        <span v-if="activeVersion.status !== 'complete'" class="preview-meta-tag">待补全</span>
        <span v-else class="preview-meta-tag preview-meta-tag--ok">可导出</span>
        <span v-if="!viewingLatest" class="preview-meta-note">· 历史方案</span>
      </p>
      <p v-else class="preview-meta preview-meta--muted">暂无图纸</p>
    </div>

    <div class="preview-header-actions">
      <button
        type="button"
        class="action-btn action-btn--pick"
        :class="{ active: pickMode }"
        :disabled="!canPick"
        :aria-pressed="pickMode"
        :title="canPick ? '点选模型位置，回对话区描述修改' : '需要可查看的模型'"
        @click="emit('togglePick')"
      >
        {{ pickMode ? "点选中…" : "点选" }}
      </button>

      <ExportMenu v-if="hasExport" :version="activeVersion" />

      <div ref="menuRef" class="preview-menu">
        <button
          type="button"
          class="action-btn action-btn--ghost preview-menu-trigger"
          :aria-expanded="menuOpen"
          aria-label="更多操作"
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
          <button
            type="button"
            @click="
              emit('openAdvanced');
              menuOpen = false;
            "
          >
            编辑 OpenSCAD…
            <span class="preview-menu-hint">不经过助手</span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
