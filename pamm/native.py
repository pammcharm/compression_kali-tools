from __future__ import annotations

from typing import Any

try:
    import pamm_native as _native
except Exception:  # pragma: no cover
    _native = None


def available() -> bool:
    return _native is not None


def compress_engine(engine: str, data: bytes) -> bytes:
    if _native is None:
        raise RuntimeError("pamm_native is not available")
    return _native.compress_engine(engine, data)


def decompress_engine(engine: str, data: bytes) -> bytes:
    if _native is None:
        raise RuntimeError("pamm_native is not available")
    return _native.decompress_engine(engine, data)


def choose_best_engine(data: bytes, fast_mode: bool, high_entropy: bool) -> tuple[str, bytes]:
    if _native is None:
        raise RuntimeError("pamm_native is not available")
    engine, payload = _native.choose_best_engine(data, fast_mode, high_entropy)
    return str(engine), bytes(payload)


def normalize_block(data: bytes, file_type: str) -> tuple[bytes, dict[str, Any]]:
    if _native is None:
        raise RuntimeError("pamm_native is not available")
    out = bytes(_native.normalize_block(data, file_type))
    return out, {"normalized": out != data, "scheme": "native" if out != data else "none"}


def denormalize_block(data: bytes, file_type: str, metadata: dict[str, Any] | None = None) -> bytes:
    if _native is None:
        raise RuntimeError("pamm_native is not available")
    if metadata and metadata.get("normalized"):
        return bytes(_native.denormalize_block(data, file_type))
    return data
