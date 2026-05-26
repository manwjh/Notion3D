# 使用方式与网络

说明：**谁在哪台设备上用什么地址**访问 Notion3D。与 [dependencies.md](dependencies.md)（装什么）和 [README § 建议部署](../README.md#建议部署)（选哪条建模路径）互补。

## 场景一览

| 场景 | 谁在用 | 浏览器 / Agent 怎么连 | 默认能否用 |
|------|--------|------------------------|------------|
| **本机 Local** | 开发者本人，浏览器与 `make dev` 在同一台电脑 | `http://localhost:5173` | ✅ 开箱即用 |
| **局域网 · 只看 Web** | 同事 / 手机 / 平板，与主机同一 Wi‑Fi 或内网 | `http://<主机 IP>:5173` | ⚙️ 需改 `NOTION3D_WEB_BASE` |
| **局域网 · MCP 异机** | Agent 宿主在**另一台**内网机器 | 宿主 MCP → `http://<主机 IP>:8000` | ⚙️ 需改 MCP env |
| **公网暴露** | 互联网任意访问 | — | ❌ **未支持**；dev 栈仅 local / 内网 |

> `make dev` 启动后 banner 会打印本机地址与 **局域网地址**（若检测到 IP）。

## 本机使用（Local）

**适合**：自己开发、自己预览、Agent 与 Notion3D 都在同一台 Mac / PC。

```
┌─────────────────────────────────────┐
│  你的电脑（make dev 在这台）           │
│  浏览器 → localhost:5173             │
│  Agent 宿主（可选）→ 127.0.0.1:8000  │
└─────────────────────────────────────┘
```

```bash
make install
cp .env.example .env    # 默认即可
make dev
```

| 入口 | 地址 |
|------|------|
| **Web 工作台**（你点这个） | http://localhost:5173 |
| Engine API（一般不用手开） | http://127.0.0.1:8000 |
| 项目链接 / MCP 返回的预览 URL | `NOTION3D_WEB_BASE` → 默认 `http://localhost:5173/p/<id>` |

MCP env（Agent 也在本机时）：

```json
{
  "NOTION3D_API_BASE": "http://127.0.0.1:8000",
  "NOTION3D_WEB_BASE": "http://localhost:5173"
}
```

## 局域网 / 内网（LAN）

**适合**：Notion3D 跑在一台工作站上，**其他人用浏览器看模型**；或 Agent 在另一台内网机器上连 Engine。

```
        ┌── 同事手机 / 笔记本
        │   浏览器 → http://192.168.x.x:5173
        ▼
┌───────────────────────────────┐
│  Notion3D 主机（make dev）      │
│  Web :5173  ·  API :8000      │
└───────────────────────────────┘
        ▲
        │ MCP（可选，Agent 在别台电脑）
   另一台内网 PC
```

### 步骤 1 — 查主机 IP

`make dev` 后看终端 banner，例如：

```
  Web     http://localhost:5173
          http://192.168.1.42:5173  （局域网）
```

或手动：`ipconfig getifaddr en0`（macOS）/ `hostname -I`（Linux）。

### 步骤 2 — 改 `.env`（在 Notion3D 主机上）

```env
# 分享链接、MCP 返回的预览 URL 必须用「别人能打开的地址」
NOTION3D_WEB_BASE=http://192.168.1.42:5173

# 若浏览器从局域网 IP 访问且遇 CORS，追加该 origin
NOTION3D_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.42:5173
```

改完后 **重启** `make dev`。

### 步骤 3 — 其他人打开 Web

同事在同一内网浏览器访问：

```
http://192.168.1.42:5173/p/<project_id>
```

Web 开发模式下 Vite 已 `host: true`，API 经本机代理到 Engine，**同事无需直连 :8000**。

### 步骤 4 — MCP（仅当 Agent 在另一台内网机器）

Agent 宿主 MCP env 不能用 `127.0.0.1`（那是 Agent 自己），应指向 **Notion3D 主机 IP**：

```json
{
  "NOTION3D_API_BASE": "http://192.168.1.42:8000",
  "NOTION3D_WEB_BASE": "http://192.168.1.42:5173"
}
```

`NOTION3D_WEB_BASE` 必须与步骤 2 **一致**，否则 Agent 给的预览链接同事打不开。

### 局域网自检

```bash
# 在 Notion3D 主机
curl -s http://127.0.0.1:8000/health

# 在同事电脑（替换 IP）
curl -s http://192.168.1.42:5173/health
open http://192.168.1.42:5173
```

## 变量对照（Local vs LAN）

| 变量 | 本机 Local | 局域网 LAN |
|------|------------|------------|
| `NOTION3D_WEB_BASE` | `http://localhost:5173` | `http://<主机 IP>:5173` |
| MCP `NOTION3D_API_BASE`（Agent 在本机） | `http://127.0.0.1:8000` | — |
| MCP `NOTION3D_API_BASE`（Agent 在异机） | — | `http://<主机 IP>:8000` |
| `NOTION3D_CORS_ORIGINS` | 默认即可 | 加上局域网 Web origin |
| 防火墙 | 通常无感 | 主机需放行 **5173**（Web）；异机 MCP 还需 **8000** |

Engine 监听 `0.0.0.0:8000`，Web dev server 监听 `0.0.0.0:5173`（Vite `host: true`），内网可达性由上述 env 与防火墙决定。

## 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| 同事打不开你发的 `/p/...` 链接 | 链接里是 `localhost` | 改 `NOTION3D_WEB_BASE` 为主机 IP 并重启 |
| Agent 建模成功但链接打不开 | MCP env 的 `WEB_BASE` 与 `.env` 不一致 | 两处改成同一局域网 URL |
| 手机能开 Web 但 3D 空白 | 少见；查浏览器控制台 / 主机防火墙 | 确认 `:5173` 可达 |
| 想从外网访问 | dev 栈非生产部署 | 需自行反向代理 + 鉴权（不在本文范围） |

## 相关文档

- [dev-modes.md](dev-modes.md) — 端口与 `WEB_TURN`
- [dependencies.md](dependencies.md) — 环境变量索引
- [agents/README.md](agents/README.md) — MCP / Web Turn 路径
