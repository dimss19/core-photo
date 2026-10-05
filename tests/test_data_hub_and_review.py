"""Tests for DataHubView, ReviewView, AppContext properties, and navigation aliases."""

import pytest
from database.models import PhotoModel, SessionModel
from imaging.processor import ImageProcessor
from storage.manager import StorageManager


def test_photo_model_timestamp_property():
    p1 = PhotoModel(captured_at="2026-10-05T12:00:00", created_at="2026-10-05T12:00:01")
    assert p1.timestamp == "2026-10-05T12:00:00"

    p2 = PhotoModel(captured_at=None, created_at="2026-10-05T12:00:01")
    assert p2.timestamp == "2026-10-05T12:00:01"

    p3 = PhotoModel(captured_at=None, created_at="")
    assert p3.timestamp == ""


def test_export_csv_report_structure(tmp_path):
    sess = SessionModel(id="S_CSV", site="GOSOWONG", date="20261005", operator="Dimas")
    photos = [
        PhotoModel(
            id=1,
            session_id="S_CSV",
            hole_id="TSD168",
            tray_number="1",
            interval_from=0.0,
            interval_to=1.5,
            jpg_path="CorePhotoData/Sessions/GOSOWONG_20261005/jpg/TSD168_01.jpg",
            md5_jpg="abc123def456",
            captured_at="2026-10-05 10:00:00",
        ),
        PhotoModel(
            id=2,
            session_id="S_CSV",
            hole_id="TSD168",
            tray_number="2",
            interval_from=1.5,
            interval_to=3.0,
            jpg_path="CorePhotoData/Sessions/GOSOWONG_20261005/jpg/TSD168_02.jpg",
            md5_jpg="789xyz012345",
            captured_at="2026-10-05 10:15:00",
        ),
    ]

    csv_path = tmp_path / "TSD168.csv"
    ImageProcessor.export_csv_report(sess, photos, csv_path)
    assert csv_path.exists()

    lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3  # Header + 2 rows

    header = lines[0].split(",")
    assert header == [
        "HoleID", "CoreIntervalFrom", "CoreIntervalTo", "TrayID",
        "Path", "Comments", "Date", "Name", "Site", "MD5",
        "Timestamp", "TrayRows", "TrayLength", "TrayWidth", "TrayCrop"
    ]

    row1 = lines[1].split(",")
    assert row1[0] == "TSD168"
    assert row1[1] == "0"
    assert row1[2] == "1.5"
    assert row1[3] == "1"
    assert row1[7] == "Dimas"
    assert row1[8] == "GOSOWONG"


def test_app_view_lifecycle_and_aliases():
    """Verify that CorePhotoApp instantiates cleanly and navigates through all primary routes and legacy aliases."""
    import app
    application = app.CorePhotoApp()
    try:
        application.update()

        # Primary routes
        routes = ["capture", "review", "browser", "data", "settings"]
        for r in routes:
            application.navigate_to(r)
            application.update()
            assert application.current_view_name in ("capture", "review", "browser", "data", "settings")

        # Legacy aliases
        application.navigate_to("session")
        application.update()
        assert application.current_view_name == "data"
        assert application.views["data"]._active_tab == "session"

        application.navigate_to("transfer")
        application.update()
        assert application.current_view_name == "data"
        assert application.views["data"]._active_tab == "transfer"

        application.navigate_to("validation")
        application.update()
        assert application.current_view_name == "review"

        application.navigate_to("dashboard")
        application.update()
        assert application.current_view_name == "capture"

        application.navigate_to("diagnostics")
        application.update()
        assert application.current_view_name == "settings"

    finally:
        application.destroy()
