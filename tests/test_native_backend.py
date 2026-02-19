from __future__ import annotations

import pytest

from pamm import native


@pytest.mark.skipif(not native.available(), reason="native extension not built")
def test_native_engine_roundtrip_and_exec_normalization() -> None:
    data = (b"ABCD" * 4096) + (b"\x00" * 1024)

    engine, comp = native.choose_best_engine(data, fast_mode=False, high_entropy=False)
    dec = native.decompress_engine(engine, comp)
    assert dec == data

    # Minimal PE-like blob: MZ + e_lfanew + PE signature.
    pe = bytearray(b"MZ" + b"\x00" * 0x3A)
    pe += (0x40).to_bytes(4, "little")
    pe += b"\x00" * (0x40 - len(pe))
    pe += b"PE\x00\x00" + b"\x01\x02\x03\x04" + b"\xAA" * 64

    norm, meta = native.normalize_block(bytes(pe), "pe-executable")
    restored = native.denormalize_block(norm, "pe-executable", meta)
    assert restored == bytes(pe)
