<script setup lang="ts">
import { ref } from "vue";
import ModelViewer from "./ModelViewer.vue";
import type { ModelPick } from "../types/pick";
import type { ModelPart } from "../types/parts";

withDefaults(
  defineProps<{
    stlUrl: string | null;
    partsUrl?: string | null;
    loading?: boolean;
    loadingLabel?: string | null;
    versionPending?: boolean;
    pick?: ModelPick | null;
  }>(),
  {
    loading: false,
    loadingLabel: null,
    versionPending: false,
    pick: null,
    partsUrl: null,
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
  captureScreenshot: () => viewerRef.value?.captureScreenshot() ?? null,
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
    <ModelViewer
      ref="viewerRef"
      :stl-url="stlUrl"
      :parts-url="partsUrl"
      :loading="loading"
      :loading-label="loadingLabel"
      :version-pending="versionPending"
      :pick="pick"
      @pick="emit('pick', $event)"
      @parts-loaded="onPartsLoaded"
    />
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
</style>
