---
name: notion3d-plan
description: >-
  Optional archive — report_design_plan for multi-part summaries. Not required
  before render_forge.
---

# Plan（可选归档）

复杂多部件时可选调用 `notion3d_report_design_plan` 记录：

- `summary` — 物件 + 关键 mm
- `assembly_spec_json` — 部件关系
- `geometry_recipes_json` — 每部件 recipe（参考用，非门禁）

**不要**为简单单件阻塞 render。

→ render：`notion3d-mcp`
