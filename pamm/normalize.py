from __future__ import annotations

from typing import Any

from . import native


def normalize_block(data: bytes, file_type: str) -> tuple[bytes, dict[str, Any]]:
    if native.available():
        return native.normalize_block(data, file_type)

    if file_type == "text":
        out = data.replace(b"\r\n", b"\n")
        return out, {"normalized": out != data, "scheme": "text-crlf" if out != data else "none"}
    return data, {"normalized": False, "scheme": "none"}


def denormalize_block(data: bytes, file_type: str, metadata: dict[str, Any] | None = None) -> bytes:
    if native.available():
        return native.denormalize_block(data, file_type, metadata)

    if metadata and metadata.get("scheme") == "text-crlf":
        return data
    return data
