"""Tests for TransferUploader offline tolerance and idempotency."""

from pathlib import Path
from database.models import PhotoModel, PhotoStatus
from transfer.uploader import TransferUploader


def test_transfer_offline_handling(tmp_path):
    uploader = TransferUploader()
    # Test checking unreachable local port (offline scenario)
    ok, msg = uploader.check_server_connectivity("http://127.0.0.1:59999/api/v1")
    assert ok is False
    assert "Server tidak dapat diakses" in msg or "Gagal" in msg


def test_transfer_missing_file_handling():
    uploader = TransferUploader()
    photo = PhotoModel(
        id=999,
        session_id="S_OFFLINE",
        hole_id="Core99",
        tray_number="1",
        interval_from=0.0,
        interval_to=2.6,
        filename_base="Core99_1_000.00_2.60",
        jpg_path="non_existent.jpg",
        status=PhotoStatus.VALID.value
    )
    ok, msg = uploader.upload_photo(photo)
    assert ok is False
    assert "tidak ditemukan" in msg
