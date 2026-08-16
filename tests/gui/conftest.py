"""Shared fixtures for GUI tests.

Forces the Qt "offscreen" platform plugin unless something already set
QT_QPA_PLATFORM (e.g. a developer deliberately running these against a real
display) — this is what lets the whole suite run in headless CI with no
real screen. The `qtbot` fixture itself comes from pytest-qt.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
