"""STL validation helpers — printability heuristics."""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_BED_MM = 220.0
MAX_TRIANGLES_WARN = 2_000_000


@dataclass
class ValidationReport:
    warnings: list[str] = field(default_factory=list)

    def extend(self, other: ValidationReport) -> None:
        self.warnings.extend(other.warnings)


def _bounds_from_binary(data: bytes, triangle_count: int) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    if triangle_count == 0:
        return None
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    offset = 84
    for _ in range(triangle_count):
        if offset + 50 > len(data):
            return None
        # normal (3) + v1 + v2 + v3 = 12 floats
        floats = struct.unpack_from("<12f", data, offset)
        for i in range(3, 12, 3):
            x, y, z = floats[i], floats[i + 1], floats[i + 2]
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            min_z, max_z = min(min_z, z), max(max_z, z)
        offset += 50
    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def _bounds_from_ascii(text: str) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    verts = re.findall(
        r"vertex\s+([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s+"
        r"([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s+"
        r"([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)",
        text,
    )
    if not verts:
        return None
    xs, ys, zs = zip(*((float(x), float(y), float(z)) for x, y, z in verts))
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def parse_stl_bounds(stl_path: Path) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    data = stl_path.read_bytes()
    if len(data) < 84:
        return None

    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + triangle_count * 50
    if triangle_count > 0 and len(data) >= expected_size:
        bounds = _bounds_from_binary(data, triangle_count)
        if bounds is not None:
            return bounds

    try:
        text = data.decode("utf-8", errors="ignore")
    except OSError:
        return None
    if "vertex" in text.lower():
        return _bounds_from_ascii(text)
    return None


def count_stl_triangles(stl_path: Path) -> int:
    data = stl_path.read_bytes()
    if len(data) >= 84:
        triangle_count = struct.unpack_from("<I", data, 80)[0]
        expected_size = 84 + triangle_count * 50
        if triangle_count > 0 and len(data) >= expected_size:
            return triangle_count

    text = data.decode("utf-8", errors="ignore")
    return len(re.findall(r"^\s*facet\s+normal", text, re.MULTILINE | re.IGNORECASE))


def analyze_stl_warnings(
    stl_path: Path,
    *,
    bed_mm: float = DEFAULT_BED_MM,
) -> ValidationReport:
    """Post-render STL heuristics (non-fatal warnings)."""
    report = ValidationReport()
    triangle_count = count_stl_triangles(stl_path)
    if triangle_count == 0:
        report.warnings.append("STL 不含三角面")
        return report
    if triangle_count > MAX_TRIANGLES_WARN:
        report.warnings.append(
            f"三角面数 {triangle_count:,} 过高，渲染/切片可能很慢"
        )

    bounds = parse_stl_bounds(stl_path)
    if bounds is None:
        report.warnings.append("无法解析 STL 边界盒")
        return report

    (min_x, min_y, min_z), (max_x, max_y, max_z) = bounds
    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z

    if max(size_x, size_y) > bed_mm:
        report.warnings.append(
            f"模型 XY  footprint {size_x:.1f}×{size_y:.1f}mm 超过默认打印床 {bed_mm:.0f}mm"
        )
    if size_z > bed_mm:
        report.warnings.append(
            f"模型高度 {size_z:.1f}mm 超过默认打印床边长 {bed_mm:.0f}mm，请确认 Z 轴行程"
        )
    return report


def merge_warnings(*reports: ValidationReport) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for report in reports:
        for warning in report.warnings:
            if warning not in seen:
                seen.add(warning)
                merged.append(warning)
    return merged
