<script setup lang="ts">
import { SAMPLE_PROMPTS, WELCOME_STEPS } from "../strings/zh";

defineProps<{
  samplePrompts?: string[];
}>();

const emit = defineEmits<{
  createProject: [];
  tryPrompt: [text: string];
}>();

const prompts = SAMPLE_PROMPTS;
</script>

<template>
  <div class="welcome-screen">
    <div class="welcome-hero">
      <div class="welcome-icon" aria-hidden="true">
        <span /><span /><span />
      </div>
      <h2 class="welcome-title">描述需求，立刻看到 3D 方案</h2>
      <p class="welcome-desc">
        连接设计助手后，用一句话说尺寸和用途，左侧即可看到 3D 方案。
      </p>
      <button type="button" class="btn-primary welcome-cta" @click="emit('createProject')">
        开始新项目
      </button>
    </div>

    <div class="welcome-steps">
      <div v-for="(s, i) in WELCOME_STEPS" :key="s.title" class="welcome-step">
        <span class="welcome-step-num">{{ i + 1 }}</span>
        <div>
          <strong>{{ s.title }}</strong>
          <p>{{ s.desc }}</p>
        </div>
      </div>
    </div>

    <div class="welcome-samples">
      <span class="welcome-samples-label">连接助手后，可试试这些描述</span>
      <div class="welcome-sample-grid">
        <button
          v-for="text in prompts"
          :key="text"
          type="button"
          class="welcome-sample-chip"
          @click="emit('tryPrompt', text)"
        >
          {{ text }}
        </button>
      </div>
    </div>
  </div>
</template>
