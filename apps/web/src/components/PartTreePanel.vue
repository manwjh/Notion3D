<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import type { ModelPart } from "../types/parts";
import type { ModelPick } from "../types/pick";

const props = defineProps<{
  parts: ModelPart[];
  pick?: ModelPick | null;
  hidden: Record<string, boolean>;
  opacities: Record<string, number>;
}>();

const emit = defineEmits<{
  pick: [part: ModelPart];
  toggle: [partId: string];
  opacity: [partId: string, value: number];
  focus: [partId: string];
  showAll: [];
  fitAll: [];
  shellMode: [];
}>();

const listRef = ref<HTMLUListElement | null>(null);

watch(
  () => props.pick?.element,
  async (element) => {
    if (!element) return;
    await nextTick();
    listRef.value
      ?.querySelector(`[data-part-id="${element}"]`)
      ?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  },
);
</script>

<template>
  <section class="part-tree-panel">
    <div class="part-tree-head">
      <strong>部件</strong>
      <span>{{ parts.length }}</span>
    </div>
    <div v-if="parts.length" class="part-tree-actions">
      <button type="button" @click="emit('showAll')">全部显示</button>
      <button type="button" @click="emit('fitAll')">适应</button>
      <button type="button" @click="emit('shellMode')">外壳</button>
    </div>
    <p v-if="!parts.length" class="part-tree-empty">暂无分件，生成装配后会显示部件树。</p>
    <ul v-else ref="listRef" class="part-tree-list">
      <li
        v-for="part in parts"
        :key="part.id"
        :data-part-id="part.id"
        :class="{ selected: pick?.element === part.id }"
        @click="emit('pick', part)"
      >
        <label class="part-tree-row" @click.stop>
          <input
            type="checkbox"
            :checked="!hidden[part.id]"
            @change="emit('toggle', part.id)"
          />
          <span class="swatch" :style="{ background: part.color }" />
          <span class="label">{{ part.label }}</span>
          <button type="button" class="fit-btn" title="聚焦" @click.stop="emit('focus', part.id)">
            ◎
          </button>
        </label>
        <input
          class="opacity"
          type="range"
          min="0.1"
          max="1"
          step="0.05"
          :value="opacities[part.id] ?? 1"
          @input="emit('opacity', part.id, Number(($event.target as HTMLInputElement).value))"
        />
      </li>
    </ul>
  </section>
</template>

<style scoped>
.part-tree-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.part-tree-head {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 0.65rem;
  font-size: 0.78rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.part-tree-head strong {
  color: var(--text);
  font-weight: 600;
}

.part-tree-actions {
  flex-shrink: 0;
  display: flex;
  gap: 0.3rem;
  padding: 0 0.65rem 0.45rem;
}

.part-tree-actions button {
  flex: 1;
  font-size: 0.68rem;
  padding: 0.22rem 0.3rem;
  border-radius: 4px;
  border: 1px solid var(--border-strong);
  background: var(--bg-elevated);
  color: var(--text-muted);
}

.part-tree-empty {
  margin: 0;
  padding: 0.5rem 0.65rem;
  font-size: 0.75rem;
  color: var(--text-subtle);
  line-height: 1.45;
}

.part-tree-list {
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  overflow-x: hidden;
  flex: 1;
  min-height: 0;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  scrollbar-gutter: stable;
}

.part-tree-list li {
  padding: 0.35rem 0.65rem 0.45rem;
  border-top: 1px solid var(--border);
  cursor: pointer;
}

.part-tree-list li.selected {
  background: rgba(77, 132, 247, 0.12);
  box-shadow: inset 3px 0 0 var(--accent);
}

.part-tree-list li:hover {
  background: rgba(255, 255, 255, 0.03);
}

.part-tree-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: var(--text);
  cursor: pointer;
}

.swatch {
  width: 9px;
  height: 9px;
  border-radius: 2px;
  flex-shrink: 0;
}

.label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fit-btn {
  border: none;
  background: transparent;
  color: #7aa2f7;
  cursor: pointer;
  padding: 0;
  font-size: 0.82rem;
}

.opacity {
  width: 100%;
  margin-top: 0.3rem;
}
</style>
