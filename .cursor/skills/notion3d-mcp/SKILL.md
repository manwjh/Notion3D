---
name: notion3d-mcp
description: >-
  Notion3D MCP tool reference and async render workflow: health, templates,
  render_forge, wait_job, versions. Use during author and render phases.
  Engine has no LLM — all modeling goes through these tools.
---

# Notion3D MCP

## 主路径（ForgeCAD）

| Tool | 用途 |
|------|------|
| `notion3d_health` | API + `forgecad_available` |
| `notion3d_list_versions` | 版本列表（含 src_files） |
| `notion3d_get_forge_sources` | **读取主脚本 + src/ 子文件**（多文件改稿） |
| `notion3d_list_templates` | 演示模板（非主路径） |
| `notion3d_apply_template` | 应用 demo 模板 |
| `notion3d_render_forge` | **提交 .forge.js → STL + parts.json**（可选 files_json） |
| `notion3d_wait_job` | 等待渲染完成 |
| `notion3d_report_design_plan` | plan 阶段 |
| `notion3d_report_design_review` | review 阶段 |

## Legacy

| Tool | 用途 |
|------|------|
| `notion3d_render_scad` | 仅 legacy OpenSCAD 模板 |

## 异步流程

```
render_forge → job_id → wait_job → version.stl_url + parts_url
```

## 产物

- `model.forge.js` — 源
- `model.stl` — 合并网格
- `parts.json` — 部件清单（Web 左栏部件树）
