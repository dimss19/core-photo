"""Comprehensive Validation Runner (PRD Section 20).
Re-runnable verification of files on disk, MD5 hashes, DB consistency, and metadata.
"""

from pathlib import Path
from typing import List, Tuple

from core.logger import get_logger
from database.models import PhotoModel, PhotoStatus, ValidationResultModel
from database.repositories import PhotoRepository, ValidationRepository
from imaging.raw import RawHandler
from .filename import validate_filename
from .interval import validate_interval

logger = get_logger(__name__)


class ValidationRunner:
    """Orchestrates photo and session validation."""

    def __init__(
        self,
        photo_repo: PhotoRepository,
        validation_repo: ValidationRepository
    ):
        self.photo_repo = photo_repo
        self.validation_repo = validation_repo

    def validate_photo(self, photo_id: int) -> Tuple[bool, List[str]]:
        """Performs rigorous validation on captured photo record."""
        photo = self.photo_repo.get_by_id(photo_id)
        if not photo:
            return False, ["Foto tidak ditemukan di database."]

        target_id = str(photo_id)
        self.validation_repo.clear_for_target("photo", target_id)
        errors: List[str] = []

        def record_check(rule: str, is_valid: bool, msg: str):
            self.validation_repo.add_result(ValidationResultModel(
                target_type="photo",
                target_id=target_id,
                is_valid=1 if is_valid else 0,
                rule_name=rule,
                message=msg
            ))
            if not is_valid:
                errors.append(f"[{rule}] {msg}")

        # 1. Filename validation
        f_ok, f_msg = validate_filename(photo.filename_base)
        record_check("FILENAME_FORMAT", f_ok, f_msg or "Nama file sesuai konvensi.")

        # 2. Interval validation
        i_ok, i_msg = validate_interval(photo.interval_from, photo.interval_to)
        record_check("DEPTH_INTERVAL", i_ok, i_msg or "Interval kedalaman valid.")

        # 3. RAW existence & integrity
        raw_path = Path(photo.raw_path) if photo.raw_path else None
        if not raw_path or not raw_path.exists():
            record_check("RAW_FILE_EXISTS", False, f"File RAW tidak ditemukan pada path: {photo.raw_path}")
        else:
            calc_md5 = RawHandler.calculate_md5(raw_path)
            md5_match = (calc_md5 == photo.md5_raw) if photo.md5_raw else True
            record_check("RAW_MD5_INTEGRITY", md5_match, "MD5 RAW cocok." if md5_match else "Integritas RAW rusak (MD5 mismatch).")

        # 4. JPG existence & integrity
        jpg_path = Path(photo.jpg_path) if photo.jpg_path else None
        if not jpg_path or not jpg_path.exists():
            record_check("JPG_FILE_EXISTS", False, f"File JPG tidak ditemukan pada path: {photo.jpg_path}")
        else:
            calc_md5 = RawHandler.calculate_md5(jpg_path)
            md5_match = (calc_md5 == photo.md5_jpg) if photo.md5_jpg else True
            record_check("JPG_MD5_INTEGRITY", md5_match, "MD5 JPG cocok." if md5_match else "Integritas JPG rusak (MD5 mismatch).")

        # 5. Thumbnail existence
        thumb_path = Path(photo.thumbnail_path) if photo.thumbnail_path else None
        if not thumb_path or not thumb_path.exists():
            record_check("THUMBNAIL_EXISTS", False, f"Thumbnail tidak ditemukan: {photo.thumbnail_path}")
        else:
            record_check("THUMBNAIL_EXISTS", True, "Thumbnail tersedia.")

        # 6. Metadata sidecar file
        if jpg_path:
            meta_json = jpg_path.with_suffix(".json")
            record_check("METADATA_SIDECAR", meta_json.exists(), "Metadata sidecar JSON tersedia." if meta_json.exists() else "File metadata .json tidak ditemukan.")

        all_valid = (len(errors) == 0)
        new_status = PhotoStatus.VALID if all_valid else PhotoStatus.INVALID
        self.photo_repo.update_status(photo_id, new_status)
        logger.info("Validation completed for photo %d: status=%s", photo_id, new_status.value)
        return all_valid, errors
