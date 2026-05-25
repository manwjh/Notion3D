---
name: notion3d-pipeline
description: >-
  Notion3D design pipeline orchestrator: multi-phase workflow intake → plan →
  author → render → review. Routes to notion3d-intake, notion3d-plan,
  notion3d-forge-author, notion3d-mcp, notion3d-review skills. Use for all
  Notion3D Web/MCP modeling tasks.
---

# Notion3D 设计流水线（总览）

```
用户描述 → intake → plan → author → render → review → 完成
```

## Skills（按序）

| Skill | 职责 |
|-------|------|
| [notion3d-intake](../notion3d-intake/SKILL.md) | 澄清需求、A/B/C 分类 |
| [notion3d-plan](../notion3d-plan/SKILL.md) | `report_design_plan` |
| [notion3d-forge-author](../notion3d-forge-author/SKILL.md) | 写/改 `.forge.js` |
| [notion3d-mcp](../notion3d-mcp/SKILL.md) | `render_forge` / `wait_job` |
| [notion3d-review](../notion3d-review/SKILL.md) | `report_design_review` |

## 参考

- [docs/design-pipeline.md](../../docs/design-pipeline.md)
- [docs/cad-backend-v2.md](../../docs/cad-backend-v2.md)
