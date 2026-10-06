"""Universal Hot-Folder / Watchdog Ingest Camera Adapter.
Allows Core Photo to support ANY tethered camera (Canon, Nikon, Sony, Fuji, etc.)
100% driver-free, future-proof for 10-20+ years.
Works seamlessly with vendor tethering tools (EOS Utility, Nikon NX Tether,
Sony Imaging Edge, Fuji X Acquire, Wi-Fi tethering, or direct SD card ingest).
"""

from datetime import datetime
import io
from pathlib import Path
import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
from PIL import Image, ExifTags

from core.logger import get_logger
from ..capabilities import CameraCapabilities
from ..interface import (
    AbstractCameraAdapter,
    CameraInfo,
    CameraState,
    CaptureResult,
)

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS: Set[str] = {
    ".cr2", ".cr3",   # Canon RAW
    ".nef", ".nrw",   # Nikon RAW
    ".arw", ".srf",   # Sony RAW
    ".raf",           # Fujifilm RAW
    ".dng",           # Adobe / Universal RAW
    ".rw2",           # Panasonic Lumix RAW
    ".orf",           # Olympus RAW
    ".pef",           # Pentax RAW
    ".jpg", ".jpeg",  # Standard JPEG
    ".png",           # PNG
    ".tif", ".tiff",  # TIFF
}


class _HotFolderWatcher:
    """Monitors a directory for newly arrived images using Watchdog or polling fallback."""

    def __init__(self, watch_dir: Path, on_new_file_callback: Callable[[Path], None]):
        self.watch_dir = watch_dir
        self.on_new_file_callback = on_new_file_callback
        self._observer = None
        self._polling_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._known_files: Set[str] = set()

    def start(self) -> None:
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        # Record existing files
        for p in self.watch_dir.iterdir():
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                self._known_files.add(p.name)

        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class _Handler(FileSystemEventHandler):
                def __init__(outer_self):
                    super().__init__()

                def on_created(outer_self, event):
                    if not event.is_directory:
                        p = Path(event.src_path)
                        if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                            # Allow time for file write completion
                            time.sleep(0.2)
                            self.on_new_file_callback(p)

                def on_moved(outer_self, event):
                    if not event.is_directory:
                        p = Path(event.dest_path)
                        if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                            time.sleep(0.2)
                            self.on_new_file_callback(p)

            self._observer = Observer()
            self._observer.schedule(_Handler(), str(self.watch_dir), recursive=False)
            self._observer.start()
            logger.info("Watchdog file observer started on: %s", self.watch_dir)
        except Exception as e:
            logger.warning("Watchdog observer unavailable (%s), falling back to background polling.", e)
            self._stop_event.clear()
            self._polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._polling_thread.start()

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self.watch_dir.exists():
                    for p in self.watch_dir.iterdir():
                        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                            if p.name not in self._known_files:
                                self._known_files.add(p.name)
                                # Wait a moment for write completion
                                time.sleep(0.3)
                                self.on_new_file_callback(p)
            except Exception as e:
                logger.debug("Hot folder polling check error: %s", e)
            time.sleep(0.5)

    def stop(self) -> None:
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=2.0)
            except Exception:
                pass
            self._observer = None

        if self._polling_thread:
            self._stop_event.set()
            self._polling_thread.join(timeout=2.0)
            self._polling_thread = None


class HotFolderAdapter(AbstractCameraAdapter):
    """Universal Camera Ingest Adapter via Hot-Folder Watcher."""

    def __init__(self, watch_dir: Optional[Path] = None):
        self.watch_dir = watch_dir or Path(r"C:\CorePhotos\HotFolder")
        self._state = CameraState.DISCONNECTED
        self._watcher: Optional[_HotFolderWatcher] = None
        self._lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_capture: Optional[CaptureResult] = None
        self._frame_callback: Optional[Callable[[np.ndarray], None]] = None
        self._file_queue: queue.Queue = queue.Queue()

        self._info = CameraInfo(
            model="Universal Hot-Folder Ingest",
            vendor="Tethered (Canon / Nikon / Sony / Any)",
            serial_number="HOT_FOLDER_01",
            firmware_version="Universal v1.0",
            adapter_name="HotFolderAdapter",
            device_id=str(self.watch_dir),
        )
        self._capabilities = CameraCapabilities(
            can_capture=True,
            can_live_view=True,
            supports_iso=True,
            supports_exposure=True,
            supports_aperture=True,
            supports_focus=False,
            supports_zoom=False,
            supported_resolutions=[
                (6000, 4000),  # 24MP Modern DSLR/Mirrorless
                (5184, 3456),  # 18MP Canon EOS 60D Native Sensor Max
                (4000, 3000),  # 12MP High Res
                (3840, 2160),  # 4K UHD
                (1920, 1080),  # Full HD 1080p
                (1280, 720),   # HD 720p
            ],
        )
        self.target_resolution = (5184, 3456)
        self.resolution_mode = "best_native"

    def connect(self, device_id: Any = None) -> bool:
        if device_id and str(device_id).strip():
            self.watch_dir = Path(str(device_id).strip())

        self._state = CameraState.CONNECTING
        logger.info("Connecting Universal Hot-Folder Adapter at: %s", self.watch_dir)
        try:
            self.watch_dir.mkdir(parents=True, exist_ok=True)
            self._watcher = _HotFolderWatcher(self.watch_dir, self._on_new_image_arrived)
            self._watcher.start()

            # Pre-load newest existing image if present
            self._scan_existing_latest()

            self._state = CameraState.READY
            self._info.device_id = str(self.watch_dir)
            logger.info("Universal Hot-Folder Adapter connected and watching: %s", self.watch_dir)
            return True
        except Exception as e:
            logger.error("Failed to connect Hot-Folder Adapter: %s", e)
            self._state = CameraState.ERROR
            return False

    def disconnect(self) -> bool:
        if self._watcher:
            self._watcher.stop()
            self._watcher = None
        self._state = CameraState.DISCONNECTED
        logger.info("Universal Hot-Folder Adapter disconnected.")
        return True

    def get_state(self) -> CameraState:
        return self._state

    def get_info(self) -> CameraInfo:
        return self._info

    def get_capabilities(self) -> CameraCapabilities:
        return self._capabilities

    def start_live_view(self, callback: Optional[Callable[[np.ndarray], None]] = None) -> bool:
        self._frame_callback = callback
        self._state = CameraState.STREAMING
        # Emit initial standby frame or latest frame
        frame = self.get_live_frame()
        if frame is not None and self._frame_callback:
            try:
                self._frame_callback(frame)
            except Exception:
                pass
        return True

    def stop_live_view(self) -> bool:
        self._frame_callback = None
        if self._state == CameraState.STREAMING:
            self._state = CameraState.READY
        return True

    def get_live_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
        return self._generate_standby_frame()

    def capture(self) -> CaptureResult:
        """Captures either the queued incoming tethered photo or the latest frame."""
        self._state = CameraState.CAPTURING

        # 1. Try to get newly arrived file from queue (wait up to 1.5s)
        try:
            res = self._file_queue.get(timeout=1.5)
            self._state = CameraState.STREAMING if self._frame_callback else CameraState.READY
            return res
        except queue.Empty:
            pass

        # 2. If nothing in queue, return latest captured result
        with self._lock:
            if self._latest_capture is not None:
                self._state = CameraState.STREAMING if self._frame_callback else CameraState.READY
                return self._latest_capture

        # 3. Fallback: generate a captured frame from current standby
        frame = self.get_live_frame()
        h, w = frame.shape[:2]
        with io.BytesIO() as bio:
            Image.fromarray(frame).save(bio, format="PNG")
            raw_bytes = bio.getvalue()

        self._state = CameraState.STREAMING if self._frame_callback else CameraState.READY
        return CaptureResult(
            raw_bytes=raw_bytes,
            format="png",
            width=w,
            height=h,
            metadata={
                "camera_model": self._info.model,
                "camera_serial": self._info.serial_number,
                "adapter": "HotFolderAdapter",
                "source": "Standby/HotFolder",
            },
            preview_rgb=frame,
        )

    def set_setting(self, key: str, value: Any) -> bool:
        if key == "folder":
            new_path = Path(str(value))
            if self._watcher:
                self.disconnect()
                self.connect(new_path)
            else:
                self.watch_dir = new_path
            return True
        elif key in ("resolution", "target_resolution"):
            if isinstance(value, (list, tuple)) and len(value) == 2:
                self.target_resolution = (int(value[0]), int(value[1]))
                return True
        elif key == "resolution_mode":
            self.resolution_mode = str(value)
            return True
        return False

    def get_setting(self, key: str) -> Any:
        if key == "folder":
            return str(self.watch_dir)
        elif key in ("resolution", "target_resolution"):
            return getattr(self, "target_resolution", (5184, 3456))
        elif key == "resolution_mode":
            return getattr(self, "resolution_mode", "best_native")
        return None

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    def _on_new_image_arrived(self, file_path: Path) -> None:
        """Processes incoming file dropped by camera tethering software."""
        logger.info("New image detected in hot folder: %s", file_path.name)
        try:
            # Read bytes with retry to ensure file isn't locked by camera writing
            raw_bytes = self._read_bytes_safe(file_path)
            if not raw_bytes:
                logger.warning("Empty file received from hot folder: %s", file_path)
                return

            ext = file_path.suffix.lower()
            rgb_frame, width, height, meta = self._decode_and_extract_metadata(file_path, raw_bytes, ext)

            # Update camera info model if extracted from EXIF
            cam_make = meta.get("Make", "").strip()
            cam_model = meta.get("Model", "").strip()
            if cam_model:
                full_model = f"{cam_make} {cam_model}".strip() if cam_make and cam_make not in cam_model else cam_model
                self._info.model = full_model
                self._info.vendor = cam_make or "DSLR Vendor"

            cap_result = CaptureResult(
                raw_bytes=raw_bytes,
                format=ext.lstrip("."),
                width=width,
                height=height,
                metadata={
                    "camera_model": self._info.model,
                    "camera_serial": meta.get("SerialNumber", self._info.serial_number),
                    "iso": meta.get("ISOSpeedRatings", "Auto"),
                    "exposure_time": meta.get("ExposureTime", "Auto"),
                    "f_number": meta.get("FNumber", "Auto"),
                    "source_filename": file_path.name,
                    "adapter": "HotFolderAdapter",
                },
                preview_rgb=rgb_frame,
            )

            with self._lock:
                self._latest_capture = cap_result
                self._latest_frame = rgb_frame

            self._file_queue.put(cap_result)

            if self._frame_callback and rgb_frame is not None:
                try:
                    self._frame_callback(rgb_frame)
                except Exception as cb_err:
                    logger.debug("Frame callback error: %s", cb_err)

        except Exception as e:
            logger.error("Error processing hot folder image %s: %s", file_path, e)

    def _read_bytes_safe(self, file_path: Path, max_attempts: int = 5) -> bytes:
        """Reads file bytes with short exponential backoff to handle slow USB transfers."""
        for attempt in range(max_attempts):
            try:
                with open(file_path, "rb") as f:
                    data = f.read()
                    if len(data) > 0:
                        return data
            except (IOError, PermissionError):
                time.sleep(0.2 * (attempt + 1))
        return b""

    def _decode_and_extract_metadata(
        self, file_path: Path, raw_bytes: bytes, ext: str
    ) -> Tuple[np.ndarray, int, int, Dict[str, Any]]:
        meta: Dict[str, Any] = {}

        # 1. Try decoding via rawpy for vendor RAW formats (.cr2, .cr3, .nef, .arw, .raf, .dng)
        if ext in (".cr2", ".cr3", ".nef", ".arw", ".raf", ".dng", ".rw2", ".orf", ".pef", ".raw"):
            try:
                import rawpy
                with rawpy.imread(str(file_path)) as raw:
                    rgb = raw.postprocess(use_camera_wb=True, half_size=True)
                    h, w = rgb.shape[:2]
                    return rgb, w, h, meta
            except Exception as e:
                logger.debug("rawpy decode failed for %s: %s, falling back to PIL", file_path, e)

        # 2. Pillow decoding
        try:
            with Image.open(io.BytesIO(raw_bytes)) as pil_img:
                # Extract EXIF
                try:
                    exif_data = pil_img.getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                            if tag_name in ("Make", "Model", "ISOSpeedRatings", "ExposureTime", "FNumber", "DateTimeOriginal"):
                                meta[tag_name] = str(value)
                except Exception:
                    pass

                rgb_pil = pil_img.convert("RGB")
                w, h = rgb_pil.size
                # Resize if ultra high resolution for responsive preview
                if max(w, h) > 1920:
                    scale = 1920.0 / max(w, h)
                    preview_pil = rgb_pil.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
                    rgb = np.array(preview_pil)
                else:
                    rgb = np.array(rgb_pil)
                return rgb, w, h, meta
        except Exception as e:
            logger.warning("Pillow decode failed for %s: %s", file_path, e)

        # 3. Fallback blank pattern
        fallback = self._generate_standby_frame()
        return fallback, fallback.shape[1], fallback.shape[0], meta

    def _scan_existing_latest(self) -> None:
        """Finds most recent image in watch directory if already present."""
        try:
            candidates = [
                p for p in self.watch_dir.iterdir()
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
            ]
            if candidates:
                candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                latest = candidates[0]
                self._on_new_image_arrived(latest)
        except Exception:
            pass

    def _generate_standby_frame(self) -> np.ndarray:
        """Clean industrial technical standby pattern for Hot Folder."""
        w, h = 960, 540
        frame = np.full((h, w, 3), (24, 26, 32), dtype=np.uint8)

        # Subtle dark grid
        grid_color = (36, 40, 50)
        grid_step = 60
        for y in range(0, h, grid_step):
            frame[y:y+1, :, :] = grid_color
        for x in range(0, w, grid_step):
            frame[:, x:x+1, :] = grid_color

        # Text overlay using PIL
        pil_img = Image.fromarray(frame)
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(pil_img)
        font = ImageFont.load_default()

        title = "UNIVERSAL HOT-FOLDER TETHERING — ACTIVE"
        sub = f"Watching: {self.watch_dir} (Canon / Nikon / Sony / Any Camera)"
        instruction = "Press camera shutter or drop image into watch folder to capture"

        draw.text((20, 20), title, fill=(234, 88, 12), font=font)
        draw.text((20, 42), sub, fill=(161, 161, 170), font=font)
        draw.text((20, h - 35), instruction, fill=(113, 113, 122), font=font)

        return np.array(pil_img)
