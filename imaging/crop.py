"""Crop and framing management (PRD Section 12).
Handles standard 300x200 tray crop and coordinates transformation.
"""

from dataclasses import dataclass
from typing import Tuple
import numpy as np
from PIL import Image


@dataclass
class CropRegion:
    """Defines rectangular region for tray framing."""
    x: int
    y: int
    width: int
    height: int

    def validate_bounds(self, frame_w: int, frame_h: int) -> "CropRegion":
        """Ensures crop box stays within frame boundaries."""
        x = max(0, min(self.x, frame_w - 10))
        y = max(0, min(self.y, frame_h - 10))
        w = max(10, min(self.width, frame_w - x))
        h = max(10, min(self.height, frame_h - y))
        return CropRegion(x=x, y=y, width=w, height=h)

    def apply_to_array(self, img_array: np.ndarray, target_size: Tuple[int, int] = (300, 200)) -> np.ndarray:
        """Crops numpy array and resizes to standard crop output (PRD Section 12)."""
        h, w = img_array.shape[:2]
        safe = self.validate_bounds(w, h)
        cropped = img_array[safe.y:safe.y + safe.height, safe.x:safe.x + safe.width]

        # Resize to standard size (300 x 200)
        pil_img = Image.fromarray(cropped)
        resized = pil_img.resize(target_size, Image.Resampling.LANCZOS)
        return np.array(resized)

    def apply_to_pil(self, img: Image.Image, target_size: Tuple[int, int] = (300, 200)) -> Image.Image:
        """Crops PIL Image and resizes to target standard output."""
        w, h = img.size
        safe = self.validate_bounds(w, h)
        box = (safe.x, safe.y, safe.x + safe.width, safe.y + safe.height)
        cropped = img.crop(box)
        return cropped.resize(target_size, Image.Resampling.LANCZOS)
