from __future__ import annotations

import os
from pathlib import Path

from pamm.cli import main


def test_cli_flow(tmp_path: Path) -> None:
    src = tmp_path / "in.txt"
    src.write_text("abc" * 2000, encoding="utf-8")
    arc = tmp_path / "x.pamm"
    out = tmp_path / "out"

    assert main(["compress", str(src), "-o", str(arc)]) == 0
    assert main(["list", str(arc)]) == 0
    assert main(["extract", str(arc), "-d", str(out)]) == 0
    assert (out / "in.txt").read_text(encoding="utf-8") == src.read_text(encoding="utf-8")


def test_cli_defaults_and_doctor(tmp_path: Path) -> None:
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    src = tmp_path / "data.bin"
    src.write_bytes(b"ABCD" * 2048)

    try:
        assert main(["compress", str(src)]) == 0
        inferred_archive = src.with_suffix(src.suffix + ".pamm")
        assert inferred_archive.exists()

        assert main(["list", str(inferred_archive), "--json"]) == 0
        assert main(["doctor"]) == 0
        assert main(["completion", "--shell", "bash"]) == 0
        assert main(["completion", "--shell", "zsh"]) == 0

        assert main(["extract", str(inferred_archive)]) == 0
        inferred_dest = Path.cwd() / f"{inferred_archive.name[:-5]}_extracted"
        assert (inferred_dest / "data.bin").read_bytes() == src.read_bytes()
    finally:
        os.chdir(old_cwd)
