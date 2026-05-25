<script setup lang="ts">
import { ref } from "vue";
import ModelViewer from "./ModelViewer.vue";
import ForgePreviewViewer from "./ForgePreviewViewer.vue";
import type { ModelPick } from "../types/pick";
import type { ModelPart } from "../types/parts";

withDefaults(
  defineProps<{
    stlUrl: string | null;
    partsUrl?: string | null;
    loading?: boolean;
    loadingLabel?: string | null;
    legacyIncomplete?: boolean;
    pickMode?: boolean;
    pick?: ModelPick | null;
    viewMode?: "assembly" | "forge";
    projectId?: string | null;
    previewVersion?: number | null;
    forgePreviewEnabled?: boolean;
  }>(),
  {
    loading: false,
    loadingLabel: null,
    legacyIncomplete: false,
    pickMode: false,
    pick: null,
    partsUrl: null,
    viewMode: "assembly",
    projectId: null,
    previewVersion: null,
    forgePreviewEnabled: false,
  },
);

const emit = defineEmits<{
  pick: [value: ModelPick];
  partsLoaded: [parts: ModelPart[]];
}>();

const viewerRef = ref<InstanceType<typeof ModelViewer> | null>(null);

function onPartsLoaded(parts: ModelPart[]) {
  emit("partsLoaded", parts);
}

defineExpose({
  setPartVisible: (id: string, v: boolean) => viewerRef.value?.setPartVisible(id, v),
  setPartOpacity: (id: string, o: number) => viewerRef.value?.setPartOpacity(id, o),
  fitPart: (id: string) => viewerRef.value?.fitPart(id),
  fitAll: () => viewerRef.value?.fitAll(),
  highlightPart: (id: string | null) => viewerRef.value?.highlightPart(id),
  applyPartDefaults: (parts: ModelPart[]) => {
    for (const part of parts) {
      if (part.opacity != null && part.opacity < 1) {
        viewerRef.value?.setPartOpacity(part.id, part.opacity);
      }
    }
    const hasShell =
      parts.some((p) => (p.opacity ?? 1) < 1) ||
      parts.some((p) => /shell|外壳|壳/i.test(p.label));
    if (hasShell) {
      for (const part of parts) {
        const isShell = /shell|外壳|壳/i.test(part.label);
        viewerRef.value?.setPartOpacity(part.id, isShell ? 0.25 : 1);
      }
    } else {
      viewerRef.value?.fitAll();
    }
  },
});
</script>

<template>
  <div class="viewport-host">
    <ForgePreviewViewer
      v-if="viewMode === 'forge'"
      :project-id="projectId ?? null"
      :version="previewVersion ?? null"
      :enabled="forgePreviewEnabled"
    />
    <ModelViewer
      v-else
      ref="viewerRef"
      :stl-url="stlUrl"
      :parts-url="partsUrl"
      :loading="loading"
      :loading-label="loadingLabel"
      :legacy-incomplete="legacyIncomplete"
      :pick-mode="pickMode"
      :pick="pick"
      @pick="emit('pick', $event)"
      @parts-loaded="onPartsLoaded"
    />
    <div v-if="pickMode && viewMode === 'assembly'" class="viewport-pick-hint">
      点击模型或左侧部件树选择修改目标
    </div>
  </div>
</template>

<style scoped>
.viewport-host {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.viewport-pick-hint {
  position: absolute;
  top: 0.65rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: rgba(20, 24, 32, 0.92);
  border: 1px solid rgba(110, 168, 254, 0.45);
  color: #aeb6c8;
  font-size: 0.75rem;
  pointer-events: none;
}
</style>
