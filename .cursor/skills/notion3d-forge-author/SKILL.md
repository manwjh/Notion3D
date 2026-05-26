---
name: notion3d-forge-author
description: >-
  Write ForgeCAD for render_forge. Full API allowed; iterate from wait_job
  feedback. Templates optional.
---

# Forge Author

真源：[docs/forge-modeling-guide.md](../../docs/forge-modeling-guide.md)

## 输入

- 用户需求 + 可选 vN：`notion3d_get_forge_sources`
- 可选模板：`notion3d_apply_template` / `get_template`

## 输出

- `notion3d_render_forge(forge_code, files_json=...)`
- `notion3d_wait_job` → 读 digest / warnings → 继续改或回复用户

## 规范

- mm；多部件 `return [{ name, shape }]`
- `src/*.forge.js` + `importAssembly` 用于复杂件
- 全 ForgeCAD API 可用

→ [notion3d-mcp](../notion3d-mcp/SKILL.md)
