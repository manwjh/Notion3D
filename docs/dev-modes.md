# 本地开发模式

端口、`WEB_TURN` 与进程对照。

| 文档 | 说明 |
|------|------|
| [usage-network.md](usage-network.md) | **本机 Local / 局域网 LAN** — 谁在哪访问、URL 怎么配 |
| [README § 建议部署](../README.md#建议部署) | MCP / bridge / gateway / 手动 |
| [dependencies.md](dependencies.md) | 依赖与 env |

```bash
make install                # 首次
make dev                    # Engine + Web（默认）
make dev WEB_TURN=bridge    # + agent-bridge :8787
make dev WEB_TURN=gateway   # + gateway sidecar :8642
```

接口详解：[agents/README.md](agents/README.md)

## Engine 部署约束（Local / LAN）

Notion3D Engine 面向**单实例、本机或局域网**工作台。当前版本 intentionally 不包含：

| 能力 | 状态 | 说明 |
|------|------|------|
| 多 worker / 水平扩展 | 不支持 | Job 内存缓存 + JSON 文件；勿 `uvicorn --workers N` |
| 数据库 / 消息队列 | 无 | 数据在 `NOTION3D_DATA_DIR`（默认 `data/`） |
| API 鉴权 | 无 | 默认同网段可读写；公网暴露需前置反向代理 + 鉴权 |

**适合**：个人开发、小团队内网预览、MCP Agent 建模 + Web 工作台。

JSON 写入使用原子替换（`*.tmp` → rename），降低异常中断时的文件损坏风险；仍非多进程安全，请勿水平扩展 API。

## 本机 vs 局域网（速查）

| | **本机 Local** | **局域网 LAN** |
|--|----------------|----------------|
| **谁** | 你与 `make dev` 同一台电脑 | 同事 / 手机等同网段设备 |
| **Web 入口** | http://localhost:5173 | http://\<主机 IP\>:5173 |
| **`.env`** | 默认 | `NOTION3D_WEB_BASE=http://<IP>:5173` + CORS |
| **MCP 在本机** | `127.0.0.1:8000` | 同左 |
| **MCP 在异机** | — | MCP env 用主机 IP（:8000 / :5173） |

`make dev` banner 会打印局域网地址。详见 [usage-network.md](usage-network.md)。

## 进程与端口

| `WEB_TURN` | 进程 | 端口 | 监听 |
|------------|------|------|------|
| `off` | API + Web | 8000 / 5173 | API `0.0.0.0` · Web `0.0.0.0`（Vite） |
| `bridge` | + agent-bridge | 8787 | 127.0.0.1（sidecar 本机） |
| `gateway` | + gateway sidecar | 8642 | 默认 127.0.0.1 |
| （Forge 实时） | ForgeCAD Studio | 5174 | 127.0.0.1 |

## 自检

```bash
WEB_TURN=off bash scripts/check-dev-stack.sh
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

## 兼容旧参数

`make dev AGENT=engine|cursor_sdk|hermes` 映射为 `WEB_TURN=off|bridge|gateway`（将废弃）。
