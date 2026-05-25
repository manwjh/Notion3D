---
name: notion3d-openscad
description: >-
  Notion3D design pipeline orchestrator: multi-phase workflow intake → plan →
  author → render → review. Routes to notion3d-intake, notion3d-plan,
  notion3d-forge-author, notion3d-mcp, notion3d-review skills. Use for all
  Notion3D Web/MCP modeling tasks.
---

# Notion3D 设计流水线（总览）

Notion3D = **ForgeCAD 装配建模** + **分阶段 Agent** + **Engine 渲染** + **模板库**。

```
用户描述 → intake → plan → author(forge) → render → review → 完成
              ↓ ForgeCAD: model.stl + parts.json
              ↓ Templates: hello-assembly / open-enclosure
```

## 分阶段 Skills（按序加载）

| Skill | 职责 |
|-------|------|
| [notion3d-intake](../notion3d-intake/SKILL.md) | 澄清需求、A/B/C 分类 |
| [notion3d-plan](../notion3d-plan/SKILL.md) | 模板检索、`report_design_plan` |
| [notion3d-forge-author](../notion3d-forge-author/SKILL.md) | 写/改 .forge.js |
| [notion3d-mcp](../notion3d-mcp/SKILL.md) | MCP 工具与异步 render |
| [notion3d-review](../notion3d-review/SKILL.md) | 验收、`report_design_review` |

Legacy OpenSCAD：`templates/legacy/scad/`，仅 `notion3d_render_scad`。

## 附加资源

- [docs/cad-backend-v2.md](../../docs/cad-backend-v2.md) — ForgeCAD 后端
- [docs/design-pipeline.md](../../docs/design-pipeline.md) — 架构说明

## 本地调试

```bash
cd apps/forge-runner && npm install
make dev AGENT=cursor_sdk
```
