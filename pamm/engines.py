from __future__ import annotations

import bz2
import lzma
import zlib

from . import native

ENGINE_A = "A"
ENGINE_B = "B"
ENGINE_C = "C"
ENGINE_N = "N"


def _compress_engine_py(engine: str, data: bytes) -> bytes:
    if engine == ENGINE_A:
        return zlib.compress(data, level=6)
    if engine == ENGINE_B:
        return zlib.compress(data, level=9)
    if engine == ENGINE_C:
        return lzma.compress(data, preset=9 | lzma.PRESET_EXTREME)
    if engine == ENGINE_N:
        return data
    raise ValueError(f"Unknown engine: {engine}")


def _decompress_engine_py(engine: str, data: bytes) -> bytes:
    if engine == ENGINE_A:
        return zlib.decompress(data)
    if engine == ENGINE_B:
        return zlib.decompress(data)
    if engine == ENGINE_C:
        return lzma.decompress(data)
    if engine == ENGINE_N:
        return data
    raise ValueError(f"Unknown engine: {engine}")


def compress_engine(engine: str, data: bytes) -> bytes:
    if native.available():
        return native.compress_engine(engine, data)
    return _compress_engine_py(engine, data)


def decompress_engine(engine: str, data: bytes) -> bytes:
    if native.available():
        return native.decompress_engine(engine, data)
    return _decompress_engine_py(engine, data)


def choose_best_engine(data: bytes, fast_mode: bool, high_entropy: bool) -> tuple[str, bytes]:
    if native.available():
        return native.choose_best_engine(data, fast_mode, high_entropy)

    if fast_mode:
        return ENGINE_A, _compress_engine_py(ENGINE_A, data)

    candidates: list[tuple[str, bytes]] = [
        (ENGINE_N, _compress_engine_py(ENGINE_N, data)),
        (ENGINE_A, _compress_engine_py(ENGINE_A, data)),
        (ENGINE_B, _compress_engine_py(ENGINE_B, data)),
        (ENGINE_C, _compress_engine_py(ENGINE_C, data)),
    ]
    return min(candidates, key=lambda x: len(x[1]))
