"""Metadata validation (PRD Section 16 & 20).
Validates completeness and integrity of metadata sidecar.
"""

from typing import Any, Dict, List, Tuple

MANDATORY_METADATA_FIELDS = [
    "hole_id",
    "tray_id",
    "interval_from",
    "interval_to",
    "date",
    "operator",
    "site",
    "md5_raw",
    "md5_jpg",
    "timestamp",
    "tray_crop",
    "camera_model",
]


def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Checks metadata dictionary for missing or empty mandatory fields."""
    errors: List[str] = []

    for field in MANDATORY_METADATA_FIELDS:
        val = metadata.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Metadata field '{field}' wajib diisi dan tidak boleh kosong.")

    # Validate interval logic inside metadata
    try:
        f_val = float(metadata.get("interval_from", 0))
        t_val = float(metadata.get("interval_to", 0))
        if t_val < f_val:
            errors.append(f"Interval kedalaman tidak valid: To ({t_val}) < From ({f_val}).")
    except (ValueError, TypeError):
        errors.append("Nilai interval_from atau interval_to pada metadata bukan angka valid.")

    return len(errors) == 0, errors
