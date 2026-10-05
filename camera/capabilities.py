"""Camera capability declarations (PRD Section 7.5 & 29).
Prevents hardcoding vendor assumptions and ensures UI adapts dynamically.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class CameraCapabilities:
    """Declared capabilities of a specific camera adapter."""
    can_capture: bool = True
    can_live_view: bool = True
    supports_iso: bool = False
    supports_exposure: bool = False
    supports_aperture: bool = False
    supports_focus: bool = False
    supports_zoom: bool = False
    supports_flash: bool = False
    supports_metering: bool = False
    supported_resolutions: List[Tuple[int, int]] = field(default_factory=lambda: [(1920, 1080), (1280, 720), (640, 480)])
    supported_iso_values: List[int] = field(default_factory=list)
    supported_aperture_values: List[str] = field(default_factory=list)
    supported_shutter_speeds: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "can_capture": self.can_capture,
            "can_live_view": self.can_live_view,
            "supports_iso": self.supports_iso,
            "supports_exposure": self.supports_exposure,
            "supports_aperture": self.supports_aperture,
            "supports_focus": self.supports_focus,
            "supports_zoom": self.supports_zoom,
            "supports_flash": self.supports_flash,
            "supports_metering": self.supports_metering,
            "supported_resolutions": self.supported_resolutions,
            "supported_iso_values": self.supported_iso_values,
            "supported_aperture_values": self.supported_aperture_values,
            "supported_shutter_speeds": self.supported_shutter_speeds,
        }
