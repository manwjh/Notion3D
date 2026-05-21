# Notion3D OpenSCAD 参考

## FDM 打印约束

| 项 | 建议 |
|----|------|
| 最小壁厚 | 1.2mm（装饰 1.6mm+） |
| 最小特征 | 0.8mm 棱/柱直径 |
| 悬空 | 避免 >45° 大平面悬空；加 chamfer 或拆件 |
| 底面积 | 确保有足够接触面，避免尖底 |
| 孔 | 略小于标称（`hole_d = d - 0.2` 补偿） |
| 文本 | `linear_extrude` + `text()` 高度 ≥ 0.8mm |

## OpenSCAD 安全规则

`cad_service._sanitize_scad` 会拒绝：

- markdown 代码块需正确包裹（LLM 输出会自动剥离）
- `import`/`include` 绝对路径

## 任务分类关键词

**A 类**：立方体、球、圆柱、盒子、孔、mm、尺寸、支架、外壳、盖子

**B 类**：铁塔、房子、logo、图标、简化、造型、轮廓

**C 类**：卡通、兔子、猫、人脸、画、像照片、曲面、有机、独眼、角色

## 坐标系

- OpenSCAD：**Z 轴向上**
- Notion3D Web（Three.js）：Y-up，STL 加载时旋转
- 预览图（`preview.png`）为 OpenSCAD Z-up 视角

## 环境变量

```bash
# apps/api/.env（可选，部署用）
NOTION3D_API_HOST=0.0.0.0
NOTION3D_API_PORT=8000

# apps/mcp-server（Agent 调 API）
NOTION3D_API_BASE=http://127.0.0.1:8000
```

API Key 由 Agent 平台（Cursor / Claude Code / OpenClaw）管理，不在 Notion3D 配置。

## API 快速参考

| 方法 | 路径 |
|------|------|
| GET | `/health` |
| POST | `/api/projects/{id}/chat` |
| GET | `/api/projects/{id}/jobs/{job_id}` |
| GET | `/api/projects/{id}/jobs/active` |
| GET | `/api/projects/{id}/versions` |
| POST | `/api/projects/{id}/render-scad` |
| POST | `/api/projects/{id}/versions/{v}/resume-stl` |

## MCP Tools

见 `apps/mcp-server/notion3d_mcp/server.py` — 所有 tool 以 `notion3d_` 前缀。
