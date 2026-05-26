# 本地开发模式

端口、`WEB_TURN` 与进程对照。**部署方案**（MCP / bridge / gateway / 手动）见 [README.md § 建议部署](../README.md#建议部署)。

```bash
make dev                    # Engine + Web（默认，MCP 路径）
make dev WEB_TURN=bridge    # + agent-bridge :8787
make dev WEB_TURN=gateway   # + gateway sidecar :8642
```

接口详解：[agents/README.md](agents/README.md)

## 进程与端口

| `WEB_TURN` | 进程 | 端口 |
|------------|------|------|
| `off` | API + Web | 8000 / 5173 |
| `bridge` | + agent-bridge | 8787 |
| `gateway` | + gateway sidecar | 8642 |
| （Forge 实时） | ForgeCAD Studio | 5174 |

## 自检

```bash
WEB_TURN=off bash scripts/check-dev-stack.sh
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

## 局域网

`make dev` banner 打印 `http://<本机 IP>:5173`。分享链接时 `.env` 设置 `NOTION3D_WEB_BASE`；MCP env 中 `NOTION3D_WEB_BASE` 须一致。

## 兼容旧参数

`make dev AGENT=engine|cursor_sdk|hermes` 映射为 `WEB_TURN=off|bridge|gateway`（将废弃）。
