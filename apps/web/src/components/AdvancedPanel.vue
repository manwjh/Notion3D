<script setup lang="ts">
import type { Job } from "../api/client";
import type { JobPhase } from "../types/generation";
import ModelToolsPanel from "./ModelToolsPanel.vue";

defineProps<{
  open: boolean;
  projectId: string | null;
  scadUrl: string | null;
  version: number | null;
  generating?: boolean;
  generationPhase?: JobPhase;
  trackJob: (job: Job, prompt: string) => Promise<void>;
}>();

const emit = defineEmits<{ close: [] }>();
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="advanced-backdrop" @click.self="emit('close')">
      <aside class="advanced-drawer" role="dialog" aria-labelledby="advanced-title">
        <header class="advanced-header">
          <div>
            <h2 id="advanced-title">高级编辑</h2>
            <p class="advanced-subtitle">直接改 OpenSCAD，不经过设计助手</p>
          </div>
          <button type="button" class="btn-ghost btn-ghost--compact" @click="emit('close')">
            关闭
          </button>
        </header>
        <ModelToolsPanel
          :project-id="projectId"
          :scad-url="scadUrl"
          :version="version"
          :generating="generating"
          :generation-phase="generationPhase"
          :track-job="trackJob"
        />
      </aside>
    </div>
  </Teleport>
</template>
