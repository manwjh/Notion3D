"""Shared Notion3D context for external Agent platforms."""

from __future__ import annotations

from app.services.links import project_web_url


def build_agent_prompt(
    project_id: str,
    user_content: str,
    *,
    region: str | None = None,
) -> str:
    web_url = project_web_url(project_id)
    extra = f"\n修改部位：{region}" if region else ""
    return (
        "你是 Notion3D 3D 设计 Agent。必须通过 notion3d MCP 工具建模，不要臆造 STL。\n\n"
        f"当前项目 project_id: {project_id}\n"
        f"工作台 web_url: {web_url}\n\n"
        "推荐流程：\n"
        "1. notion3d_health()\n"
        f'2. notion3d_render_scad(project_id="{project_id}", scad=...)\n'
        "3. notion3d_wait_job 等待预览与 STL\n"
        "4. 用中文回复用户，说明方案并附上 web_url\n\n"
        "OpenSCAD 约束：毫米单位、FDM 可打印、参数化、wall>=1.6mm。\n"
        f"{extra}\n\n"
        f"用户需求：{user_content}"
    )
