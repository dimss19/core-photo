"""Tests for Validation and Preflight Engine."""

from camera.manager import CameraManager
from database.models import SessionModel
from imaging.crop import CropRegion
from storage.manager import StorageManager
from validation.filename import validate_filename
from validation.interval import validate_interval
from validation.metadata import validate_metadata
from validation.preflight import PreflightChecker


def test_validate_interval():
    ok, err = validate_interval(0.0, 2.6)
    assert ok is True

    bad, err = validate_interval(5.0, 2.0)
    assert bad is False
    assert "tidak boleh lebih kecil" in err


def test_validate_filename():
    ok, _ = validate_filename("Core01_1_000.00_2.60.jpg")
    assert ok is True

    ok, _ = validate_filename("Core01_1_000.00_2.60")
    assert ok is True

    bad, _ = validate_filename("random_name.jpg")
    assert bad is False


def test_validate_metadata():
    valid_meta = {
        "hole_id": "Core01",
        "tray_id": "1",
        "interval_from": 0.0,
        "interval_to": 2.6,
        "date": "20261005",
        "operator": "Dimas",
        "site": "PIT_NORTH",
        "md5_raw": "abcd",
        "md5_jpg": "efgh",
        "timestamp": "2026-10-05T12:00:00",
        "tray_crop": {},
        "camera_model": "Webcam"
    }
    ok, errs = validate_metadata(valid_meta)
    assert ok is True

    invalid_meta = valid_meta.copy()
    invalid_meta["hole_id"] = ""
    ok, errs = validate_metadata(invalid_meta)
    assert ok is False


def test_preflight_checks(tmp_path):
    cm = CameraManager.get_instance()
    cm.connect_camera("webcam", "0")
    sm = StorageManager(base_dir=tmp_path / "CorePhotoData")
    sess = SessionModel(id="S1", site="SITE_A", date="20261005", operator="Dimas")
    crop = CropRegion(x=10, y=10, width=300, height=200)

    # Valid preflight
    res = PreflightChecker.check(
        camera_manager=cm,
        active_session=sess,
        hole_id="Core01",
        tray_id="1",
        interval_from=0.0,
        interval_to=2.6,
        storage_manager=sm,
        crop_region=crop
    )
    assert res.is_ready is True

    # Invalid preflight (interval To < From)
    res_bad = PreflightChecker.check(
        camera_manager=cm,
        active_session=sess,
        hole_id="Core01",
        tray_id="1",
        interval_from=5.0,
        interval_to=2.0,
        storage_manager=sm,
        crop_region=crop
    )
    assert res_bad.is_ready is False
    cm.disconnect_camera()
