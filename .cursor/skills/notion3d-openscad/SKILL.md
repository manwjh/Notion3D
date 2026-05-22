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
      或 notion3d_list_templates → apply / 改参后 render
      或简单几何 → notion3d_template（Engine 规则模板，无 LLM，dev only）
- [ ] 4. notion3d_wait_job 或轮询 notion3d_get_job（等待 STL）
- [ ] 5. notion3d_list_versions — 确认 version / stl_url
- [ ] 6. （可选）本地 validate.sh 复核 SCAD（复杂件推荐）
```

**API Key 由 Agent 平台管理**（Cursor / Claude Code / OpenClaw），不在 Web 或 Notion3D API 配置。

**异步规则**：`notion3d_render_scad` / `notion3d_template` 立即返回 job；STL 可能需 1–3 分钟。用 `notion3d_wait_job` 或轮询，不要同步死等。

**断点续作**：刷新或 API 重启后 `notion3d_list_active_jobs`；仅有预览时 `notion3d_resume_stl`。

## Agent ↔ Web 衔接（必须做）

建模成功后，**把 `web_url` 给用户**（MCP 响应与 API 均包含，形如 `http://localhost:5173/p/{project_id}`）。

```
Agent 完成 notion3d_wait_job
  → 回复：「模型已生成，请在浏览器打开：{web_url}」
用户打开链接
  → Web 加载该项目：3D 预览、参数滑块、导出 STL
```

Web 与 Agent **不直连**，共享同一 API / `data/projects/`。用户也可在 Web 顶栏「复制工作台链接」分享。

接入配置见 [docs/integrations/README.md](../../docs/integrations/README.md)。

## Web 工作台（Vue 3）

Web 是 **Agent 驱动的观察面**，不是第二个 Agent：

1. **对话区**：采集意图（含 3D 点选），创建 Design Turn，转发 Agent
2. **预览区**：随 Job 更新显示 STL；旋转、点选、导出
3. **高级编辑**：手动 SCAD（`source=manual`），明确标注不经过助手

Agent 经 MCP 提交的 Job 自动绑定 `active_turn`；版本与对话通过 `turn_id` / `job_id` 关联。

## 写 OpenSCAD 规范

- **单位**：毫米；可调参数放在文件顶部
- **壁厚**：`wall >= 1.2`（FDM 推荐 1.6+）
- **流形**：boolean 后避免零厚度；`difference()` 被减体略延伸
- **禁止**：`import`/`include` 外部文件、绝对路径
- **尺寸**：默认整件适合 20–120mm 打印床；复杂件控制 `$fn`（预览 24–32，最终 48–64）
- **输出**：仅 OpenSCAD 源码（可用 ` ```openscad ` 包裹）

## 模板库

内置 SCAD 模板在仓库 `templates/builtin/`；用户另存在 `data/templates/user/`。

| MCP Tool | 说明 |
|----------|------|
| `notion3d_list_templates` | 浏览（tag / category / scope） |
| `notion3d_get_template` | 取 SCAD + meta |
| `notion3d_apply_template` | 应用到项目（可新建） |
| `notion3d_save_template` | 从 version 另存到用户库 |

复杂定制：`get_template` → 改 SCAD → `render_scad`，不要往 Engine 代码里写领域特例。

## 机械件（齿轮等）

- **不要**用简单梯形 polygon 近似齿形（易产生非封闭网格）
- **齿轮副/啮合**：渐开线齿廓 + 按中心距装配；齿数比 = 转速比
- 完整范例见 [examples.md](examples.md)「10:1 啮合齿轮副」
- API `render_stl` 会拒绝 stderr 含 `ERROR:` / `mesh is not closed` 的 SCAD

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
| 规则模板 | `apps/api/app/services/cad_service.py` | `notion3d_template` |
| 架构 | `docs/architecture.md` | Engine / MCP / Adapter |

本地调试：

```bash
make install
make api
make web
# Agent：配置 MCP，见 docs/integrations/
```

## 回复用户话术

**A 类成功**：说明版本、关键尺寸，并给出 **web_url** 让用户打开工作台预览/导出。

**B 类成功**：注明「OpenSCAD 简化造型，适合小尺寸装饰件」，并给出 **web_url**。

**C 类拒绝**：解释原因 + A/B 替代描述。

**失败**：贴 OpenSCAD stderr 或 job message，不要只说「建模失败」。

## 附加资源

- [reference.md](reference.md) — FDM 约束、API、环境变量
- [examples.md](examples.md) — Prompt 示例
- [docs/integrations/](../../docs/integrations/) — Cursor / Claude Code / OpenClaw MCP 配置
