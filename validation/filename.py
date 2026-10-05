"""Filename validation (PRD Section 11 & 15).
Validates drill core image naming convention: ID_Drillhole_NoTray_IntervalKedalaman.
"""

import re
from typing import Optional, Tuple

# Pattern matching: <HoleID>_<TrayNo>_<From>_<To>(.<ext>)?
# Example: Core01_1_000.00_2.60.jpg or Core01_1_000.00_2.60
FILENAME_REGEX = re.compile(
    r'^(?P<hole>[A-Za-z0-9_-]+)_(?P<tray>[A-Za-z0-9]+)_(?P<from>\d+(\.\d+)?)_(?P<to>\d+(\.\d+)?)(?P<ext>\.[a-zA-Z0-9]+)?$'
)


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """Validates if filename conforms to standard core naming convention."""
    if not filename or not filename.strip():
        return False, "Nama file tidak boleh kosong."

    match = FILENAME_REGEX.match(filename.strip())
    if not match:
        return False, (
            f"Format nama file '{filename}' tidak valid. "
            "Harus mengikuti konvensi: ID_Drillhole_NoTray_IntervalKedalaman (contoh: Core01_1_000.00_2.60.jpg)"
        )

    f_val = float(match.group("from"))
    t_val = float(match.group("to"))
    if t_val < f_val:
        return False, f"Interval kedalaman dalam nama file tidak valid: To ({t_val}) < From ({f_val})."

    return True, None
