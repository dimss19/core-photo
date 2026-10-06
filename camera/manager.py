"""Camera Manager (PRD Section 7.1, 8 & 32).
Orchestrates camera discovery, connection, lifecycle, and decoupling UI from SDKs.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from core.logger import get_logger
from .adapters.webcam import WebcamAdapter
from .adapters.hot_folder import HotFolderAdapter
from .adapters.direct_usb import DirectUsbAdapter
from .capabilities import CameraCapabilities
from .interface import (
    AbstractCameraAdapter,
    CameraInfo,
    CameraState,
    CaptureResult,
)

logger = get_logger(__name__)


class CameraManager:
    """Central camera subsystem manager."""

    _instance: Optional["CameraManager"] = None

    def __init__(self):
        self._active_adapter: Optional[AbstractCameraAdapter] = None
        self._registered_adapters: Dict[str, type] = {
            "webcam": WebcamAdapter,
            "hot_folder": HotFolderAdapter,
            "hotfolder": HotFolderAdapter,
            "direct_usb": DirectUsbAdapter,
            "direct": DirectUsbAdapter,
            "ptp": DirectUsbAdapter,
        }

    @classmethod
    def get_instance(cls) -> "CameraManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_adapter(self, name: str, adapter_cls: type) -> None:
        """Enables future camera vendor adapters to plug in without modifying core (PRD Section 7.4)."""
        self._registered_adapters[name.lower()] = adapter_cls
        logger.info("Registered camera adapter plugin: %s", name)

    def detect_cameras(self) -> List[Dict[str, Any]]:
        """Scans system for available camera devices (PRD Section 8)."""
        available: List[Dict[str, Any]] = []

        # 1. Direct USB Camera (Native Windows WIA & PTP - 0 DLLs, 0 Software)
        available.append({
            "id": "direct_usb",
            "name": "Direct USB DSLR (Canon / Nikon / Sony — No Software Needed)",
            "adapter": "direct_usb",
            "supported": True,
            "status": "Ready"
        })

        # 2. Universal Hot-Folder Ingest (Supports all DSLRs: Canon, Nikon, Sony, Fuji, etc.)
        available.append({
            "id": "hot_folder",
            "name": "Universal Hot-Folder Ingest (Tethered / Wi-Fi)",
            "adapter": "hot_folder",
            "supported": True,
            "status": "Ready"
        })

        # 2. Check default webcam / UVC DirectShow adapter indices
        try:
            import cv2
            for idx in range(3):
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap.isOpened():
                    available.append({
                        "id": str(idx),
                        "name": f"USB Video Camera {idx}",
                        "adapter": "webcam",
                        "supported": True,
                        "status": "Ready"
                    })
                    cap.release()
        except Exception as e:
            logger.debug("Hardware camera scan exception: %s", e)

        # 3. Always include technical simulation feed
        available.append({
            "id": "sim",
            "name": "Core Tray Sample Feed (Canon EOS 60D)",
            "adapter": "webcam",
            "supported": True,
            "status": "Ready"
        })

        return available

    def connect_camera(self, adapter_name: str = "webcam", device_id: Any = "0") -> bool:
        """Connects to specified camera using appropriate adapter."""
        if self._active_adapter:
            self._active_adapter.disconnect()

        norm_name = str(adapter_name).lower()
        norm_dev = str(device_id).lower()
        if norm_name in ("hot_folder", "hotfolder") or norm_dev in ("hot_folder", "hotfolder"):
            adapter_name = "hot_folder"
        elif norm_name in ("direct_usb", "direct", "ptp") or norm_dev in ("direct_usb", "direct", "ptp"):
            adapter_name = "direct_usb"

        adapter_cls = self._registered_adapters.get(adapter_name.lower(), WebcamAdapter)
        adapter = adapter_cls()
        success = adapter.connect(device_id)
        if success:
            self._active_adapter = adapter
            # Apply configured camera resolution
            try:
                from config.config_manager import get_config
                cfg = get_config()
                res = cfg.get("camera", "default_resolution", [5184, 3456])
                res_mode = cfg.get("camera", "resolution_mode", "best_native")
                if isinstance(res, (list, tuple)) and len(res) == 2:
                    adapter.set_setting("resolution", (int(res[0]), int(res[1])))
                adapter.set_setting("resolution_mode", res_mode)
            except Exception as ex:
                logger.debug("Could not apply initial resolution config: %s", ex)

            info = adapter.get_info()
            logger.info("Connected to camera: %s (State: %s)", info.model, adapter.get_state().value)
            return True
        logger.error("Failed to connect camera adapter %s with device %s", adapter_name, device_id)
        return False

    def disconnect_camera(self) -> bool:
        if self._active_adapter:
            res = self._active_adapter.disconnect()
            self._active_adapter = None
            return res
        return True

    def get_status_summary(self) -> str:
        """Human-readable status for UI (PRD Section 5.2):
        'Camera: Canon EOS R7 — Connected'
        """
        if not self._active_adapter:
            return "Camera: None — Disconnected"

        state = self._active_adapter.get_state()
        info = self._active_adapter.get_info()
        if state in (CameraState.READY, CameraState.STREAMING, CameraState.CAPTURING):
            return f"Camera: {info.model} — Connected"
        if state == CameraState.CONNECTING:
            return f"Camera: {info.model} — Connecting..."
        if state == CameraState.ERROR:
            return f"Camera: {info.model} — Error"
        return "Camera: Disconnected"

    def is_ready(self) -> bool:
        if not self._active_adapter:
            return False
        return self._active_adapter.get_state() in (
            CameraState.READY,
            CameraState.STREAMING,
            CameraState.CAPTURING,
        )

    def get_capabilities(self) -> CameraCapabilities:
        if not self._active_adapter:
            return CameraCapabilities(can_capture=False, can_live_view=False)
        return self._active_adapter.get_capabilities()

    def get_info(self) -> Optional[CameraInfo]:
        if not self._active_adapter:
            return None
        return self._active_adapter.get_info()

    def start_live_view(self, callback: Optional[Callable[[np.ndarray], None]] = None) -> bool:
        if not self._active_adapter:
            return False
        return self._active_adapter.start_live_view(callback)

    def stop_live_view(self) -> bool:
        if not self._active_adapter:
            return False
        return self._active_adapter.stop_live_view()

    def get_live_frame(self) -> Optional[np.ndarray]:
        if not self._active_adapter:
            return None
        return self._active_adapter.get_live_frame()

    def capture(self) -> CaptureResult:
        if not self._active_adapter:
            raise RuntimeError("No camera connected. Cannot capture.")
        return self._active_adapter.capture()

    def get_current_resolution(self) -> Tuple[int, int]:
        """Returns the active resolution tuple (width, height)."""
        if self._active_adapter:
            res = self._active_adapter.get_setting("resolution")
            if isinstance(res, (list, tuple)) and len(res) == 2:
                return (int(res[0]), int(res[1]))
        try:
            from config.config_manager import get_config
            cfg = get_config()
            c_res = cfg.get("camera", "default_resolution", [5184, 3456])
            return (int(c_res[0]), int(c_res[1]))
        except Exception:
            return (5184, 3456)

    def get_resolution_mode(self) -> str:
        """Returns active resolution mode (e.g. 'best_native', 'custom')."""
        if self._active_adapter:
            mode = self._active_adapter.get_setting("resolution_mode")
            if mode:
                return str(mode)
        try:
            from config.config_manager import get_config
            return str(get_config().get("camera", "resolution_mode", "best_native"))
        except Exception:
            return "best_native"

    def set_resolution(self, width: int, height: int, mode: str = "custom") -> bool:
        """Configures capture resolution and persists to application settings."""
        success = True
        if self._active_adapter:
            self._active_adapter.set_setting("resolution", (width, height))
            self._active_adapter.set_setting("resolution_mode", mode)
        try:
            from config.config_manager import get_config
            cfg = get_config()
            cfg.set("camera", "default_resolution", [width, height])
            cfg.set("camera", "resolution_mode", mode)
            logger.info("Camera resolution configured: %dx%d (Mode: %s)", width, height, mode)
        except Exception as e:
            logger.error("Failed saving resolution config: %s", e)
            success = False
        return success

    def get_supported_resolutions(self) -> List[Tuple[int, int]]:
        """Returns list of supported resolutions for connected camera."""
        caps = self.get_capabilities()
        if caps and caps.supported_resolutions:
            return caps.supported_resolutions
        return [
            (6000, 4000),
            (5184, 3456),
            (4000, 3000),
            (3840, 2160),
            (1920, 1080),
            (1280, 720),
        ]


def get_camera_manager() -> CameraManager:
    return CameraManager.get_instance()
