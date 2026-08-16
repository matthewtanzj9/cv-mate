"""Pure-function tests for filename sanitization/collision handling."""

from cvmate.gui.naming import sanitize_filename, unique_path


def test_sanitize_filename_strips_invalid_chars():
    assert sanitize_filename('ok:button?.png') == "ok_button_.png"


def test_sanitize_filename_forces_png_extension():
    assert sanitize_filename("icon") == "icon.png"
    assert sanitize_filename("icon.jpg") == "icon.png"
    assert sanitize_filename("icon.png") == "icon.png"


def test_sanitize_filename_empty_input_uses_default():
    assert sanitize_filename("") == "template.png"
    assert sanitize_filename("   ") == "template.png"


def test_sanitize_filename_custom_default():
    # An input of only dots survives char-sanitization (dots aren't in the
    # invalid-char set) but is stripped away entirely by rstrip("."),
    # leaving nothing — that's the case the `default` fallback covers.
    assert sanitize_filename("...", default="fallback") == "fallback.png"


def test_unique_path_returns_plain_path_when_free(tmp_path):
    assert unique_path(tmp_path, "x.png") == tmp_path / "x.png"


def test_unique_path_appends_suffix_on_collision(tmp_path):
    (tmp_path / "x.png").write_bytes(b"")
    assert unique_path(tmp_path, "x.png") == tmp_path / "x_1.png"


def test_unique_path_increments_past_multiple_collisions(tmp_path):
    (tmp_path / "x.png").write_bytes(b"")
    (tmp_path / "x_1.png").write_bytes(b"")
    assert unique_path(tmp_path, "x.png") == tmp_path / "x_2.png"
