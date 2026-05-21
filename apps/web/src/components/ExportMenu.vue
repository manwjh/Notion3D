<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import type { ModelVersion } from "../api/client";

const props = defineProps<{
  version: ModelVersion | null | undefined;
  prominent?: boolean;
}>();

const open = ref(false);
const rootRef = ref<HTMLElement | null>(null);

const stlItem = computed(() =>
  props.version?.stl_url
    ? { label: "3D 模型 (STL)", href: props.version.stl_url, download: true }
    : null,
);

const items = computed(() => {
  const list = [];
  if (stlItem.value) list.push(stlItem.value);
  if (props.version?.scad_url) {
    list.push({ label: "源码 (高级)", href: props.version.scad_url, external: true });
  }
  return list as { label: string; href: string; external?: boolean; download?: boolean }[];
});

function onDocClick(e: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(e.target as Node)) open.value = false;
}

onMounted(() => document.addEventListener("mousedown", onDocClick));
onUnmounted(() => document.removeEventListener("mousedown", onDocClick));
</script>

<template>
  <div ref="rootRef" class="export-menu">
    <a
      v-if="prominent && stlItem"
      class="btn-primary export-download-btn"
      :href="stlItem.href"
      download
    >
      下载模型
    </a>
    <template v-else>
      <button
        type="button"
        :class="prominent ? 'btn-primary' : 'action-btn action-btn--primary'"
        :disabled="items.length === 0"
        :aria-expanded="open"
        @click="open = !open"
      >
        导出 ▾
      </button>
      <div v-if="open && items.length" class="export-menu-dropdown">
        <a
          v-for="item in items"
          :key="item.label"
          :href="item.href"
          :target="item.external ? '_blank' : undefined"
          :rel="item.external ? 'noreferrer' : undefined"
          :download="item.download || undefined"
          @click="open = false"
        >
          {{ item.label }}
        </a>
      </div>
    </template>
  </div>
</template>
