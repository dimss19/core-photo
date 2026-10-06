"""Tests for StorageManager and session path handling."""

import pytest
import shutil
from pathlib import Path
from storage.manager import StorageManager


@pytest.fixture
def temp_storage(tmp_path):
    sm = StorageManager(base_dir=tmp_path / "CorePhotoData")
    yield sm
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_storage_structure_creation(temp_storage):
    assert temp_storage.base_dir.exists()
    assert temp_storage.sessions_dir.exists()
    assert temp_storage.logs_dir.exists()
    assert temp_storage.config_dir.exists()
    assert temp_storage.backup_dir.exists()


def test_sanitize_identifier(temp_storage):
    assert temp_storage.sanitize_identifier("SITE/NORTH\\A:1*2?3\"4<5>6|7") == "SITE_NORTH_A_1_2_3_4_5_6_7"
    assert temp_storage.sanitize_identifier("../../../etc/passwd") == "etc_passwd"
    assert temp_storage.sanitize_identifier("") == "unnamed"


def test_create_session_storage(temp_storage):
    paths = temp_storage.create_session_storage("PIT1", "20261005")
    assert paths.session_dir.exists()
    assert paths.raw_dir.exists()
    assert paths.jpg_dir.exists()
    assert paths.thumbnail_dir.exists()
    assert paths.raw_dir.name == "raw"
    assert paths.jpg_dir.name == "jpg"
    assert paths.thumbnail_dir.name == "thumbs"
    assert "PIT1_20261005" in paths.session_dir.name


def test_storage_space_check(temp_storage):
    free_mb = temp_storage.get_available_space_mb()
    assert free_mb > 0
    assert temp_storage.is_storage_sufficient(min_mb=1.0) is True


def test_delete_session_storage(temp_storage):
    paths = temp_storage.create_session_storage("PIT_DEL", "20261006")
    folder_name = paths.session_dir.name
    assert folder_name in temp_storage.list_sessions()

    # Delete
    deleted = temp_storage.delete_session(folder_name)
    assert deleted is True
    assert folder_name not in temp_storage.list_sessions()
    assert not paths.session_dir.exists()

