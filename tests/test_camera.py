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


def test_hot_folder_adapter_lifecycle(tmp_path):
    from camera.adapters.hot_folder import HotFolderAdapter
    from PIL import Image
    import numpy as np

    watch_dir = tmp_path / "HotFolder"
    adapter = HotFolderAdapter(watch_dir=watch_dir)
    assert adapter.connect() is True
    assert adapter.get_state() in (CameraState.READY, CameraState.STREAMING)

    info = adapter.get_info()
    assert info.adapter_name == "HotFolderAdapter"

    # Simulate camera dropping a photo into the hot folder
    img_path = watch_dir / "IMG_1234.JPG"
    arr = np.full((100, 100, 3), (150, 120, 90), dtype=np.uint8)
    Image.fromarray(arr).save(img_path, format="JPEG")

    # Ingest the arrived image
    adapter._on_new_image_arrived(img_path)

    res = adapter.capture()
    assert len(res.raw_bytes) > 0
    assert res.width == 100
    assert res.height == 100
    assert res.format == "jpg"

    assert adapter.disconnect() is True
    assert adapter.get_state() == CameraState.DISCONNECTED


def test_camera_manager_hot_folder(tmp_path):
    cm = CameraManager.get_instance()
    cams = cm.detect_cameras()
    assert any(c["adapter"] == "hot_folder" for c in cams)

    watch_dir = tmp_path / "CMHotFolder"
    assert cm.connect_camera("hot_folder", str(watch_dir)) is True
    assert cm.is_ready() is True
    assert "Hot-Folder" in cm.get_status_summary()

    cm.disconnect_camera()


def test_direct_usb_adapter_lifecycle():
    from camera.adapters.direct_usb import DirectUsbAdapter
    adapter = DirectUsbAdapter()
    assert adapter.connect() is True
    assert adapter.get_state() in (CameraState.READY, CameraState.STREAMING)

    info = adapter.get_info()
    assert info.adapter_name == "DirectUsbAdapter"

    caps = adapter.get_capabilities()
    assert caps.can_capture is True
    assert caps.can_live_view is True

    frame = adapter.get_live_frame()
    assert frame is not None
    assert frame.shape[0] > 0
    assert frame.shape[1] > 0

    res = adapter.capture()
    assert len(res.raw_bytes) > 0
    assert res.width > 0
    assert res.height > 0

    assert adapter.disconnect() is True
    assert adapter.get_state() == CameraState.DISCONNECTED


def test_camera_manager_direct_usb():
    cm = CameraManager.get_instance()
    cams = cm.detect_cameras()
    assert any(c["adapter"] == "direct_usb" for c in cams)

    assert cm.connect_camera("direct_usb", "0") is True
    assert cm.is_ready() is True
    assert "Direct USB" in cm.get_status_summary()

    cm.disconnect_camera()


def test_camera_manager():
    cm = CameraManager.get_instance()
    cams = cm.detect_cameras()
    assert len(cams) >= 1

    cm.connect_camera("webcam", "0")
    assert cm.is_ready() is True
    assert "Camera:" in cm.get_status_summary()

    cm.disconnect_camera()


def test_camera_resolution_configuration():
    cm = CameraManager.get_instance()
    cm.connect_camera("direct_usb", "0")

    # Verify supported resolutions contains DSLR best native
    supp = cm.get_supported_resolutions()
    assert (5184, 3456) in supp  # 18MP Canon 60D
    assert (6000, 4000) in supp  # 24MP Modern DSLR

    # Test setting resolution
    assert cm.set_resolution(5184, 3456, mode="best_native") is True
    assert cm.get_current_resolution() == (5184, 3456)
    assert cm.get_resolution_mode() == "best_native"

    # Test setting custom resolution
    assert cm.set_resolution(1920, 1080, mode="1080p") is True
    assert cm.get_current_resolution() == (1920, 1080)

    # Test custom manual dimensions
    assert cm.set_resolution(3840, 2160, mode="custom") is True
    assert cm.get_current_resolution() == (3840, 2160)
    assert cm.get_resolution_mode() == "custom"

    # Revert to best native
    assert cm.set_resolution(5184, 3456, mode="best_native") is True
    assert cm.get_current_resolution() == (5184, 3456)

    cm.disconnect_camera()

