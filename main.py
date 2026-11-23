#!/usr/bin/env python3
"""Publish this repository's news collage as the entry image.

The whole job is a careful copy: take ``entry.png`` from the bot
directory and place it, untouched, in the output directory as
``entry.png``.  Before copying, the bytes are sanity-checked so a
corrupt or oversized asset fails loudly instead of being submitted.

Locations come from the environment when the grader provides them:
``MAKEFUN_BOT_DIR`` says where the repository was mounted (falling
back to the folder this script lives in) and ``MAKEFUN_OUTPUT_DIR``
says where the result belongs (falling back to ``/output``).
"""

import os
import sys
from pathlib import Path

# Every PNG file opens with this fixed eight-byte signature.
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# The bounty caps the submitted picture at one mebibyte.
MAX_IMAGE_BYTES = 1024 * 1024

IMAGE_NAME = "entry.png"


def fail(reason: str) -> "SystemExit":
    """Report a problem on stderr and exit with a failure code."""
    print(f"news-image entry: {reason}", file=sys.stderr)
    return SystemExit(1)


def bot_directory() -> Path:
    """Where the entry's files were mounted for this run."""
    override = os.environ.get("MAKEFUN_BOT_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent


def output_directory() -> Path:
    """Where the finished entry image has to be written."""
    override = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if override:
        return Path(override)
    return Path("/output")


def check_dimensions(payload: bytes) -> None:
    """Refuse a PNG whose IHDR header reports more than 1024x1024.

    The first chunk of a PNG is always IHDR: after the signature and
    the chunk's length/type fields, its opening fields are the image
    width and height as big-endian 32-bit integers.
    """
    if len(payload) < 24 or payload[12:16] != b"IHDR":
        raise fail(f"{IMAGE_NAME} has no readable IHDR header")
    width = int.from_bytes(payload[16:20], "big")
    height = int.from_bytes(payload[20:24], "big")
    if width > 1024 or height > 1024:
        raise fail(f"{IMAGE_NAME} is {width}x{height}, over 1024x1024")


def load_collage(source: Path) -> bytes:
    """Read the collage and refuse anything that is not a sane PNG."""
    if not source.is_file():
        raise fail(f"{IMAGE_NAME} is missing from {source.parent}")
    payload = source.read_bytes()
    if not payload.startswith(PNG_MAGIC):
        raise fail(f"{IMAGE_NAME} does not start with a PNG signature")
    if len(payload) > MAX_IMAGE_BYTES:
        raise fail(
            f"{IMAGE_NAME} is {len(payload)} bytes, over the "
            f"{MAX_IMAGE_BYTES}-byte limit"
        )
    check_dimensions(payload)
    return payload


def main() -> int:
    source = bot_directory() / IMAGE_NAME
    payload = load_collage(source)

    target_dir = output_directory()
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / IMAGE_NAME).write_bytes(payload)
    except OSError as exc:
        raise fail(f"could not write the entry image: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
