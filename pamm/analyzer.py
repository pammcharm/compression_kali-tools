from __future__ import annotations

import math
from collections import Counter

from .types import AnalysisResult

SIGNATURES: dict[bytes, str] = {
    b"\x89PNG": "png",
    b"\xff\xd8\xff": "jpeg",
    b"PK\x03\x04": "zip",
    b"\x1f\x8b\x08": "gzip",
    b"7z\xbc\xaf\x27\x1c": "7z",
    b"Rar!\x1a\x07": "rar",
    b"MZ": "pe-executable",
    b"\x7fELF": "elf-executable",
    b"\xcf\xfa\xed\xfe": "mach-o",
    b"\xca\xfe\xba\xbe": "mach-o",
}

COMPRESSED_TYPES = {"png", "jpeg", "zip", "gzip", "7z", "rar"}


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def repetition_score(data: bytes) -> str:
    if len(data) < 64:
        return "low"
    chunk = 8
    windows = [data[i : i + chunk] for i in range(0, len(data) - chunk + 1, chunk)]
    unique = len(set(windows))
    ratio = 1.0 - (unique / max(1, len(windows)))
    if ratio >= 0.45:
        return "high"
    if ratio >= 0.2:
        return "medium"
    return "low"


def zero_block_density(data: bytes, block_size: int = 4096) -> float:
    if not data:
        return 0.0
    blocks = [data[i : i + block_size] for i in range(0, len(data), block_size)]
    zero_blocks = sum(1 for b in blocks if b and all(x == 0 for x in b))
    return zero_blocks / len(blocks)


def detect_type(data: bytes) -> str:
    for sig, name in SIGNATURES.items():
        if data.startswith(sig):
            return name
    if data[:2] == b"#!":
        return "script"
    if all((32 <= b <= 126) or b in (9, 10, 13) for b in data[:4096]):
        return "text"
    return "binary"


def analyze_bytes(data: bytes) -> AnalysisResult:
    ftype = detect_type(data)
    entropy = shannon_entropy(data)
    zero_density = zero_block_density(data)
    rep_score = repetition_score(data)
    executable = ftype in {"pe-executable", "elf-executable", "mach-o"}
    already = ftype in COMPRESSED_TYPES or entropy > 7.8
    return AnalysisResult(
        file_type=ftype,
        entropy=round(entropy, 4),
        zero_block_density=round(zero_density, 4),
        repetition_score=rep_score,
        already_compressed=already,
        executable_hint=executable,
    )
