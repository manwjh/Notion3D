<script setup lang="ts">
import { computed } from "vue";
import { parseModelParams, setModelParam } from "../utils/modelParams";

const props = defineProps<{
  code: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{ change: [code: string] }>();

const params = computed(() => parseModelParams(props.code));

function update(name: string, value: number) {
  emit("change", setModelParam(props.code, name, value));
}
</script>

<template>
  <div v-if="params.length" class="param-panel param-panel--embedded">
    <div class="param-panel-header">
      <span class="param-panel-title">尺寸参数</span>
    </div>
    <div class="param-grid">
      <label v-for="p in params" :key="p.name" class="param-field">
        <span class="param-label">{{ p.label }}</span>
        <div class="param-controls">
          <input
            type="range"
            :min="p.min"
            :max="p.max"
            :step="p.value < 1 ? 0.1 : 1"
            :value="p.value"
            :disabled="disabled"
            @input="update(p.name, parseFloat(($event.target as HTMLInputElement).value))"
          />
          <input
            type="number"
            class="param-num"
            :value="p.value"
            :step="p.value < 1 ? 0.1 : 1"
            :disabled="disabled"
            @change="
              update(p.name, parseFloat(($event.target as HTMLInputElement).value))
            "
          />
          <span class="param-unit">{{ p.unit }}</span>
        </div>
      </label>
    </div>
  </div>
</template>
