"""Headless (offscreen) tests for PythonHighlighter's regex-based rules."""

from PySide6.QtGui import QTextDocument

from cvmate.gui.highlighter import (
    COMMENT_FORMAT,
    KEYWORD_FORMAT,
    NUMBER_FORMAT,
    STRING_FORMAT,
    PythonHighlighter,
)


def _color_at(document: QTextDocument, block_number: int, position: int):
    block = document.findBlockByNumber(block_number)
    for format_range in block.layout().formats():
        if format_range.start <= position < format_range.start + format_range.length:
            return format_range.format.foreground().color()
    return None


def _highlighted_document(text: str) -> QTextDocument:
    doc = QTextDocument()
    highlighter = PythonHighlighter(doc)  # attaches itself to the document
    doc.setPlainText(text)
    # Without a view attached to the document, Qt doesn't synchronously lay
    # out blocks on `setPlainText` — force it so `block.layout().formats()`
    # is populated for the assertions below.
    highlighter.rehighlight()
    return doc


def test_def_keyword_is_highlighted():
    doc = _highlighted_document("def foo():\n    return 42")
    assert _color_at(doc, 0, 1) == KEYWORD_FORMAT.foreground().color()  # inside "def"


def test_return_keyword_is_highlighted():
    doc = _highlighted_document("def foo():\n    return 42")
    assert _color_at(doc, 1, 5) == KEYWORD_FORMAT.foreground().color()  # inside "return"


def test_numbers_are_highlighted():
    doc = _highlighted_document("x = 42")
    assert _color_at(doc, 0, 4) == NUMBER_FORMAT.foreground().color()  # "42"


def test_string_rule_wins_over_keyword_looking_substring():
    doc = _highlighted_document('x = "def"  # not a keyword')
    # "def" appears inside a string literal here — it must be colored as a
    # string, not re-colored as the `def` keyword.
    assert _color_at(doc, 0, 5) == STRING_FORMAT.foreground().color()


def test_comment_rule_applies_after_the_hash():
    text = 'x = "def"  # not a keyword'
    doc = _highlighted_document(text)
    comment_index = text.index("#")
    assert _color_at(doc, 0, comment_index + 2) == COMMENT_FORMAT.foreground().color()
