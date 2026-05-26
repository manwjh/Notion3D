---
name: notion3d-pipeline
description: >-
  Notion3D render-first modeling: health → render_forge → wait_job → iterate.
  Optional plan/review archives. Use for all Notion3D Web/MCP modeling tasks.
---

# Notion3D 建模（render-first）

真源：[docs/forge-modeling-guide.md](../../docs/forge-modeling-guide.md)

```
用户描述 → render_forge → wait_job → 读反馈 → 改 forge → … → 交付
```

## 原则

1. **优先出可见结果** — 合理默认尺寸，不要问卷
2. **渲染结果是真理** — mesh / spatial_digest / 用户截图 > recipe 正则
3. **指哪改哪** — `get_forge_sources(vN)` 增量改稿
4. **校验是建议** — `装配校验：` / `建模建议：` 不阻塞交付
5. **plan/review 可选** — 复杂装配时可 `report_design_plan` 归档

## Skill

| Skill | 用途 |
|-------|------|
| [notion3d-mcp](../notion3d-mcp/SKILL.md) | MCP 工具与主循环 |

## 模板（可选起点）

sketch-enclosure · sketch-bracket · loft-hull · hello-assembly

## 参考

- [docs/design-pipeline.md](../../docs/design-pipeline.md)
- [docs/cad-backend-v2.md](../../docs/cad-backend-v2.md)
