<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import type { Health } from "../api/client";
import { STATUS } from "../strings/zh";

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
      :class="`sys-status-btn--${!health ? 'unknown' : health.forgecad_available ? 'ok' : 'warn'}`"
      :aria-expanded="open"
      aria-label="服务状态"
      title="服务状态"
      @click="open = !open"
    >
      <span
        class="sys-status-dot"
        :class="`sys-status-dot--${!health ? 'unknown' : health.forgecad_available ? 'ok' : 'warn'}`"
        aria-hidden="true"
      />
    </button>
    <div v-if="open" class="sys-status-popover" role="dialog" :aria-label="STATUS.popoverTitle">
      <p class="sys-status-title">{{ STATUS.popoverTitle }}</p>
      <p v-if="!health" class="sys-status-empty">{{ STATUS.serviceUnreachable }}</p>
      <ul v-else class="sys-status-list">
        <li :class="health.status === 'ok' ? 'ok' : 'warn'">
          <span class="sys-status-item-dot" aria-hidden="true" />
          <div>
            <strong>Notion3D</strong>
            <span>{{ health.status === "ok" ? STATUS.workbenchReady : STATUS.workbenchMissing }}</span>
          </div>
        </li>
        <li :class="health.forgecad_available ? 'ok' : 'warn'">
          <span class="sys-status-item-dot" aria-hidden="true" />
          <div>
            <strong>ForgeCAD</strong>
            <span>{{ health.forgecad_available ? STATUS.forgeReady : STATUS.forgeMissing }}</span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
