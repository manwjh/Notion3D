<script setup lang="ts">
defineProps<{
  compact?: boolean;
}>();
</script>

<template>
  <div class="agent-guide" :class="{ 'agent-guide--compact': compact }">
    <p class="agent-guide-title">用 Agent 建模</p>
    <p class="agent-guide-desc">
      在 Cursor、Claude Code 或 OpenClaw 中配置 Notion3D MCP，由 Agent 生成 OpenSCAD 并提交渲染。
      完成后 Agent 会给你工作台链接，在此预览、调参、导出 STL。
    </p>
    <ol class="agent-guide-steps">
      <li>启动 <code>make api</code>（本页面已连接）</li>
      <li>Agent 调用 <code>notion3d_create_project</code> → <code>notion3d_render_scad</code></li>
      <li>打开 Agent 返回的 <code>web_url</code>，或从顶栏项目列表选择</li>
    </ol>
  </div>
</template>
