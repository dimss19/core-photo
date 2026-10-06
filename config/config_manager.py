"""Centralized Configuration Manager for Core Photo.
Complies with AI Agent Development Rules:
- All configuration managed by Configuration Manager
- No hardcoded paths
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "name": "Core Photo",
        "version": "1.0.0",
        "theme": "dark",
        "color_theme": "blue",
        "language": "id"
    },
    "storage": {
        "base_dir": "CorePhotoData",
        "backup_dir": "CorePhotoData/Backup",
        "logs_dir": "CorePhotoData/Logs",
        "sessions_dir": "CorePhotoData/Sessions"
    },
    "camera": {
        "default_adapter": "webcam",
        "preferred_index": 0,
        "default_resolution": [5184, 3456],
        "resolution_mode": "best_native",
        "fps": 30
    },
    "imaging": {
        "crop_width": 300,
        "crop_height": 200,
        "jpg_quality": 95,
        "thumbnail_size": [150, 100],
        "preserve_raw": True
    },
    "validation": {
        "min_interval_diff": 0.0,
        "require_comments": False,
        "strict_naming": True
    },
    "transfer": {
        "server_url": "http://127.0.0.1:8000/api/v1",
        "api_key": "",
        "timeout_seconds": 30,
        "max_retries": 3,
        "chunk_size_kb": 1024
    },
    "logging": {
        "level": "INFO",
        "file_logging": True,
        "max_file_size_mb": 10,
        "backup_count": 5
    }
}


class ConfigManager:
    """Manages application settings and configuration persistence."""

    _instance: Optional["ConfigManager"] = None

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            # Default to config/settings.json relative to repository root
            base_path = Path(__file__).resolve().parent.parent
            self.config_path = base_path / "config" / "settings.json"
        else:
            self.config_path = Path(config_path)

        self._config: Dict[str, Any] = {}
        self.load()

    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> "ConfigManager":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance

    def load(self) -> Dict[str, Any]:
        """Loads configuration from JSON file or falls back to defaults."""
        if not self.config_path.exists():
            logger.warning(
                "Config file %s not found. Creating with default values.",
                self.config_path
            )
            self._config = DEFAULT_CONFIG.copy()
            self.save()
            return self._config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge loaded with defaults for any missing keys
                self._config = self._deep_merge(DEFAULT_CONFIG.copy(), loaded)
        except Exception as e:
            logger.error("Error reading config %s: %s. Using defaults.", self.config_path, e)
            self._config = DEFAULT_CONFIG.copy()

        return self._config

    def save(self) -> bool:
        """Saves current configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info("Configuration saved successfully to %s", self.config_path)
            return True
        except Exception as e:
            logger.error("Failed to save config to %s: %s", self.config_path, e)
            return False

    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Retrieves a configuration value."""
        sec_dict = self._config.get(section, {})
        if key is None:
            return sec_dict if sec_dict else default
        if isinstance(sec_dict, dict):
            return sec_dict.get(key, default)
        return default

    def set(self, section: str, key: str, value: Any, auto_save: bool = True) -> None:
        """Sets a configuration value and optionally persists it."""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        if auto_save:
            self.save()

    def as_dict(self) -> Dict[str, Any]:
        """Returns deep copy of configuration."""
        import copy
        return copy.deepcopy(self._config)

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge update dict into base dict."""
        for key, val in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(val, dict):
                base[key] = self._deep_merge(base[key], val)
            else:
                base[key] = val
        return base


def get_config() -> ConfigManager:
    """Helper to access global ConfigManager instance."""
    return ConfigManager.get_instance()
