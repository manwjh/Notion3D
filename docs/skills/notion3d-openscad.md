---
name: notion3d-openscad
description: >-
  Notion3D OpenSCAD modeling workflow: classify prompts, generate FDM-printable
  parametric SCAD, validate syntax, render previews, export STL, and integrate
  via Notion3D MCP Server + API. Use for Notion3D repo work, SCAD/STL tasks,
  Cursor/Claude Code/OpenClaw agent integration, or 3D printing prep.
---

# Notion3D OpenSCAD 建模

Notion3D 流水线：**文本 → OpenSCAD → 预览图 → 3D 网格 → 导出**。

**Agent 集成方式**：MCP Server（`apps/mcp-server`）+ 本 Skill。不要直接臆造 STL，通过 MCP 调 API。

## 何时启用

- 用户在 Notion3D Web 里描述模型，或在仓库里改建模逻辑
- 需要写/改 `model.scad`、调试 `cad_service.py` / MCP tools
- 在 Cursor / Claude Code / OpenClaw 中通过 MCP 操作 Notion3D
- 用户要「生成可打印模型」而非 mesh 艺术图

## 任务分类（先做）

| 类型 | 示例 | 策略 |
|------|------|------|
| **A 几何/参数化** | 立方体、盒子、支架、带孔件、指定 mm 尺寸 | 全力 OpenSCAD，优先参数化 |
| **B 符号/地标近似** | 埃菲尔铁塔、简单 logo、几何化图标 | 简化 lattice/轮廓，告知「装饰件级别」 |
| **C 不适合 OpenSCAD** | 卡通动物、人脸、曲面雕塑、「帮我画」 | **不要硬写**；说明局限，建议 A/B 类改写 |

分类为 C 时，给出可执行的 A/B 类替代 prompt。

## Agent 工作流（MCP）

```
Task Progress:
- [ ] 1. notion3d_health — 确认 API + OpenSCAD 就绪
- [ ] 2. notion3d_create_project（或选用已有 project_id）
- [ ] 3. 你生成 OpenSCAD → notion3d_render_scad（首选）
      或简单几何 → notion3d_chat（仅规则模板，无 LLM）
- [ ] 4. notion3d_wait_job 或轮询 notion3d_get_job（预览→STL 两阶段）
- [ ] 5. notion3d_list_versions — 确认 version / preview_url / stl_url
- [ ] 6. （可选）本地 validate.sh / multi-preview.sh 复核 SCAD
```

**API Key 由 Agent 平台管理**（Cursor / Claude Code / OpenClaw），不在 Web 或 Notion3D API 配置。

**异步规则**：`notion3d_render_scad` / `notion3d_chat` 立即返回 job；STL 可能需 1–3 分钟。用 `notion3d_wait_job` 或轮询，不要同步死等。

**断点续作**：刷新或 API 重启后 `notion3d_list_active_jobs`；仅有预览时 `notion3d_resume_stl`。

## Agent ↔ Web 衔接（必须做）

建模成功后，**把 `web_url` 给用户**（形如 `http://localhost:5173/p/{project_id}`）。

接入配置见 [docs/integrations/README.md](../integrations/README.md)。

## Web 工作台（Vue 3）

Web 是 **可视化工作台**，不是第二个 Agent：

1. **Agent 建模**：MCP 中 `notion3d_render_scad` 或 `notion3d_chat`
2. **打开 web_url**：用户预览、导出 STL
3. **快速调整**：规则模板 + 参数滑块 + 语义部位
4. **高级**：3D 点选、OpenSCAD 源码

## 写 OpenSCAD 规范

- **单位**：毫米；可调参数放在文件顶部
- **壁厚**：`wall >= 1.2`（FDM 推荐 1.6+）
- **流形**：boolean 后避免零厚度；`difference()` 被减体略延伸
- **禁止**：`import`/`include` 外部文件、绝对路径
- **尺寸**：默认整件适合 20–120mm 打印床；复杂件控制 `$fn`（预览 24–32，最终 48–64）
- **输出**：仅 OpenSCAD 源码（可用 ` ```openscad ` 包裹）

## 本地校验脚本

```bash
.cursor/skills/notion3d-openscad/scripts/validate.sh path/to/model.scad
.cursor/skills/notion3d-openscad/scripts/multi-preview.sh path/to/model.scad /tmp/previews/
.cursor/skills/notion3d-openscad/scripts/export-stl.sh model.scad model.stl
```

**必须用 Read 工具查看 PNG**，确认比例/方向/薄壁。

## 系统组件

| 组件 | 路径 | 说明 |
|------|------|------|
| Web | `apps/web` | Vue 3 + Vite，http://localhost:5173 |
| API | `apps/api` | http://localhost:8000/docs |
| MCP Server | `apps/mcp-server` | Agent 统一工具层 |
| Skill 主文档 | `docs/skills/notion3d-openscad.md` | 跨平台共享 |
| 产物 | `data/projects/{id}/versions/{n}/` | scad / preview.png / stl |
| 规则模板 | `apps/api/app/services/cad_service.py` | Web chat 简单几何 |
| 任务分类 | `apps/api/app/services/task_class.py` | A/B/C 分类（Agent 侧使用）

本地调试：

```bash
make install
make api
make web
# Agent：配置 MCP，见 docs/integrations/
```

## 回复用户话术

**A 类成功**：说明版本、关键尺寸、预览/导出路径。

**B 类成功**：注明「OpenSCAD 简化造型，适合小尺寸装饰件」。

**C 类拒绝**：解释原因 + A/B 替代描述。

**失败**：贴 OpenSCAD stderr 或 job message，不要只说「建模失败」。

## 附加资源

- [reference.md](reference.md) — FDM 约束、API、环境变量
- [examples.md](examples.md) — Prompt 示例
- [docs/integrations/](../../docs/integrations/) — Cursor / Claude Code / OpenClaw MCP 配置
