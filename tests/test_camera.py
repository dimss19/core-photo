"""Tests for Camera Adapter and CameraManager."""

from camera.adapters.webcam import WebcamAdapter
from camera.interface import CameraState
from camera.manager import CameraManager


def test_webcam_adapter_lifecycle():
    adapter = WebcamAdapter()
    assert adapter.connect("0") is True
    assert adapter.get_state() in (CameraState.READY, CameraState.STREAMING)

    info = adapter.get_info()
    assert info.adapter_name == "WebcamAdapter"

    caps = adapter.get_capabilities()
    assert caps.can_capture is True

    # Capture test
    res = adapter.capture()
    assert len(res.raw_bytes) > 0
    assert res.width > 0
    assert res.height > 0

    assert adapter.disconnect() is True
    assert adapter.get_state() == CameraState.DISCONNECTED


def test_camera_manager():
    cm = CameraManager.get_instance()
    cams = cm.detect_cameras()
    assert len(cams) >= 1

    cm.connect_camera("webcam", "0")
    assert cm.is_ready() is True
    assert "Camera:" in cm.get_status_summary()

    cm.disconnect_camera()
