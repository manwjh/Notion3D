<script setup lang="ts">
import { computed } from "vue";
import type { Health, WebChatMode } from "../api/client";
import { STATUS_BAR } from "../strings/zh";

type SegmentTone = "busy" | "warn" | "muted";

type StatusSegment = {
  text: string;
  tone?: SegmentTone;
};

const props = defineProps<{
  health: Health | null;
  validationWarnings: string[];
  projectSelected: boolean;
  jobStatusLabel: string | null;
  partCount: number;
  versionIncomplete: boolean;
  hasModel: boolean;
  selectedPartLabel: string | null;
}>();

const segments = computed((): StatusSegment[] => {
  const items: StatusSegment[] = [];

  if (props.jobStatusLabel) {
    items.push({ text: props.jobStatusLabel, tone: "busy" });
  } else if (!props.projectSelected) {
    items.push({ text: STATUS_BAR.noProject, tone: "muted" });
  } else if (props.partCount > 0) {
    items.push({ text: STATUS_BAR.partCount(props.partCount) });
  } else if (props.versionIncomplete) {
    items.push({ text: STATUS_BAR.pendingMesh, tone: "warn" });
  } else if (!props.hasModel) {
    items.push({ text: STATUS_BAR.noModel, tone: "muted" });
  }

  if (props.selectedPartLabel) {
    items.push({ text: STATUS_BAR.selectedPart(props.selectedPartLabel) });
  }

  const chatMode: WebChatMode | undefined = props.health?.web_chat_mode;
  if (chatMode === "setup_required" && !props.jobStatusLabel) {
    items.push({ text: STATUS_BAR.manualEditOnly, tone: "muted" });
  }

  return items;
});

function toneClass(tone?: SegmentTone): string | undefined {
  if (tone === "busy") return "workbench-status-busy";
  if (tone === "warn") return "workbench-status-warn";
  if (tone === "muted") return "workbench-status-muted";
  return undefined;
}
</script>

<template>
  <footer class="workbench-status-bar" role="contentinfo">
    <span>单位 mm</span>
    <template v-for="(segment, index) in segments" :key="index">
      <span class="sep">·</span>
      <span :class="toneClass(segment.tone)">{{ segment.text }}</span>
    </template>
    <template v-if="validationWarnings.length">
      <span class="sep">·</span>
      <span class="workbench-status-warn">
        {{ STATUS_BAR.validationCount(validationWarnings.length) }}
      </span>
    </template>
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

.workbench-status-busy {
  color: #8eb8ff;
}

.workbench-status-warn {
  color: var(--warn);
}

.workbench-status-muted {
  color: var(--text-subtle);
  opacity: 0.85;
}
</style>
