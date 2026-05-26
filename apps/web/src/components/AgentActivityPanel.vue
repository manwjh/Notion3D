<script setup lang="ts">
import type { AgentActivityStep } from "../api/client";

defineProps<{
  steps: AgentActivityStep[];
  activeJobMessage?: string | null;
}>();

function statusIcon(status: string) {
  if (status === "done") return "✓";
  if (status === "error") return "!";
  return "…";
}
</script>

<template>
  <div v-if="steps.length || activeJobMessage" class="agent-activity" aria-live="polite">
    <p class="agent-activity-title">Agent 处理过程</p>
    <ul class="agent-activity-list">
      <li
        v-for="step in steps"
        :key="step.id"
        class="agent-activity-item"
        :class="`agent-activity-item--${step.status}`"
      >
        <span class="agent-activity-icon" aria-hidden="true">{{ statusIcon(step.status) }}</span>
        <span class="agent-activity-body">
          <span class="agent-activity-label">{{ step.label }}</span>
          <span v-if="step.detail" class="agent-activity-detail">{{ step.detail }}</span>
        </span>
      </li>
      <li v-if="activeJobMessage" class="agent-activity-item agent-activity-item--running">
        <span class="agent-activity-icon spinner spinner--inline" aria-hidden="true" />
        <span class="agent-activity-body">
          <span class="agent-activity-label">{{ activeJobMessage }}</span>
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.agent-activity {
  margin: 0.25rem 0 0.5rem;
  padding: 0.65rem 0.75rem;
  border-radius: 10px;
  border: 1px solid rgba(62, 111, 214, 0.28);
  background: rgba(20, 28, 44, 0.85);
  font-size: 0.78rem;
  line-height: 1.4;
}

.agent-activity-title {
  margin: 0 0 0.45rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #8eb8ff;
  letter-spacing: 0.02em;
}

.agent-activity-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.agent-activity-item {
  display: flex;
  align-items: flex-start;
  gap: 0.45rem;
  color: #c8d4e8;
}

.agent-activity-item--running .agent-activity-label {
  color: #9ec5ff;
}

.agent-activity-item--done .agent-activity-icon {
  color: #7fd4a0;
}

.agent-activity-item--error .agent-activity-icon {
  color: #f0a0a0;
}

.agent-activity-icon {
  flex-shrink: 0;
  width: 1rem;
  text-align: center;
  font-weight: 700;
  font-size: 0.72rem;
  margin-top: 0.1rem;
}

.agent-activity-body {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.agent-activity-label {
  word-break: break-word;
}

.agent-activity-detail {
  color: #8a96aa;
  font-size: 0.72rem;
}
</style>
