---
name: notion3d-mcp
description: Notion3D MCP render-first loop and optional archives.
---

# Notion3D MCP

真源：`apps/mcp-server/notion3d_mcp/server.py` · [docs/forge-modeling-guide.md](../../docs/forge-modeling-guide.md)

## 主路径 Tools

| Tool | 用途 |
|------|------|
| `notion3d_health` | API + `forgecad_available` |
| `notion3d_render_forge` | 提交 `.forge.js` → STL + parts |
| `notion3d_wait_job` | 完成；含 `spatial_digest`、advisory warnings |
| `notion3d_get_forge_sources` | 读主脚本 + `src/` 改稿 |
| `notion3d_apply_template` | 可选起点：sketch-enclosure / sketch-bracket / loft-hull |

## 可选归档

| Tool | 用途 |
|------|------|
| `notion3d_report_design_plan` | 记录 summary / assembly_spec / geometry_recipes |
| `notion3d_report_design_review` | 显式验收（Engine 也会 auto-complete） |

## 辅助 Tools

`notion3d_list_projects` · `notion3d_create_project` · `notion3d_get_job` · `notion3d_list_active_jobs` · `notion3d_list_versions` · `notion3d_list_templates` · `notion3d_get_template` · `notion3d_save_template` · `notion3d_list_messages` · `notion3d_get_design_state` · `notion3d_get_project_state` · `notion3d_wait_agent`

## 主循环

```
health → render_forge → wait_job → (get_forge_sources → render_forge)*
```

warnings 为可选改进；满意后用自然语言回复用户，不必强制 report_design_review。
