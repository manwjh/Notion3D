<script setup lang="ts">
import { computed } from "vue";
import type { GenerationState } from "../types/generation";
import { GENERATION_STEPS, phaseLabel, stepIndex } from "../types/generation";

const props = defineProps<{
  state: GenerationState;
  hasModel: boolean;
}>();

const activeStep = computed(() => stepIndex(props.state.phase));
const label = computed(() => phaseLabel(props.state.phase, props.state.detail));

const footnote = computed(() => {
  switch (props.state.phase) {
    case "generating":
      return "复杂造型可能需要 1–3 分钟，请稍候";
    case "previewing":
      return "预览图已显示在左侧，3D 模型仍在计算";
    case "rendering":
      return "3D 模型即将呈现";
    default:
      return "正在处理你的请求…";
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

      <ol class="gen-steps">
        <li
          v-for="(step, i) in GENERATION_STEPS"
          :key="step.id"
          class="gen-step"
          :class="{ done: activeStep > i, active: activeStep === i }"
        >
          <span class="gen-step-num">{{ activeStep > i ? "✓" : i + 1 }}</span>
          <div class="gen-step-body">
            <strong>{{ step.label }}</strong>
            <span>{{ activeStep === i ? step.hint : activeStep > i ? "已完成" : "等待中" }}</span>
          </div>
        </li>
      </ol>

      <p class="gen-footnote">{{ footnote }}</p>
    </div>
  </div>
</template>
