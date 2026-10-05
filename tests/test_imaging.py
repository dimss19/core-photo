"""Tests for ImageProcessor, Crop, and RawHandler."""

import io
import numpy as np
from PIL import Image
from database.db import DatabaseManager
from database.models import SessionModel, TrayModel
from database.repositories import PhotoRepository, SessionRepository, TrayRepository
from imaging.crop import CropRegion
from imaging.processor import ImageProcessor, format_core_filename
from imaging.raw import RawHandler
from storage.manager import StorageManager


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
