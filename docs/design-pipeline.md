# Notion3D 设计流水线

LLM 设计 与 ForgeCAD Engine 渲染分离，Agent 按 Skill 分阶段执行。

## 流程

```mermaid
flowchart TD
  U[用户消息 / Design Turn] --> I[intake]
  I --> P[plan + report_design_plan]
  P -->|A/B| A[forge-author]
  P -->|C / chat_only| Chat[对话 + review pass]
  A --> R[render_forge + wait_job]
  R --> E[ForgeCAD → STL + parts]
  E --> V[review + report_design_review]
  V -->|pass| Done[完成]
  V -->|retry| P
  V -->|retry author| A
```

## Skills

```
.cursor/skills/
  notion3d-pipeline/      总览
  notion3d-intake/
  notion3d-plan/
  notion3d-forge-author/
  notion3d-mcp/
  notion3d-review/
```

## 禁止

- 跳过 plan 直接写复杂装配
- 单轮完成 intake + author + review
- Agent 新建模走 legacy OpenSCAD（见 [architecture.md](architecture.md#legacy-engine-保留)）

## 相关

- [AGENTS.md](../AGENTS.md) — MCP 工作流
- [cad-backend-v2.md](cad-backend-v2.md) — 渲染产物
