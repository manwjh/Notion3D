"""cad_validation static and STL analysis tests."""

from __future__ import annotations

import struct
from pathlib import Path

from app.services.cad_validation import (
    analyze_scad_warnings,
    analyze_stl_warnings,
    count_stl_triangles,
    parse_stl_bounds,
)


def _write_binary_stl(path: Path, triangles: list[tuple[tuple[float, float, float], ...]]) -> None:
    header = b" " * 80
    body = bytearray()
    for verts in triangles:
        body.extend(struct.pack("<3f", 0.0, 0.0, 1.0))
        for x, y, z in verts:
            body.extend(struct.pack("<3f", x, y, z))
        body.extend(struct.pack("<H", 0))
    path.write_bytes(header + struct.pack("<I", len(triangles)) + body)


def test_analyze_scad_warns_thin_wall():
    scad = "wall = 0.8;\ncube(10);\n"
    warnings = analyze_scad_warnings(scad).warnings
    assert any("0.8" in w and "1.2" in w for w in warnings)


def test_analyze_scad_warns_below_recommended_wall():
    scad = "wall = 1.4;\ncube(10);\n"
    warnings = analyze_scad_warnings(scad).warnings
    assert any("1.4" in w and "1.6" in w for w in warnings)


def test_analyze_scad_ok_wall():
    scad = "wall = 2.0;\ncube(10);\n"
    assert analyze_scad_warnings(scad).warnings == []


def test_parse_stl_bounds_binary(tmp_path: Path):
    stl = tmp_path / "box.stl"
    _write_binary_stl(
        stl,
        [
            ((0, 0, 0), (10, 0, 0), (0, 10, 0)),
            ((10, 10, 5), (0, 10, 5), (10, 0, 5)),
        ],
    )
    bounds = parse_stl_bounds(stl)
    assert bounds is not None
    (min_x, min_y, min_z), (max_x, max_y, max_z) = bounds
    assert min_x == 0
    assert max_x == 10
    assert min_z == 0
    assert max_z == 5


def test_analyze_stl_warns_oversized_footprint(tmp_path: Path):
    stl = tmp_path / "big.stl"
    _write_binary_stl(
        stl,
        [
            ((0, 0, 0), (250, 0, 0), (0, 250, 0)),
            ((250, 250, 10), (0, 250, 10), (250, 0, 10)),
        ],
    )
    warnings = analyze_stl_warnings(stl, bed_mm=220).warnings
    assert any("250" in w for w in warnings)


def test_count_stl_triangles_binary(tmp_path: Path):
    stl = tmp_path / "tri.stl"
    _write_binary_stl(stl, [((0, 0, 0), (1, 0, 0), (0, 1, 0))])
    assert count_stl_triangles(stl) == 1
