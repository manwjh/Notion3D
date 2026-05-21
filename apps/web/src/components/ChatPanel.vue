<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import type { ChatMessage, Health, Job, ModelPick } from "../api/client";
import { getJob, getProjectState, sendTurn } from "../api/client";
import { mergeSessionPhase, sleep } from "../composables/useDesignTurn";
import { EDIT_HINTS, EDIT_REGIONS } from "../config/editHints";
import {
  MODE_HINT,
  MODE_LABEL,
  SAMPLE_PROMPTS as DEFAULT_SAMPLES,
  assistantDisplayName,
  type WebChatMode,
} from "../strings/zh";
import {
  SESSION_STEPS,
  phaseLabel,
  stepIndex,
  type GenerationState,
  type JobPhase,
} from "../types/generation";
import { formatPickShort } from "../types/pick";

const props = withDefaults(
  defineProps<{
    projectId: string | null;
    samplePrompts?: string[];
    hasModel?: boolean;
    initialPrompt?: string | null;
    autoSubmitInitial?: boolean;
    pick?: ModelPick | null;
    generation: GenerationState | null;
    health?: Health | null;
  }>(),
  {
    samplePrompts: () => DEFAULT_SAMPLES,
    hasModel: false,
    initialPrompt: null,
    autoSubmitInitial: false,
    pick: null,
  },
);

const emit = defineEmits<{
  consumeInitialPrompt: [];
  requestProject: [];
  clearPick: [];
  turnComplete: [];
  trackJob: [job: Job, prompt: string];
  openSetup: [];
}>();

const VISIBLE_HINTS = 3;

const messages = ref<ChatMessage[]>([]);
const input = ref("");
const selectedRegion = ref<string | null>(null);
const showAllHints = ref(false);
const sending = ref(false);
const agentBusy = ref(false);
const agentExternalUrl = ref<string | null>(null);
const submitError = ref<string | null>(null);
const bottomRef = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const chatMode = computed<WebChatMode>(() => props.health?.web_chat_mode ?? "setup_required");
const modeLabel = computed(() => MODE_LABEL[chatMode.value]);
const modeHint = computed(() => MODE_HINT[chatMode.value]);

const assistantName = computed(() =>
  assistantDisplayName(props.health?.agent_active, props.health?.assistant_label),
);

const session = computed(() =>
  mergeSessionPhase(props.generation, agentBusy.value),
);

const phase = computed<JobPhase>(() =>
  submitError.value ? "failed" : sending.value ? "submitting" : session.value.phase,
);

const busy = computed(() => sending.value || session.value.busy);
const canSend = computed(() => chatMode.value === "agent" && !busy.value);

const statusDetail = computed(() => session.value.detail ?? submitError.value);

const showProgress = computed(
  () => busy.value && phase.value !== "done" && phase.value !== "failed",
);

const currentStep = computed(() => stepIndex(phase.value));

const inputPlaceholder = computed(() => {
  if (!props.projectId) return "先新建项目，然后描述想要的 3D 物件…";
  if (chatMode.value === "setup_required") return "请先连接设计助手（右上角「助手」）…";
  if (props.pick) return "说说想怎么改这里…";
  if (selectedRegion.value) return `说说想怎么改「${selectedRegion.value}」…`;
  if (props.hasModel) return "继续描述想改什么，或选下方快捷语…";
  return `跟 ${assistantName.value} 说说用途、尺寸、结构…`;
});

const hints = computed(() =>
  showAllHints.value ? EDIT_HINTS : EDIT_HINTS.slice(0, VISIBLE_HINTS),
);

function messageTone(content: string, role: ChatMessage["role"]) {
  if (role !== "assistant") return "default";
  if (content.includes("失败") || content.includes("不可用")) return "error";
  if (content.includes("好了") || content.includes("初稿")) return "success";
  return "default";
}

async function refreshMessages(projectId: string) {
  const state = await getProjectState(projectId);
  messages.value = state.messages;
  return state;
}

async function hydrateProject(projectId: string) {
  try {
    const state = await refreshMessages(projectId);
    agentExternalUrl.value = state.agent.external_url ?? null;
    if (state.agent.active) {
      const lastUser = [...state.messages].reverse().find((m) => m.role === "user");
      void pollAgentRun(projectId, lastUser?.content ?? "");
    }
  } catch (err) {
    console.error(err);
  }
}

watch(
  () => props.projectId,
  (pid) => {
    if (!pid) {
      messages.value = [];
      submitError.value = null;
      selectedRegion.value = null;
      agentBusy.value = false;
      agentExternalUrl.value = null;
      return;
    }
    void hydrateProject(pid);
  },
  { immediate: true },
);

watch(
  () => props.generation?.phase,
  (p) => {
    if ((p === "done" || p === "failed") && props.projectId) {
      refreshMessages(props.projectId).catch(console.error);
    }
  },
);

watch([messages, phase, statusDetail], async () => {
  await nextTick();
  bottomRef.value?.scrollIntoView({ behavior: "smooth" });
});

watch(
  () => [props.initialPrompt, props.autoSubmitInitial, props.projectId] as const,
  async ([prompt, auto, pid]) => {
    if (!prompt || !pid) return;
    if (auto) {
      emit("consumeInitialPrompt");
      await submitText(prompt);
      return;
    }
    input.value = prompt;
    emit("consumeInitialPrompt");
    await nextTick();
    textareaRef.value?.focus();
  },
);

async function pollAgentRun(projectId: string, prompt: string) {
  if (agentBusy.value) return;
  agentBusy.value = true;
  let tracked = false;
  const deadline = Date.now() + 600_000;
  try {
    while (Date.now() < deadline) {
      const state = await getProjectState(projectId);
      const st = state.agent;
      if (st.external_url) agentExternalUrl.value = st.external_url;
      if (st.active_job_id && !tracked) {
        tracked = true;
        const job = state.active_job ?? (await getJob(projectId, st.active_job_id));
        emit("trackJob", job, prompt);
      }
      if (!st.active) break;
      await sleep(2000);
    }
  } finally {
    agentBusy.value = false;
  }
}

async function submitText(text: string) {
  if (!props.projectId || !text.trim() || busy.value) return;
  if (chatMode.value === "setup_required") {
    submitError.value = "请先连接设计助手";
    emit("openSetup");
    return;
  }

  const prompt = text.trim();
  const region = props.pick ? null : selectedRegion.value;
  sending.value = true;
  submitError.value = null;
  agentExternalUrl.value = null;

  try {
    const turn = await sendTurn(props.projectId, prompt, props.pick, region);
    await refreshMessages(props.projectId);

    if (turn.routing === "agent") {
      await pollAgentRun(props.projectId, prompt);
      await refreshMessages(props.projectId);
      emit("turnComplete");
      emit("clearPick");
      selectedRegion.value = null;
      return;
    }

    emit("turnComplete");
  } catch (err) {
    submitError.value = err instanceof Error ? err.message : "发送失败，请稍后重试";
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

async function useSample(text: string) {
  if (!props.projectId) {
    input.value = text;
    emit("requestProject");
    return;
  }
  await submitText(text);
}
</script>

<template>
  <div class="chat-panel">
    <header class="chat-header">
      <div class="chat-header-main">
        <h2>设计对话</h2>
        <span class="chat-mode-badge" :title="modeHint">{{ modeLabel }}</span>
      </div>
      <span
        v-if="phaseLabel(phase, statusDetail ?? undefined)"
        class="chat-status"
        :class="{
          'chat-status--error': phase === 'failed',
          'chat-status--busy': showProgress,
        }"
      >
        <span v-if="showProgress" class="spinner" aria-hidden="true" />
        {{ phaseLabel(phase, statusDetail ?? undefined) }}
      </span>
    </header>

    <div v-if="submitError" class="chat-error-banner" role="alert">{{ submitError }}</div>

    <div
      v-if="chatMode === 'setup_required' && projectId"
      class="chat-mode-banner"
      role="status"
    >
      设计助手未连接，Web 对话暂不可用。
      <button type="button" class="link-btn" @click="emit('openSetup')">连接设计助手</button>
    </div>

    <div v-if="agentExternalUrl" class="chat-mode-banner" role="status">
      助手会话：
      <a :href="agentExternalUrl" target="_blank" rel="noopener">在外部查看</a>
    </div>

    <div v-if="showProgress" class="session-progress" aria-live="polite">
      <div
        v-for="(step, i) in SESSION_STEPS"
        :key="step.id"
        class="session-step"
        :class="{ active: currentStep === i, done: currentStep > i }"
      >
        {{ step.label }}
      </div>
    </div>

    <div class="chat-messages">
      <div v-if="!projectId" class="chat-onboarding">
        <p class="chat-hint-title">在这里描述，左侧看模型</p>
        <p class="chat-hint">新建项目后，用一句话说尺寸和用途即可开始。</p>
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
          <p class="chat-hint-title">说说你想做什么</p>
          <p class="chat-hint">{{ modeHint }}</p>
          <div class="prompt-chips prompt-chips--grid">
            <button
              v-for="text in samplePrompts"
              :key="text"
              type="button"
              class="prompt-chip"
              :disabled="busy"
              @click="useSample(text)"
            >
              {{ text }}
            </button>
          </div>
        </template>
        <template v-else>
          <p class="chat-hint-title">继续迭代方案</p>
          <ul class="chat-tip-list">
            <li>直接说：「孔加大」「整体缩小 10%」</li>
            <li>在 3D 视图中点选位置，再描述修改</li>
            <li>左侧可微调参数</li>
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

      <div v-if="busy && sending" class="chat-bubble chat-bubble--assistant chat-bubble--loading">
        <span class="chat-role">助手</span>
        <p><span class="spinner spinner--inline" aria-hidden="true" /> 收到，开始处理…</p>
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
            :disabled="!canSend"
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
          :disabled="!canSend"
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
            点选位置：<strong>{{ formatPickShort(pick) }}</strong>
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
          :disabled="!canSend"
          @keydown.enter.exact.prevent="handleSubmit()"
        />
        <button
          type="submit"
          class="btn-primary chat-send-btn"
          :disabled="!canSend || !input.trim()"
          aria-label="发送"
        >
          {{ busy ? "…" : "↑" }}
        </button>
      </div>
      <p class="chat-form-hint">Enter 发送 · Shift+Enter 换行</p>
    </form>
  </div>
</template>

<style scoped>
.chat-mode-banner {
  margin: 0 0 0.5rem;
  padding: 0.55rem 0.75rem;
  font-size: 0.82rem;
  background: #f8fafc;
  border-radius: 8px;
  color: #475569;
  line-height: 1.4;
}
.link-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  padding: 0 0.15rem;
  font: inherit;
  text-decoration: underline;
}
.session-progress {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
  margin-bottom: 0.65rem;
}
.session-step {
  text-align: center;
  font-size: 0.72rem;
  padding: 0.35rem 0.25rem;
  border-radius: 6px;
  background: #f1f5f9;
  color: #94a3b8;
}
.session-step.active {
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 600;
}
.session-step.done {
  background: #dcfce7;
  color: #166534;
}
</style>
