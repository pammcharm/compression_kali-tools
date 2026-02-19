from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from pamm.archive import create_archive


@dataclass(slots=True)
class BenchResult:
    tool: str
    input_file: str
    raw_size: int
    archive_size: int
    ratio: float
    seconds: float


def run_cmd(cmd: list[str]) -> float:
    start = time.perf_counter()
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return time.perf_counter() - start


def bench_file(path: Path, tmp: Path, include_pamm_encrypted: bool) -> list[BenchResult]:
    raw_size = path.stat().st_size
    results: list[BenchResult] = []

    pamm_out = tmp / f"{path.name}.pamm"
    start = time.perf_counter()
    create_archive(str(path), str(pamm_out), fast_mode=False, password=None)
    dt = time.perf_counter() - start
    results.append(BenchResult("pamm", path.name, raw_size, pamm_out.stat().st_size, pamm_out.stat().st_size / raw_size, dt))

    pa_out = tmp / f"{path.name}.pa"
    start = time.perf_counter()
    create_archive(str(path), str(pa_out), fast_mode=True, password=None)
    dt = time.perf_counter() - start
    results.append(BenchResult("pa", path.name, raw_size, pa_out.stat().st_size, pa_out.stat().st_size / raw_size, dt))

    if include_pamm_encrypted:
        pamm_enc = tmp / f"{path.name}.enc.pamm"
        start = time.perf_counter()
        create_archive(str(path), str(pamm_enc), fast_mode=False, password="benchmark-password")
        dt = time.perf_counter() - start
        results.append(BenchResult("pamm+aes", path.name, raw_size, pamm_enc.stat().st_size, pamm_enc.stat().st_size / raw_size, dt))

    if shutil.which("7z"):
        out7z = tmp / f"{path.name}.7z"
        dt = run_cmd(["7z", "a", "-t7z", "-mx=9", str(out7z), str(path)])
        results.append(BenchResult("7z", path.name, raw_size, out7z.stat().st_size, out7z.stat().st_size / raw_size, dt))

    if shutil.which("zstd"):
        outz = tmp / f"{path.name}.zst"
        dt = run_cmd(["zstd", "-19", "-q", "-o", str(outz), str(path)])
        results.append(BenchResult("zstd-19", path.name, raw_size, outz.stat().st_size, outz.stat().st_size / raw_size, dt))

    if shutil.which("xz"):
        outx = tmp / f"{path.name}.xz"
        with outx.open("wb") as f:
            start = time.perf_counter()
            subprocess.run(["xz", "-9e", "-c", str(path)], check=True, stdout=f, stderr=subprocess.DEVNULL)
            dt = time.perf_counter() - start
        results.append(BenchResult("xz-9e", path.name, raw_size, outx.stat().st_size, outx.stat().st_size / raw_size, dt))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark PAMM vs 7z/zstd/xz on corpus files")
    parser.add_argument("corpus", help="Path to extracted corpus directory (Calgary/Canterbury/Silesia)")
    parser.add_argument("--min-bytes", type=int, default=1024, help="Skip files smaller than this")
    parser.add_argument("--max-files", type=int, default=25, help="Maximum files to benchmark")
    parser.add_argument("--encrypted", action="store_true", help="Include encrypted .pamm benchmark")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of table")
    args = parser.parse_args()

    corpus = Path(args.corpus)
    if not corpus.exists() or not corpus.is_dir():
        raise SystemExit("Corpus path must be a directory")

    files = [p for p in corpus.rglob("*") if p.is_file() and p.stat().st_size >= args.min_bytes]
    files.sort(key=lambda p: p.stat().st_size, reverse=True)
    files = files[: args.max_files]
    if not files:
        raise SystemExit("No files matched benchmark filters")

    rows: list[BenchResult] = []
    with tempfile.TemporaryDirectory(prefix="pamm-bench-") as td:
        tmp = Path(td)
        for f in files:
            rows.extend(bench_file(f, tmp, args.encrypted))

    if args.json:
        print(json.dumps([r.__dict__ for r in rows], indent=2))
        return 0

    print(f"{'tool':<10} {'file':<28} {'raw':>10} {'archive':>10} {'ratio':>8} {'sec':>8}")
    print("-" * 80)
    for r in rows:
        print(f"{r.tool:<10} {r.input_file[:28]:<28} {r.raw_size:>10} {r.archive_size:>10} {r.ratio:>8.3f} {r.seconds:>8.3f}")

    print("\nSummary by tool")
    by_tool: dict[str, list[BenchResult]] = {}
    for r in rows:
        by_tool.setdefault(r.tool, []).append(r)
    for tool, group in sorted(by_tool.items()):
        raw = sum(x.raw_size for x in group)
        arch = sum(x.archive_size for x in group)
        sec = sum(x.seconds for x in group)
        print(f"{tool:<10} ratio={arch/raw:.3f} total_sec={sec:.3f} files={len(group)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
