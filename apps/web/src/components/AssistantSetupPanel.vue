<script setup lang="ts">
import { computed, ref } from "vue";
import type { Health } from "../api/client";
import { ASSISTANT_LABEL } from "../strings/zh";

const props = defineProps<{
  health: Health | null;
  open?: boolean;
}>();

const emit = defineEmits<{ close: [] }>();

const showTech = ref<string | null>(null);

const providers = computed(() => {
  const list = props.health?.agent_providers ?? [];
  const order = ["cursor_sdk", "hermes"];
  return [...list].sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
});

const SETUP: Record<string, { title: string; desc: string; steps: string[] }> = {
  cursor_sdk: {
    title: "Cursor SDK（本机）",
    desc: "Dashboard → Integrations 获取 Key，经 agent-bridge 运行。",
    steps: [
      "在项目根目录 .env 填写 CURSOR_API_KEY",
      "运行 make dev AGENT=cursor_sdk（或 make dev-cursor）",
    ],
  },
  hermes: {
    title: "Hermes Agent",
    desc: "本机 hermes gateway + notion3d MCP；LLM Key 在 Hermes 配置。",
    steps: [
      "安装 hermes CLI，合并 config/hermes-notion3d-mcp.yaml 到 ~/.hermes/config.yaml",
      "在 ~/.hermes/.env 启用 API_SERVER_ENABLED 与 API_SERVER_KEY",
      "运行 make dev AGENT=hermes（或 make dev-hermes）",
    ],
  },
};

function label(id: string) {
  return ASSISTANT_LABEL[id] ?? id;
}
</script>

<template>
  <div v-if="open" class="setup-backdrop" role="presentation" @click="emit('close')">
    <div class="setup-card" role="dialog" aria-labelledby="setup-title" @click.stop>
      <header class="setup-header">
        <h3 id="setup-title">连接设计助手</h3>
        <p>Web 对话需外部 Agent。任选一种方式配置后重启 dev 栈。</p>
        <button type="button" class="setup-close" aria-label="关闭" @click="emit('close')">×</button>
      </header>

      <article
        v-for="p in providers"
        :key="p.id"
        class="setup-option"
        :class="{ ready: p.ready }"
      >
        <div class="setup-option-head">
          <strong>{{ SETUP[p.id]?.title ?? label(p.id) }}</strong>
          <span v-if="p.ready" class="setup-badge ok">已就绪</span>
          <span v-else class="setup-badge">未连接</span>
        </div>
        <p>{{ SETUP[p.id]?.desc ?? p.note }}</p>
        <p v-if="!p.ready && p.note" class="setup-note">{{ p.note }}</p>
        <ol v-if="showTech === p.id && SETUP[p.id]" class="setup-steps">
          <li v-for="s in SETUP[p.id].steps" :key="s">{{ s }}</li>
        </ol>
        <button
          v-if="SETUP[p.id]"
          type="button"
          class="btn-ghost setup-steps-toggle"
          @click="showTech = showTech === p.id ? null : p.id"
        >
          {{ showTech === p.id ? "收起步骤" : "配置步骤" }}
        </button>
      </article>

      <footer class="setup-footer">
        <a class="setup-link" href="https://github.com/NousResearch/hermes-agent" target="_blank" rel="noopener">
          Hermes 文档
        </a>
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
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: max(1rem, env(safe-area-inset-top)) max(1rem, env(safe-area-inset-right))
    max(1rem, env(safe-area-inset-bottom)) max(1rem, env(safe-area-inset-left));
}
.setup-card {
  background: var(--bg-elevated);
  color: var(--text);
  border: 1px solid var(--border-strong);
  border-radius: 16px;
  max-width: 520px;
  width: 100%;
  max-height: min(90dvh, 640px);
  overflow-y: auto;
  padding: 1.25rem 1.5rem 1rem;
  box-shadow: var(--shadow-pop);
  position: relative;
}
.setup-header h3 {
  margin: 0 0 0.35rem;
  font-size: 1.15rem;
}
.setup-header p {
  margin: 0;
  color: var(--text-muted);
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
  color: var(--text-muted);
}
.setup-option {
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  padding: 0.85rem 1rem;
  margin: 1rem 0;
  background: var(--bg-surface);
}
.setup-option.ready {
  border-color: rgba(92, 184, 138, 0.45);
  background: var(--success-soft);
}
.setup-option-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  flex-wrap: wrap;
}
.setup-badge {
  font-size: 0.72rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: var(--bg-input);
  color: var(--text-muted);
}
.setup-badge.ok {
  background: var(--success-soft);
  color: var(--success);
}
.setup-option p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}
.setup-note {
  margin-top: 0.35rem !important;
  font-size: 0.8rem !important;
}
.setup-steps {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
  font-size: 0.82rem;
  color: var(--text-muted);
}
.setup-steps-toggle {
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.82rem;
}
.setup-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.setup-link {
  font-size: 0.85rem;
  color: #8eb8ff;
}

@media (max-width: 640px) {
  .setup-backdrop {
    align-items: flex-end;
    padding: 0;
  }

  .setup-card {
    max-width: none;
    max-height: min(92dvh, 720px);
    border-radius: 14px 14px 0 0;
    padding: 1rem 1rem max(1rem, env(safe-area-inset-bottom));
  }
}
</style>
