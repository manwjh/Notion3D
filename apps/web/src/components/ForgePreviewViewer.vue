<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { startForgePreview } from "../api/client";

const props = defineProps<{
  projectId: string | null;
  version: number | null;
  enabled?: boolean;
}>();

const embedUrl = ref<string | null>(null);
const error = ref<string | null>(null);
const loading = ref(false);

async function loadPreview() {
  if (!props.enabled || !props.projectId || props.version == null) {
    embedUrl.value = null;
    error.value = null;
    return;
  }
  loading.value = true;
  error.value = null;
  try {
    const result = await startForgePreview(props.projectId, props.version);
    embedUrl.value = result.embed_url ?? result.url;
  } catch (e) {
    embedUrl.value = null;
    error.value = e instanceof Error ? e.message : "Forge 预览启动失败";
  } finally {
    loading.value = false;
  }
}

watch(
  () => [props.projectId, props.version, props.enabled] as const,
  () => {
    void loadPreview();
  },
  { immediate: true },
);

onMounted(() => {
  void loadPreview();
});
</script>

<template>
  <div class="forge-preview-shell">
    <div v-if="loading" class="forge-preview-status">
      <span class="spinner" aria-hidden="true" />
      正在启动 ForgeCAD 实时预览…
    </div>
    <div v-else-if="error" class="forge-preview-status forge-preview-status--error">
      <p>{{ error }}</p>
      <span>请确认已运行 <code>cd apps/forge-runner && npm install</code></span>
      <button type="button" class="btn-secondary btn-secondary--compact" @click="loadPreview">
        重试
      </button>
    </div>
    <iframe
      v-else-if="embedUrl"
      class="forge-preview-frame"
      :src="embedUrl"
      title="ForgeCAD 实时预览"
      allow="fullscreen"
    />
    <div v-else class="forge-preview-status">
      <p>选择有 Forge 源码的版本以启用实时预览</p>
    </div>
  </div>
</template>

<style scoped>
.forge-preview-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #0f1218;
}

.forge-preview-frame {
  flex: 1;
  width: 100%;
  border: none;
  min-height: 0;
}

.forge-preview-status {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: #aeb6c8;
  font-size: 0.9rem;
  padding: 1.5rem;
  text-align: center;
}

.forge-preview-status--error p {
  margin: 0;
  color: #f0a8a8;
}

.forge-preview-status code {
  font-size: 0.8rem;
  color: #8ec0ff;
}
</style>
