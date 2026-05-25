from app.services.cad_parts import build_part_scad, parse_scad_parts, parts_manifest


GEAR_PAIR = """\
module spur_gear(z) {
  cube([z, z, z]);
}

// notion3d:part gear_small 小齿轮 #E74C3C
color("#E74C3C") {
  rotate([0, 0, 90])
    spur_gear(teeth_1);
}

// notion3d:part gear_large 大齿轮
color("#3498DB")
  translate([30, 0, 0])
    spur_gear(teeth_2);
"""


def test_parse_scad_parts():
    preamble, parts = parse_scad_parts(GEAR_PAIR)
    assert "module spur_gear" in preamble
    assert len(parts) == 2
    assert parts[0].id == "gear_small"
    assert parts[0].label == "小齿轮"
    assert parts[0].color == "#E74C3C"
    assert "spur_gear(teeth_1)" in parts[0].body
    assert parts[1].id == "gear_large"
    assert parts[1].label == "大齿轮"
    assert parts[1].color == "#3498DB"


def test_build_part_scad_keeps_preamble():
    preamble, parts = parse_scad_parts(GEAR_PAIR)
    isolated = build_part_scad(preamble, parts[0])
    assert "module spur_gear" in isolated
    assert "spur_gear(teeth_1)" in isolated
    assert "spur_gear(teeth_2)" not in isolated


def test_parts_manifest_urls():
    _, parts = parse_scad_parts(GEAR_PAIR)
    manifest = parts_manifest("proj1", 3, parts)
    assert manifest["parts"][0]["stl_url"].endswith("/parts/gear_small.stl")
