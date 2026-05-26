from app.services.atomic_io import atomic_write_text


def test_atomic_write_text(tmp_path):
    target = tmp_path / "nested" / "meta.json"
    atomic_write_text(target, '{"ok": true}')
    assert target.read_text(encoding="utf-8") == '{"ok": true}'
    assert not target.with_suffix(".json.tmp").exists()
