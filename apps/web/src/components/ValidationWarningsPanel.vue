<script setup lang="ts">
defineProps<{
  warnings: string[];
}>();
</script>

<template>
  <div v-if="warnings.length" class="validation-warnings" role="alert">
    <p class="validation-warnings-title">建模 / 装配提示（可选改进）</p>
    <ul class="validation-warnings-list">
      <li v-for="(warning, index) in warnings" :key="index">{{ warning }}</li>
    </ul>
  </div>
</template>

<style scoped>
.validation-warnings {
  margin: 0 1rem 0.5rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid rgba(230, 170, 60, 0.35);
  background: rgba(230, 170, 60, 0.08);
  font-size: 0.78rem;
  line-height: 1.45;
}

.validation-warnings-title {
  margin: 0 0 0.35rem;
  font-weight: 600;
  color: #f0c674;
}

.validation-warnings-list {
  margin: 0;
  padding-left: 1.1rem;
  color: #e8dcc8;
}

.validation-warnings-list li + li {
  margin-top: 0.25rem;
}
</style>
