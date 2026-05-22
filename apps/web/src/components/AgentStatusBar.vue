<script setup lang="ts">
defineProps<{
  agentReady: boolean;
}>();
</script>

<template>
  <div
    v-if="!agentReady"
    class="agent-status agent-status--warn"
    role="status"
  >
    <span class="agent-status-dot" aria-hidden="true" />
    <span class="agent-status-text">助手未连接</span>
  </div>
</template>
