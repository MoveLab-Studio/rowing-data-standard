"""Generate committed Level 1–2 FIT fixtures from the sample sessions."""

from __future__ import annotations

from pathlib import Path

from rowing_data import write_fit
from sample_sessions import gps_update_session, stroke_boundary_session

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    write_fit(stroke_boundary_session(), FIXTURE_DIR / "stroke-boundary.fit")
    write_fit(gps_update_session(), FIXTURE_DIR / "gps-update.fit")


if __name__ == "__main__":
    main()
