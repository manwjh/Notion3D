"""Generation tracks and tool registry for Notion3D multi-tool platform."""

from __future__ import annotations

from enum import Enum

from app.services import task_class


class GenerationTrack(str, Enum):
    parametric = "parametric"  # OpenSCAD
    mesh = "mesh"  # future: AI mesh APIs
    template = "template"  # form-driven SCAD presets


class ToolId(str, Enum):
    parametric = "parametric"
    symbolic = "symbolic"
    name_sign = "name-sign"
    mesh_character = "mesh-character"
    upload_stl = "upload-stl"


TOOL_META: dict[ToolId, dict] = {
    ToolId.parametric: {
        "track": GenerationTrack.parametric,
        "title": "参数化零件",
        "description": "立方体、盒子、支架等可编辑几何体，OpenSCAD 参数化建模。",
        "available": True,
        "sample_prompts": ["20mm 立方体", "40×30×20mm 带孔盒子", "直径 30mm 圆柱"],
    },
    ToolId.symbolic: {
        "track": GenerationTrack.parametric,
        "title": "装饰/地标",
        "description": "铁塔、房子、logo 等简化轮廓造型，适合小尺寸装饰件。",
        "available": True,
        "sample_prompts": ["简化埃菲尔铁塔，高 100mm", "40×30×25mm 小房子，三角屋顶"],
    },
    ToolId.name_sign: {
        "track": GenerationTrack.template,
        "title": "名牌/字牌",
        "description": "大首字母 + 嵌入式姓名，一键生成打印用字牌。",
        "available": True,
        "sample_prompts": [],
    },
    ToolId.mesh_character: {
        "track": GenerationTrack.mesh,
        "title": "角色/宠物造型",
        "description": "卡通、动物、有机造型（mesh AI，即将接入）。",
        "available": False,
        "sample_prompts": [],
    },
    ToolId.upload_stl: {
        "track": GenerationTrack.mesh,
        "title": "上传模型",
        "description": "导入 STL，切片并发送到拓竹（即将支持）。",
        "available": False,
        "sample_prompts": [],
    },
}


def tool_track(tool: str | ToolId | None) -> GenerationTrack:
    try:
        tid = ToolId(tool or ToolId.parametric.value)
    except ValueError:
        tid = ToolId.parametric
    return TOOL_META[tid]["track"]


def enhance_prompt(prompt: str, tool: str | ToolId | None) -> str:
    try:
        tid = ToolId(tool or ToolId.parametric.value)
    except ValueError:
        tid = ToolId.parametric

    if tid == ToolId.symbolic:
        return f"简化装饰造型（OpenSCAD lattice/轮廓，适合 FDM 小件）：{prompt}"

    if tid == ToolId.name_sign:
        return prompt  # frontend sends full structured prompt

    return prompt


def check_prompt_allowed(prompt: str, tool: str | ToolId | None) -> str | None:
    """Return refusal message if prompt should be blocked; else None."""
    try:
        tid = ToolId(tool or ToolId.parametric.value)
    except ValueError:
        tid = ToolId.parametric

    kind = task_class.classify_prompt(prompt)

    if tid == ToolId.parametric and kind == "unsupported":
        return (
            "这类描述（卡通/角色/有机造型）不适合「参数化零件」工具。\n"
            "你可以：\n"
            "1. 改用「装饰/地标」做简化轮廓\n"
            "2. 改用「名牌/字牌」做文字造型\n"
            "3. 等「角色/宠物造型」工具接入 mesh 生成\n\n"
            "示例：「25mm 立方体」「40×30 带孔盒子」"
        )

    if tid == ToolId.symbolic and kind == "unsupported":
        return (
            "OpenSCAD 无法做精细卡通/有机角色。可尝试：\n"
            "• 「兔子剪影徽章，厚 3mm，宽 40mm」\n"
            "• 或等待「角色/宠物造型」mesh 工具"
        )

    if tid in (ToolId.mesh_character, ToolId.upload_stl):
        return "该工具尚未开放，请关注后续版本。"

    return None


def build_name_sign_prompt(name: str, width_mm: float = 80, depth_mm: float = 30, height_mm: float = 5) -> str:
    safe = name.strip()[:32]
    initial = safe[0].upper() if safe else "A"
    return (
        f"生成 3D 打印名牌：姓名「{safe}」，"
        f"大写首字母「{initial}」立体突出，姓名文字嵌入底座；"
        f"底座约 {width_mm}×{depth_mm}×{height_mm} mm，wall=1.6，FDM 友好，"
        "使用 linear_extrude 与 text()，无外部 import。"
    )


def list_tools() -> list[dict]:
    out = []
    for tid in ToolId:
        meta = TOOL_META[tid]
        out.append(
            {
                "id": tid.value,
                "track": meta["track"].value,
                "title": meta["title"],
                "description": meta["description"],
                "available": meta["available"],
                "sample_prompts": meta["sample_prompts"],
            }
        )
    return out
