"""Minimal regex-rule-based Python syntax highlighting.

Not a full IDE-grade highlighter — just enough (keywords, strings,
comments, numbers) to make scripts readable in the editor.
"""

from __future__ import annotations

import keyword
import re

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat

from . import theme

# Rules are applied in order; later rules (strings, comments) are applied
# after keywords so a keyword-looking token inside a string/comment gets
# re-colored correctly (comments/strings should win over bare keyword text).
#
# Colors come from theme.py (not hardcoded here) so the editor's syntax
# coloring and the rest of the GUI's dark theme always agree with each
# other — these are dark-background-tuned colors and need the matching
# dark editor background theme.py's stylesheet applies.


def _format(color: str, *, bold: bool = False) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(700)
    return fmt


KEYWORD_FORMAT = _format(theme.TOKEN_KEYWORD, bold=True)
STRING_FORMAT = _format(theme.TOKEN_STRING)
COMMENT_FORMAT = _format(theme.TOKEN_COMMENT)
NUMBER_FORMAT = _format(theme.TOKEN_NUMBER)

_KEYWORD_PATTERN = re.compile(r"\b(" + "|".join(keyword.kwlist) + r")\b")
_NUMBER_PATTERN = QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b")
_STRING_PATTERN = QRegularExpression(r"(\"[^\"\\]*(\\.[^\"\\]*)*\")|('[^'\\]*(\\.[^'\\]*)*')")
_COMMENT_PATTERN = QRegularExpression(r"#[^\n]*")


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document) -> None:
        super().__init__(document)

    def highlightBlock(self, text: str) -> None:
        for match in _KEYWORD_PATTERN.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), KEYWORD_FORMAT)

        self._apply_regex(text, _NUMBER_PATTERN, NUMBER_FORMAT)
        # Strings and comments are applied last so they win over any
        # keyword-looking substring inside them.
        self._apply_regex(text, _STRING_PATTERN, STRING_FORMAT)
        self._apply_regex(text, _COMMENT_PATTERN, COMMENT_FORMAT)

    def _apply_regex(self, text: str, pattern: QRegularExpression, fmt: QTextCharFormat) -> None:
        it = pattern.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
