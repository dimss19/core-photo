"""Unit and integration tests for Wi-Fi DSLR Camera subsystem."""

from pathlib import Path
import numpy as np
from PIL import Image

from camera.adapters.wifi_dslr import WiFiDslrAdapter
from camera.interface import CameraState
from camera.manager import CameraManager
from config.config_manager import get_config


def test_wifi_dslr_adapter_lifecycle(tmp_path):
    tether_dir = tmp_path / "WiFiTether"
    adapter = WiFiDslrAdapter(tether_dir=tether_dir, camera_ip="192.168.1.150")

    assert adapter.connect() is True
    assert adapter.get_state() in (CameraState.READY, CameraState.STREAMING)

    info = adapter.get_info()
    assert info.adapter_name == "WiFiDslrAdapter"
    assert "Wi-Fi" in info.model

    caps = adapter.get_capabilities()
    assert caps.can_capture is True
    assert caps.can_live_view is True
    assert caps.supports_iso is True
    assert caps.supports_exposure is True

    # Check live view frame generation
    frame = adapter.get_live_frame()
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape[0] > 0 and frame.shape[1] > 0

    # Start and stop live view
    assert adapter.start_live_view() is True
    assert adapter.stop_live_view() is True

    assert adapter.disconnect() is True
    assert adapter.get_state() == CameraState.DISCONNECTED


def test_wifi_dslr_incoming_photo_ingest(tmp_path):
    tether_dir = tmp_path / "IncomingTether"
    tether_dir.mkdir(parents=True, exist_ok=True)
    adapter = WiFiDslrAdapter(tether_dir=tether_dir)
    assert adapter.connect() is True

    # Create dummy DSLR capture in tether folder
    dummy_img = tether_dir / "IMG_8820.JPG"
    arr = np.full((120, 160, 3), (120, 100, 80), dtype=np.uint8)
    Image.fromarray(arr).save(dummy_img, format="JPEG")

    # Ingest photo
    adapter._on_new_image_arrived(dummy_img)

    res = adapter.capture()
    assert len(res.raw_bytes) > 0
    assert res.width == 160
    assert res.height == 120
    assert res.format == "jpg"
    assert res.metadata.get("adapter") == "WiFiDslrAdapter"

    adapter.disconnect()


def test_wifi_dslr_exif_metadata_extraction(tmp_path):
    tether_dir = tmp_path / "ExifTest"
    tether_dir.mkdir(parents=True, exist_ok=True)
    adapter = WiFiDslrAdapter(tether_dir=tether_dir)

    img_path = tether_dir / "TEST_EXIF.JPG"
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    Image.fromarray(arr).save(img_path, format="JPEG")

    # Test extraction does not crash and returns dict
    meta = adapter._extract_exif_metadata(img_path)
    assert isinstance(meta, dict)


def test_wifi_dslr_ip_reachability_test():
    # Test with empty IP
    ok, msg = WiFiDslrAdapter.test_ip_reachability("")
    assert ok is False
    assert "tidak valid" in msg.lower()

    # Test with unassigned local IP on non-listening port
    ok2, msg2 = WiFiDslrAdapter.test_ip_reachability("192.0.2.1", port=15740, timeout=0.1)
    assert ok2 is False
    assert isinstance(msg2, str)


def test_camera_manager_wifi_dslr_integration(tmp_path):
    cm = CameraManager.get_instance()

    # 1. Verification in detect_cameras
    cams = cm.detect_cameras()
    wifi_cams = [c for c in cams if c.get("adapter") == "wifi_dslr"]
    assert len(wifi_cams) >= 1
    assert "Wi-Fi DSLR" in wifi_cams[0]["name"]

    # 2. Connection via CameraManager
    tether_dir = tmp_path / "CM_WiFiTether"
    assert cm.connect_camera("wifi_dslr", str(tether_dir)) is True
    assert cm.is_ready() is True

    summary = cm.get_status_summary()
    assert "Wi-Fi DSLR" in summary
    assert "Connected" in summary

    # 3. Wi-Fi IP reachability helper on CameraManager
    reachable, msg = cm.test_wifi_connection("")
    assert reachable is False

    cm.disconnect_camera()
    assert cm.is_ready() is False


def test_wifi_dslr_config_persistence():
    cfg = get_config()
    cfg.set("camera", "connection_type", "wifi_dslr")
    cfg.set("camera", "wifi_ip", "192.168.1.120")
    cfg.set("camera", "tether_folder", "C:\\TestTether")

    assert cfg.get("camera", "connection_type") == "wifi_dslr"
    assert cfg.get("camera", "wifi_ip") == "192.168.1.120"
    assert cfg.get("camera", "tether_folder") == "C:\\TestTether"
