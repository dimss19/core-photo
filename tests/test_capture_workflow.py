"""Tests for Capture and Review/Retake Workflow (PRD Section 14)."""

import pytest
from core.app_context import get_app_context
from database.models import PhotoStatus, SessionModel, TrayModel
from imaging.crop import CropRegion
from storage.manager import StorageManager


def test_capture_and_retake_workflow(tmp_path):
    ctx = get_app_context()
    ctx.storage_manager = StorageManager(base_dir=tmp_path / "CoreData")
    paths = ctx.storage_manager.create_session_storage("SITE_WORKFLOW", "20261010")

    from database.db import DatabaseManager
    from database.repositories import (
        EventRepository,
        PhotoRepository,
        SessionRepository,
        TransferRepository,
        TrayRepository,
        ValidationRepository,
    )
    from imaging.processor import ImageProcessor
    from validation.runner import ValidationRunner

    db = DatabaseManager(paths.db_path)
    ctx.session_db = db
    ctx.session_paths = paths
    ctx.session_repo = SessionRepository(db)
    ctx.tray_repo = TrayRepository(db)
    ctx.photo_repo = PhotoRepository(db)
    ctx.transfer_repo = TransferRepository(db)
    ctx.validation_repo = ValidationRepository(db)
    ctx.event_repo = EventRepository(db)
    ctx.image_processor = ImageProcessor(photo_repo=ctx.photo_repo)
    ctx.validation_runner = ValidationRunner(
        photo_repo=ctx.photo_repo,
        validation_repo=ctx.validation_repo,
    )

    sess = ctx.session_repo.create(SessionModel(
        id="S_WORKFLOW",
        site="SITE_WORKFLOW",
        date="20261010",
        operator="Tech1"
    ))
    ctx.active_session = sess
    ctx.camera_manager.connect_camera(adapter_name="webcam", device_id="sim")

    # 1. Execute Capture
    photo = ctx.execute_capture(
        hole_id="DH_01",
        tray_id="1",
        interval_from=0.0,
        interval_to=2.0,
        crop_region=CropRegion(x=10, y=10, width=400, height=300),
        comments="First capture test"
    )

    assert photo is not None
    assert photo.status == PhotoStatus.PROCESSED.value
    assert photo.is_active == 1
    assert ctx.last_photo.id == photo.id

    # 2. Test Retake Action (PRD Section 14)
    ctx.retake_current()

    # Verify photo marked superseded
    updated = ctx.photo_repo.get_by_id(photo.id)
    assert updated.status == PhotoStatus.SUPERSEDED.value
    assert updated.is_active == 0

    # 3. New capture after retake
    photo2 = ctx.execute_capture(
        hole_id="DH_01",
        tray_id="1",
        interval_from=0.0,
        interval_to=2.0,
        crop_region=CropRegion(x=10, y=10, width=400, height=300),
        comments="Retake capture"
    )

    assert photo2.id != photo.id
    assert photo2.status == PhotoStatus.PROCESSED.value
    assert photo2.is_active == 1

    # Cleanup
    ctx.close_active_session()
