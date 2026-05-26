# Web Turn · bridge

**接口 2** 的一种 sidecar：`bridge` → agent-bridge `:8787` → `@cursor/sdk` Agent → notion3d-mcp → Engine。

← [Agent 接入总览](README.md) · 完整依赖表：[dependencies.md](../dependencies.md)

## Sidecar 依赖

| 组件 | 来源 | 说明 |
|------|------|------|
| **agent-bridge** | 仓库 `apps/agent-bridge` | `make install`；HTTP `:8787` |
| **@cursor/sdk** | agent-bridge `package.json` | 调 Cursor 云端 Agent 运行时 |
| **notion3d-mcp** | 仓库 `apps/mcp-server` | bridge 进程内 spawn；**必须** `pip install -e apps/mcp-server` |
| **LLM** | Cursor 云端 | `.env` 中 `CURSOR_API_KEY`；**不在 Notion3D Engine 内** |

`make dev WEB_TURN=bridge` 会预检 `CURSOR_API_KEY` 与 `import notion3d_mcp`。

## 部署

```env
NOTION3D_WEB_TURN=bridge
CURSOR_API_KEY=crsr_...
NOTION3D_WEB_TURN_BRIDGE_BASE=http://127.0.0.1:8787
```

```bash
make install
make dev WEB_TURN=bridge
# 或单独：make bridge（需 Engine + Web 已运行）
```

## 验证

```bash
curl -s http://127.0.0.1:8787/health
# api_ready: true · runtime: bridge
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
# web_turn: bridge · web_chat_mode: agent（sidecar 就绪时）
```

Web 右侧「对话」可发送自然语言；UI 不暴露 bridge 细节。

## MCP 辅助工具（Web Turn）

浏览器经 `POST /turn` 发起建模时，Engine 内 `agent.active=true`，直到 bridge/gateway 侧 Agent 跑完。若你在**同一 Engine** 上另开 MCP 会话（监控脚本、第二 Agent、自动化测试），可用：

| Tool | 用途 |
|------|------|
| `notion3d_get_project_state` | 一次拉取 messages、active_turn、active_job、agent 状态 |
| `notion3d_wait_agent` | 阻塞直到 `agent.active` 为 false（内部走 `GET .../state/events` SSE，失败则轮询） |

与建模主路径的 `notion3d_wait_job` 不同：`wait_job` 等 **Forge 渲染 Job**；`wait_agent` 等 **Web Turn Agent 回合**（sidecar 调 LLM + MCP 建模的那一段）。

### 集成示例（OpenClaw / 任意 MCP 宿主）

用户已在 Web 右侧发送「做一个 40mm 立方体」后，宿主内辅助 Agent 等待并检查结果：

```
notion3d_get_project_state(project_id="<uuid>")
# agent.active == true → 继续等

notion3d_wait_agent(project_id="<uuid>", max_wait_seconds=600)
# 返回最新 state；agent.active == false 后可读 messages / 调 wait_job
```

等价 REST（无 MCP 时）：

```bash
# 单次快照
curl -s http://127.0.0.1:8000/api/projects/<uuid>/state | python3 -m json.tool

# SSE（直到 agent 结束）
curl -N http://127.0.0.1:8000/api/projects/<uuid>/state/events
```

典型顺序：**Web 用户发消息** → 外部 `notion3d_wait_agent` → 若 `active_job_id` 出现则 `notion3d_wait_job` → Web 刷新预览。

## 数据流

```
Web POST /turn → Engine → bridge :8787 → Cursor Agent + notion3d-mcp → Engine → Web 预览
```

## 故障排查

| 现象 | 检查 |
|------|------|
| `dev.sh` 报未安装 MCP | `cd apps/mcp-server && pip install -e .` |
| `api_ready: false` | `CURSOR_API_KEY` 有效；`curl bridge/health` |
| `web_chat_mode: setup_required` | bridge 进程是否运行；`NOTION3D_WEB_TURN_BRIDGE_BASE` |
