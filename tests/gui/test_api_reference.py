"""Pure content tests for the API reference panel — no Qt/display needed
at all, since render_api_reference_html() is a plain string function.
"""

from cvmate.gui.api_reference import render_api_reference_html


def test_mentions_every_core_class():
    html = render_api_reference_html()
    for name in ("Screen", "Region", "Match", "Pattern", "MatchResult", "DebugConfig", "ScaleRange"):
        assert name in html


def test_mentions_every_exception():
    html = render_api_reference_html()
    for name in (
        "PatternNotFoundError",
        "CvMateTimeoutError",
        "InvalidRegionError",
        "AssetNotFoundError",
    ):
        assert name in html


def test_mentions_key_region_methods():
    html = render_api_reference_html()
    for method in ("find(pattern)", "find_all(", "exists(pattern)", "wait_for_appear(", "wait_for_vanish("):
        assert method in html


def test_is_valid_looking_html():
    html = render_api_reference_html()
    assert "<h2>" in html
    assert html.count("<h2>") == html.count("</h2>")
