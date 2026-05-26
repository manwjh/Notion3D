<script setup lang="ts">
import { computed, ref } from "vue";
import type { Job } from "../api/client";
import type { JobPhase } from "../types/generation";
import type { ModelPart } from "../types/parts";
import type { ModelPick } from "../types/pick";
import PartTreePanel from "./PartTreePanel.vue";
import ModelToolsPanel from "./ModelToolsPanel.vue";

const props = defineProps<{
  parts: ModelPart[];
  pick?: ModelPick | null;
  srcFiles?: string[];
  hasForgeSource?: boolean;
  projectId: string | null;
  sourceUrl: string | null;
  forgeSourcesUrl?: string | null;
  version: number | null;
  generating?: boolean;
  generationPhase?: JobPhase;
  trackJob: (job: Job, prompt: string) => Promise<void>;
  hidden: Record<string, boolean>;
  opacities: Record<string, number>;
}>();

const emit = defineEmits<{
  pick: [part: ModelPart];
  clearPick: [];
  toggle: [partId: string];
  opacity: [partId: string, value: number];
  focus: [partId: string];
  showAll: [];
  fitAll: [];
  shellMode: [];
}>();

const toolsRef = ref<InstanceType<typeof ModelToolsPanel> | null>(null);

const files = computed(() => {
  const list: string[] = [];
  if (props.hasForgeSource) list.push("model.forge.js");
  for (const f of props.srcFiles ?? []) list.push(`src/${f}`);
  if (!list.length && props.sourceUrl) {
    list.push("model.forge.js");
  }
  return list;
});

const selectedPart = computed(() => {
  const element = props.pick?.element;
  if (!element) return null;
  return props.parts.find((part) => part.id === element) ?? null;
});

const toolsSectionTitle = computed(() =>
  selectedPart.value ? `精修 · ${selectedPart.value.label}` : "参数 / 代码",
);

function openFile(filePath: string) {
  toolsRef.value?.openFile(filePath);
}
</script>

<template>
  <aside class="structure-panel">
    <PartTreePanel
      :parts="parts"
      :pick="pick"
      :hidden="hidden"
      :opacities="opacities"
      @pick="emit('pick', $event)"
      @toggle="emit('toggle', $event)"
      @opacity="(id, v) => emit('opacity', id, v)"
      @focus="emit('focus', $event)"
      @show-all="emit('showAll')"
      @fit-all="emit('fitAll')"
      @shell-mode="emit('shellMode')"
    />

    <section v-if="files.length" class="structure-section structure-files">
      <div class="structure-section-head">文件</div>
      <ul class="structure-file-list">
        <li v-for="file in files" :key="file">
          <button type="button" class="structure-file-btn" @click="openFile(file)">
            {{ file }}
          </button>
        </li>
      </ul>
    </section>

    <section v-if="projectId && sourceUrl" class="structure-section structure-tools">
      <div class="structure-section-head">{{ toolsSectionTitle }}</div>
      <ModelToolsPanel
        ref="toolsRef"
        embedded
        :project-id="projectId"
        :source-url="sourceUrl"
        :forge-sources-url="forgeSourcesUrl"
        :version="version"
        :generating="generating"
        :generation-phase="generationPhase"
        :track-job="trackJob"
        :selected-part="selectedPart"
        @clear-pick="emit('clearPick')"
      />
    </section>
  </aside>
</template>

<style scoped>
.structure-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  background: var(--bg-surface);
}

.structure-section {
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.structure-section-head {
  padding: 0.5rem 0.65rem 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.structure-file-list {
  list-style: none;
  margin: 0;
  padding: 0 0.65rem 0.55rem;
  max-height: 100px;
  overflow: auto;
}

.structure-file-btn {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  font-family: ui-monospace, Menlo, Monaco, Consolas, monospace;
  font-size: 0.72rem;
  color: #8ec0ff;
  padding: 0.2rem 0;
  cursor: pointer;
}

.structure-file-btn:hover {
  color: #b8d8ff;
  text-decoration: underline;
}

.structure-tools {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.structure-tools :deep(.model-tools-panel) {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
</style>
