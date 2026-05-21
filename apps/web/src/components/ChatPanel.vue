<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import type { ChatMessage, Job, ModelPick } from "../api/client";
import { listMessages, sendChat } from "../api/client";
import AgentGuidePanel from "./AgentGuidePanel.vue";
import { EDIT_HINTS, EDIT_REGIONS } from "../config/editHints";
import { phaseLabel, type GenerationState, type JobPhase } from "../types/generation";
import { formatPickShort } from "../types/pick";

const props = withDefaults(
  defineProps<{
    projectId: string | null;
    samplePrompts?: string[];
    hasModel?: boolean;
    initialPrompt?: string | null;
    pick?: ModelPick | null;
    generation: GenerationState | null;
    trackJob: (job: Job, prompt: string) => Promise<void>;
  }>(),
  {
    samplePrompts: () => [],
    hasModel: false,
    initialPrompt: null,
    pick: null,
  },
);

const emit = defineEmits<{
  consumeInitialPrompt: [];
  requestProject: [];
  clearPick: [];
}>();

const VISIBLE_HINTS = 3;

const messages = ref<ChatMessage[]>([]);
const input = ref("");
const selectedRegion = ref<string | null>(null);
const showAllHints = ref(false);
const sending = ref(false);
const submitError = ref<string | null>(null);
const bottomRef = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const phase = computed<JobPhase>(() =>
  submitError.value ? "failed" : sending.value ? "submitting" : props.generation?.phase ?? "idle",
);

const statusDetail = computed(() => submitError.value ?? props.generation?.detail ?? null);
const busy = computed(() => sending.value || (props.generation?.busy ?? false));
const showProgress = computed(
  () => busy.value || (phase.value !== "idle" && phase.value !== "done" && phase.value !== "failed"),
);

const hints = computed(() =>
  showAllHints.value ? EDIT_HINTS : EDIT_HINTS.slice(0, VISIBLE_HINTS),
);


const inputPlaceholder = computed(() => {
  if (!props.projectId) return "先选择或新建项目；复杂建模请用 Agent + MCP…";
  if (props.pick) return "描述对此处的修改，例如：缩小一点、加厚…";
  if (selectedRegion.value) return `描述对「${selectedRegion.value}」的修改…`;
  if (props.hasModel) return "说说想怎么改，例如：孔加大、整体缩小 10%…";
  return "描述模型，例如：40×30×20mm 带孔盒子";
});

const progressSteps = ["解析描述", "生成模型", "预览图", "3D 模型"];

function messageTone(content: string, role: ChatMessage["role"]) {
  if (role !== "assistant") return "default";
  if (content.includes("失败") || content.includes("不适合")) return "error";
  if (content.includes("完成") || content.includes("渲染")) return "success";
  return "default";
}

function isStepActive(i: number) {
  const p = phase.value;
  return (
    (i === 0 && (p === "submitting" || p === "generating")) ||
    (i === 1 && p === "generating") ||
    (i === 2 && p === "previewing") ||
    (i === 3 && (p === "rendering" || p === "done"))
  );
}

function isStepDone(i: number) {
  const p = phase.value;
  return p === "done" || (p === "rendering" && i < 3) || (p === "previewing" && i < 2);
}

watch(
  () => props.initialPrompt,
  async (v) => {
    if (v) {
      input.value = v;
      emit("consumeInitialPrompt");
      await nextTick();
      textareaRef.value?.focus();
    }
  },
);

watch(
  () => props.projectId,
  (pid) => {
    if (!pid) {
      messages.value = [];
      submitError.value = null;
      selectedRegion.value = null;
      return;
    }
    listMessages(pid).then((m) => (messages.value = m)).catch(console.error);
  },
  { immediate: true },
);

watch(
  () => props.generation?.phase,
  (p) => {
    if ((p === "done" || p === "failed") && props.projectId) {
      listMessages(props.projectId).then((m) => (messages.value = m)).catch(console.error);
    }
  },
);

watch([messages, phase, statusDetail], async () => {
  await nextTick();
  bottomRef.value?.scrollIntoView({ behavior: "smooth" });
});

async function submitText(text: string) {
  if (!props.projectId || !text.trim() || busy.value) return;
  const prompt = text.trim();
  const region = props.pick ? null : selectedRegion.value;
  sending.value = true;
  submitError.value = null;
  try {
    const job = await sendChat(props.projectId, prompt, props.pick, region);
    messages.value = await listMessages(props.projectId);
    await props.trackJob(job, prompt);
    emit("clearPick");
    selectedRegion.value = null;
  } catch (err) {
    submitError.value = err instanceof Error ? err.message : "请求失败，请稍后重试";
  } finally {
    sending.value = false;
  }
}

async function handleSubmit(e?: Event) {
  e?.preventDefault();
  if (!input.value.trim()) return;
  if (!props.projectId) {
    emit("requestProject");
    return;
  }
  const text = input.value.trim();
  input.value = "";
  await submitText(text);
}
</script>

<template>
  <div class="chat-panel">
    <header class="chat-header">
      <div class="chat-header-main">
        <h2>快速调整</h2>
        <span class="chat-mode-badge" :class="hasModel ? 'edit' : 'create'">
          {{ hasModel ? "规则修改" : "简单模板" }}
        </span>
      </div>
      <span
        v-if="phaseLabel(phase, statusDetail ?? undefined)"
        class="chat-status"
        :class="{
          'chat-status--error': phase === 'failed',
          'chat-status--busy': showProgress && phase !== 'failed',
          'chat-status--ok': !showProgress,
        }"
      >
        <span v-if="showProgress" class="spinner" aria-hidden="true" />
        {{ phaseLabel(phase, statusDetail ?? undefined) }}
      </span>
    </header>

    <div v-if="submitError" class="chat-error-banner" role="alert">{{ submitError }}</div>

    <AgentGuidePanel v-if="!projectId" compact />

    <div v-if="showProgress" class="job-progress job-progress--4" aria-live="polite">
      <div
        v-for="(label, i) in progressSteps"
        :key="label"
        class="job-step"
        :class="{ active: isStepActive(i), done: isStepDone(i) }"
      >
        {{ label }}
      </div>
    </div>

    <div class="chat-messages">
      <div v-if="!projectId" class="chat-onboarding chat-onboarding--compact">
        <p class="chat-hint">
          在左侧创建项目后，在这里描述简单模型（立方体、盒子等）。复杂造型请用 Cursor Agent 或 MCP。
        </p>
        <div v-if="samplePrompts.length" class="prompt-chips prompt-chips--grid">
          <button
            v-for="text in samplePrompts"
            :key="text"
            type="button"
            class="prompt-chip"
            @click="
              input = text;
              emit('requestProject');
            "
          >
            {{ text }}
          </button>
        </div>
      </div>

      <div v-else-if="messages.length === 0 && !busy" class="chat-onboarding">
        <template v-if="!hasModel">
          <p class="chat-hint-title">简单几何：规则模板</p>
          <p class="chat-hint">
            立方体、盒子等可直接描述。复杂结构请在 Agent 中用 <code>notion3d_render_scad</code> 提交 SCAD。
          </p>
          <div class="prompt-chips prompt-chips--grid">
            <button
              v-for="text in samplePrompts"
              :key="text"
              type="button"
              class="prompt-chip"
              :disabled="busy"
              @click="input = text"
            >
              {{ text }}
            </button>
          </div>
        </template>
        <template v-else>
          <p class="chat-hint-title">模型已就绪，可以这样改</p>
          <ul class="chat-tip-list">
            <li>点选下方部位 + 说「加大一点」</li>
            <li>直接说「孔加大」「整体缩小 10%」</li>
            <li>在左侧参数面板拖动滑块</li>
          </ul>
        </template>
      </div>

      <div
        v-for="m in messages"
        :key="m.id"
        class="chat-bubble"
        :class="[
          `chat-bubble--${m.role}`,
          `chat-bubble--${messageTone(m.content, m.role)}`,
        ]"
      >
        <span class="chat-role">{{ m.role === "user" ? "你" : "助手" }}</span>
        <p>{{ m.content }}</p>
      </div>

      <div v-if="busy" class="chat-bubble chat-bubble--assistant chat-bubble--loading">
        <span class="chat-role">助手</span>
        <p>
          <span class="spinner spinner--inline" aria-hidden="true" />
          {{ phaseLabel(phase, statusDetail ?? undefined) ?? "处理中…" }}
        </p>
      </div>

      <div ref="bottomRef" />
    </div>

    <form class="chat-form" @submit="handleSubmit">
      <div v-if="hasModel && !pick" class="edit-region-bar">
        <span class="edit-region-label">改哪里</span>
        <div class="region-chips">
          <button
            v-for="r in EDIT_REGIONS"
            :key="r.id"
            type="button"
            class="region-chip"
            :class="{ active: selectedRegion === r.label }"
            :disabled="busy"
            @click="selectedRegion = selectedRegion === r.label ? null : r.label"
          >
            {{ r.label }}
          </button>
        </div>
      </div>

      <div v-if="hasModel" class="edit-hints-bar">
        <button
          v-for="hint in hints"
          :key="hint"
          type="button"
          class="edit-hint-chip"
          :disabled="busy"
          @click="input = hint"
        >
          {{ hint }}
        </button>
        <button
          v-if="EDIT_HINTS.length > VISIBLE_HINTS"
          type="button"
          class="edit-hint-chip edit-hint-chip--more"
          @click="showAllHints = !showAllHints"
        >
          {{ showAllHints ? "收起" : "更多" }}
        </button>
      </div>

      <div
        v-if="pick || selectedRegion"
        class="context-banner"
        :class="pick ? 'context-banner--pick' : 'context-banner--region'"
      >
        <span class="context-banner-dot" aria-hidden="true" />
        <span class="context-banner-text">
          <template v-if="pick">
            3D 点选：<strong>{{ formatPickShort(pick) }}</strong>
          </template>
          <template v-else>
            修改部位：<strong>{{ selectedRegion }}</strong>
          </template>
        </span>
        <button
          type="button"
          class="context-banner-clear"
          @click="pick ? emit('clearPick') : (selectedRegion = null)"
        >
          清除
        </button>
      </div>

      <div class="chat-input-wrap">
        <textarea
          ref="textareaRef"
          v-model="input"
          :placeholder="inputPlaceholder"
          rows="2"
          :disabled="busy"
          @keydown.enter.exact.prevent="handleSubmit()"
        />
        <button
          type="submit"
          class="btn-primary chat-send-btn"
          :disabled="busy || !input.trim()"
          aria-label="发送"
        >
          {{ busy ? "…" : "↑" }}
        </button>
      </div>
      <p class="chat-form-hint">Enter 发送 · Shift+Enter 换行</p>
    </form>
  </div>
</template>
