from __future__ import annotations

from pathlib import Path

from pamm.archive import create_archive, extract_archive, list_archive


def test_roundtrip_pamm(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("hello world\n" * 1000, encoding="utf-8")
    (src / "b.bin").write_bytes((b"\x00" * 1024) + (b"ABCD" * 2048))

    arc = tmp_path / "out.pamm"
    out = tmp_path / "out"

    create_archive(str(src), str(arc), fast_mode=False, password="pw123")
    meta = list_archive(str(arc))
    assert meta["encrypted"] is True
    extract_archive(str(arc), str(out), password="pw123")

    assert (out / "a.txt").read_text(encoding="utf-8") == (src / "a.txt").read_text(encoding="utf-8")
    assert (out / "b.bin").read_bytes() == (src / "b.bin").read_bytes()


def test_roundtrip_pa(tmp_path: Path) -> None:
    src = tmp_path / "single.bin"
    src.write_bytes(b"X" * 10000 + b"Y" * 5000)

    arc = tmp_path / "out.pa"
    out = tmp_path / "out2"

    create_archive(str(src), str(arc), fast_mode=True)
    meta = list_archive(str(arc))
    assert meta["mode"] == "pa"
    extract_archive(str(arc), str(out))

    assert (out / "single.bin").read_bytes() == src.read_bytes()
