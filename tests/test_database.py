"""Tests for DatabaseManager and Repositories."""

import pytest
from pathlib import Path
from database.db import DatabaseManager
from database.models import PhotoModel, PhotoStatus, SessionModel, TrayModel
from database.repositories import PhotoRepository, SessionRepository, TrayRepository


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test.db"
    db = DatabaseManager(db_file)
    yield db


def test_session_lifecycle(temp_db):
    s_repo = SessionRepository(temp_db)
    s = s_repo.create(SessionModel(id="S1", site="MINE_A", date="20261005", operator="Dimas"))
    assert s.id == "S1"

    active = s_repo.get_active()
    assert active is not None
    assert active.site == "MINE_A"

    all_sess = s_repo.list_all()
    assert len(all_sess) == 1


def test_tray_and_photo_repositories(temp_db):
    s_repo = SessionRepository(temp_db)
    t_repo = TrayRepository(temp_db)
    p_repo = PhotoRepository(temp_db)

    s_repo.create(SessionModel(id="S2", site="MINE_B", date="20261005", operator="Dimas"))
    tray = t_repo.create(TrayModel(session_id="S2", hole_id="Core02", tray_id="1", interval_from=0.0, interval_to=2.5))
    assert tray.id is not None

    photo = p_repo.create(PhotoModel(
        session_id="S2",
        tray_id=tray.id,
        hole_id="Core02",
        tray_number="1",
        interval_from=0.0,
        interval_to=2.5,
        filename_base="Core02_1_000.00_2.50",
        raw_path="RAW/Core02_1_000.00_2.50.png",
        status=PhotoStatus.CAPTURED.value
    ))
    assert photo.id is not None

    # Test search
    results = p_repo.search(hole_id="Core02")
    assert len(results) == 1
    assert results[0].hole_id == "Core02"

    # Test retake: superseded
    p_repo.mark_as_superseded(photo.id)
    updated = p_repo.get_by_id(photo.id)
    assert updated.status == PhotoStatus.SUPERSEDED.value
    assert updated.is_active == 0
