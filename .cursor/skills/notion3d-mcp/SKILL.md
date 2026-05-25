# Notion3D MCP

## Tools

| Tool | 用途 |
|------|------|
| `notion3d_health` | API + `forgecad_available` |
| `notion3d_list_versions` | 版本列表（含 src_files） |
| `notion3d_get_forge_sources` | 读取主脚本 + `src/` 子文件 |
| `notion3d_list_templates` | 演示模板（非主路径） |
| `notion3d_apply_template` | 应用 demo 模板 |
| `notion3d_render_forge` | 提交 `.forge.js` → STL + parts |
| `notion3d_wait_job` | 等待渲染完成 |
| `notion3d_report_design_plan` | plan 阶段 |
| `notion3d_report_design_review` | review 阶段 |

## 异步流程

```
render_forge → job_id → wait_job → version.stl_url + parts_url
```
