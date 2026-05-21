<script setup lang="ts">
import { ref } from "vue";
import { projectWebUrl } from "../composables/useProjectRoute";

const props = defineProps<{
  projectId: string | null;
  webUrl?: string | null;
}>();

const copied = ref(false);

async function copyLink() {
  const url = props.webUrl ?? (props.projectId ? projectWebUrl(props.projectId) : null);
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    /* ignore */
  }
}
</script>

<template>
  <button
    v-if="projectId"
    type="button"
    class="btn-secondary btn-secondary--compact project-link-btn"
    :title="webUrl ?? projectWebUrl(projectId)"
    @click="copyLink"
  >
    {{ copied ? "已复制链接" : "复制工作台链接" }}
  </button>
</template>
