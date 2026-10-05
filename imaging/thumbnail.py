"""Thumbnail generator (PRD Section 13 & 15).
Produces lightweight thumbnails for fast grid navigation in Photo Browser.
"""

from pathlib import Path
from typing import Tuple
from PIL import Image

from core.logger import get_logger

logger = get_logger(__name__)


class ThumbnailGenerator:
    """Generates and saves image thumbnails."""

    @staticmethod
    def generate(
        source_img: Image.Image,
        destination_path: Path,
        size: Tuple[int, int] = (150, 100),
        quality: int = 85
    ) -> Path:
        """Resizes image to thumbnail dimensions and saves as JPG."""
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        thumb = source_img.copy()
        thumb.thumbnail(size, Image.Resampling.LANCZOS)
        thumb.convert("RGB").save(str(destination_path), "JPEG", quality=quality, optimize=True)
        logger.debug("Generated thumbnail at: %s", destination_path)
        return destination_path
