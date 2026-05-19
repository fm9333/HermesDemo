from pathlib import Path


def test_desktop_layout_uses_fixed_viewport_and_independent_scroll_regions():
    styles = Path("hermes_app/web/static/styles.css").read_text(encoding="utf-8")

    assert "height: 100dvh;" in styles
    assert "overflow: hidden;" in styles
    assert "grid-template-rows: auto minmax(0, 1fr);" in styles

    assert ".shell {" in styles
    assert "height: 100%;" in styles
    assert "grid-template-rows: minmax(0, 1fr);" in styles

    assert ".rail-nav {" in styles
    assert "overflow-y: auto;" in styles
    assert ".messages {" in styles
    assert "overscroll-behavior: contain;" in styles
    assert ".panel-list {" in styles
