# Notion3D 文档

## 入门

| 文档 | 说明 |
|------|------|
| [../README.md](../README.md) | 项目概览与快速开始 |
| [dev-modes.md](dev-modes.md) | 本地运行（`make dev AGENT=...`） |
| [agents/README.md](agents/README.md) | **连接 Agent**（按环境选路径） |

## Agent 接入

| 文档 | 说明 |
|------|------|
| [agents/README.md](agents/README.md) | 总览：cursor_sdk / hermes / OpenClaw / engine |
| [agents/hermes.md](agents/hermes.md) | Hermes + Web 设计助手 |
| [agents/openclaw.md](agents/openclaw.md) | OpenClaw + notion3d-mcp |
| [integrations/README.md](integrations/README.md) | Cursor IDE / Claude Code MCP |
| [../AGENTS.md](../AGENTS.md) | MCP 工具、Skills、工作流速查 |

## 架构与流水线

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | 三层边界、Design Turn、Engine API |
| [design-pipeline.md](design-pipeline.md) | intake → plan → author → render → review |
| [cad-backend-v2.md](cad-backend-v2.md) | ForgeCAD 安装、STL 渲染、Forge 实时预览 |

Skills 正文：`.cursor/skills/*/SKILL.md`
