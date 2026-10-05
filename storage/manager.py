"""Storage Manager for Core Photo application.
Strictly manages all file paths and directories without hardcoded paths.
Includes security checks against path traversal and disk space verification.
"""

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from config.config_manager import get_config
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SessionPaths:
    """Paths associated with a single photography session."""
    session_dir: Path
    raw_dir: Path
    jpg_dir: Path
    thumbnail_dir: Path
    db_path: Path

    def exists(self) -> bool:
        return self.session_dir.exists()


class StorageManager:
    """Central manager for disk paths, session directories, and disk capacity checks."""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            config = get_config()
            cfg_base = config.get("storage", "base_dir", "CorePhotoData")
            self.base_dir = Path(cfg_base).resolve()
        else:
            self.base_dir = Path(base_dir).resolve()

        self.sessions_dir = self.base_dir / "Sessions"
        self.logs_dir = self.base_dir / "Logs"
        self.config_dir = self.base_dir / "Config"
        self.backup_dir = self.base_dir / "Backup"

        self._ensure_base_structure()

    def _ensure_base_structure(self) -> None:
        """Creates the root directory structure."""
        for folder in [self.base_dir, self.sessions_dir, self.logs_dir, self.config_dir, self.backup_dir]:
            folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_identifier(value: str) -> str:
        """Sanitizes user input to prevent directory traversal and invalid path characters.
        Allows alphanumeric, dash, and underscore.
        """
        if not value:
            return "unnamed"
        # Strip path traversal sequences like ../ or ..\
        clean = re.sub(r'[\/\\:\*\?"<>\|\.]+', '_', value.strip())
        clean = re.sub(r'_+', '_', clean).strip('_')
        return clean or "unnamed"

    def get_session_paths(self, folder_name: str) -> SessionPaths:
        """Resolves session paths while strictly verifying sandbox directory boundary."""
        safe_name = self.sanitize_identifier(folder_name)
        session_path = (self.sessions_dir / safe_name).resolve()

        # Security check: Ensure session_path is within self.sessions_dir
        if not str(session_path).startswith(str(self.sessions_dir)):
            raise ValueError(f"Path traversal detected: {folder_name}")

        # Prefer lowercase existing folders or defaults matching legacy structure:
        #   session_dir/
        #     ├── jpg/
        #     ├── raw/
        #     ├── thumbs/
        #     └── <HoleID>.csv
        return SessionPaths(
            session_dir=session_path,
            raw_dir=session_path / "raw",
            jpg_dir=session_path / "jpg",
            thumbnail_dir=session_path / "thumbs",
            db_path=session_path / "session.db"
        )

    def create_session_storage(
        self,
        site: str,
        date_str: str,
        suffix: Optional[str] = None
    ) -> SessionPaths:
        """Creates session directories:
        SITE_YYYYMMDD/
          ├── jpg/
          ├── raw/
          ├── thumbs/
          └── session.db
        If directory exists, appends unique suffix to prevent overwriting existing data.
        """
        safe_site = self.sanitize_identifier(site)
        safe_date = self.sanitize_identifier(date_str)
        base_folder = f"{safe_site}_{safe_date}"

        folder_name = base_folder
        if suffix:
            safe_suffix = self.sanitize_identifier(suffix)
            folder_name = f"{base_folder}_{safe_suffix}"

        counter = 1
        paths = self.get_session_paths(folder_name)
        while paths.session_dir.exists() and not suffix:
            # If session exists without explicit suffix, create an incremented one
            folder_name = f"{base_folder}_{counter:02d}"
            paths = self.get_session_paths(folder_name)
            counter += 1

        paths.session_dir.mkdir(parents=True, exist_ok=True)
        paths.raw_dir.mkdir(parents=True, exist_ok=True)
        paths.jpg_dir.mkdir(parents=True, exist_ok=True)
        paths.thumbnail_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Session storage created at: %s", paths.session_dir)
        return paths

    def list_sessions(self) -> List[str]:
        """Lists all existing session folder names."""
        if not self.sessions_dir.exists():
            return []
        return [
            item.name for item in self.sessions_dir.iterdir()
            if item.is_dir()
        ]

    def get_available_space_mb(self, target_path: Optional[Path] = None) -> float:
        """Returns available disk space in megabytes for the target directory."""
        path_to_check = target_path if target_path else self.base_dir
        try:
            usage = shutil.disk_usage(path_to_check)
            return usage.free / (1024 * 1024)
        except Exception as e:
            logger.error("Failed to check disk usage for %s: %s", path_to_check, e)
            return 0.0

    def is_storage_sufficient(self, min_mb: float = 500.0, target_path: Optional[Path] = None) -> bool:
        """Checks if available storage exceeds minimum required threshold."""
        free_mb = self.get_available_space_mb(target_path)
        return free_mb >= min_mb
