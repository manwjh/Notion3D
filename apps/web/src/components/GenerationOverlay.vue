<script setup lang="ts">
import { computed } from "vue";
import type { GenerationState } from "../types/generation";
import { phaseLabel } from "../types/generation";

const props = defineProps<{
  state: GenerationState;
  hasModel: boolean;
}>();

const label = computed(() => phaseLabel(props.state.phase, props.state.detail));

const footnote = computed(() => {
  switch (props.state.phase) {
    case "generating":
      return "复杂造型可能需要 1–3 分钟";
    case "rendering":
      return "OpenSCAD 正在计算几何体";
    default:
      return null;
  }
});
</script>

<template>
  <div
    class="gen-overlay"
    :class="{ 'gen-overlay--dim': hasModel }"
    aria-live="polite"
  >
    <div class="gen-overlay-card">
      <div class="gen-visual" aria-hidden="true">
        <div class="gen-ring" />
        <div class="gen-cube">
          <span /><span /><span /><span /><span /><span />
        </div>
      </div>

      <p class="gen-title">{{ label ?? "处理中…" }}</p>

      <p v-if="state.prompt" class="gen-prompt" :title="state.prompt">
        「{{
          state.prompt.length > 48 ? `${state.prompt.slice(0, 48)}…` : state.prompt
        }}」
      </p>

      <p v-if="footnote" class="gen-footnote">{{ footnote }}</p>
    </div>
  </div>
</template>
