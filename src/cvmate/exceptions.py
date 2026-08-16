"""Exception hierarchy for cv-mate.

All library-raised exceptions derive from :class:`CvMateError`, so callers
can catch broadly (``except CvMateError``) or narrowly (``except
PatternNotFoundError``) as needed. FR15 requires failures to be explicit and
catchable rather than silent.
"""

from __future__ import annotations


class CvMateError(Exception):
    """Base class for all cv-mate exceptions."""


class PatternNotFoundError(CvMateError):
    """Raised by :meth:`Region.find` when no match clears the pattern's
    confidence threshold on a single-shot search."""


class CvMateTimeoutError(CvMateError):
    """Raised by :meth:`Region.wait_for_appear`/:meth:`Region.wait_for_vanish`
    when the timeout elapses before the expected condition is observed.

    Named ``CvMateTimeoutError`` (not ``TimeoutError``) so it doesn't shadow
    the builtin exception of the same name.
    """


class InvalidRegionError(CvMateError):
    """Raised when a :class:`Region` is constructed or resized with
    non-sensical geometry (e.g. negative or zero width/height)."""


class AssetNotFoundError(CvMateError):
    """Raised when a named image asset cannot be resolved to a file, or the
    file exists but cannot be decoded as an image."""
