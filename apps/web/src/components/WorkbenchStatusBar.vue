<script setup lang="ts">
import { computed } from "vue";
import type { Health } from "../api/client";

const props = defineProps<{
  health: Health | null;
  validationWarnings: string[];
  agentReady: boolean;
}>();

const forgeStatus = computed(() => {
  if (!props.health?.forgecad_available) return "Forge 未就绪";
  if (props.health.forge_preview_running) return "Forge 预览运行中";
  return "Forge 就绪";
});
</script>

<template>
  <footer class="workbench-status-bar" role="contentinfo">
    <span>单位 mm</span>
    <span class="sep">·</span>
    <span>ForgeCAD</span>
    <span class="sep">·</span>
    <span :class="{ warn: !health?.forgecad_available }">{{ forgeStatus }}</span>
    <span class="sep">·</span>
    <span :class="agentReady ? 'ok' : 'warn'">
      {{ agentReady ? "助手已连接" : "助手未连接" }}
    </span>
    <span v-if="validationWarnings.length" class="workbench-status-warn">
      <span class="sep">·</span>
      {{ validationWarnings.length }} 条校验提示
    </span>
  </footer>
</template>

<style scoped>
.workbench-status-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.15rem;
  padding: 0.28rem 0.85rem;
  border-top: 1px solid var(--border);
  background: #10141c;
  font-size: 0.68rem;
  color: var(--text-subtle);
  flex-shrink: 0;
}

.sep {
  opacity: 0.45;
}

.ok {
  color: var(--success);
}

.warn {
  color: var(--warn);
}

.workbench-status-warn {
  color: var(--warn);
}
</style>
