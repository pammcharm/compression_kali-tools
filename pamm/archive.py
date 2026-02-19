from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .analyzer import analyze_bytes
from .container import MODE_FAST, MODE_FULL, pack_container, unpack_container
from .crypto import decrypt_block, derive_keys, encrypt_block, hmac_sha256
from .engines import choose_best_engine, decompress_engine
from .normalize import denormalize_block, normalize_block

FAST_BLOCK_SIZE = 1 * 1024 * 1024
FULL_BLOCK_SIZE = 4 * 1024 * 1024


def _iter_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    files = [p for p in input_path.rglob("*") if p.is_file()]
    files.sort()
    return files


def _rel_path(base: Path, file_path: Path) -> str:
    if base.is_file():
        return file_path.name
    return str(file_path.relative_to(base))


def create_archive(
    input_path: str,
    output_path: str,
    fast_mode: bool = False,
    password: str | None = None,
) -> dict[str, Any]:
    src = Path(input_path)
    dst = Path(output_path)
    files = _iter_files(src)

    block_size = FAST_BLOCK_SIZE if fast_mode else FULL_BLOCK_SIZE

    blocks_blob = bytearray()
    file_entries: list[dict[str, Any]] = []
    total_raw = 0

    keys = derive_keys(password) if password else None

    for fp in files:
        data = fp.read_bytes()
        analysis = analyze_bytes(data[: min(len(data), 2 * 1024 * 1024)])
        total_raw += len(data)

        block_entries: list[dict[str, Any]] = []
        for i in range(0, len(data), block_size):
            raw_block = data[i : i + block_size]
            normalized, norm_meta = normalize_block(raw_block, analysis.file_type)
            engine, comp = choose_best_engine(
                normalized,
                fast_mode=fast_mode,
                high_entropy=analysis.entropy >= 7.2,
            )

            nonce = b""
            payload = comp
            if keys is not None:
                nonce, payload = encrypt_block(keys.enc_key, comp)

            offset = len(blocks_blob)
            blocks_blob.extend(payload)
            block_entries.append(
                {
                    "id": len(block_entries),
                    "engine": engine,
                    "offset": offset,
                    "size": len(payload),
                    "raw_size": len(raw_block),
                    "sha256": hashlib.sha256(raw_block).hexdigest(),
                    "nonce": nonce.hex() if nonce else "",
                    "normalization": norm_meta,
                }
            )

        file_entries.append(
            {
                "path": _rel_path(src, fp),
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "analysis": {
                    "type": analysis.file_type,
                    "entropy": analysis.entropy,
                    "zero_blocks": analysis.zero_block_density,
                    "repetition": analysis.repetition_score,
                    "already_compressed": analysis.already_compressed,
                    "executable_hint": analysis.executable_hint,
                },
                "blocks": block_entries,
            }
        )

    metadata = {
        "format": "pamm",
        "mode": "pa" if fast_mode else "pamm",
        "block_size": block_size,
        "source": str(src),
        "files": file_entries,
    }

    body_preview = json.dumps(metadata, separators=(",", ":")).encode("utf-8") + bytes(blocks_blob)
    archive_hmac = hmac_sha256(keys.hmac_key, body_preview) if keys else None

    out = pack_container(
        mode=MODE_FAST if fast_mode else MODE_FULL,
        encrypted=keys is not None,
        salt=keys.salt if keys else b"",
        metadata=metadata,
        payload=bytes(blocks_blob),
        hmac_value=archive_hmac,
    )
    dst.write_bytes(out)

    return {
        "files": len(file_entries),
        "raw_size": total_raw,
        "archive_size": len(out),
        "ratio": (len(out) / total_raw) if total_raw else 1.0,
    }


def extract_archive(
    archive_path: str,
    output_dir: str,
    password: str | None = None,
) -> dict[str, Any]:
    src = Path(archive_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    blob = src.read_bytes()
    env = unpack_container(blob)
    keys = None

    if env.encrypted:
        if not password:
            raise ValueError("Archive is encrypted; provide --password")
        keys = derive_keys(password, env.salt)
        body_preview = json.dumps(env.metadata, separators=(",", ":")).encode("utf-8") + env.payload
        expected = hmac_sha256(keys.hmac_key, body_preview)
        if expected != env.hmac_sha256:
            raise ValueError("HMAC verification failed; wrong password or tampered archive")

    restored = 0
    for file_entry in env.metadata["files"]:
        out_path = out_dir / file_entry["path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        chunks: list[bytes] = []
        for block in file_entry["blocks"]:
            start = block["offset"]
            end = start + block["size"]
            payload = env.payload[start:end]

            comp = payload
            if keys is not None:
                nonce = bytes.fromhex(block["nonce"])
                comp = decrypt_block(keys.enc_key, nonce, payload)

            normalized = decompress_engine(block["engine"], comp)
            raw = denormalize_block(
                normalized,
                file_entry["analysis"]["type"],
                block.get("normalization"),
            )
            if hashlib.sha256(raw).hexdigest() != block["sha256"]:
                raise ValueError(f"Block checksum mismatch for {file_entry['path']}")
            chunks.append(raw)

        file_data = b"".join(chunks)[: file_entry["size"]]
        if hashlib.sha256(file_data).hexdigest() != file_entry["sha256"]:
            raise ValueError(f"File checksum mismatch for {file_entry['path']}")

        out_path.write_bytes(file_data)
        restored += 1

    return {"files_restored": restored, "output_dir": str(out_dir)}


def list_archive(archive_path: str) -> dict[str, Any]:
    env = unpack_container(Path(archive_path).read_bytes())
    return {
        "mode": "pa" if env.mode == MODE_FAST else "pamm",
        "encrypted": env.encrypted,
        "files": [
            {
                "path": f["path"],
                "size": f["size"],
                "blocks": len(f["blocks"]),
                "analysis": f["analysis"],
            }
            for f in env.metadata["files"]
        ],
    }
