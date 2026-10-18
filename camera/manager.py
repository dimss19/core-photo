"""Camera Manager (PRD Section 7.1, 8 & 32).
Orchestrates camera discovery, connection, lifecycle, and decoupling UI from SDKs.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from core.logger import get_logger
from .adapters.webcam import WebcamAdapter
from .adapters.hot_folder import HotFolderAdapter
from .adapters.direct_usb import DirectUsbAdapter
from .adapters.wifi_dslr import WiFiDslrAdapter
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
            "wifi_dslr": WiFiDslrAdapter,
            "wifi": WiFiDslrAdapter,
            "dslr_wifi": WiFiDslrAdapter,
            "tether": WiFiDslrAdapter,
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

    def test_wifi_connection(self, ip: str, port: int = 15740) -> Tuple[bool, str]:
        """Tests whether camera is reachable over Wi-Fi network."""
        return WiFiDslrAdapter.test_ip_reachability(ip, port)

    _windows_camera_names_cache: Optional[List[str]] = None

    @classmethod
    def get_windows_camera_friendly_names(cls) -> List[str]:
        """Returns Windows PnP friendly names for Camera class (best-effort).

        Example: ['USB2.0 HD UVC WebCam', 'EOS Webcam Utility'].
        Cached per-process; never raises.
        """
        if cls._windows_camera_names_cache is not None:
            return cls._windows_camera_names_cache
        names: List[str] = []
        try:
            import subprocess
            ps = (
                "Get-PnpDevice -Class Camera -Status OK "
                "| Select-Object -ExpandProperty FriendlyName"
            )
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=6,
            )
            if out.returncode == 0 and out.stdout:
                for line in out.stdout.splitlines():
                    s = line.strip()
                    if s and s.lower() != "friendlyname":
                        names.append(s)
        except Exception as e:
            logger.debug("Windows camera friendly-name query failed: %s", e)
        cls._windows_camera_names_cache = names
        return names

    def list_webcam_devices(self, max_index: int = 8) -> List[Dict[str, Any]]:
        """Enumerates physical UVC/DirectShow webcams with real resolution.

        Returns list of dicts: index, id, name, adapter='webcam',
        width, height, fps, backend, supported, status.
        Index 0 is labelled Integrated/Primary, index >= 1 External USB.
        Never raises; returns [] when OpenCV is missing.
        """
        devices: List[Dict[str, Any]] = []
        try:
            import cv2
        except ImportError as e:
            logger.debug("OpenCV missing, cannot enumerate webcams: %s", e)
            return devices

        friendly = self.get_windows_camera_friendly_names()
        consecutive_miss = 0
        for idx in range(max(1, max_index)):
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            except Exception as e:
                logger.debug("Webcam index %d open exception: %s", idx, e)
                consecutive_miss += 1
                if consecutive_miss >= 2:
                    break
                continue
            try:
                if not cap.isOpened():
                    consecutive_miss += 1
                    if consecutive_miss >= 2:
                        break
                    continue
                consecutive_miss = 0
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
                try:
                    ret, frame = cap.read()
                    if ret and frame is not None and len(frame.shape) >= 2:
                        fh, fw = int(frame.shape[0]), int(frame.shape[1])
                        if fw > 0 and fh > 0:
                            w, h = fw, fh
                except Exception:
                    pass
                if w <= 0:
                    w = 640
                if h <= 0:
                    h = 480
                try:
                    backend = str(cap.getBackendName())
                except Exception:
                    backend = "DSHOW"
                kind = "Integrated / Primary" if idx == 0 else "External USB"
                base = f"{kind} Webcam — Index {idx} ({w}x{h})"
                # Attach Windows friendly name when count matches, else as hint
                extra = ""
                if friendly:
                    if len(friendly) > idx:
                        extra = f" [{friendly[idx]}]"
                    elif idx == 0:
                        extra = f" [{friendly[0]}]"
                devices.append({
                    "index": idx,
                    "id": str(idx),
                    "name": base + extra,
                    "adapter": "webcam",
                    "width": w,
                    "height": h,
                    "fps": fps,
                    "backend": backend,
                    "supported": True,
                    "status": "Ready",
                })
            finally:
                try:
                    cap.release()
                except Exception:
                    pass
        return devices

    def get_preferred_webcam_index(self) -> int:
        """Returns configured preferred webcam index (default 0)."""
        try:
            from config.config_manager import get_config
            cfg = get_config()
            return int(cfg.get("camera", "preferred_index", 0))
        except Exception:
            return 0

    def detect_cameras(self) -> List[Dict[str, Any]]:
        """Scans system for available camera devices (PRD Section 8)."""
        available: List[Dict[str, Any]] = []

        # 1. Wi-Fi DSLR Camera (Canon / Nikon / Sony / Fuji Tethering & IP Remote)
        available.append({
            "id": "wifi_dslr",
            "name": "Wi-Fi DSLR Wireless Tethering (Canon / Nikon / Sony / Fuji)",
            "adapter": "wifi_dslr",
            "supported": True,
            "status": "Ready"
        })

        # 2. Direct USB Camera (Native Windows WIA & PTP - 0 DLLs, 0 Software)
        available.append({
            "id": "direct_usb",
            "name": "Direct USB DSLR (Canon / Nikon / Sony — Cable)",
            "adapter": "direct_usb",
            "supported": True,
            "status": "Ready"
        })

        # 3. Universal Hot-Folder Ingest
        available.append({
            "id": "hot_folder",
            "name": "Universal Hot-Folder Ingest",
            "adapter": "hot_folder",
            "supported": True,
            "status": "Ready"
        })

        # 4. Physical UVC / DirectShow webcams (integrated + external USB)
        try:
            for dev in self.list_webcam_devices():
                available.append({
                    "id": dev["id"],
                    "name": dev["name"],
                    "adapter": "webcam",
                    "supported": True,
                    "status": "Ready",
                    "width": dev.get("width"),
                    "height": dev.get("height"),
                })
        except Exception as e:
            logger.debug("Hardware camera scan exception: %s", e)

        # 5. Technical simulation feed
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
        if norm_name in ("wifi_dslr", "wifi", "dslr_wifi", "tether") or norm_dev in ("wifi_dslr", "wifi", "dslr_wifi", "tether"):
            adapter_name = "wifi_dslr"
        elif norm_name in ("hot_folder", "hotfolder") or norm_dev in ("hot_folder", "hotfolder"):
            adapter_name = "hot_folder"
        elif norm_name in ("direct_usb", "direct", "ptp") or norm_dev in ("direct_usb", "direct", "ptp"):
            adapter_name = "direct_usb"

        adapter_cls = self._registered_adapters.get(adapter_name.lower(), WebcamAdapter)

        # FIX: jangan teruskan index numerik basi (mis. "2") sebagai folder
        # Hot-Folder. Biarkan adapter memakai watch_dir default / terkonfigurasi.
        if adapter_cls is HotFolderAdapter:
            dev_s = str(device_id).strip() if device_id is not None else ""
            low_s = dev_s.lower()
            if not dev_s or low_s in ("hot_folder", "hotfolder", "default", "none", "auto") or dev_s.isdigit():
                try:
                    from config.config_manager import get_config as _get_cfg
                    _cfg = _get_cfg()
                    _t = str(_cfg.get("camera", "tether_folder", "") or "").strip()
                    # tether_folder milik mode Wi-Fi; hanya pakai bila berupa path valid
                    if _t and ("/" in _t or "\\" in _t or (_t[1:2] == ":" if len(_t) > 1 else False)):
                        from pathlib import Path as _P
                        if _P(_t).exists() or len(_t) > 3:
                            device_id = _t
                        else:
                            device_id = None
                    else:
                        # Coba folder HotFolder standar di bawah storage base
                        try:
                            from pathlib import Path as _P2
                            _base = str(_cfg.get("storage", "base_dir", "CorePhotoData") or "CorePhotoData")
                            device_id = str(_P2(_base) / "HotFolder")
                        except Exception:
                            device_id = None
                except Exception:
                    device_id = None

        adapter = adapter_cls()
        success = adapter.connect(device_id)
        # FIX: fallback webcam bila index basi (mis. external index 2 sudah
        # dicabut tapi config masih menunjuk ke sana). Cari index fisik lain
        # yang benar-benar bisa dibuka sebelum menyerah ke standby.
        if success and adapter_cls is WebcamAdapter:
            try:
                _req = str(device_id).lower() if device_id is not None else "0"
                _is_sim_req = _req in ("sim", "simulator", "sample")
                if not _is_sim_req and getattr(adapter, "_is_simulated", False):
                    _alternatives: list = []
                    try:
                        for _dev in self.list_webcam_devices():
                            _idx = str(_dev.get("index", _dev.get("id")))
                            if _idx != str(device_id):
                                _alternatives.append(_idx)
                    except Exception:
                        pass
                    if str(device_id) != "0" and "0" not in _alternatives:
                        _alternatives.append("0")
                    for _fid in _alternatives:
                        try:
                            _alt = WebcamAdapter()
                            if _alt.connect(_fid):
                                if not getattr(_alt, "_is_simulated", False):
                                    try:
                                        adapter.disconnect()
                                    except Exception:
                                        pass
                                    adapter = _alt
                                    device_id = _fid
                                    logger.info(
                                        "Webcam index %s unavailable, auto-fallback to working index %s",
                                        _req, _fid,
                                    )
                                    break
                                try:
                                    _alt.disconnect()
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception as _fb_e:
                logger.debug("Webcam auto-fallback exception: %s", _fb_e)
        if success:
            self._active_adapter = adapter
            # Apply configured camera resolution + persist webcam selection
            try:
                from config.config_manager import get_config
                cfg = get_config()
                res = cfg.get("camera", "default_resolution", [5184, 3456])
                res_mode = cfg.get("camera", "resolution_mode", "best_native")
                if isinstance(res, (list, tuple)) and len(res) == 2:
                    adapter.set_setting("resolution", (int(res[0]), int(res[1])))
                adapter.set_setting("resolution_mode", res_mode)
                if adapter_cls is WebcamAdapter:
                    try:
                        idx = int(str(device_id))
                        cfg.set("camera", "preferred_index", idx)
                        cfg.set("camera", "device_id", str(device_id))
                        cfg.set("camera", "default_adapter", "webcam")
                    except (ValueError, TypeError):
                        # 'sim' simulator or non-numeric id: don't overwrite index
                        pass
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
