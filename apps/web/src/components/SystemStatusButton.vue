<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import type { Health } from "../api/client";

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
</script>

<template>
  <div ref="rootRef" class="sys-status">
    <button
      type="button"
      class="sys-status-btn"
      :class="`sys-status-btn--${!health ? 'unknown' : health.openscad_available ? 'ok' : 'warn'}`"
      :aria-expanded="open"
      aria-label="系统状态"
      title="系统状态"
      @click="open = !open"
    >
      <span
        class="sys-status-dot"
        :class="`sys-status-dot--${!health ? 'unknown' : health.openscad_available ? 'ok' : 'warn'}`"
        aria-hidden="true"
      />
    </button>
    <div v-if="open" class="sys-status-popover" role="dialog" aria-label="系统状态详情">
      <p class="sys-status-title">系统状态</p>
      <p v-if="!health" class="sys-status-empty">无法连接服务，请确认后端已启动（make api）。</p>
      <ul v-else class="sys-status-list">
        <li :class="health.openscad_available ? 'ok' : 'warn'">
          <span class="sys-status-item-dot" aria-hidden="true" />
          <div>
            <strong>建模引擎</strong>
            <span>{{ health.openscad_available ? "OpenSCAD 就绪" : "未安装 OpenSCAD" }}</span>
          </div>
        </li>
        <li class="ok">
          <span class="sys-status-item-dot" aria-hidden="true" />
          <div>
            <strong>Agent 接入</strong>
            <span>通过 MCP（{{ health.mcp_server ?? "notion3d" }}），智能建模由 Cursor / Claude Code / OpenClaw 负责</span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
