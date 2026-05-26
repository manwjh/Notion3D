<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import type {
  ChatMessage,
  DesignTurn,
  Health,
  Job,
  ModelPick,
  ModelVersion,
  ProjectCapabilities,
} from "../api/client";
import { getJob, getProjectState, sendTurn } from "../api/client";
import { mergeSessionPhase, sleep } from "../composables/useDesignTurn";
import {
  CHAT,
  DESIGN_PHASE_LABEL,
  assistantDisplayName,
  type WebChatMode,
} from "../strings/zh";
import { phaseLabel, type GenerationState, type JobPhase } from "../types/generation";
import { formatPickShort } from "../types/pick";
import ChatMessageBody from "./ChatMessageBody.vue";
import DesignContextBanner from "./DesignContextBanner.vue";
import type { DesignContextView } from "./DesignContextBanner.vue";

const props = withDefaults(
  defineProps<{
    projectId: string | null;
    hasModel?: boolean;
    initialPrompt?: string | null;
    autoSubmitInitial?: boolean;
    pick?: ModelPick | null;
    generation: GenerationState | null;
    activeTurn?: DesignTurn | null;
    designContext?: DesignContextView | null;
    health?: Health | null;
    narrow?: boolean;
    versions?: ModelVersion[];
    selectedVersion?: number | null;
    agentBusyExternal?: boolean;
  }>(),
  {
    hasModel: false,
    initialPrompt: null,
    autoSubmitInitial: false,
    pick: null,
    activeTurn: null,
    designContext: null,
    narrow: false,
    versions: () => [],
    selectedVersion: null,
    agentBusyExternal: false,
  },
);

const emit = defineEmits<{
  consumeInitialPrompt: [];
  requestProject: [];
  clearPick: [];
  turnComplete: [];
  trackJob: [job: Job, prompt: string];
  selectVersion: [version: number];
  agentBusyChange: [busy: boolean];
}>();

const messages = ref<ChatMessage[]>([]);
const input = ref("");
const sending = ref(false);
const agentBusy = ref(false);
const submitError = ref<string | null>(null);
const capabilities = ref<ProjectCapabilities | null>(null);
const bottomRef = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const chatMode = computed<WebChatMode | null>(() => {
  const fromState = capabilities.value?.web_chat_mode;
  if (fromState) return fromState;
  if (props.health?.web_chat_mode) return props.health.web_chat_mode;
  return null;
});

const assistantChecking = computed(() => chatMode.value === null);
const chatHint = computed(() =>
  assistantChecking.value
    ? CHAT.checking
    : chatMode.value === "agent"
      ? CHAT.hintReady
      : CHAT.hintUnavailable,
);

const assistantName = computed(() => assistantDisplayName(null, null));

const session = computed(() =>
  mergeSessionPhase(
    props.generation,
    agentBusy.value || props.agentBusyExternal,
    props.activeTurn,
  ),
);

const phase = computed<JobPhase>(() =>
  submitError.value ? "failed" : sending.value ? "submitting" : session.value.phase,
);

const anyBusy = computed(() => sending.value || session.value.busy);
const canSend = computed(
  () => chatMode.value === "agent" && !sending.value && !anyBusy.value,
);

watch(
  () => chatMode.value,
  (mode) => {
    if (mode === "agent") submitError.value = null;
  },
);

const statusDetail = computed(() => session.value.detail ?? submitError.value);
const activityLabel = computed(() => {
  if (sending.value) return "已发送…";
  if (session.value.lane === "render") {
    return phaseLabel(phase.value, statusDetail.value ?? undefined) ?? "正在生成 3D 模型…";
  }
  if (session.value.lane === "agent") {
    const dp = session.value.designPhase;
    if (dp && DESIGN_PHASE_LABEL[dp]) return DESIGN_PHASE_LABEL[dp];
    return CHAT.processing;
  }
  return null;
});

const designPhaseBadge = computed(() => {
  const dp = props.activeTurn?.design_phase;
  if (!dp || dp === "done") return null;
  return DESIGN_PHASE_LABEL[dp] ?? dp;
});

const versionByJobId = computed(() => {
  const map = new Map<string, number>();
  for (const v of props.versions) {
    if (v.job_id) map.set(v.job_id, v.version);
  }
  return map;
});

const versionByTurnId = computed(() => {
  const map = new Map<string, number>();
  for (const v of props.versions) {
    if (v.turn_id) map.set(v.turn_id, v.version);
  }
  if (props.activeTurn?.version != null) {
    map.set(props.activeTurn.id, props.activeTurn.version);
  }
  return map;
});

function versionForMessage(m: ChatMessage): ModelVersion | null {
  if (!props.versions.length) return null;
  let vNum: number | undefined;
  if (m.job_id) vNum = versionByJobId.value.get(m.job_id);
  if (vNum == null && m.turn_id) vNum = versionByTurnId.value.get(m.turn_id);
  if (vNum == null) return null;
  return props.versions.find((v) => v.version === vNum) ?? null;
}

function roleLabel(m: ChatMessage): string {
  if (m.role === "user") return "你";
  if (m.role === "system") return "系统";
  return assistantName.value;
}

const inputPlaceholder = computed(() => {
  if (!props.projectId) return CHAT.placeholderNoProject;
  if (chatMode.value === "setup_required") return CHAT.placeholderUnavailable;
  if (assistantChecking.value) return CHAT.placeholderChecking;
  if (anyBusy.value && !sending.value) return CHAT.placeholderBusy;
  if (props.pick?.element) return CHAT.placeholderPickElement;
  if (props.pick) return CHAT.placeholderPick;
  if (props.hasModel) return CHAT.placeholderHasModel;
  return CHAT.placeholderDefault;
});

watch(agentBusy, (v) => emit("agentBusyChange", v), { immediate: true });

function messageTone(content: string, role: ChatMessage["role"]) {
  if (role === "system") return "system";
  if (role !== "assistant") return "default";
  if (content.includes("失败") || content.includes("不可用")) return "error";
  if (content.includes("好了") || content.includes("完成")) return "success";
  return "default";
}

async function refreshMessages(projectId: string) {
  const state = await getProjectState(projectId);
  messages.value = state.messages;
  capabilities.value = state.capabilities;
  return state;
}

async function hydrateProject(projectId: string) {
  try {
    const state = await refreshMessages(projectId);
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
      agentBusy.value = false;
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

watch([messages, phase, statusDetail, activityLabel], async () => {
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
  if (!props.projectId || !text.trim() || sending.value) return;
  if (chatMode.value !== "agent") {
    submitError.value =
      chatMode.value === null ? CHAT.submitChecking : CHAT.submitUnavailable;
    return;
  }
  if (anyBusy.value) {
    submitError.value = CHAT.submitBusy;
    return;
  }

  const prompt = text.trim();
  sending.value = true;
  submitError.value = null;

  try {
    const turn = await sendTurn(
      props.projectId,
      prompt,
      props.pick,
      props.pick?.element ?? null,
    );
    await refreshMessages(props.projectId);

    if (turn.routing === "agent") {
      await pollAgentRun(props.projectId, prompt);
      await refreshMessages(props.projectId);
      emit("turnComplete");
      emit("clearPick");
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

function focusInput() {
  void nextTick(() => textareaRef.value?.focus());
}

function prefillFromPick(p: ModelPick) {
  const name = p.label ?? p.element ?? "选中部件";
  if (!input.value.trim()) {
    input.value = `请修改「${name}」：`;
  }
}

watch(
  () => props.pick,
  (pick) => {
    if (pick) focusInput();
  },
);

defineExpose({ focusInput, prefillFromPick });
</script>

<template>
  <div class="chat-panel">
    <header class="chat-header">
      <div class="chat-header-main">
        <h2>{{ CHAT.panelTitle }}</h2>
        <span v-if="designPhaseBadge" class="chat-design-phase-badge">{{ designPhaseBadge }}</span>
      </div>
      <span v-if="activityLabel" class="chat-status chat-status--busy">
        <span class="spinner" aria-hidden="true" />
        {{ activityLabel }}
      </span>
    </header>

    <div v-if="projectId && versions.length > 0" class="version-timeline">
      <span class="version-timeline-label">方案</span>
      <button
        v-for="v in versions"
        :key="v.version"
        type="button"
        class="version-timeline-btn"
        :class="{
          active: selectedVersion === v.version,
          'version-timeline-btn--partial': v.status !== 'complete',
        }"
        :title="v.prompt ?? undefined"
        @click="emit('selectVersion', v.version)"
      >
        v{{ v.version }}
      </button>
    </div>

    <div class="chat-panel-notices">
      <DesignContextBanner v-if="designContext" :context="designContext" />
      <div v-if="submitError" class="chat-error-banner" role="alert">{{ submitError }}</div>
    </div>

    <div class="chat-messages">
      <div v-if="!projectId" class="chat-onboarding">
        <p class="chat-hint-title">{{ CHAT.onboardingTitle }}</p>
        <p class="chat-hint">{{ CHAT.onboardingBody }}</p>
      </div>

      <div v-else-if="messages.length === 0 && !anyBusy" class="chat-onboarding">
        <p class="chat-hint-title">{{ hasModel ? CHAT.continueTitle : CHAT.startTitle }}</p>
        <p class="chat-hint">{{ hasModel ? CHAT.continueHint : chatHint }}</p>
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
        <div class="chat-bubble-head">
          <span class="chat-role">{{ roleLabel(m) }}</span>
          <button
            v-if="m.role === 'assistant' && versionForMessage(m)"
            type="button"
            class="chat-version-link"
            :class="{ active: selectedVersion === versionForMessage(m)!.version }"
            @click="emit('selectVersion', versionForMessage(m)!.version)"
          >
            v{{ versionForMessage(m)!.version }}
          </button>
        </div>
        <ChatMessageBody :content="m.content" :role="m.role" />
      </div>

      <div v-if="anyBusy" class="chat-activity">
        <span class="spinner spinner--inline" aria-hidden="true" />
        {{ activityLabel ?? "处理中…" }}
      </div>

      <div ref="bottomRef" />
    </div>

    <form class="chat-form" @submit="handleSubmit">
      <div v-if="pick" class="context-banner context-banner--pick">
        <span class="context-banner-dot" aria-hidden="true" />
        <span class="context-banner-text">
          {{ pick.element ? "选中部件" : "点选位置" }}：<strong>{{ formatPickShort(pick) }}</strong>
        </span>
        <button type="button" class="context-banner-clear" @click="emit('clearPick')">清除</button>
      </div>

      <div class="chat-input-wrap">
        <textarea
          ref="textareaRef"
          v-model="input"
          :placeholder="inputPlaceholder"
          rows="2"
          @keydown.enter.exact.prevent="handleSubmit()"
        />
        <button
          type="submit"
          class="btn-primary chat-send-btn"
          :disabled="!canSend || !input.trim() || anyBusy"
          aria-label="发送"
        >
          {{ sending ? "…" : "↑" }}
        </button>
      </div>
      <p class="chat-form-hint">Enter 发送 · Shift+Enter 换行</p>
    </form>
  </div>
</template>
