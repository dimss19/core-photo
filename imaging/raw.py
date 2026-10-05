"""RAW Image Handler (PRD Section 13 & 19).
Saves RAW bytes immediately before any further processing for crash resistance.
"""

import hashlib
import io
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from PIL import Image

from core.logger import get_logger

logger = get_logger(__name__)


class RawHandler:
    """Manages RAW storage and decoding."""

    @staticmethod
    def calculate_md5(file_path: Path) -> str:
        """Calculates MD5 hash of a file for integrity verification (PRD Section 13)."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def save_raw(raw_bytes: bytes, destination_path: Path) -> Tuple[Path, str]:
        """Saves RAW bytes immediately to disk and returns (saved_path, md5_checksum)."""
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with open(destination_path, "wb") as f:
            f.write(raw_bytes)

        md5 = RawHandler.calculate_md5(destination_path)
        logger.info("Saved RAW file: %s (MD5: %s, size: %d bytes)", destination_path, md5, len(raw_bytes))
        return destination_path, md5

    @staticmethod
    def decode_raw_to_rgb(raw_path: Path) -> np.ndarray:
        """Decodes saved RAW file into RGB numpy array.
        Handles standard formats (PNG/TIFF/JPG) or DSLR RAW via rawpy if available.
        """
        if not raw_path.exists():
            raise FileNotFoundError(f"RAW file not found: {raw_path}")

        ext = raw_path.suffix.lower()

        # Try rawpy for professional camera vendor raw formats (.cr2, .cr3, .nef, .arw, .dng)
        if ext in ('.cr2', '.cr3', '.nef', '.arw', '.dng', '.raw'):
            try:
                import rawpy
                with rawpy.imread(str(raw_path)) as raw:
                    rgb = raw.postprocess(use_camera_wb=True)
                    return rgb
            except Exception as e:
                logger.debug("rawpy decode failed or format unsupported: %s. Falling back to PIL.", e)

        # Fallback to Pillow
        with Image.open(raw_path) as img:
            rgb_img = img.convert("RGB")
            return np.array(rgb_img)
