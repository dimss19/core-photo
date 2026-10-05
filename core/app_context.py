"""Application Context & Service Layer.
Enforces separation of concerns: UI views only communicate through AppContext.
Ensures UI never directly touches raw OpenCV, direct SQL, or unmanaged paths.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from camera.capabilities import CameraCapabilities
from camera.interface import CameraInfo, CaptureResult
from camera.manager import CameraManager, get_camera_manager
from config.config_manager import ConfigManager, get_config
from core.logger import get_logger
from database.db import DatabaseManager
from database.models import (
    ApplicationEventModel,
    PhotoModel,
    PhotoStatus,
    SessionModel,
    SessionStatus,
    TransferModel,
    TransferStatus,
    TrayModel,
    ValidationResultModel,
)
from database.repositories import (
    EventRepository,
    PhotoRepository,
    SessionRepository,
    TransferRepository,
    TrayRepository,
    ValidationRepository,
)
from imaging.crop import CropRegion
from imaging.processor import ImageProcessor
from storage.manager import SessionPaths, StorageManager
from validation.preflight import PreflightChecker, PreflightResult
from validation.runner import ValidationRunner

logger = get_logger(__name__)


class AppContext:
    """Singleton context coordinating application state, services, and repositories."""

    _instance: Optional["AppContext"] = None

    def __init__(self):
        self.config_manager = get_config()
        self.storage_manager = StorageManager()
        self.camera_manager = get_camera_manager()

        self.active_session: Optional[SessionModel] = None
        self.session_paths: Optional[SessionPaths] = None
        self.session_db: Optional[DatabaseManager] = None

        # Repositories (bound when session is active)
        self.session_repo: Optional[SessionRepository] = None
        self.tray_repo: Optional[TrayRepository] = None
        self.photo_repo: Optional[PhotoRepository] = None
        self.transfer_repo: Optional[TransferRepository] = None
        self.validation_repo: Optional[ValidationRepository] = None
        self.event_repo: Optional[EventRepository] = None

        self.image_processor: Optional[ImageProcessor] = None
        self.validation_runner: Optional[ValidationRunner] = None

        self.current_tray: Optional[TrayModel] = None
        self.last_photo: Optional[PhotoModel] = None

        # Frame callback subscribers (e.g. Capture screen)
        self._frame_subscribers: List[Callable[[np.ndarray], None]] = []

        # Attempt to resume any previously active session on startup (PRD Section 10 & 19)
        self._auto_restore_session()

    @property
    def config(self) -> ConfigManager:
        return self.config_manager

    @classmethod
    def get_instance(cls) -> "AppContext":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _auto_restore_session(self) -> None:
        """Checks for existing sessions and restores the latest active session."""
        try:
            sessions = self.storage_manager.list_sessions()
            if not sessions:
                return

            # Sort descending to find most recent
            sessions.sort(reverse=True)
            for folder in sessions:
                try:
                    paths = self.storage_manager.get_session_paths(folder)
                    if paths.db_path.exists():
                        db = DatabaseManager(paths.db_path)
                        s_repo = SessionRepository(db)
                        active = s_repo.get_active()
                        if active:
                            self._bind_session(active, paths, db)
                            logger.info("Auto-restored active session: %s", active.id)
                            break
                except Exception as e:
                    logger.debug("Could not inspect session %s: %s", folder, e)
        except Exception as e:
            logger.error("Error during session auto-restore: %s", e)

    def _bind_session(self, session: SessionModel, paths: SessionPaths, db: DatabaseManager) -> None:
        """Binds active session and its repositories."""
        self.active_session = session
        self.session_paths = paths
        self.session_db = db

        self.session_repo = SessionRepository(db)
        self.tray_repo = TrayRepository(db)
        self.photo_repo = PhotoRepository(db)
        self.transfer_repo = TransferRepository(db)
        self.validation_repo = ValidationRepository(db)
        self.event_repo = EventRepository(db)

        self.image_processor = ImageProcessor(photo_repo=self.photo_repo)
        self.validation_runner = ValidationRunner(
            photo_repo=self.photo_repo,
            validation_repo=self.validation_repo
        )

        # Log session activation event
        self.event_repo.log_event(
            session_id=session.id,
            event_type="SESSION_ACTIVE",
            description=f"Session {session.id} bound (Site: {session.site}, Operator: {session.operator})"
        )

    def create_new_session(self, site: str, operator: str, date_str: str) -> SessionModel:
        """Initializes a new session storage and database."""
        paths = self.storage_manager.create_session_storage(site, date_str)
        db = DatabaseManager(paths.db_path)
        s_repo = SessionRepository(db)

        session_id = f"{paths.session_dir.name}"
        session = SessionModel(
            id=session_id,
            site=site,
            date=date_str,
            operator=operator,
            status=SessionStatus.ACTIVE.value
        )
        session = s_repo.create(session)
        self._bind_session(session, paths, db)
        return session

    def create_session(self, site: str, operator: str, date: str = "", date_str: str = "") -> SessionModel:
        """Alias for create_new_session."""
        from datetime import datetime
        effective_date = date_str or date or datetime.now().strftime("%Y%m%d")
        return self.create_new_session(site=site, operator=operator, date_str=effective_date)

    def open_session(self, folder_name: str) -> Optional[SessionModel]:
        """Loads an existing session from storage."""
        paths = self.storage_manager.get_session_paths(folder_name)
        if not paths.db_path.exists():
            return None

        db = DatabaseManager(paths.db_path)
        s_repo = SessionRepository(db)
        session = s_repo.get_active() or (s_repo.list_all()[0] if s_repo.list_all() else None)
        if session:
            self._bind_session(session, paths, db)
        return session

    def list_available_sessions(self) -> List[str]:
        return self.storage_manager.list_sessions()

    # Preflight & Capture
    def run_preflight(
        self,
        hole_id: str,
        tray_id: str,
        interval_from: float,
        interval_to: float,
        crop_region: Optional[CropRegion] = None
    ) -> PreflightResult:
        return PreflightChecker.check(
            camera_manager=self.camera_manager,
            active_session=self.active_session,
            hole_id=hole_id,
            tray_id=tray_id,
            interval_from=interval_from,
            interval_to=interval_to,
            storage_manager=self.storage_manager,
            crop_region=crop_region
        )

    def execute_capture(
        self,
        hole_id: str,
        tray_id: str,
        interval_from: float,
        interval_to: float,
        crop_region: Optional[CropRegion] = None,
        comments: str = "",
        tray_rows: int = 1,
        tray_length: float = 0.0,
        tray_width: float = 0.0
    ) -> PhotoModel:
        """Executes hardware capture and processing."""
        if not self.active_session or not self.session_paths:
            raise RuntimeError("Tidak ada sesi aktif. Buat atau buka sesi terlebih dahulu.")

        if not self.camera_manager.is_ready():
            raise RuntimeError("Kamera tidak siap untuk capture.")

        # Ensure tray record exists
        tray = None
        if self.tray_repo:
            tray = self.tray_repo.get_by_hole_and_tray(self.active_session.id, hole_id, tray_id)
            if not tray:
                tray = self.tray_repo.create(TrayModel(
                    session_id=self.active_session.id,
                    hole_id=hole_id,
                    tray_id=tray_id,
                    interval_from=interval_from,
                    interval_to=interval_to,
                    tray_rows=tray_rows,
                    tray_length=tray_length,
                    tray_width=tray_width,
                    comments=comments
                ))

        capture_res = self.camera_manager.capture()
        meta = capture_res.metadata.copy()
        meta["format"] = capture_res.format

        assert self.image_processor is not None
        photo = self.image_processor.process_capture(
            raw_bytes=capture_res.raw_bytes,
            session_paths=self.session_paths,
            session=self.active_session,
            tray=tray or TrayModel(session_id=self.active_session.id, hole_id=hole_id, tray_id=tray_id, interval_from=interval_from, interval_to=interval_to),
            crop_region=crop_region,
            camera_meta=meta
        )

        self.last_photo = photo
        return photo

    def retake_current(self) -> None:
        """Marks current photo as superseded for retake (PRD Section 14)."""
        if self.last_photo and self.last_photo.id and self.photo_repo:
            self.photo_repo.mark_as_superseded(self.last_photo.id)
            if self.event_repo and self.active_session:
                self.event_repo.log_event(
                    session_id=self.active_session.id,
                    event_type="RETAKE",
                    description=f"Photo {self.last_photo.id} marked as SUPERSEDED for retake"
                )

    def validate_photo(self, photo_id: int) -> Tuple[bool, List[str]]:
        if not self.validation_runner:
            return False, ["Validation runner not initialized"]
        return self.validation_runner.validate_photo(photo_id)

    # Live View Distribution
    def subscribe_live_frames(self, callback: Callable[[np.ndarray], None]) -> None:
        if callback not in self._frame_subscribers:
            self._frame_subscribers.append(callback)
            if len(self._frame_subscribers) == 1:
                self.camera_manager.start_live_view(self._on_live_frame)

    def unsubscribe_live_frames(self, callback: Callable[[np.ndarray], None]) -> None:
        if callback in self._frame_subscribers:
            self._frame_subscribers.remove(callback)
            if len(self._frame_subscribers) == 0:
                self.camera_manager.stop_live_view()

    def _on_live_frame(self, frame_rgb: np.ndarray) -> None:
        for cb in list(self._frame_subscribers):
            try:
                cb(frame_rgb)
            except Exception as e:
                logger.debug("Subscriber frame callback error: %s", e)


def get_app_context() -> AppContext:
    return AppContext.get_instance()
