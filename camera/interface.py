"""Abstract Camera Interface (PRD Section 7.2 & 32).
Core application only communicates through this abstraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional
import numpy as np

from .capabilities import CameraCapabilities


class CameraState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    READY = "READY"
    STREAMING = "STREAMING"
    CAPTURING = "CAPTURING"
    ERROR = "ERROR"


@dataclass
class CameraInfo:
    """Device information returned by camera adapter."""
    model: str = "Unknown Camera"
    serial_number: str = "N/A"
    vendor: str = "Generic"
    firmware_version: str = "1.0"
    adapter_name: str = "GenericAdapter"
    device_id: str = "0"


@dataclass
class CaptureResult:
    """Result of camera capture operation."""
    raw_bytes: bytes
    format: str  # 'raw', 'dng', 'png', 'jpg'
    width: int
    height: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    preview_rgb: Optional[np.ndarray] = None


class AbstractCameraAdapter(ABC):
    """Base interface for all camera adapters (Webcam, Canon, Nikon, Sony, etc.)."""

    @abstractmethod
    def connect(self, device_id: Any = None) -> bool:
        """Connects to the physical camera device."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnects and releases camera resources."""
        pass

    @abstractmethod
    def get_state(self) -> CameraState:
        """Returns the current state of the camera."""
        pass

    @abstractmethod
    def get_info(self) -> CameraInfo:
        """Returns device hardware details."""
        pass

    @abstractmethod
    def get_capabilities(self) -> CameraCapabilities:
        """Returns camera supported capabilities."""
        pass

    @abstractmethod
    def start_live_view(self, callback: Optional[Callable[[np.ndarray], None]] = None) -> bool:
        """Starts streaming preview frames."""
        pass

    @abstractmethod
    def stop_live_view(self) -> bool:
        """Stops streaming preview frames."""
        pass

    @abstractmethod
    def get_live_frame(self) -> Optional[np.ndarray]:
        """Returns the latest RGB frame from live view stream."""
        pass

    @abstractmethod
    def capture(self) -> CaptureResult:
        """Triggers single exposure capture and returns raw capture result."""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> bool:
        """Updates camera parameter (ISO, exposure, white balance, etc.)."""
        pass

    @abstractmethod
    def get_setting(self, key: str) -> Any:
        """Reads current camera parameter."""
        pass
