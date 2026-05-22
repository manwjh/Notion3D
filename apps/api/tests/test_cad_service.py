"""cad_service SCAD sanitization and render validation."""

import asyncio

from app.services.cad_service import CadError, _sanitize_scad, render_stl

NON_MANIFOLD_SCAD = """difference() {
  cube(10, center=true);
  translate([0, 0, 5]) cube(12, center=true);
}
"""


def test_sanitize_strips_markdown_fence():
    src = "```openscad\ncube(10);\n```"
    assert _sanitize_scad(src) == "cube(10);"


def test_sanitize_rejects_absolute_import():
    src = 'import("/tmp/part.scad");'
    try:
        _sanitize_scad(src)
        assert False, "expected CadError"
    except Exception as exc:
        assert "绝对路径" in str(exc)


def test_render_stl_rejects_non_manifold_stderr(monkeypatch, tmp_path):
    async def fake_communicate():
        return b"", b"ERROR: The given mesh is not closed! Unable to convert to CGAL_Nef_Polyhedron.\n"

    class FakeProc:
        returncode = 0

        async def communicate(self):
            return await fake_communicate()

    async def fake_exec(*args, **kwargs):
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(
        "app.services.cad_service.openscad_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.services.cad_service._sanitize_scad",
        lambda code: code,
    )

    out = tmp_path / "model.stl"
    out.write_text("dummy")

    try:
        asyncio.run(render_stl(NON_MANIFOLD_SCAD, out))
        assert False, "expected CadError"
    except CadError as exc:
        assert "mesh is not closed" in str(exc).lower()
