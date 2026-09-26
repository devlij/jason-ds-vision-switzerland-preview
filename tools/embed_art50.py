"""Append EU AI Act Art. 50 PNG text chunks without recompressing IDAT."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

COUNTRY = "Switzerland"

TITLE = "Jason D's Vision \u2014 AI-generated artistic interpretation"
DESCRIPTION = (
    "AI-generated artistic interpretation from the Jason D's Vision "
    f"{COUNTRY} gallery. Created with generative AI; not a photograph."
)
COPYRIGHT = "Jason D's Vision \u2014 AI-generated content"
SOFTWARE = "Jason D's Vision library pipeline"
COMMENT = (
    "EU AI Act Art. 50 transparency note: this image is AI-generated content. "
    "Machine-readable disclosure embedded 2026-09-24."
)


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _text_chunk(keyword: str, text: str) -> bytes:
    data = keyword.encode("latin-1") + b"\x00" + text.encode("latin-1")
    return _chunk(b"tEXt", data)


def _itxt_chunk(keyword: str, text: str) -> bytes:
    data = (
        keyword.encode("latin-1")
        + b"\x00"
        + b"\x00"  # compression flag: uncompressed
        + b"\x00"  # compression method
        + b"\x00"  # language tag
        + b"\x00"  # translated keyword
        + text.encode("utf-8")
    )
    return _chunk(b"iTXt", data)


def art50_chunks() -> list[bytes]:
    return [
        _itxt_chunk("Title", TITLE),
        _text_chunk("Description", DESCRIPTION),
        _itxt_chunk("Copyright", COPYRIGHT),
        _text_chunk("Software", SOFTWARE),
        _text_chunk("Comment", COMMENT),
    ]


def embed(path: str | Path) -> None:
    """Insert the five Art. 50 chunks immediately before IEND. IDAT bytes stay put."""
    file_path = Path(path)
    raw = file_path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"not a png: {file_path}")
    iend = raw.rfind(b"IEND")
    if iend < 8:
        raise SystemExit(f"no IEND: {file_path}")
    # length field sits 4 bytes before the IEND tag
    start = iend - 4
    if raw[start : start + 4] != b"\x00\x00\x00\x00":
        raise SystemExit(f"unexpected IEND length: {file_path}")
    injected = b"".join(art50_chunks())
    file_path.write_bytes(raw[:start] + injected + raw[start:])
