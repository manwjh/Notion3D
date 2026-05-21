"""Prompt task classification and LLM prompts for OpenSCAD modeling."""

from __future__ import annotations

from typing import Literal

TaskKind = Literal["geometry", "symbolic", "unsupported"]

GEOMETRY = (
    "立方体", "立方", "盒子", "球", "sphere", "圆柱", "cylinder", "孔", "hole",
    "mm", "毫米", "尺寸", "边长", "直径", "支架", "外壳", "盖子", "底座", "cube", "box",
)

SYMBOLIC = (
    "铁塔", "塔", "房子", "建筑", "logo", "图标", "轮廓", "剪影", "简化", "造型",
    "eiffel", "tower", "house",
)

UNSUPPORTED = (
    "卡通", "兔子", "猫", "狗", "动物", "人脸", "角色", "画一", "帮我画", "像照片",
    "有机", "曲面", "雕塑", "独眼", "cartoon", "rabbit", "character",
)

TASK_RULES: dict[TaskKind, dict[str, str]] = {
    "geometry": {
        "label": "A 几何/参数化",
        "instruction": (
            "生成参数化几何体，尺寸明确，优先 cube/sphere/cylinder/difference/linear_extrude。"
        ),
        "success_note": "可在左侧预览；可在 OpenSCAD 面板编辑代码并渲染新版本。",
    },
    "symbolic": {
        "label": "B 符号/地标近似",
        "instruction": (
            "用简化 lattice、hull、linear_extrude 拼轮廓，不追求精细还原；控制面数；适合小尺寸装饰件。"
        ),
        "success_note": "OpenSCAD 简化造型；可在代码面板继续修改。",
    },
    "unsupported": {
        "label": "C 不适合 OpenSCAD",
        "instruction": (
            "不要模拟有机/卡通 mesh。改为 2D 剪影 linear_extrude 或简单几何组合，注释说明为简化替代。"
        ),
        "success_note": "已用简化几何替代；OpenSCAD 不适合卡通/有机造型，详见对话建议。",
    },
}


def classify_prompt(prompt: str) -> TaskKind:
    p = prompt.lower()
    if any(k.lower() in p for k in UNSUPPORTED):
        return "unsupported"
    if any(k.lower() in p for k in SYMBOLIC):
        return "symbolic"
    if any(k.lower() in p for k in GEOMETRY):
        return "geometry"
    if len(prompt) < 24 and any("\u4e00" <= c <= "\u9fff" for c in prompt):
        return "symbolic"
    return "geometry"


def success_message(prompt: str, version: int) -> str:
    kind = classify_prompt(prompt)
    note = TASK_RULES[kind]["success_note"]
    return f"建模完成：版本 v{version}。{note}"


def llm_system_prompt(prompt: str) -> str:
    kind = classify_prompt(prompt)
    rules = TASK_RULES[kind]
    return (
        "你是 Notion3D 项目的 OpenSCAD 专家。只输出可执行的 OpenSCAD 源码"
        "（可用 ```openscad 代码块包裹），不要解释文字。\n\n"
        f"任务类型：{rules['label']}\n"
        f"{rules['instruction']}\n\n"
        "通用 FDM 约束：\n"
        "- 单位毫米；可调参数放在文件顶部\n"
        "- wall >= 1.6；流形、可打印、避免大角度悬空\n"
        "- 禁止 import/include 外部文件\n"
        "- 默认整件适合 120mm 以内打印床\n"
        "- 注释行标明模型名与 FDM-friendly"
    )


def llm_user_prompt(prompt: str, existing_scad: str | None = None) -> str:
    user = f"用户需求：{prompt}"
    if existing_scad and existing_scad.strip():
        user += (
            f"\n\n当前 OpenSCAD 代码：\n```openscad\n{existing_scad.strip()}\n```\n"
            "请在此基础上修改并输出完整代码。"
        )
    return user
