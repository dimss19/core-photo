"""Camera package for Core Photo."""
from .capabilities import CameraCapabilities
from .interface import (
    AbstractCameraAdapter,
    CameraInfo,
    CameraState,
    CaptureResult,
)
from .manager import CameraManager, get_camera_manager

__all__ = [
    "CameraCapabilities",
    "AbstractCameraAdapter",
    "CameraInfo",
    "CameraState",
    "CaptureResult",
    "CameraManager",
    "get_camera_manager",
]
