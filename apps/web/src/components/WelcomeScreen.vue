<script setup lang="ts">
import AgentGuidePanel from "./AgentGuidePanel.vue";

defineProps<{
  samplePrompts: string[];
}>();

const emit = defineEmits<{
  createProject: [];
  pickPrompt: [text: string];
}>();

const steps = [
  { n: 1, title: "Agent 建模", desc: "在 Cursor / Claude Code / OpenClaw 中用 MCP 描述需求，Agent 生成 SCAD 并渲染" },
  { n: 2, title: "打开工作台", desc: "Agent 返回 web_url，或从顶栏选择 Agent 创建的项目" },
  { n: 3, title: "预览与导出", desc: "在此旋转 3D、调参数滑块、下载 STL" },
];
</script>

<template>
  <div class="welcome-screen">
    <AgentGuidePanel />

    <div class="welcome-hero">
      <div class="welcome-icon" aria-hidden="true">
        <span /><span /><span />
      </div>
      <h2 class="welcome-title">OpenSCAD 建模工作台</h2>
      <p class="welcome-desc">
        智能建模由 Agent 负责；本页面用于预览、微调与导出。也可手动新建项目体验简单模板。
      </p>
      <button type="button" class="btn-secondary welcome-cta-secondary" @click="emit('createProject')">
        手动新建项目
      </button>
    </div>

    <div class="welcome-steps">
      <div v-for="s in steps" :key="s.n" class="welcome-step">
        <span class="welcome-step-num">{{ s.n }}</span>
        <div>
          <strong>{{ s.title }}</strong>
          <p>{{ s.desc }}</p>
        </div>
      </div>
    </div>

    <div v-if="samplePrompts.length" class="welcome-samples">
      <span class="welcome-samples-label">简单模板示例（右侧快速调整）</span>
      <div class="welcome-sample-grid">
        <button
          v-for="text in samplePrompts"
          :key="text"
          type="button"
          class="welcome-sample-chip"
          @click="emit('pickPrompt', text)"
        >
          {{ text }}
        </button>
      </div>
    </div>
  </div>
</template>
