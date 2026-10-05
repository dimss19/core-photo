"""Interval validation (PRD Section 11).
Validates drill core depth intervals: To >= From, positive numbers.
"""

from typing import Any, Optional, Tuple


def validate_interval(interval_from: Any, interval_to: Any) -> Tuple[bool, Optional[str]]:
    """Validates depth interval inputs.
    Returns (is_valid, error_message).
    """
    try:
        f_val = float(interval_from)
        t_val = float(interval_to)
    except (ValueError, TypeError):
        return False, "Nilai interval kedalaman harus berupa angka numerik valid."

    if f_val < 0.0 or t_val < 0.0:
        return False, "Interval kedalaman tidak boleh bernilai negatif."

    if t_val < f_val:
        return False, f"Core Interval To ({t_val:.2f}) tidak boleh lebih kecil dari Core Interval From ({f_val:.2f})."

    return True, None
