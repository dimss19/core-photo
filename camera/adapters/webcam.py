"""Webcam Camera Adapter using OpenCV (PRD Section 7.3).
First concrete adapter implementation for Core Photo.
Includes thread-safe live view capture and synthetic pattern fallback for testing.
"""

import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from core.logger import get_logger
from ..capabilities import CameraCapabilities
from ..interface import (
    AbstractCameraAdapter,
    CameraInfo,
    CameraState,
    CaptureResult,
)

logger = get_logger(__name__)


class WebcamAdapter(AbstractCameraAdapter):
    """Adapter for standard USB / integrated webcams using OpenCV."""

    def __init__(self, device_index: int = 0, preferred_resolution: Tuple[int, int] = (1920, 1080)):
        self.device_index = device_index
        self.preferred_resolution = preferred_resolution
        self._cap: Optional[Any] = None
        self._state = CameraState.DISCONNECTED
        self._is_simulated = False
        self._lock = threading.Lock()
        self._live_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_callback: Optional[Callable[[np.ndarray], None]] = None
        self._info = CameraInfo(
            model="Integrated/USB Webcam",
            vendor="Generic USB",
            serial_number=f"CAM_{device_index}",
            firmware_version="UVC 1.5",
            adapter_name="WebcamAdapter",
            device_id=str(device_index),
        )
        self._capabilities = CameraCapabilities(
            can_capture=True,
            can_live_view=True,
            supports_iso=False,
            supports_exposure=True,
            supports_aperture=False,
            supports_focus=False,
            supports_zoom=False,
            supported_resolutions=[(1920, 1080), (1280, 720), (640, 480)],
        )

    def connect(self, device_id: Any = None) -> bool:
        if device_id is not None:
            try:
                self.device_index = int(device_id)
            except (ValueError, TypeError):
                self.device_index = 0

        self._state = CameraState.CONNECTING
        logger.info("Connecting to webcam index %d...", self.device_index)

        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not installed. Using simulated camera pattern.")
            self._is_simulated = True
            self._state = CameraState.READY
            return True

        try:
            # On Windows, cv2.CAP_DSHOW provides fast and reliable DirectShow initialization
            cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                # Fallback to default backend
                cap = cv2.VideoCapture(self.device_index)

            if not cap.isOpened():
                logger.warning(
                    "Physical camera index %d could not be opened. Falling back to simulated core tray stream.",
                    self.device_index
                )
                self._is_simulated = True
                self._state = CameraState.READY
                return True

            # Attempt to set preferred resolution
            w, h = self.preferred_resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            logger.info("Webcam connected with resolution: %dx%d", actual_w, actual_h)

            self._cap = cap
            self._is_simulated = False
            self._state = CameraState.READY
            self._info.model = f"USB Video Device (Index {self.device_index})"
            return True
        except Exception as e:
            logger.error("Failed to connect to webcam: %s. Enabling simulation mode.", e)
            self._is_simulated = True
            self._state = CameraState.READY
            return True

    def disconnect(self) -> bool:
        logger.info("Disconnecting camera...")
        self.stop_live_view()
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception as e:
                    logger.error("Error releasing camera: %s", e)
                self._cap = None
            self._state = CameraState.DISCONNECTED
        logger.info("Camera disconnected.")
        return True

    def get_state(self) -> CameraState:
        return self._state

    def get_info(self) -> CameraInfo:
        return self._info

    def get_capabilities(self) -> CameraCapabilities:
        return self._capabilities

    def start_live_view(self, callback: Optional[Callable[[np.ndarray], None]] = None) -> bool:
        if self._state == CameraState.STREAMING:
            return True

        self._frame_callback = callback
        self._stop_event.clear()
        self._live_thread = threading.Thread(target=self._live_view_loop, daemon=True)
        self._live_thread.start()
        self._state = CameraState.STREAMING
        logger.info("Live View started.")
        return True

    def stop_live_view(self) -> bool:
        if self._state != CameraState.STREAMING and not self._live_thread:
            return True

        self._stop_event.set()
        if self._live_thread and self._live_thread.is_alive():
            self._live_thread.join(timeout=1.0)
        self._live_thread = None
        self._state = CameraState.READY if self._cap or self._is_simulated else CameraState.DISCONNECTED
        logger.info("Live View stopped.")
        return True

    def get_live_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
            return None

    def capture(self) -> CaptureResult:
        """Captures a frame, returning raw image bytes and metadata (PRD Section 13)."""
        logger.info("Executing capture...")
        self._state = CameraState.CAPTURING

        frame_rgb = None
        with self._lock:
            if self._latest_frame is not None:
                frame_rgb = self._latest_frame.copy()

        if frame_rgb is None:
            if self._is_simulated or self._cap is None:
                frame_rgb = self._generate_simulated_frame()
            else:
                ret, frame_bgr = self._cap.read()
                if ret and frame_bgr is not None:
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                else:
                    frame_rgb = self._generate_simulated_frame()

        h, w = frame_rgb.shape[:2]

        # For webcam, we encode lossless PNG/TIFF to serve as the uncompressed RAW equivalent
        if OPENCV_AVAILABLE:
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            success, raw_encoded = cv2.imencode('.png', frame_bgr)
            raw_bytes = raw_encoded.tobytes() if success else b""
        else:
            raw_bytes = frame_rgb.tobytes()

        self._state = CameraState.STREAMING if self._live_thread else CameraState.READY
        logger.info("Capture completed (%dx%d, %d bytes)", w, h, len(raw_bytes))

        return CaptureResult(
            raw_bytes=raw_bytes,
            format="png",  # Raw capture format
            width=w,
            height=h,
            metadata={
                "camera_model": self._info.model,
                "camera_serial": self._info.serial_number,
                "exposure_mode": "Auto",
            },
            preview_rgb=frame_rgb
        )

    def set_setting(self, key: str, value: Any) -> bool:
        if not OPENCV_AVAILABLE or self._is_simulated or not self._cap:
            return False
        if key == "exposure":
            return bool(self._cap.set(cv2.CAP_PROP_EXPOSURE, float(value)))
        return False

    def get_setting(self, key: str) -> Any:
        if not OPENCV_AVAILABLE or self._is_simulated or not self._cap:
            return None
        if key == "exposure":
            return self._cap.get(cv2.CAP_PROP_EXPOSURE)
        return None

    def _live_view_loop(self) -> None:
        """Background thread reading camera frames at ~30 FPS."""
        while not self._stop_event.is_set():
            frame_rgb = None
            if self._is_simulated or self._cap is None:
                frame_rgb = self._generate_simulated_frame()
                time.sleep(0.033)  # ~30 FPS
            else:
                with self._lock:
                    ret, frame_bgr = self._cap.read()
                if ret and frame_bgr is not None:
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                else:
                    time.sleep(0.05)
                    continue

            with self._lock:
                self._latest_frame = frame_rgb

            if self._frame_callback and frame_rgb is not None:
                try:
                    self._frame_callback(frame_rgb)
                except Exception as e:
                    logger.debug("Live view callback exception: %s", e)

    def _generate_simulated_frame(self) -> np.ndarray:
        """Generates realistic synthetic core tray pattern for testing and fallback."""
        w, h = 640, 480
        # Background tray: dark wooden/metallic core tray
        img = np.full((h, w, 3), (60, 65, 70), dtype=np.uint8)

        # Draw 3 core rock rows
        row_height = 80
        margin = 30
        for i in range(3):
            y_start = margin + i * (row_height + 25)
            y_end = y_start + row_height
            # Rock core cylinder simulation
            rock_color = (130 + i * 15, 120 + i * 10, 110 + i * 12)
            img[y_start:y_end, 50:w - 50] = rock_color

            # Add core fracture markings
            for frac_x in range(120, w - 80, 75):
                img[y_start:y_end, frac_x:frac_x + 3] = (30, 30, 30)

        # Simulation watermark / overlay
        if OPENCV_AVAILABLE:
            cv2.putText(img, "CORE TRAY SIMULATION STREAM", (70, 460),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 220, 255), 2)
            # Ruler markings at top
            cv2.line(img, (50, 20), (w - 50, 20), (220, 220, 220), 2)
            for tick in range(50, w - 50, 40):
                cv2.line(img, (tick, 15), (tick, 25), (255, 255, 255), 2)

        return img
