<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { ModelPart } from "../types/parts";
import {
  applyPartBlockEdit,
  focusPartInSources,
  type ForgeSources,
  type PartCodeFocus,
} from "../utils/partCode";
import ForgeCodeEditor from "./ForgeCodeEditor.vue";
import ParamPanel from "./ParamPanel.vue";

const props = defineProps<{
  part: ModelPart;
  sources: ForgeSources;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  change: [sources: ForgeSources];
  expandFullCode: [focus: PartCodeFocus];
  clearPick: [];
}>();

const showAllParams = ref(false);
const blockDraft = ref("");
const blockDirty = ref(false);

const focus = computed(() => focusPartInSources(props.sources, props.part));

watch(
  () => [focus.value?.editableBlock?.text, props.part.id] as const,
  ([text]) => {
    blockDraft.value = text ?? focus.value?.snippet ?? "";
    blockDirty.value = false;
  },
  { immediate: true },
);

const paramFilter = computed(() => {
  if (showAllParams.value) return undefined;
  return focus.value?.relatedParamNames;
});

const snippetHighlight = computed(() => {
  if (focus.value?.editableBlock) return null;
  return focus.value?.highlightLines ?? null;
});

function onParamChange(code: string) {
  emit("change", { ...props.sources, main: code });
}

function onBlockChange(value: string) {
  blockDraft.value = value;
  blockDirty.value = true;
}

function applyBlockEdit() {
  if (!focus.value?.editableBlock || !blockDirty.value) return;
  emit("change", applyPartBlockEdit(props.sources, focus.value, blockDraft.value));
  blockDirty.value = false;
}

function openFullCode() {
  if (focus.value) emit("expandFullCode", focus.value);
}
</script>

<template>
  <section class="part-refine-panel">
    <div class="part-refine-head">
      <div class="part-refine-title">
        <span class="part-refine-label">部件精修</span>
        <strong>{{ part.label }}</strong>
        <span v-if="focus?.shapeVar" class="part-refine-var">{{ focus.shapeVar }}</span>
      </div>
      <button type="button" class="part-refine-clear" title="取消选中" @click="emit('clearPick')">
        ✕
      </button>
    </div>

    <template v-if="focus">
      <p v-if="focus.sourceLabel" class="part-refine-file">
        源码：<code>{{ focus.sourceLabel }}</code>
        <span v-if="part.source_ref" class="part-refine-ref">已映射</span>
      </p>

      <ParamPanel
        v-if="paramFilter?.length || (showAllParams && sources.main)"
        :code="sources.main"
        :param-names="paramFilter"
        :disabled="disabled"
        class="param-panel--part"
        @change="onParamChange"
      />
      <p v-else-if="!showAllParams" class="part-refine-hint">
        该部件没有独立可调参数，可直接编辑下方几何代码。
      </p>

      <button
        v-if="focus.relatedParamNames.length"
        type="button"
        class="part-refine-toggle"
        @click="showAllParams = !showAllParams"
      >
        {{ showAllParams ? "只看本部件参数" : "显示全部参数" }}
      </button>

      <div class="part-refine-code">
        <div class="part-refine-code-head">
          {{ focus.editableBlock ? "几何代码（可编辑）" : "相关代码" }}
        </div>
        <ForgeCodeEditor
          v-if="focus.editableBlock"
          :model-value="blockDraft"
          compact
          min-height="80px"
          max-height="180px"
          :disabled="disabled"
          @update:model-value="onBlockChange"
        />
        <ForgeCodeEditor
          v-else
          :model-value="focus.snippet"
          compact
          readonly
          :highlight-lines="snippetHighlight"
          :show-line-numbers="false"
          min-height="60px"
          max-height="140px"
        />
        <button
          v-if="focus.editableBlock && blockDirty"
          type="button"
          class="part-refine-apply-block"
          :disabled="disabled"
          @click="applyBlockEdit"
        >
          应用代码片段
        </button>
      </div>

      <button type="button" class="part-refine-full" @click="openFullCode">
        在完整脚本中定位
      </button>
    </template>

    <p v-else class="part-refine-miss">
      无法在 Forge 脚本中定位「{{ part.label }}」。请展开完整代码，或在对话区描述修改。
    </p>
  </section>
</template>

<style scoped>
.part-refine-panel {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.45rem 0.65rem 0.55rem;
  border-bottom: 1px solid var(--border);
  background: rgba(77, 132, 247, 0.06);
}

.part-refine-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.35rem;
}

.part-refine-title {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.35rem;
  font-size: 0.78rem;
}

.part-refine-label {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.part-refine-title strong {
  color: var(--text);
}

.part-refine-var {
  font-family: ui-monospace, Menlo, Monaco, Consolas, monospace;
  font-size: 0.68rem;
  color: #8ec0ff;
}

.part-refine-clear {
  border: none;
  background: transparent;
  color: var(--text-subtle);
  cursor: pointer;
  font-size: 0.82rem;
  line-height: 1;
  padding: 0.1rem 0.25rem;
}

.part-refine-clear:hover {
  color: var(--text);
}

.part-refine-file {
  margin: 0;
  font-size: 0.68rem;
  color: var(--text-subtle);
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.part-refine-file code {
  color: #8ec0ff;
}

.part-refine-ref {
  font-size: 0.62rem;
  color: #6ea8fe;
  border: 1px solid rgba(110, 168, 254, 0.35);
  border-radius: 3px;
  padding: 0.05rem 0.25rem;
}

.part-refine-hint,
.part-refine-miss {
  margin: 0;
  font-size: 0.72rem;
  color: var(--text-subtle);
  line-height: 1.45;
}

.part-refine-toggle,
.part-refine-full,
.part-refine-apply-block {
  align-self: flex-start;
  font-size: 0.68rem;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
  border: 1px solid var(--border-strong);
  background: var(--bg-elevated);
  color: var(--text-muted);
  cursor: pointer;
}

.part-refine-toggle:hover,
.part-refine-full:hover,
.part-refine-apply-block:hover {
  color: var(--text);
  border-color: var(--accent);
}

.part-refine-apply-block {
  margin-top: 0.35rem;
  border-color: var(--accent);
  color: var(--accent);
}

.part-refine-code-head {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}
</style>
