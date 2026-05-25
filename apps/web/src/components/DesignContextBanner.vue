<script setup lang="ts">
import { computed } from "vue";
import {
  DESIGN_PHASE_LABEL,
  PLAN_STRATEGY_LABEL,
  REVIEW_STATUS_LABEL,
} from "../strings/zh";

export type DesignContextView = {
  phase?: string | null;
  revision?: number | null;
  planSummary?: string | null;
  planStrategy?: string | null;
  planTemplateId?: string | null;
  planAssumptions?: string[];
  planModules?: string[];
  reviewStatus?: string | null;
  reviewNotes?: string[];
};

const props = defineProps<{
  context: DesignContextView | null;
}>();

const visible = computed(() => {
  const c = props.context;
  if (!c) return false;
  return Boolean(
    c.planSummary ||
      c.planStrategy ||
      c.planTemplateId ||
      (c.planAssumptions?.length ?? 0) > 0 ||
      (c.planModules?.length ?? 0) > 0 ||
      (c.reviewNotes?.length ?? 0) > 0 ||
      c.reviewStatus,
  );
});

const phaseLabel = computed(() => {
  const p = props.context?.phase;
  if (!p) return null;
  return DESIGN_PHASE_LABEL[p] ?? p;
});

const strategyLabel = computed(() => {
  const s = props.context?.planStrategy;
  if (!s) return null;
  return PLAN_STRATEGY_LABEL[s] ?? s;
});

const reviewLabel = computed(() => {
  const s = props.context?.reviewStatus;
  if (!s) return null;
  return REVIEW_STATUS_LABEL[s] ?? s;
});
</script>

<template>
  <div v-if="visible && context" class="design-context-banner" role="complementary">
    <div class="design-context-head">
      <strong class="design-context-title">设计方案</strong>
      <span v-if="phaseLabel" class="design-context-phase">{{ phaseLabel }}</span>
      <span v-if="context.revision != null && context.revision > 0" class="design-context-revision">
        迭代 {{ context.revision }}
      </span>
    </div>

    <p v-if="context.planSummary" class="design-context-summary">{{ context.planSummary }}</p>

    <dl class="design-context-meta">
      <div v-if="strategyLabel">
        <dt>策略</dt>
        <dd>{{ strategyLabel }}</dd>
      </div>
      <div v-if="context.planTemplateId">
        <dt>模板</dt>
        <dd>{{ context.planTemplateId }}</dd>
      </div>
      <div v-if="reviewLabel">
        <dt>验收</dt>
        <dd>{{ reviewLabel }}</dd>
      </div>
    </dl>

    <ul v-if="context.planModules?.length" class="design-context-list">
      <li v-for="(item, i) in context.planModules" :key="`m-${i}`">模块：{{ item }}</li>
    </ul>

    <ul v-if="context.planAssumptions?.length" class="design-context-list design-context-list--muted">
      <li v-for="(item, i) in context.planAssumptions" :key="`a-${i}`">{{ item }}</li>
    </ul>

    <ul v-if="context.reviewNotes?.length" class="design-context-list design-context-list--review">
      <li v-for="(item, i) in context.reviewNotes" :key="`r-${i}`">{{ item }}</li>
    </ul>
  </div>
</template>
