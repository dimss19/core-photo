"""Tests for Review Screen and Auto-Transfer to Server Folder (PRD Section 17 & 21)."""

import pytest
from pathlib import Path
from core.app_context import get_app_context
from database.db import DatabaseManager
from database.models import PhotoModel, PhotoStatus, SessionModel, TransferStatus, TrayModel
from database.repositories import (
    EventRepository,
    PhotoRepository,
    SessionRepository,
    TransferRepository,
    TrayRepository,
    ValidationRepository,
)
from imaging.processor import ImageProcessor
from storage.manager import StorageManager
from validation.runner import ValidationRunner


def test_review_auto_transfer_to_server_folder(tmp_path):
    ctx = get_app_context()
    ctx.storage_manager = StorageManager(base_dir=tmp_path / "CoreData")
    server_dir = tmp_path / "ServerShare"
    server_dir.mkdir(parents=True, exist_ok=True)

    paths = ctx.storage_manager.create_session_storage("SITE_REV_TEST", "20261011")
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
        id="S_REV_TEST",
        site="SITE_REV_TEST",
        date="20261011",
        operator="Geologist1"
    ))
    ctx.active_session = sess

    # Configure server folder in config
    ctx.config.set("transfer", "server_folder", str(server_dir))
    ctx.config.set("storage", "server_folder", str(server_dir))

    # Connect camera simulator and capture 2 photos
    ctx.camera_manager.connect_camera(adapter_name="webcam", device_id="sim")
    photo1 = ctx.execute_capture(
        hole_id="DH_REV",
        tray_id="1",
        interval_from=0.0,
        interval_to=2.0,
        comments="Tray 1"
    )
    photo2 = ctx.execute_capture(
        hole_id="DH_REV",
        tray_id="2",
        interval_from=2.0,
        interval_to=4.0,
        comments="Tray 2"
    )

    assert photo1.id is not None
    assert photo2.id is not None

    # 1. Test transfer single photo via AppContext
    ok, msg = ctx.transfer_photo_to_server_folder(photo1)
    assert ok is True
    assert "berhasil" in msg.lower() or "transferred" in msg.lower()

    # Verify transferred files on server folder
    dest_sess = server_dir / paths.session_dir.name
    assert dest_sess.exists()
    assert (dest_sess / "jpg" / Path(photo1.jpg_path).name).exists()
    assert (dest_sess / f"DH_REV.csv").exists()

    transfer_rec = ctx.transfer_repo.get_by_photo_id(photo1.id)
    assert transfer_rec is not None
    assert transfer_rec.status == TransferStatus.SUCCESS.value

    # 2. Test sync entire session to server folder
    sync_ok, sync_msg, count = ctx.sync_session_to_server_folder()
    assert sync_ok is True
    assert count >= 1
    assert (dest_sess / "jpg" / Path(photo2.jpg_path).name).exists()

    transfer_rec2 = ctx.transfer_repo.get_by_photo_id(photo2.id)
    assert transfer_rec2 is not None
    assert transfer_rec2.status == TransferStatus.SUCCESS.value

    # 3. Test ReviewView helper methods without GUI display loop
    from ui.review import ReviewView
    import customtkinter as ctk

    root = ctk.CTk()
    navigated_route = []
    advanced_trays = []

    review_view = ReviewView(
        root,
        navigate_fn=lambda r: navigated_route.append(r),
        advance_tray_fn=lambda: advanced_trays.append(True)
    )
    review_view.refresh()

    # Verify photos loaded in review
    assert len(review_view._photos) >= 2
    assert review_view._current_index >= 0

    # Test _on_save_next on ReviewView
    initial_idx = review_view._current_index
    review_view._on_save_next()

    # Check feedback label
    assert "approved" in review_view.lbl_decision_feedback.cget("text").lower()

    # Cleanup
    root.destroy()
    ctx.close_active_session()
