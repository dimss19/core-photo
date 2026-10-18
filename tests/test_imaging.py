"""Tests for ImageProcessor, Crop, and RawHandler."""

import io
import numpy as np
from PIL import Image
from database.db import DatabaseManager
from database.models import SessionModel, TrayModel
from database.repositories import PhotoRepository, SessionRepository, TrayRepository, ValidationRepository
from imaging.crop import CropRegion
from imaging.processor import ImageProcessor, format_core_filename
from imaging.raw import RawHandler
from storage.manager import StorageManager
from validation.runner import ValidationRunner


def test_filename_formatting():
    name = format_core_filename("Core01", "1", 0.0, 2.6)
    assert name == "Core01_1_000.00_2.60"


def test_imaging_pipeline(tmp_path):
    sm = StorageManager(base_dir=tmp_path / "Data")
    paths = sm.create_session_storage("SITE_TEST", "20261005")
    db = DatabaseManager(paths.db_path)
    s_repo = SessionRepository(db)
    t_repo = TrayRepository(db)
    p_repo = PhotoRepository(db)

    sess = s_repo.create(SessionModel(id="S_TEST", site="SITE_TEST", date="20261005", operator="Dimas"))
    tray = t_repo.create(TrayModel(session_id="S_TEST", hole_id="Core01", tray_id="1", interval_from=0.0, interval_to=2.6))

    # Generate synthetic image
    arr = np.zeros((480, 640, 3), dtype=np.uint8)
    arr[100:300, 100:500] = [120, 100, 80]
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    processor = ImageProcessor(photo_repo=p_repo)
    photo = processor.process_capture(
        raw_bytes=raw_bytes,
        session_paths=paths,
        session=sess,
        tray=tray,
        crop_region=CropRegion(x=50, y=50, width=500, height=350),
        camera_meta={"format": "png", "camera_model": "TestCam"}
    )

    assert photo.status == "PROCESSED"
    assert (paths.raw_dir / f"{photo.filename_base}.png").exists()
    assert (paths.jpg_dir / f"{photo.filename_base}.jpg").exists()
    assert (paths.thumbnail_dir / f"{photo.filename_base}_thumb.jpg").exists()
    assert (paths.jpg_dir / f"{photo.filename_base}.json").exists()
    assert len(photo.md5_raw) == 32
    assert len(photo.md5_jpg) == 32
    assert photo.timestamp != ""

    # Test CSV report export
    csv_file = paths.session_dir / "Core01.csv"
    ImageProcessor.export_csv_report(sess, [photo], csv_file)
    assert csv_file.exists()
    lines = csv_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    header = lines[0].split(",")
    assert len(header) == 15
    assert header[0] == "HoleID"
    assert header[-1] == "TrayCrop"
    row = lines[1].split(",")
    assert row[0] == "Core01"
    assert row[1] == "0"
    assert row[2] == "2.6"


def test_max_photo_size_enforcement(tmp_path):
    """Verifies that ImageProcessor enforces the configured maximum photo size (e.g. 10MB or custom limit)."""
    sm = StorageManager(base_dir=tmp_path / "Data")
    paths = sm.create_session_storage("SITE_LIMIT", "20261014")
    db = DatabaseManager(paths.db_path)
    s_repo = SessionRepository(db)
    t_repo = TrayRepository(db)
    p_repo = PhotoRepository(db)
    v_repo = ValidationRepository(db)

    sess = s_repo.create(SessionModel(id="S_LIMIT", site="SITE_LIMIT", date="20261014", operator="Operator"))
    tray = t_repo.create(TrayModel(session_id="S_LIMIT", hole_id="BH_01", tray_id="1", interval_from=0.0, interval_to=1.5))

    # Generate high-entropy / high-resolution image
    rng = np.random.default_rng(42)
    noise_arr = rng.integers(0, 256, (1200, 1600, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(noise_arr).save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    processor = ImageProcessor(photo_repo=p_repo)

    # 1. Test user default of 10.0 MB
    assert processor.config.get("imaging", "max_photo_size_mb") == 10.0

    # 2. Test strict enforcement with tight limit (0.15 MB = 153.6 KB)
    processor.config.set("imaging", "max_photo_size_mb", 0.15)
    max_bytes = int(0.15 * 1024 * 1024)

    photo = processor.process_capture(
        raw_bytes=raw_bytes,
        session_paths=paths,
        session=sess,
        tray=tray,
        crop_region=CropRegion(x=0, y=0, width=1600, height=1200),
        camera_meta={"format": "png", "camera_model": "DSLR_Test"}
    )

    jpg_file = paths.jpg_dir / f"{photo.filename_base}.jpg"
    assert jpg_file.exists()
    assert jpg_file.stat().st_size <= max_bytes, f"File size {jpg_file.stat().st_size} exceeds {max_bytes}"

    # 3. Test validation runner validates max file size
    v_runner = ValidationRunner(photo_repo=p_repo, validation_repo=v_repo, config=processor.config)
    is_valid, errors = v_runner.validate_photo(photo.id)
    assert is_valid, f"Validation failed: {errors}"

    # Reset config back to default 10.0
    processor.config.set("imaging", "max_photo_size_mb", 10.0)
    processor.config.save()

