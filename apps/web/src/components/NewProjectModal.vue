<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

const props = defineProps<{
  open: boolean;
  busy?: boolean;
  samplePrompts?: string[];
}>();

const emit = defineEmits<{
  close: [];
  submit: [name: string];
}>();

const projectName = ref("我的模型");
const inputRef = ref<HTMLInputElement | null>(null);

const templates = [
  { name: "我的盒子", icon: "📦" },
  { name: "定制零件", icon: "⚙️" },
  { name: "装饰摆件", icon: "✨" },
];

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
      class="modal-card modal-card--wide"
      role="dialog"
      aria-labelledby="new-project-title"
      @click.stop
    >
      <h3 id="new-project-title">新建建模项目</h3>
      <p class="modal-desc">给项目取个名字，然后开始用对话描述模型。</p>

      <div class="modal-templates">
        <button
          v-for="t in templates"
          :key="t.name"
          type="button"
          class="modal-template-btn"
          :disabled="busy"
          @click="projectName = t.name"
        >
          <span aria-hidden="true">{{ t.icon }}</span>
          {{ t.name }}
        </button>
      </div>

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
            {{ busy ? "创建中…" : "开始建模" }}
          </button>
        </div>
      </form>

      <p v-if="samplePrompts?.length" class="modal-footnote">
        创建后可试试：{{ samplePrompts.slice(0, 2).join("、") }}…
      </p>
    </div>
  </div>
</template>
