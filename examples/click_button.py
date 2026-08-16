"""Minimal cv-mate example: find an image on screen and click it.

Run standalone (FR17): `python examples/click_button.py`

Requires a Windows desktop and a real "ok_button.png" image asset next to
this script (or update the path below) — this is a manual smoke test, not
part of the automated test suite.
"""

from cvmate import CvMateTimeoutError, Pattern, PatternNotFoundError, Screen


def main() -> None:
    screen = Screen()
    ok_button = Pattern("ok_button.png", threshold=0.85)

    try:
        screen.wait_for_appear(ok_button, timeout=10.0).click()
        print("Clicked the OK button.")
    except (PatternNotFoundError, CvMateTimeoutError) as exc:
        print(f"Could not find the OK button: {exc}")


if __name__ == "__main__":
    main()
