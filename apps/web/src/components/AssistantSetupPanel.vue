<script setup lang="ts">
import { ref } from "vue";
import type { AgentProvider, Health } from "../api/client";

defineProps<{
  health: Health | null;
  open?: boolean;
}>();

const emit = defineEmits<{ close: [] }>();

const showTech = ref(false);

const options = [
  {
    id: "cursor_sdk",
    title: "Cursor 本机助手",
    desc: "推荐。配置 API Key 后可在 Web 直接对话设计复杂模型。",
    steps: ["在项目根目录 .env 填写 CURSOR_API_KEY", "运行 make dev（会自动启动助手服务）"],
  },
  {
    id: "openclaw",
    title: "OpenClaw",
    desc: "在本机运行 OpenClaw，适合已有 OpenClaw 工作流的用户。",
    steps: ["安装 openclaw CLI", "配置 notion3d 工具指向本机 API"],
  },
];

function isReady(id: string, providers: AgentProvider[] | undefined) {
  return providers?.find((p) => p.id === id)?.ready ?? false;
}
</script>

<template>
  <div v-if="open" class="setup-backdrop" role="presentation" @click="emit('close')">
    <div class="setup-card" role="dialog" aria-labelledby="setup-title" @click.stop>
      <header class="setup-header">
        <h3 id="setup-title">连接设计助手</h3>
        <p>Web 对话需连接设计助手。配置 API Key 后运行 make dev 即可开始建模。</p>
        <button type="button" class="setup-close" aria-label="关闭" @click="emit('close')">×</button>
      </header>

      <div class="setup-options">
        <article
          v-for="opt in options"
          :key="opt.id"
          class="setup-option"
          :class="{ ready: isReady(opt.id, health?.agent_providers) }"
        >
          <div class="setup-option-head">
            <strong>{{ opt.title }}</strong>
            <span v-if="isReady(opt.id, health?.agent_providers)" class="setup-badge ok">已就绪</span>
            <span v-else class="setup-badge">未连接</span>
          </div>
          <p>{{ opt.desc }}</p>
          <ol v-if="showTech" class="setup-steps">
            <li v-for="s in opt.steps" :key="s">{{ s }}</li>
          </ol>
        </article>
      </div>

      <footer class="setup-footer">
        <button type="button" class="btn-ghost" @click="showTech = !showTech">
          {{ showTech ? "收起技术说明" : "查看配置步骤" }}
        </button>
        <button type="button" class="btn-primary" @click="emit('close')">知道了</button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.setup-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(15, 18, 24, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.setup-card {
  background: var(--surface, #fff);
  border-radius: 16px;
  max-width: 520px;
  width: 100%;
  padding: 1.25rem 1.5rem 1rem;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.18);
  position: relative;
}
.setup-header h3 {
  margin: 0 0 0.35rem;
  font-size: 1.15rem;
}
.setup-header p {
  margin: 0;
  color: var(--text-muted, #6b7280);
  font-size: 0.9rem;
  line-height: 1.45;
  padding-right: 1.5rem;
}
.setup-close {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  border: none;
  background: transparent;
  font-size: 1.4rem;
  cursor: pointer;
  color: var(--text-muted, #6b7280);
}
.setup-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 1rem 0;
}
.setup-option {
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 12px;
  padding: 0.85rem 1rem;
}
.setup-option.ready {
  border-color: #86efac;
  background: #f0fdf4;
}
.setup-option-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}
.setup-badge {
  font-size: 0.72rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: #f3f4f6;
  color: #6b7280;
}
.setup-badge.ok {
  background: #dcfce7;
  color: #166534;
}
.setup-option p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted, #6b7280);
}
.setup-steps {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
  font-size: 0.82rem;
  color: var(--text-muted, #6b7280);
}
.setup-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}
</style>
