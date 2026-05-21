<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { renderScad, type Job } from "../api/client";
import type { JobPhase } from "../types/generation";
import { parseScadParams } from "../utils/scadParams";
import ParamPanel from "./ParamPanel.vue";

const props = defineProps<{
  projectId: string | null;
  scadUrl: string | null;
  version: number | null;
  generating?: boolean;
  generationPhase?: JobPhase;
  trackJob: (job: Job, prompt: string) => Promise<void>;
}>();

const tab = ref<"params" | "code">("params");
const code = ref("");
const busy = ref(false);
const status = ref<string | null>(null);
const dirty = ref(false);

const GENERATING_PLACEHOLDER = `// 正在生成模型参数…
// 完成后可在此查看高级代码`;

const hasParams = computed(() => parseScadParams(code.value).length > 0);

watch(
  () => [props.scadUrl, props.version] as const,
  ([url, ver], _, onCleanup) => {
    if (!url || ver == null) {
      code.value = "";
      dirty.value = false;
      return;
    }
    let cancelled = false;
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error("无法加载模型数据");
        return r.text();
      })
      .then((text) => {
        if (!cancelled) {
          code.value = text;
          dirty.value = false;
        }
      })
      .catch((e) => {
        if (!cancelled) status.value = e instanceof Error ? e.message : "加载失败";
      });
    onCleanup(() => {
      cancelled = true;
    });
  },
  { immediate: true },
);

watch(
  () => props.version,
  () => {
    if (hasParams.value) tab.value = "params";
  },
);

function onCodeChange(newCode: string) {
  code.value = newCode;
  dirty.value = true;
}

function onEditorInput(e: Event) {
  if (props.generating && !code.value) return;
  onCodeChange((e.target as HTMLTextAreaElement).value);
}

async function handleApply() {
  if (!props.projectId || !code.value.trim() || busy.value) return;
  busy.value = true;
  status.value = "正在更新模型…";
  try {
    const label = dirty.value ? "调整参数" : "重新生成";
    const job = await renderScad(props.projectId, code.value, label);
    await props.trackJob(job, label);
    status.value = "已提交";
    dirty.value = false;
    setTimeout(() => {
      status.value = null;
    }, 2500);
  } catch (e) {
    status.value = e instanceof Error ? e.message : "更新失败";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div v-if="projectId" class="model-tools-panel">
    <div class="model-tools-header">
      <div class="model-tools-tabs" role="tablist" aria-label="模型工具">
        <button
          type="button"
          role="tab"
          :aria-selected="tab === 'params'"
          class="model-tools-tab"
          :class="{ active: tab === 'params' }"
          @click="tab = 'params'"
        >
          参数调整
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="tab === 'code'"
          class="model-tools-tab"
          :class="{ active: tab === 'code' }"
          @click="tab = 'code'"
        >
          高级代码
        </button>
      </div>
      <div class="model-tools-actions">
        <span v-if="dirty" class="model-tools-dirty">未保存</span>
        <span v-if="status" class="model-tools-status">{{ status }}</span>
        <button
          type="button"
          class="btn-primary model-tools-apply"
          :disabled="!code.trim() || busy || (generating && !code)"
          @click="handleApply"
        >
          {{ busy ? "更新中…" : dirty ? "应用更改" : "重新生成" }}
        </button>
      </div>
    </div>

    <div
      v-if="tab === 'params'"
      class="model-tools-body model-tools-body--params"
      role="tabpanel"
    >
      <p v-if="generating && !code" class="model-tools-waiting">
        <span class="spinner spinner--inline" aria-hidden="true" />
        模型生成中，参数将在此显示…
      </p>
      <template v-else-if="hasParams">
        <ParamPanel
          :code="code"
          :disabled="busy || (generating && !code)"
          @change="onCodeChange"
        />
        <p class="model-tools-tip">拖动滑块调整尺寸，然后点击「应用更改」。</p>
      </template>
      <p v-else class="model-tools-empty">
        当前模型没有可调参数。如需精细控制，可切换到「高级代码」标签，或在右侧用对话描述修改。
      </p>
    </div>

    <div v-else class="model-tools-body model-tools-body--code" role="tabpanel">
      <textarea
        class="scad-editor"
        :class="{ 'scad-editor--waiting': generating && !code }"
        :value="generating && !code ? GENERATING_PLACEHOLDER : code"
        placeholder="// 高级用户可在此编辑 OpenSCAD 源码…"
        spellcheck="false"
        :disabled="busy || (generating && !code)"
        :readonly="generating && !code"
        @input="onEditorInput"
      />
      <p v-if="generating && !code && generationPhase" class="scad-waiting-hint">
        {{
          generationPhase === "previewing"
            ? "预览已显示，3D 模型仍在计算中…"
            : generationPhase === "rendering"
              ? "3D 模型即将加载…"
              : "正在理解你的描述并生成模型…"
        }}
      </p>
    </div>
  </div>
</template>
