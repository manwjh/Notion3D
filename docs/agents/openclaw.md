# OpenClaw 接入 Notion3D

OpenClaw 经 **notion3d-mcp** 调 Engine 建模。不经 Web 设计助手；用 Web 工作台预览 STL 与 Forge 实时。

← [Agent 接入总览](README.md)

## 前置

1. 本机已安装 [OpenClaw](https://docs.openclaw.ai/)（`openclaw` 在 PATH）
2. OpenClaw 中已配置 LLM provider（Key 在 OpenClaw，不在 Notion3D）
3. `make install`（含 `notion3d-mcp`、`apps/forge-runner`）

## 1. 启动 Engine 与 Web

```bash
make install
make dev AGENT=engine
```

启动 API `:8000` 与 Web `:5173`（无设计助手 sidecar）。

```bash
curl -s http://127.0.0.1:8000/health | grep forgecad_available
# true
```

## 2. 安装 notion3d MCP

```bash
cd apps/mcp-server && pip install -e .
# 确认 notion3d-mcp 在 PATH
which notion3d-mcp
```

## 3. 配置 OpenClaw MCP

将 [config/openclaw-notion3d-mcp.json](../../config/openclaw-notion3d-mcp.json) 合并进 `~/.openclaw/openclaw.json` 的 `mcp.servers`：

```json
{
  "mcp": {
    "servers": {
      "notion3d": {
        "command": "notion3d-mcp",
        "env": {
          "NOTION3D_API_BASE": "http://127.0.0.1:8000",
          "NOTION3D_WEB_BASE": "http://localhost:5173"
        }
      }
    }
  }
}
```

或用 CLI：

```bash
openclaw mcp set notion3d '{"command":"notion3d-mcp","env":{"NOTION3D_API_BASE":"http://127.0.0.1:8000","NOTION3D_WEB_BASE":"http://localhost:5173"}}'
```

重启 OpenClaw gateway。

局域网预览时，将 `NOTION3D_WEB_BASE` 改为 `http://<本机 IP>:5173`（与 Notion3D `.env` 一致）。

## 4. 验证 MCP

在 OpenClaw 中调用 `notion3d_health`，确认 `forgecad_available: true`。

## 5. 建模工作流

标准流水线（详见 [AGENTS.md](../../AGENTS.md)）：

```
notion3d_health()
notion3d_report_design_plan(...)
notion3d_render_forge(forge_code, files_json=...)
notion3d_wait_job(...)
notion3d_report_design_review(...)
```

改稿：`notion3d_get_forge_sources(version)` → 修改 → `render_forge`  
演示：`notion3d_apply_template`（`hello-assembly` / `open-enclosure`）

Forge 编写约定（便于 Web **部件精修**）：

- 每个部件用 `const partId = ...`，`return` 中 `shape: partId`
- 复杂部件拆到 `src/xxx.forge.js` + `importAssembly`

## 6. Web 预览

建模完成后打开项目：

```
http://localhost:5173/p/<project_id>
```

| 视口模式 | 说明 |
|----------|------|
| **装配** | STL 分件预览 + 部件树 |
| **Forge 实时** | ForgeCAD Studio `:5174`，可调 `param()` |

左栏可手动改参数 / 代码 / 点选部件精修（需渲染产物含 `source_ref`）。

## 架构

```
OpenClaw Agent → notion3d-mcp → Engine :8000 → forge-runner → Web :5173 预览
```

## 故障排查

| 现象 | 检查 |
|------|------|
| MCP 工具列表无 notion3d | gateway 是否重启；`openclaw mcp list` |
| `notion3d_health` 失败 | Engine `:8000` 是否运行；`NOTION3D_API_BASE` |
| 渲染失败 | `forgecad_available`；`apps/forge-runner` 是否 `npm install` |
| Web 链接无效 | `NOTION3D_WEB_BASE` 与浏览器访问地址一致 |

## 参考

- [OpenClaw MCP](https://docs.openclaw.ai/cli/mcp)
- [AGENTS.md](../../AGENTS.md) — MCP 工具列表
- [design-pipeline.md](../design-pipeline.md) — 分阶段流水线
