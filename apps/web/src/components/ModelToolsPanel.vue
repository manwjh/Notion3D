<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { renderForge, renderScad, type Job } from "../api/client";
import type { JobPhase } from "../types/generation";
import {
  parseModelParams,
  type SourceBackend,
} from "../utils/modelParams";
import ParamPanel from "./ParamPanel.vue";

const MAIN_FILE = "__main__";

const props = defineProps<{
  projectId: string | null;
  sourceUrl: string | null;
  forgeSourcesUrl?: string | null;
  sourceBackend: SourceBackend;
  version: number | null;
  generating?: boolean;
  generationPhase?: JobPhase;
  trackJob: (job: Job, prompt: string) => Promise<void>;
  embedded?: boolean;
}>();

const tab = ref<"params" | "code">("params");
const codeExpanded = ref(false);
const activeFile = ref(MAIN_FILE);
const forgeMain = ref("");
const forgeFiles = ref<Record<string, string>>({});
const busy = ref(false);
const status = ref<string | null>(null);
const dirty = ref(false);

const isForge = computed(() => props.sourceBackend === "forge");

const code = computed({
  get() {
    if (activeFile.value === MAIN_FILE) return forgeMain.value;
    return forgeFiles.value[activeFile.value] ?? "";
  },
  set(value: string) {
    if (activeFile.value === MAIN_FILE) forgeMain.value = value;
    else forgeFiles.value = { ...forgeFiles.value, [activeFile.value]: value };
    dirty.value = true;
  },
});

const fileKeys = computed(() => {
  const keys = [MAIN_FILE];
  keys.push(...Object.keys(forgeFiles.value).sort());
  return keys;
});

const hasMultiFile = computed(() => Object.keys(forgeFiles.value).length > 0);

function fileLabel(key: string) {
  return key === MAIN_FILE ? "model.forge.js" : `src/${key}`;
}

const GENERATING_PLACEHOLDER = computed(() =>
  isForge.value
    ? `// 正在生成 ForgeCAD 脚本…\n// 完成后可在此查看与编辑`
    : `// 正在生成 OpenSCAD…\n// 完成后可在此查看与编辑`,
);

const hasParams = computed(() =>
  activeFile.value === MAIN_FILE && parseModelParams(code.value, props.sourceBackend).length > 0,
);

const codePlaceholder = computed(() =>
  isForge.value
    ? "// 在此编辑 ForgeCAD (.forge.js) 源码…"
    : "// 在此编辑 OpenSCAD 源码（legacy）…",
);

watch(
  () => [props.forgeSourcesUrl, props.sourceUrl, props.version, props.sourceBackend] as const,
  ([sourcesUrl, url, ver], _, onCleanup) => {
    if ((!sourcesUrl && !url) || ver == null) {
      forgeMain.value = "";
      forgeFiles.value = {};
      activeFile.value = MAIN_FILE;
      dirty.value = false;
      return;
    }
    let cancelled = false;
    const load = async () => {
      try {
        if (isForge.value && sourcesUrl) {
          const res = await fetch(sourcesUrl);
          if (!res.ok) throw new Error("无法加载 Forge 源码包");
          const data = (await res.json()) as { forge_code: string; files?: Record<string, string> };
          if (cancelled) return;
          forgeMain.value = data.forge_code;
          forgeFiles.value = data.files ?? {};
          activeFile.value = MAIN_FILE;
          dirty.value = false;
          return;
        }
        if (!url) return;
        const res = await fetch(url);
        if (!res.ok) throw new Error("无法加载模型源码");
        const text = await res.text();
        if (cancelled) return;
        forgeMain.value = text;
        forgeFiles.value = {};
        activeFile.value = MAIN_FILE;
        dirty.value = false;
      } catch (e) {
        if (!cancelled) status.value = e instanceof Error ? e.message : "加载失败";
      }
    };
    void load();
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
}

function onEditorInput(e: Event) {
  if (props.generating && !code.value) return;
  onCodeChange((e.target as HTMLTextAreaElement).value);
}

async function handleApply() {
  if (!props.projectId || !forgeMain.value.trim() || busy.value) return;
  busy.value = true;
  status.value = "正在更新模型…";
  try {
    const label = dirty.value ? "调整参数" : "重新生成";
    const files = hasMultiFile.value ? forgeFiles.value : undefined;
    const job = isForge.value
      ? await renderForge(props.projectId, forgeMain.value, label, "manual", files)
      : await renderScad(props.projectId, forgeMain.value, label);
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
  <div v-if="projectId" class="model-tools-panel" :class="{ 'model-tools-panel--embedded': embedded }">
    <div v-if="!embedded" class="model-tools-header">
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
          :disabled="!forgeMain.trim() || busy || (generating && !forgeMain)"
          @click="handleApply"
        >
          {{ busy ? "更新中…" : dirty ? "应用更改" : "重新生成" }}
        </button>
      </div>
    </div>

    <template v-if="embedded">
      <div class="model-tools-embedded-body">
        <p v-if="generating && !forgeMain" class="model-tools-waiting">
          <span class="spinner spinner--inline" aria-hidden="true" />
          模型生成中…
        </p>
        <template v-else-if="hasParams">
          <ParamPanel
            :code="code"
            :backend="sourceBackend"
            :disabled="busy || (generating && !forgeMain)"
            class="param-panel--embedded"
            @change="onCodeChange"
          />
        </template>
        <p v-else class="model-tools-empty">无可调参数，展开下方代码或直接对话修改。</p>

        <details :open="codeExpanded" class="model-tools-code-details" @toggle="codeExpanded = ($event.target as HTMLDetailsElement).open">
          <summary>高级代码</summary>
          <div v-if="hasMultiFile" class="model-tools-files">
            <button
              v-for="key in fileKeys"
              :key="key"
              type="button"
              class="model-tools-file-tab"
              :class="{ active: activeFile === key }"
              @click="activeFile = key"
            >
              {{ fileLabel(key) }}
            </button>
          </div>
          <textarea
            class="scad-editor scad-editor--embedded"
            :value="generating && !forgeMain ? GENERATING_PLACEHOLDER : code"
            :placeholder="codePlaceholder"
            spellcheck="false"
            :disabled="busy || (generating && !forgeMain)"
            :readonly="generating && !forgeMain"
            @input="onEditorInput"
          />
        </details>

        <div class="model-tools-embedded-actions">
          <span v-if="dirty" class="model-tools-dirty">未保存</span>
          <span v-if="status" class="model-tools-status">{{ status }}</span>
          <button
            type="button"
            class="btn-primary model-tools-apply"
            :disabled="!forgeMain.trim() || busy || (generating && !forgeMain)"
            @click="handleApply"
          >
            {{ busy ? "更新中…" : "应用更改" }}
          </button>
        </div>
      </div>
    </template>

    <div
      v-else-if="tab === 'params'"
      class="model-tools-body model-tools-body--params"
      role="tabpanel"
    >
      <p v-if="generating && !forgeMain" class="model-tools-waiting">
        <span class="spinner spinner--inline" aria-hidden="true" />
        模型生成中，参数将在此显示…
      </p>
      <template v-else-if="hasParams">
        <ParamPanel
          :code="code"
          :backend="sourceBackend"
          :disabled="busy || (generating && !forgeMain)"
          @change="onCodeChange"
        />
        <p class="model-tools-tip">拖动滑块后点「应用更改」。此路径不经过设计助手。</p>
      </template>
      <p v-else class="model-tools-empty">
        当前模型没有可调参数。如需精细控制，可切换到「高级代码」标签，或在对话区描述修改。
      </p>
    </div>

    <div v-else class="model-tools-body model-tools-body--code" role="tabpanel">
      <div v-if="hasMultiFile" class="model-tools-files" role="tablist" aria-label="源文件">
        <button
          v-for="key in fileKeys"
          :key="key"
          type="button"
          role="tab"
          class="model-tools-file-tab"
          :class="{ active: activeFile === key }"
          :aria-selected="activeFile === key"
          @click="activeFile = key"
        >
          {{ fileLabel(key) }}
        </button>
      </div>
      <textarea
        class="scad-editor"
        :class="{ 'scad-editor--waiting': generating && !forgeMain }"
        :value="generating && !forgeMain ? GENERATING_PLACEHOLDER : code"
        :placeholder="codePlaceholder"
        spellcheck="false"
        :disabled="busy || (generating && !forgeMain)"
        :readonly="generating && !forgeMain"
        @input="onEditorInput"
      />
      <p v-if="generating && !forgeMain && generationPhase" class="scad-waiting-hint">
        {{
          generationPhase === "rendering"
            ? "3D 模型即将加载…"
            : "正在生成 3D 模型…"
        }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.model-tools-files {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  padding: 0.5rem 0.75rem 0;
  border-bottom: 1px solid #2a3140;
}

.model-tools-file-tab {
  font-size: 0.72rem;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
  border: 1px solid #3a4254;
  background: #1f2530;
  color: #aeb6c8;
  cursor: pointer;
}

.model-tools-file-tab.active {
  border-color: #6ea8fe;
  color: #dbe4ff;
  background: #253049;
}

.model-tools-panel--embedded {
  border-top: none;
  background: transparent;
  max-height: none;
}

.model-tools-embedded-body {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0 0.65rem 0.65rem;
  min-height: 0;
  overflow: auto;
}

.model-tools-code-details summary {
  cursor: pointer;
  font-size: 0.72rem;
  color: var(--text-muted);
  padding: 0.25rem 0;
}

.scad-editor--embedded {
  min-height: 100px;
  max-height: 160px;
  margin-top: 0.35rem;
}

.model-tools-embedded-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}
</style>
