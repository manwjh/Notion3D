<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import type { Health } from "../api/client";
import { MODE_LABEL, type WebChatMode } from "../strings/zh";

defineProps<{ health: Health | null }>();

const open = ref(false);
const rootRef = ref<HTMLElement | null>(null);

function onDocClick(e: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(e.target as Node)) {
    open.value = false;
  }
}

onMounted(() => document.addEventListener("mousedown", onDocClick));
onUnmounted(() => document.removeEventListener("mousedown", onDocClick));

function modeLabel(health: Health | null) {
  const mode = (health?.web_chat_mode ?? "setup_required") as WebChatMode;
  return MODE_LABEL[mode];
}
</script>

<template>
  <div ref="rootRef" class="sys-status">
    <button
      type="button"
      class="sys-status-btn"
      :class="`sys-status-btn--${!health ? 'unknown' : health.openscad_available ? 'ok' : 'warn'}`"
      :aria-expanded="open"
      aria-label="连接状态"
      title="连接状态"
      @click="open = !open"
    >
      <span
        class="sys-status-dot"
        :class="`sys-status-dot--${!health ? 'unknown' : health.openscad_available ? 'ok' : 'warn'}`"
        aria-hidden="true"
      />
    </button>
    <div v-if="open" class="sys-status-popover" role="dialog" aria-label="连接状态">
      <p class="sys-status-title">连接状态</p>
      <p v-if="!health" class="sys-status-empty">无法连接服务，请运行 make dev AGENT=… 启动。</p>
      <ul v-else class="sys-status-list">
        <li :class="health.openscad_available ? 'ok' : 'warn'">
          <span class="sys-status-item-dot" aria-hidden="true" />
          <div>
            <strong>建模引擎</strong>
            <span>{{ health.openscad_available ? "就绪" : "未安装 OpenSCAD" }}</span>
          </div>
        </li>
        <li :class="health.web_chat_mode === 'agent' ? 'ok' : 'warn'">
          <span class="sys-status-item-dot" aria-hidden="true" />
          <div>
            <strong>对话模式</strong>
            <span>{{ modeLabel(health) }}</span>
          </div>
        </li>
        <li v-if="health.web_chat_mode === 'agent'" class="ok">
          <span class="sys-status-item-dot" aria-hidden="true" />
          <div>
            <strong>设计助手</strong>
            <span>{{ health.assistant_label ?? "已连接" }}</span>
          </div>
        </li>
        <li v-else class="warn">
          <span class="sys-status-item-dot" aria-hidden="true" />
          <div>
            <strong>设计助手</strong>
            <span>未连接 — 顶栏「助手」可查看配置</span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
