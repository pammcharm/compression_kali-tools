#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PY = VENV / "bin" / "python"
PIP = [str(PY), "-m", "pip"]


class StepError(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("\n$", " ".join(cmd))
    res = subprocess.run(cmd, cwd=cwd or ROOT, env=env)
    if res.returncode != 0:
        raise StepError(f"command failed ({res.returncode}): {' '.join(cmd)}")


def ensure_venv(recreate: bool) -> None:
    if recreate and VENV.exists():
        shutil.rmtree(VENV)
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])


def install_all() -> None:
    run(PIP + ["install", "-U", "pip", "setuptools", "wheel"])
    # Includes pybind11 build dependency and project runtime deps.
    run(PIP + ["install", "-e", ".", "pytest"])


def run_tests() -> None:
    run([str(PY), "-m", "pytest", "-q"])


def run_cli_smoke() -> None:
    smoke_dir = Path("/tmp/pamm_run_all")
    src = smoke_dir / "src"
    out = smoke_dir / "out"
    src.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    (src / "a.txt").write_text("run-all smoke test\n" * 2000, encoding="utf-8")
    archive = smoke_dir / "smoke.pamm"

    run([str(PY), "-m", "pamm.cli", "compress", str(src), "-o", str(archive)])
    run([str(PY), "-m", "pamm.cli", "list", str(archive)])
    run([str(PY), "-m", "pamm.cli", "extract", str(archive), "-d", str(out)])

    original = (src / "a.txt").read_bytes()
    restored = (out / "a.txt").read_bytes()
    if original != restored:
        raise StepError("CLI smoke check failed: restored data mismatch")


def run_benchmark_smoke() -> None:
    corpus = Path("/tmp/pamm_run_all_corpus")
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "sample.txt").write_text("hello benchmark " * 20000, encoding="utf-8")
    with (corpus / "zeros.bin").open("wb") as f:
        f.write(b"\x00" * 300_000)

    run([str(PY), "benchmarks/benchmark.py", str(corpus), "--max-files", "2"])


def check_native_import() -> None:
    run(
        [
            str(PY),
            "-c",
            "import pamm.native as n; print('native_available', n.available()); assert n.available()",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="One-shot setup + build + test + smoke-run for PAMM")
    parser.add_argument("--recreate-venv", action="store_true", help="Delete and recreate .venv")
    parser.add_argument("--skip-bench", action="store_true", help="Skip benchmark smoke run")
    args = parser.parse_args()

    try:
        ensure_venv(recreate=args.recreate_venv)
        install_all()
        check_native_import()
        run_tests()
        run_cli_smoke()
        if not args.skip_bench:
            run_benchmark_smoke()
    except StepError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    print("\nAll steps passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
