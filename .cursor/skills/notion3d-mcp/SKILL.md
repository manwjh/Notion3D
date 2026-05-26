# Notion3D MCP

真源：`apps/mcp-server/notion3d_mcp/server.py`。完整 Engine 映射见 [docs/architecture.md](../../../docs/architecture.md#mcp-tools)。

## 主路径 Tools

| Tool | 用途 |
|------|------|
| `notion3d_health` | API + `forgecad_available` |
| `notion3d_report_design_plan` | plan 阶段（`task_class` A/B/C，`strategy`） |
| `notion3d_render_forge` | 提交 `.forge.js` → STL + parts；可选 `files_json` 多文件 |
| `notion3d_wait_job` | 等待渲染完成 |
| `notion3d_report_design_review` | review 阶段（`pass` / `retry` / `accept_warnings`） |
| `notion3d_get_forge_sources` | 读取主脚本 + `src/` 子文件（改稿前） |
| `notion3d_apply_template` | 应用 demo 模板（`hello-assembly` / `open-enclosure`） |

## 辅助 Tools

| Tool | 用途 |
|------|------|
| `notion3d_list_projects` | 项目列表 |
| `notion3d_create_project` | 创建项目（返回 `web_url`） |
| `notion3d_get_job` | 单次 Job 状态 |
| `notion3d_list_active_jobs` | 进行中 Job |
| `notion3d_list_versions` | 版本列表（含 `src_files`） |
| `notion3d_list_templates` | 模板浏览（非主路径） |
| `notion3d_get_template` | 模板详情 + `forge_code` |
| `notion3d_save_template` | 版本另存为用户模板 |
| `notion3d_list_messages` | 对话历史 |
| `notion3d_get_design_state` | 当前 turn phase / plan / review |
| `notion3d_get_project_state` | 统一快照（messages / turn / job / agent） |
| `notion3d_wait_agent` | 等待 Web Turn Agent 结束（`agent.active` → false） |

## 异步流程

```
render_forge → job_id → wait_job → version.stl_url + parts_url
```

## 典型工作流

```
health → report_design_plan → render_forge → wait_job → report_design_review
```

改稿：`get_forge_sources(version)` → 修改 → `render_forge`
