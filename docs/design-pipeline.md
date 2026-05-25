# Notion3D 设计流水线

Agent 按 Skill 分阶段执行；Engine 只负责 ForgeCAD 渲染。

## 流程

```mermaid
flowchart TD
  U[用户消息] --> I[intake]
  I --> P[plan]
  P -->|A/B| A[forge-author]
  P -->|C / chat_only| Chat[对话]
  A --> R[render_forge + wait_job]
  R --> V[review]
  V -->|pass| Done[完成]
  V -->|retry| P
```

## Skills

`notion3d-pipeline` → `intake` → `plan` → `forge-author` → `mcp` → `review`

## 禁止

- 跳过 plan 直接写复杂装配
- 单轮完成 intake + author + review

详见 [AGENTS.md](../AGENTS.md)。
