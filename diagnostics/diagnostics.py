"""Diagnostics and Crash Recovery Engine (PRD Section 19 & 25).
Provides automated system tests (Camera, Storage, DB, Server) and resumes incomplete captures.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from camera.manager import get_camera_manager
from config.config_manager import get_config
from core.logger import get_logger
from database.models import PhotoStatus
from database.repositories import PhotoRepository
from imaging.processor import ImageProcessor
from storage.manager import StorageManager
from transfer.uploader import TransferUploader

logger = get_logger(__name__)


class DiagnosticsManager:
    """Orchestrates hardware tests, environment diagnostics, and crash recovery."""

    _instance: Optional["DiagnosticsManager"] = None

    def __init__(self):
        self.config = get_config()
        self.storage = StorageManager()
        self.camera = get_camera_manager()

    @classmethod
    def get_instance(cls) -> "DiagnosticsManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def run_all_checks(self) -> Dict[str, Any]:
        """Runs all 5 system diagnostic suites."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "camera": self._check_camera(),
            "storage": self._check_storage(),
            "database": self._check_database(),
            "server": self._check_server(),
            "recovery": self._check_crash_recovery(),
        }
        logger.info("Diagnostics completed: %s", results)
        return results

    def _check_camera(self) -> Dict[str, Any]:
        cams = self.camera.detect_cameras()
        info = self.camera.get_info()
        caps = self.camera.get_capabilities()
        return {
            "detected_devices": cams,
            "connected": self.camera.is_ready(),
            "active_model": info.model if info else "None",
            "active_adapter": info.adapter_name if info else "None",
            "can_capture": caps.can_capture,
            "can_live_view": caps.can_live_view,
            "supported_resolutions": caps.supported_resolutions,
        }

    def _check_storage(self) -> Dict[str, Any]:
        free_mb = self.storage.get_available_space_mb()
        sessions = self.storage.list_sessions()
        return {
            "base_dir": str(self.storage.base_dir),
            "free_space_mb": round(free_mb, 1),
            "free_space_gb": round(free_mb / 1024, 2),
            "sufficient": free_mb >= 500.0,
            "sessions_count": len(sessions),
            "sessions_list": sessions,
        }

    def _check_database(self) -> Dict[str, Any]:
        from core.app_context import get_app_context
        ctx = get_app_context()
        if ctx.session_db:
            try:
                row = ctx.session_db.execute_one("SELECT 1 as test")
                return {"status": "OK", "session_db": str(ctx.session_db.db_path)}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}
        return {"status": "NO_ACTIVE_SESSION_DB"}

    def _check_server(self) -> Dict[str, Any]:
        uploader = TransferUploader()
        server_url = self.config.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
        ok, msg = uploader.check_server_connectivity(server_url)
        return {
            "server_url": server_url,
            "connected": ok,
            "message": msg
        }

    def _check_crash_recovery(self) -> Dict[str, Any]:
        """Detects incomplete captures needing recovery (PRD Section 19)."""
        from core.app_context import get_app_context
        ctx = get_app_context()

        incomplete: List[Dict[str, Any]] = []
        if ctx.photo_repo:
            photos = ctx.photo_repo.get_incomplete_photos()
            for p in photos:
                incomplete.append({
                    "id": p.id,
                    "filename_base": p.filename_base,
                    "raw_path": p.raw_path,
                    "status": p.status
                })

        return {
            "incomplete_captures_found": len(incomplete),
            "items": incomplete
        }

    def resume_incomplete_captures(self) -> int:
        """Resumes processing of RAW files found after a crash without forcing retake (PRD Section 19)."""
        from core.app_context import get_app_context
        ctx = get_app_context()

        if not ctx.photo_repo or not ctx.session_paths or not ctx.active_session:
            return 0

        incomplete = ctx.photo_repo.get_incomplete_photos()
        recovered_count = 0

        processor = ImageProcessor(photo_repo=ctx.photo_repo)
        for photo in incomplete:
            raw_path = Path(photo.raw_path)
            if raw_path.exists():
                try:
                    logger.info("Resuming processing for recovered photo %s", photo.filename_base)
                    raw_bytes = raw_path.read_bytes()
                    # Re-run processing pipeline
                    from database.models import TrayModel
                    tray = TrayModel(
                        session_id=photo.session_id,
                        hole_id=photo.hole_id,
                        tray_id=photo.tray_number,
                        interval_from=photo.interval_from,
                        interval_to=photo.interval_to
                    )
                    processor.process_capture(
                        raw_bytes=raw_bytes,
                        session_paths=ctx.session_paths,
                        session=ctx.active_session,
                        tray=tray,
                        camera_meta={"format": raw_path.suffix.lstrip(".")}
                    )
                    ctx.validate_photo(photo.id)
                    recovered_count += 1
                except Exception as e:
                    logger.error("Failed to recover photo %s: %s", photo.filename_base, e)

        return recovered_count

    def read_recent_logs(self, max_lines: int = 100) -> str:
        """Reads recent lines from the rotating log file for the UI Log Viewer."""
        log_file = self.storage.logs_dir / "corephoto.log"
        if not log_file.exists():
            return "File log belum dibuat."
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                return "".join(lines[-max_lines:])
        except Exception as e:
            return f"Gagal membaca log: {e}"

    def export_report(self, destination_path: Path) -> Path:
        """Exports diagnostic summary as structured JSON."""
        data = self.run_all_checks()
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with open(destination_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return destination_path


def get_diagnostics() -> DiagnosticsManager:
    return DiagnosticsManager.get_instance()
