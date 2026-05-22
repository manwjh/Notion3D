<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

const props = defineProps<{
  open: boolean;
  busy?: boolean;
}>();

const emit = defineEmits<{ close: []; submit: [name: string] }>();

const projectName = ref("我的模型");
const inputRef = ref<HTMLInputElement | null>(null);

watch(
  () => props.open,
  async (v) => {
    if (v) {
      projectName.value = "我的模型";
      await nextTick();
      inputRef.value?.focus();
      inputRef.value?.select();
    }
  },
);

function handleSubmit(e: Event) {
  e.preventDefault();
  const name = projectName.value.trim();
  if (!name || props.busy) return;
  emit("submit", name);
}
</script>

<template>
  <div v-if="open" class="modal-backdrop" role="presentation" @click="emit('close')">
    <div
      class="modal-card"
      role="dialog"
      aria-labelledby="new-project-title"
      @click.stop
    >
      <h3 id="new-project-title">新建设计项目</h3>
      <p class="modal-desc">取个名字即可。创建后在对话区描述想要的 3D 物件。</p>

      <form @submit="handleSubmit">
        <label class="modal-field-label" for="project-name">项目名称</label>
        <input
          id="project-name"
          ref="inputRef"
          v-model="projectName"
          type="text"
          name="name"
          placeholder="例如：手机支架"
          :disabled="busy"
          autocomplete="off"
        />
        <div class="modal-actions">
          <button type="button" class="btn-ghost" :disabled="busy" @click="emit('close')">
            取消
          </button>
          <button type="submit" class="btn-primary" :disabled="busy">
            {{ busy ? "创建中…" : "创建并开始" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
