"""Format edit context (semantic region or 3D pick) for LLM prompts."""


def format_region_prompt(content: str, region: str | None) -> str:
    if not region or not region.strip():
        return content
    return (
        f"{content}\n\n"
        "[用户指定的修改部位]\n"
        f"- 部位：{region.strip()}\n"
        "请只修改该部位相关的 OpenSCAD 参数或几何，不要改动其他部分。"
    )


def format_pick_prompt(content: str, pick: dict | None) -> str:
    if not pick:
        return content

    label = pick.get("label") or ""
    x = pick.get("x", 0)
    y = pick.get("y", 0)
    z = pick.get("z", 0)
    nx = pick.get("nx", 0)
    ny = pick.get("ny", 1)
    nz = pick.get("nz", 0)

    return (
        f"{content}\n\n"
        "[用户选中的模型位置（高级 3D 点选）]\n"
        f"- 区域：{label}\n"
        f"- 坐标（模型居中坐标系，mm，Y 轴向上）：x={x:.2f}, y={y:.2f}, z={z:.2f}\n"
        f"- 表面法向：nx={nx:.3f}, ny={ny:.3f}, nz={nz:.3f}\n"
        "请针对该位置附近的几何进行修改；若 OpenSCAD 有对应 module/参数，优先调整相关部分。"
    )


def format_edit_prompt(
    content: str,
    pick: dict | None = None,
    region: str | None = None,
) -> str:
    if pick:
        return format_pick_prompt(content, pick)
    return format_region_prompt(content, region)
