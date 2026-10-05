"""Camera Manager (PRD Section 7.1, 8 & 32).
Orchestrates camera discovery, connection, lifecycle, and decoupling UI from SDKs.
"""

from typing import Any, Callable, Dict, List, Optional
import numpy as np

from core.logger import get_logger
from .adapters.webcam import WebcamAdapter
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

        # Check default webcam adapter indices (up to 3 indices)
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

        # Always ensure at least the primary webcam/simulator is available
        if not available:
            available.append({
                "id": "0",
                "name": "Webcam (Primary / Simulator)",
                "adapter": "webcam",
                "supported": True,
                "status": "Ready"
            })

        return available

    def connect_camera(self, adapter_name: str = "webcam", device_id: Any = "0") -> bool:
        """Connects to specified camera using appropriate adapter."""
        if self._active_adapter:
            self._active_adapter.disconnect()

        adapter_cls = self._registered_adapters.get(adapter_name.lower(), WebcamAdapter)
        adapter = adapter_cls()
        success = adapter.connect(device_id)
        if success:
            self._active_adapter = adapter
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


def get_camera_manager() -> CameraManager:
    return CameraManager.get_instance()
