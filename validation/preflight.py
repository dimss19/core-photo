"""Pre-flight Check Engine (PRD Section 9 & 24).
Validates 10 critical operational readiness checks before permitting capture.
Provides human-readable actions for any failing check.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from camera.manager import CameraManager
from database.models import SessionModel
from imaging.crop import CropRegion
from storage.manager import StorageManager
from .interval import validate_interval


@dataclass
class PreflightItem:
    name: str
    passed: bool
    message: str
    remedy_action: str


@dataclass
class PreflightResult:
    is_ready: bool
    items: List[PreflightItem] = field(default_factory=list)

    @property
    def summary_errors(self) -> List[str]:
        return [f"{it.name}: {it.message} -> {it.remedy_action}" for it in self.items if not it.passed]


class PreflightChecker:
    """Evaluates all 10 pre-flight criteria."""

    @staticmethod
    def check(
        camera_manager: CameraManager,
        active_session: Optional[SessionModel],
        hole_id: str,
        tray_id: str,
        interval_from: float,
        interval_to: float,
        storage_manager: StorageManager,
        crop_region: Optional[CropRegion] = None,
        min_storage_mb: float = 300.0,
    ) -> PreflightResult:
        items: List[PreflightItem] = []

        # 1. Camera connected
        cam_info = camera_manager.get_info()
        cam_connected = cam_info is not None and camera_manager.is_ready()
        items.append(PreflightItem(
            name="Camera Connected",
            passed=cam_connected,
            message="Kamera terhubung." if cam_connected else "Kamera tidak terhubung.",
            remedy_action="" if cam_connected else "Periksa kabel USB kamera atau pastikan webcam aktif."
        ))

        # 2. Camera ready
        cam_ready = camera_manager.is_ready()
        items.append(PreflightItem(
            name="Camera Ready",
            passed=cam_ready,
            message="Kamera siap." if cam_ready else "Kamera sedang sibuk atau error.",
            remedy_action="" if cam_ready else "Tunggu beberapa saat atau buka menu Diagnostics untuk reconnect."
        ))

        # 3. Session aktif
        session_valid = active_session is not None and bool(active_session.id)
        items.append(PreflightItem(
            name="Active Session",
            passed=session_valid,
            message=f"Sesi aktif: {active_session.site} ({active_session.date})" if session_valid else "Tidak ada sesi aktif.",
            remedy_action="" if session_valid else "Buat sesi baru atau buka sesi sebelumnya di Dashboard."
        ))

        # 4. Hole ID terisi
        hole_ok = bool(hole_id and hole_id.strip())
        items.append(PreflightItem(
            name="Hole ID",
            passed=hole_ok,
            message=f"Hole ID: {hole_id}" if hole_ok else "Hole ID belum diisi.",
            remedy_action="" if hole_ok else "Isi Hole ID (contoh: Core01)."
        ))

        # 5. Tray ID terisi
        tray_ok = bool(tray_id and str(tray_id).strip())
        items.append(PreflightItem(
            name="Tray ID",
            passed=tray_ok,
            message=f"Tray ID: {tray_id}" if tray_ok else "Tray ID belum diisi.",
            remedy_action="" if tray_ok else "Isi nomor Tray (contoh: 1, 2, dll)."
        ))

        # 6. Interval valid (To >= From)
        interval_valid, int_err = validate_interval(interval_from, interval_to)
        items.append(PreflightItem(
            name="Depth Interval",
            passed=interval_valid,
            message=f"Interval valid ({interval_from:.2f} - {interval_to:.2f} m)" if interval_valid else (int_err or "Interval invalid"),
            remedy_action="" if interval_valid else "Pastikan Core Interval To lebih besar atau sama dengan From."
        ))

        # 7. Tray data lengkap
        data_complete = hole_ok and tray_ok and interval_valid
        items.append(PreflightItem(
            name="Tray Data Completeness",
            passed=data_complete,
            message="Data tray lengkap." if data_complete else "Data tray belum lengkap.",
            remedy_action="" if data_complete else "Lengkapi seluruh field wajib pada data tray."
        ))

        # 8. Storage tersedia
        storage_ok = storage_manager.is_storage_sufficient(min_mb=min_storage_mb)
        avail_mb = storage_manager.get_available_space_mb()
        items.append(PreflightItem(
            name="Storage Space",
            passed=storage_ok,
            message=f"Penyimpanan tersedia ({avail_mb:.1f} MB bebas)." if storage_ok else f"Penyimpanan hampir penuh ({avail_mb:.1f} MB tersisa).",
            remedy_action="" if storage_ok else "Kosongkan ruang disk sebelum melanjutkan capture."
        ))

        # 9. Tray Crop tersedia
        crop_ok = crop_region is not None and crop_region.width > 20 and crop_region.height > 20
        items.append(PreflightItem(
            name="Tray Crop Region",
            passed=crop_ok,
            message="Tray Crop telah disetel." if crop_ok else "Tray Crop belum disetel.",
            remedy_action="" if crop_ok else "Sesuaikan area framing Tray Crop pada Live View."
        ))

        # 10. Camera configuration valid
        caps = camera_manager.get_capabilities()
        cam_cfg_ok = caps.can_capture
        items.append(PreflightItem(
            name="Camera Configuration",
            passed=cam_cfg_ok,
            message="Konfigurasi kamera valid." if cam_cfg_ok else "Kamera tidak mendukung capture.",
            remedy_action="" if cam_cfg_ok else "Pilih kamera yang kompatibel."
        ))

        all_passed = all(item.passed for item in items)
        return PreflightResult(is_ready=all_passed, items=items)
