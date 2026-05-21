<script setup lang="ts">
defineProps<{
  hasModel: boolean;
  hasExportable: boolean;
  busy: boolean;
  version: number | null;
}>();

const phases = [
  { id: "brief", label: "提需求" },
  { id: "design", label: "出方案" },
  { id: "iterate", label: "一起改" },
  { id: "export", label: "导出" },
] as const;
</script>

<template>
  <nav class="project-status" aria-label="设计协作状态">
    <template v-for="(p, i) in phases" :key="p.id">
      <span class="project-status-wrap">
        <span
          class="project-status-item"
          :class="{
            active:
              (p.id === 'brief' && !hasModel && !busy) ||
              (p.id === 'design' && busy) ||
              (p.id === 'iterate' && hasModel && !hasExportable && !busy) ||
              (p.id === 'export' && hasExportable),
            done:
              (p.id === 'brief' && (hasModel || busy)) ||
              (p.id === 'design' && hasModel && !busy) ||
              (p.id === 'iterate' && hasExportable),
          }"
        >
          <span class="project-status-dot" aria-hidden="true" />
          {{ p.label }}
          <span v-if="p.id === 'iterate' && version" class="project-status-meta">v{{ version }}</span>
        </span>
        <span v-if="i < phases.length - 1" class="project-status-sep" aria-hidden="true" />
      </span>
    </template>
  </nav>
</template>
