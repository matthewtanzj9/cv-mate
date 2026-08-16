"""cv-mate: a general-purpose, OpenCV-based gameplay automation framework.

Detect on-screen visual patterns and trigger mouse actions from a
Sikuli-style scripting API::

    from cvmate import Screen, Pattern

    screen = Screen()
    screen.find(Pattern("ok_button.png")).click()

See the README for the full API and the ``examples/`` folder for
runnable scripts.
"""

from .config import DebugConfig, ScaleRange
from .exceptions import (
    AssetNotFoundError,
    CvMateError,
    CvMateTimeoutError,
    InvalidRegionError,
    PatternNotFoundError,
)
from .match import MatchResult
from .pattern import Pattern
from .region import Match, Region
from .screen import Screen

__version__ = "0.1.0"

__all__ = [
    "Screen",
    "Region",
    "Match",
    "Pattern",
    "MatchResult",
    "DebugConfig",
    "ScaleRange",
    "CvMateError",
    "PatternNotFoundError",
    "CvMateTimeoutError",
    "InvalidRegionError",
    "AssetNotFoundError",
    "__version__",
]
