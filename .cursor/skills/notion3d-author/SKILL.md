---
name: notion3d-author
description: >-
  LEGACY OpenSCAD only — use notion3d-forge-author for all new modeling.
  Only load when editing templates/legacy/scad or explicitly using
  notion3d_render_scad.
---

# Notion3D Author（Legacy OpenSCAD）

**新建模请用 [notion3d-forge-author](../notion3d-forge-author/SKILL.md)。** 本 Skill 仅用于 legacy SCAD 模板（`templates/legacy/scad/`）或 `notion3d_render_scad`。

## 何时用

- 用户项目 `cad_backend=openscad_legacy`
- `scope=legacy` 模板
- 明确维护旧 SCAD 资产

## 执行路径

| plan.strategy | 动作 |
|---------------|------|
| template_apply | `notion3d_apply_template`（legacy 模板）→ wait_job |
| template_edit | get_template → 改 SCAD → `notion3d_render_scad` |
| from_scratch | 写 SCAD → `notion3d_render_scad` |

## OpenSCAD 规范

- 单位 mm；参数放文件顶部 `name = 数值;`
- `wall >= 1.6`（FDM）
- 禁止 `import`/`include` 外部路径
- 多部件：`// notion3d:part <id> [label] [#color]`

## 完成后

→ **notion3d-mcp**：`notion3d_wait_job` → **notion3d-review**
