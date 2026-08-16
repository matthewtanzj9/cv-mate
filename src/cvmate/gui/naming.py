"""Filename sanitization/collision-avoidance for captured template images.

Pure functions, no Qt dependency — fully unit-testable headlessly.
"""

from __future__ import annotations

import re
from pathlib import Path

# Characters invalid in Windows filenames, plus control characters.
_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

DEFAULT_STEM = "template"


def sanitize_filename(raw: str, default: str = DEFAULT_STEM) -> str:
    """Turn arbitrary user input into a safe ``<stem>.png`` filename.

    Strips characters invalid on Windows, drops any extension the user
    typed (a ``.png`` suffix is always forced regardless), and falls back
    to ``default`` if nothing usable remains.
    """
    cleaned = _INVALID_CHARS.sub("_", raw).strip().rstrip(".")
    stem = Path(cleaned).stem.strip() if cleaned else ""
    if not stem:
        stem = default
    return f"{stem}.png"


def unique_path(directory: Path, filename: str) -> Path:
    """``directory/filename``, or ``directory/filename_1``, ``_2``, ... if
    that path already exists. Never overwrites an existing file."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem, suffix = Path(filename).stem, Path(filename).suffix
    n = 1
    while True:
        candidate = directory / f"{stem}_{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1
