# ForgeCAD 建模指南

Notion3D Agent 与 Web Turn 的 ForgeCAD 参考。范式：**render-first** — 先出几何，再按 `spatial_digest` / `validation_warnings` 迭代。

全量 API：`apps/forge-runner/node_modules/forgecad/docs/permanent/API/`；`cd apps/forge-runner && npx forgecad skill install`。

## 工作方式

| 步骤 | Agent 做法 |
|------|------------|
| **Render** | `notion3d_render_forge` → `notion3d_wait_job` |
| **Sense** | 读 `spatial_summary`、`validation_warnings`（**可选改进**）、截图 |
| **Iterate** | `get_forge_sources(vN)` → 改 forge / src → 再 render |
| **Archive**（可选） | `report_design_plan` / `report_design_review` |

## Geometry Recipes（可选参考）

Plan 可声明 `geometry_recipes` 作记录；**不是 render 门禁**。

| recipe | 适用 | ForgeCAD |
|--------|------|----------|
| `sketch_extrude` | 板、凸台 | constrainedSketch → extrude → fillet |
| `sketch_extrude_shell` | 外壳 | extrude → subtract 内腔 → fillet |
| `loft` | 流线外形 | 多截面 loft |
| `sweep` | 管路 | sweep |
| `revolve` | 回转件 | revolve |
| `union_bracket` | 支架 | union(box…) → fillet |
| `primitive_shell` | 简易圆筒壳 | cylinder subtract |
| `primitive_layout` | 占位 / 布局 | box/cylinder 布尔 |

## 模板（快捷起点）

| template_id | 说明 |
|-------------|------|
| sketch-enclosure | 草图空心壳 |
| sketch-bracket | L 支架 |
| loft-hull | 放样流线 |
| hello-assembly | 演示多部件 |

## Author 规范

- 单位 mm；`param("Label", default, { min, max, unit: "mm" })`
- 多部件：`return [{ name: "PartId", shape: ... }, ...]`
- 复杂件：`src/part.forge.js` + `importAssembly`
- 外壳 name 含 Shell/外壳 → Web 半透明

## 渲染后反馈

- `spatial_digest.capability.strengths` — 已用特征
- `validation_warnings` 中 `建模建议：` / `装配校验：` — 可选改进，不阻塞交付
