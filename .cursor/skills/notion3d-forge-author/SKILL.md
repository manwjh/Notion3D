---
name: notion3d-forge-author
description: >-
  Notion3D ForgeCAD authoring phase: write parametric assembly .forge.js strictly
  from an approved design plan. Use after notion3d_report_design_plan, before
  notion3d_render_forge. Do not re-interpret user intent here.
---

# Notion3D Forge Author

Design Turn 第三阶段：**只执行 plan，写 ForgeCAD 脚本**。

## 输入

- 已提交的 `notion3d_report_design_plan`
- 有上一版时：`notion3d_get_forge_sources(project_id, version)` → 改 forge_code / files → render_forge
- `template_apply` 时：`notion3d_apply_template`（无需手写代码）

## 执行路径

| plan.strategy | 动作 |
|---------------|------|
| template_apply | `notion3d_apply_template` + params → wait_job |
| template_edit | get_template → 改 .forge.js → `notion3d_render_forge` |
| from_scratch | 写 .forge.js → `notion3d_render_forge` |
| 改上一版 | 在 vN 的 forge 基础上改 → `notion3d_render_forge` |

## ForgeCAD 规范

- 单位 mm；参数用 `param("Label", default, { min, max, unit: "mm" })`
- 多部件：`return [ { name: "PartId", shape: geom.color("#RRGGBB") }, ... ]`
- **部件精修**：每个部件用独立 `const partId = ...`（变量名与 return 中 shape 一致）；复杂部件可拆到 `src/part-name.forge.js` + `importAssembly`
- `return` 中 `name` 与 Web 部件树 label 一致，便于点选精修
- 外壳命名含 `Shell` / `外壳` → Web 半透明模式
- 多文件：`importAssembly("src/foo.forge.js")` + `files_json='{"foo.forge.js":"..."}'`
- 可用 `lib.bolt` / `lib.explode` 等 ForgeCAD 标准库

## 禁止

- 偏离 plan 的尺寸/部件清单
- 在本阶段改 plan（应 review→retry→plan）

## 完成后

→ **notion3d-mcp**：`notion3d_wait_job` → **notion3d-review**
