<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import type {
  AgentActivityStep,
  ChatMessage,
  DesignTurn,
  Health,
  Job,
  ModelPick,
  ModelVersion,
  ProjectCapabilities,
  TurnImage,
} from "../api/client";
import { getJob, getProjectState, sendTurn, waitAgentRun } from "../api/client";
import { mergeSessionPhase } from "../composables/useDesignTurn";
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
import ValidationWarningsPanel from "./ValidationWarningsPanel.vue";
import AgentActivityPanel from "./AgentActivityPanel.vue";
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
    validationWarnings?: string[];
    captureViewport?: () => string | null;
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
    validationWarnings: () => [],
    captureViewport: undefined,
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
  activeTurnChange: [turn: DesignTurn | null];
}>();

const messages = ref<ChatMessage[]>([]);
const input = ref("");
const sending = ref(false);
const agentBusy = ref(false);
const agentActive = ref(false);
const submitError = ref<string | null>(null);
const capabilities = ref<ProjectCapabilities | null>(null);
const agentActivity = ref<AgentActivityStep[]>([]);
const bottomRef = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

type PendingImage = {
  dataUrl: string;
  mimeType: string;
  filename: string;
};

const pendingImages = ref<PendingImage[]>([]);
const composerNotice = ref<string | null>(null);
const MAX_PENDING_IMAGES = 3;

const canCaptureViewport = computed(
  () => Boolean(props.captureViewport) && props.hasModel && !composerDisabled.value,
);

const TEXTAREA_MIN_HEIGHT = 44;
const TEXTAREA_MAX_HEIGHT = 132;

const chatMode = computed<WebChatMode | null>(() => {
  const fromState = capabilities.value?.web_chat_mode;
  const fromHealth = props.health?.web_chat_mode;
  // Project state refreshes readiness on every SSE tick; prefer agent if either source says so.
  if (fromState === "agent" || fromHealth === "agent") return "agent";
  if (fromState === "setup_required" || fromHealth === "setup_required") {
    return "setup_required";
  }
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
    agentActive.value,
  ),
);

const phase = computed<JobPhase>(() =>
  submitError.value ? "failed" : sending.value ? "submitting" : session.value.phase,
);

const anyBusy = computed(() => sending.value || session.value.busy);
const canSend = computed(
  () =>
    chatMode.value === "agent" &&
    !sending.value &&
    !anyBusy.value &&
    (input.value.trim().length > 0 || pendingImages.value.length > 0),
);

function attachDataUrl(dataUrl: string, filename = "screenshot.png", mimeType = "image/png") {
  if (pendingImages.value.length >= MAX_PENDING_IMAGES) return;
  pendingImages.value.push({ dataUrl, mimeType, filename });
}

function removePendingImage(index: number) {
  pendingImages.value.splice(index, 1);
}

function pendingToTurnImages(): TurnImage[] {
  return pendingImages.value.map((img) => ({
    data: img.dataUrl,
    mime_type: img.mimeType,
    filename: img.filename,
  }));
}

function attachViewportScreenshot() {
  composerNotice.value = null;
  if (!props.hasModel) {
    composerNotice.value = CHAT.screenshotNeedModel;
    return;
  }
  const dataUrl = props.captureViewport?.();
  if (!dataUrl) {
    composerNotice.value = CHAT.screenshotFailed;
    return;
  }
  attachDataUrl(dataUrl, "viewport.png");
  composerNotice.value = CHAT.screenshotAttached;
}

function openImagePicker() {
  fileInputRef.value?.click();
}

async function onImageFilesSelected(event: Event) {
  const inputEl = event.target as HTMLInputElement;
  const files = inputEl.files;
  if (!files?.length) return;
  for (const file of Array.from(files)) {
    if (pendingImages.value.length >= MAX_PENDING_IMAGES) break;
    if (!file.type.startsWith("image/")) continue;
    const dataUrl = await readFileAsDataUrl(file);
    attachDataUrl(dataUrl, file.name, file.type || "image/png");
  }
  inputEl.value = "";
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function onComposerPaste(event: ClipboardEvent) {
  const items = event.clipboardData?.items;
  if (!items?.length) return;
  for (const item of Array.from(items)) {
    if (pendingImages.value.length >= MAX_PENDING_IMAGES) break;
    if (!item.type.startsWith("image/")) continue;
    const file = item.getAsFile();
    if (!file) continue;
    event.preventDefault();
    const dataUrl = await readFileAsDataUrl(file);
    attachDataUrl(dataUrl, file.name || "pasted.png", file.type || "image/png");
  }
}

watch(
  () => chatMode.value,
  (mode) => {
    if (mode === "agent") submitError.value = null;
  },
);

const statusDetail = computed(() => session.value.detail ?? submitError.value);
const activityLabel = computed(() => {
  if (sending.value) return "已发送…";
  const steps = agentActivity.value;
  const running = steps.filter((s) => s.status === "running").pop();
  if (running) return running.label;
  if (session.value.lane === "render") {
    return phaseLabel(phase.value, statusDetail.value ?? undefined) ?? "正在生成 3D 模型…";
  }
  if (session.value.lane === "agent") {
    const last = steps[steps.length - 1];
    if (last?.status === "done") return last.label;
    const dp = session.value.designPhase;
    if (dp && DESIGN_PHASE_LABEL[dp]) return DESIGN_PHASE_LABEL[dp];
    return CHAT.processing;
  }
  return null;
});

const renderJobMessage = computed(() => {
  if (session.value.lane !== "render" && !props.generation?.busy) return null;
  return props.generation?.detail ?? statusDetail.value ?? null;
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
  if (m.role === "user") return CHAT.roleUser;
  if (m.role === "system") return CHAT.roleSystem;
  return assistantName.value;
}

const composerDisabled = computed(
  () => !props.projectId || chatMode.value !== "agent" || assistantChecking.value,
);

function resizeTextarea() {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = "auto";
  const next = Math.min(Math.max(el.scrollHeight, TEXTAREA_MIN_HEIGHT), TEXTAREA_MAX_HEIGHT);
  el.style.height = `${next}px`;
}

function resetTextareaHeight() {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = `${TEXTAREA_MIN_HEIGHT}px`;
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
  agentActivity.value = state.agent.activity ?? [];
  agentActive.value = state.agent.active;
  emit("activeTurnChange", state.active_turn);
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
      agentActive.value = false;
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

watch(input, async () => {
  await nextTick();
  resizeTextarea();
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
  try {
    await waitAgentRun(projectId, (state) => {
      messages.value = state.messages;
      capabilities.value = state.capabilities;
      agentActivity.value = state.agent.activity ?? [];
      agentActive.value = state.agent.active;
      emit("activeTurnChange", state.active_turn);
      const st = state.agent;
      if (st.active_job_id && !tracked) {
        tracked = true;
        if (state.active_job) {
          emit("trackJob", state.active_job, prompt);
        } else {
          getJob(projectId, st.active_job_id)
            .then((job) => emit("trackJob", job, prompt))
            .catch(console.error);
        }
      }
    });
  } finally {
    agentBusy.value = false;
    agentActive.value = false;
  }
}

async function submitText(text: string) {
  if (!props.projectId || sending.value) return;
  const trimmed = text.trim();
  if (!trimmed && pendingImages.value.length === 0) return;
  if (chatMode.value !== "agent") {
    submitError.value =
      chatMode.value === null ? CHAT.submitChecking : CHAT.submitUnavailable;
    return;
  }
  if (anyBusy.value) {
    submitError.value = CHAT.submitBusy;
    return;
  }

  const prompt = trimmed || "请查看截图并检查当前模型。";
  sending.value = true;
  submitError.value = null;
  composerNotice.value = null;
  const images = pendingToTurnImages();
  pendingImages.value = [];

  try {
    const turn = await sendTurn(
      props.projectId,
      prompt,
      props.pick,
      props.pick?.element ?? null,
      images,
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
    submitError.value = err instanceof Error ? err.message : CHAT.submitFailed;
  } finally {
    sending.value = false;
  }
}

async function handleSubmit(e?: Event) {
  e?.preventDefault();
  if (!input.value.trim() && pendingImages.value.length === 0) return;
  if (!props.projectId) {
    emit("requestProject");
    return;
  }
  const text = input.value.trim();
  input.value = "";
  resetTextareaHeight();
  await submitText(text);
}

function focusInput() {
  void nextTick(() => textareaRef.value?.focus());
}

function prefillFromPick(p: ModelPick) {
  const name = p.label ?? p.element ?? CHAT.pickElement;
  if (!input.value.trim()) {
    input.value = CHAT.prefillModify(name);
    void nextTick(resizeTextarea);
  }
}

watch(
  () => props.pick,
  (pick) => {
    if (pick) focusInput();
  },
);

defineExpose({ focusInput, prefillFromPick, attachViewportScreenshot, attachDataUrl });

onMounted(() => {
  resizeTextarea();
});
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
      <span class="version-timeline-label">{{ CHAT.versionLabel }}</span>
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
      <ValidationWarningsPanel :warnings="validationWarnings" />
      <div v-if="composerNotice" class="chat-composer-notice">{{ composerNotice }}</div>
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
        <ChatMessageBody :content="m.content" :role="m.role" :images="m.images" />
      </div>

      <AgentActivityPanel
        v-if="agentActivity.length || (anyBusy && renderJobMessage)"
        :steps="agentActivity"
        :active-job-message="anyBusy ? renderJobMessage : null"
      />

      <div v-else-if="anyBusy" class="chat-activity">
        <span class="spinner spinner--inline" aria-hidden="true" />
        {{ activityLabel ?? CHAT.activityFallback }}
      </div>

      <div ref="bottomRef" />
    </div>

    <form class="chat-form" @submit="handleSubmit">
      <div
        class="chat-composer"
        :class="{
          'chat-composer--busy': anyBusy && !sending,
          'chat-composer--disabled': composerDisabled,
        }"
      >
        <div v-if="pick" class="chat-composer-context">
          <span class="chat-composer-context-chip">
            <span class="chat-composer-context-dot" aria-hidden="true" />
            <span class="chat-composer-context-text">
              {{ pick.element ? CHAT.pickElement : CHAT.pickLocation }}：
              <strong>{{ formatPickShort(pick) }}</strong>
            </span>
            <button
              type="button"
              class="chat-composer-context-clear"
              :aria-label="CHAT.clearPick"
              @click="emit('clearPick')"
            >
              ×
            </button>
          </span>
        </div>

        <label class="sr-only" for="chat-composer-input">{{ CHAT.panelTitle }}</label>
        <input
          ref="fileInputRef"
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          multiple
          class="sr-only"
          @change="onImageFilesSelected"
        />

        <div v-if="pendingImages.length" class="chat-composer-images">
          <div
            v-for="(img, index) in pendingImages"
            :key="`${img.filename}-${index}`"
            class="chat-composer-image-chip"
          >
            <img :src="img.dataUrl" :alt="img.filename" class="chat-composer-image-thumb" />
            <button
              type="button"
              class="chat-composer-image-remove"
              :aria-label="CHAT.removeImage"
              @click="removePendingImage(index)"
            >
              ×
            </button>
          </div>
        </div>

        <textarea
          id="chat-composer-input"
          ref="textareaRef"
          v-model="input"
          class="chat-composer-input"
          :placeholder="inputPlaceholder"
          :title="CHAT.inputHint"
          rows="1"
          :aria-busy="anyBusy"
          @input="resizeTextarea"
          @paste="onComposerPaste"
          @keydown.enter.exact.prevent="handleSubmit()"
        />

        <div class="chat-composer-footer">
          <div class="chat-composer-actions">
            <button
              type="button"
              class="chat-icon-btn"
              :disabled="!canCaptureViewport || pendingImages.length >= MAX_PENDING_IMAGES"
              :aria-label="CHAT.attachScreenshot"
              :title="hasModel ? CHAT.attachScreenshot : CHAT.screenshotNeedModel"
              @click="attachViewportScreenshot"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path
                  d="M4 7h3l2-2h6l2 2h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.75"
                  stroke-linejoin="round"
                />
                <circle
                  cx="12"
                  cy="13"
                  r="3.25"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.75"
                />
              </svg>
            </button>
            <button
              type="button"
              class="chat-icon-btn"
              :disabled="composerDisabled || pendingImages.length >= MAX_PENDING_IMAGES"
              :aria-label="CHAT.attachImage"
              :title="CHAT.attachImage"
              @click="openImagePicker"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <rect
                  x="4"
                  y="5"
                  width="16"
                  height="14"
                  rx="2"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.75"
                />
                <circle cx="9" cy="10" r="1.35" fill="currentColor" />
                <path
                  d="M7 17l4-4 3 3 3-4 3 5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.75"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>
          </div>
          <button
            type="submit"
            class="chat-send-btn"
            :disabled="!canSend"
            :aria-label="sending ? CHAT.sendBusy : CHAT.sendLabel"
            :aria-busy="sending"
          >
            <span v-if="sending" class="spinner chat-send-spinner" aria-hidden="true" />
            <svg
              v-else
              class="chat-send-icon"
              viewBox="0 0 24 24"
              width="18"
              height="18"
              aria-hidden="true"
            >
              <path
                d="M12 5v14M5 12l7-7 7 7"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </form>
  </div>
</template>
