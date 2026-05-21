<script setup lang="ts">
defineProps<{
  step: "describe" | "preview" | "adjust" | "export";
  busy: boolean;
}>();

const steps = [
  { id: "describe" as const, label: "描述" },
  { id: "preview" as const, label: "预览" },
  { id: "adjust" as const, label: "调整" },
  { id: "export" as const, label: "导出" },
];
const order = ["describe", "preview", "adjust", "export"] as const;

function stepIndex(id: string) {
  return order.indexOf(id as (typeof order)[number]);
}
</script>

<template>
  <nav class="workflow-bar" aria-label="建模流程">
    <template v-for="(s, i) in steps" :key="s.id">
      <span class="workflow-item-wrap">
        <span
          class="workflow-item"
          :class="{
            done: i < stepIndex(step),
            active: s.id === step || (busy && s.id === 'preview' && step === 'describe'),
          }"
        >
          <span class="workflow-item-num">{{ i < stepIndex(step) ? "✓" : i + 1 }}</span>
          {{ s.label }}
        </span>
        <span v-if="i < steps.length - 1" class="workflow-sep" aria-hidden="true" />
      </span>
    </template>
  </nav>
</template>
