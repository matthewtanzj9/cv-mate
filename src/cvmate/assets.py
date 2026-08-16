"""Image-asset resolution and loading (FR14).

Patterns are usually authored as a bare filename (``Pattern("ok_button.png")``)
resolved against a project's local image-asset folder, rather than a full
path — this module is where that resolution and the underlying
``cv2.imread`` + decode-error handling lives, plus a small cache so a
`Pattern` reused across many `find()` calls doesn't re-read/re-decode the
file from disk each time.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .exceptions import AssetNotFoundError

# Default folder scripts' relative image filenames are resolved against, when
# a Pattern doesn't specify its own asset_folder. Scripts typically override
# this per-Pattern or via CVMATE_ASSET_DIR; cwd is a reasonable zero-config
# default for a standalone `python my_script.py` (FR17).
DEFAULT_ASSET_FOLDER = Path(".")

_image_cache: dict[Path, np.ndarray] = {}


def resolve_asset_path(filename: str | Path, asset_folder: str | Path | None = None) -> Path:
    """Resolve ``filename`` to a concrete file path.

    If ``filename`` is already an absolute/existing path it's returned as-is
    (resolved). Otherwise it's looked up relative to ``asset_folder``
    (defaulting to :data:`DEFAULT_ASSET_FOLDER`).
    """
    path = Path(filename)
    if path.is_absolute() and path.is_file():
        return path.resolve()

    base = Path(asset_folder) if asset_folder is not None else DEFAULT_ASSET_FOLDER
    candidate = (base / path).resolve()
    if candidate.is_file():
        return candidate

    # Fall back to treating `filename` as directly relative to cwd, in case
    # it was given as e.g. "images/ok_button.png" with no asset_folder.
    if path.is_file():
        return path.resolve()

    raise AssetNotFoundError(
        f"Could not find image asset {str(filename)!r} "
        f"(looked in {base.resolve()!r} and the current directory)"
    )


def load_image(path: Path) -> np.ndarray:
    """Load and cache an image from ``path`` as a BGR ``np.ndarray``."""
    cached = _image_cache.get(path)
    if cached is not None:
        return cached

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise AssetNotFoundError(f"File exists but could not be decoded as an image: {path!r}")

    _image_cache[path] = image
    return image


def clear_cache() -> None:
    """Drop all cached images (mainly useful for tests)."""
    _image_cache.clear()
