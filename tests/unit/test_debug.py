"""Regression tests for debug-mode observability (NFR10, FR19).

Covers a real bug found via manual testing: DebugConfig(enabled=True) used
to produce zero visible output in a plain script (or a GUI-launched
subprocess) because Python's logging module silently drops DEBUG records
unless a handler + level are configured — the NullHandler cv-mate attaches
by default (correct for a well-behaved library) meant "enabled" and
"visible" were quietly two different things.
"""

from __future__ import annotations

import logging

from cvmate.debug import _LOGGER_NAME, ensure_visible_when_enabled, get_logger


def _reset_logger() -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)


def test_disabled_is_a_noop():
    _reset_logger()
    get_logger()  # attaches the default NullHandler

    ensure_visible_when_enabled(False)

    logger = logging.getLogger(_LOGGER_NAME)
    assert logger.handlers == [logger.handlers[0]]
    assert isinstance(logger.handlers[0], logging.NullHandler)
    assert logger.level == logging.NOTSET


def test_enabled_attaches_a_visible_handler_and_debug_level():
    _reset_logger()
    get_logger()

    ensure_visible_when_enabled(True)

    logger = logging.getLogger(_LOGGER_NAME)
    assert logger.level == logging.DEBUG
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def test_enabled_is_idempotent_no_duplicate_handlers():
    _reset_logger()
    get_logger()

    ensure_visible_when_enabled(True)
    ensure_visible_when_enabled(True)

    logger = logging.getLogger(_LOGGER_NAME)
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) == 1


def test_enabled_respects_a_handler_the_host_already_configured():
    _reset_logger()
    logger = logging.getLogger(_LOGGER_NAME)
    custom_handler = logging.StreamHandler()
    logger.addHandler(custom_handler)  # host app configured its own logging first

    ensure_visible_when_enabled(True)

    # cv-mate shouldn't pile on a second handler when the host already has one.
    assert logger.handlers == [custom_handler]
