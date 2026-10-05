"""Review and Retake Screen (PRD Section 14).
Enables the operator to review captured JPG/RAW, inspect validation status,
and choose to either Save & advance to Next Tray or Retake.
Designed with Light Mode aesthetics and clear visual action hierarchy.
"""

import os
from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk
from PIL import Image

from core.app_context import get_app_context
from core.logger import get_logger

logger = get_logger(__name__)


class ReviewView(ctk.CTkFrame):
    """Post-capture inspection and decision screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], advance_tray_fn: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="#F8FAFC", **kwargs)
        self.navigate_fn = navigate_fn
        self.advance_tray_fn = advance_tray_fn
        self.ctx = get_app_context()
        self._ctk_image: Optional[ctk.CTkImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=3)  # Image display
        self.grid_columnconfigure(1, weight=2)  # Metadata & Actions
        self.grid_rowconfigure(0, weight=1)

        # ----------------- Left: Large Photo Preview -----------------
        preview_panel = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        preview_panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        preview_panel.grid_rowconfigure(1, weight=1)
        preview_panel.grid_columnconfigure(0, weight=1)

        header_box = ctk.CTkFrame(preview_panel, fg_color="transparent")
        header_box.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(
            header_box,
            text="👁️ Review Hasil Foto Tray",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_box,
            text="Hasil potongan standar 300x200 pixel. Pastikan seluruh core berada di dalam bidang crop dan fokus tajam.",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).pack(anchor="w", pady=(2, 0))

        # Preview Container
        self.img_container = ctk.CTkFrame(preview_panel, fg_color="#F1F5F9", corner_radius=8, border_width=1, border_color="#CBD5E1")
        self.img_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        self.img_container.grid_rowconfigure(0, weight=1)
        self.img_container.grid_columnconfigure(0, weight=1)

        self.img_label = ctk.CTkLabel(self.img_container, text="Belum ada foto yang diambil.", font=ctk.CTkFont(size=13), text_color="#64748B")
        self.img_label.grid(row=0, column=0)

        # Filename & Status Footer
        self.filename_banner = ctk.CTkLabel(
            preview_panel,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#059669"
        )
        self.filename_banner.grid(row=2, column=0, sticky="w", padx=16, pady=(4, 14))

        # ----------------- Right: Metadata & Decision -----------------
        right_panel = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        ctk.CTkLabel(
            right_panel,
            text="Rincian & Validasi Foto",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            right_panel,
            text="Informasi metadata dan verifikasi integritas file.",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # Metadata Card
        meta_card = ctk.CTkFrame(right_panel, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color="#E2E8F0")
        meta_card.pack(fill="x", padx=10, pady=6)

        self.lbl_meta_hole = ctk.CTkLabel(meta_card, text="Hole ID: -", font=ctk.CTkFont(size=13, weight="bold"), text_color="#1E293B")
        self.lbl_meta_hole.pack(anchor="w", padx=14, pady=(10, 3))

        self.lbl_meta_tray = ctk.CTkLabel(meta_card, text="Nomor Tray: -", font=ctk.CTkFont(size=13), text_color="#334155")
        self.lbl_meta_tray.pack(anchor="w", padx=14, pady=3)

        self.lbl_meta_interval = ctk.CTkLabel(meta_card, text="Interval: -", font=ctk.CTkFont(size=13), text_color="#334155")
        self.lbl_meta_interval.pack(anchor="w", padx=14, pady=3)

        self.lbl_meta_md5 = ctk.CTkLabel(meta_card, text="MD5 RAW: -", font=ctk.CTkFont(family="Consolas", size=11), text_color="#64748B")
        self.lbl_meta_md5.pack(anchor="w", padx=14, pady=(4, 10))

        # Validation Status Badge
        self.validation_badge = ctk.CTkFrame(right_panel, fg_color="#ECFDF5", corner_radius=8, border_width=1, border_color="#A7F3D0")
        self.validation_badge.pack(fill="x", padx=10, pady=10)

        self.validation_badge_lbl = ctk.CTkLabel(
            self.validation_badge,
            text="STATUS: TERVALIDASI (VALID)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#065F46"
        )
        self.validation_badge_lbl.pack(pady=8)

        # Decision Actions Section
        ctk.CTkLabel(
            right_panel,
            text="Keputusan Operator:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=10, pady=(12, 2))

        ctk.CTkLabel(
            right_panel,
            text="Pilih tindakan untuk foto tray ini:",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # 1. Save and Next Tray (Primary Emerald Button)
        self.btn_save_next = ctk.CTkButton(
            right_panel,
            text="✅  Simpan & Lanjut Tray Berikutnya",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            corner_radius=8,
            fg_color="#059669",
            hover_color="#047857",
            command=self._on_save_next
        )
        self.btn_save_next.pack(fill="x", padx=10, pady=(4, 2))

        ctk.CTkLabel(
            right_panel,
            text="Menyetujui foto, menaikkan nomor tray, dan kembali ke live view.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # 2. Retake (Danger Red Button)
        self.btn_retake = ctk.CTkButton(
            right_panel,
            text="🔄  Ambil Ulang (Retake Foto)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self._on_retake
        )
        self.btn_retake.pack(fill="x", padx=10, pady=(4, 2))

        ctk.CTkLabel(
            right_panel,
            text="Tandai foto ini gagal dan ambil ulang tanpa mengubah nomor tray.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # 3. Open Folder
        self.btn_open_folder = ctk.CTkButton(
            right_panel,
            text="📂  Buka Folder Foto di Explorer",
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=8,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            command=self._on_open_folder
        )
        self.btn_open_folder.pack(fill="x", padx=10, pady=4)

    def refresh(self) -> None:
        """Loads last captured photo details."""
        photo = self.ctx.last_photo
        if not photo:
            self.img_label.configure(text="Belum ada foto yang diambil.\nAmbil foto dari menu Capture terlebih dahulu.")
            self.filename_banner.configure(text="")
            self.lbl_meta_hole.configure(text="Hole ID: -")
            self.lbl_meta_tray.configure(text="Nomor Tray: -")
            self.lbl_meta_interval.configure(text="Interval: -")
            self.lbl_meta_md5.configure(text="MD5: -")
            self.btn_save_next.configure(state="disabled", fg_color="#94A3B8")
            self.btn_retake.configure(state="disabled", fg_color="#94A3B8")
            return

        self.btn_save_next.configure(state="normal", fg_color="#059669")
        self.btn_retake.configure(state="normal", fg_color="#EF4444")

        self.filename_banner.configure(text=f"Nama File: {photo.filename_base}.jpg")
        self.lbl_meta_hole.configure(text=f"Hole ID: {photo.hole_id}")
        self.lbl_meta_tray.configure(text=f"Nomor Tray: {photo.tray_number}")
        self.lbl_meta_interval.configure(text=f"Interval: {photo.interval_from:.2f} m - {photo.interval_to:.2f} m")
        self.lbl_meta_md5.configure(text=f"MD5 RAW: {photo.md5_raw[:16]}...\nMD5 JPG: {photo.md5_jpg[:16]}...")

        # Update validation badge
        if photo.status == "VALID":
            self.validation_badge.configure(fg_color="#ECFDF5", border_color="#A7F3D0")
            self.validation_badge_lbl.configure(text="STATUS: TERVALIDASI LENGKAP (VALID)", text_color="#065F46")
        else:
            self.validation_badge.configure(fg_color="#FFFBEB", border_color="#FDE68A")
            self.validation_badge_lbl.configure(text=f"STATUS: {photo.status}", text_color="#92400E")

        # Load image
        jpg_path = Path(photo.jpg_path)
        if jpg_path.exists():
            try:
                pil_img = Image.open(jpg_path)
                disp_w = 480
                disp_h = 320
                self._ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(disp_w, disp_h))
                self.img_label.configure(image=self._ctk_image, text="")
            except Exception as e:
                logger.error("Error loading preview image %s: %s", jpg_path, e)
                self.img_label.configure(text="Gagal memuat file gambar.")
        else:
            self.img_label.configure(text="File JPG belum tersedia di disk.")

    def _on_save_next(self) -> None:
        """Saves current capture as accepted, advances tray, and returns to capture."""
        if self.advance_tray_fn:
            self.advance_tray_fn()
        self.navigate_fn("capture")

    def _on_retake(self) -> None:
        """Marks current capture as superseded and returns to capture for retake (PRD Section 14)."""
        logger.info("Operator triggered Retake for last photo.")
        self.ctx.retake_current()
        # Return to capture without advancing tray
        self.navigate_fn("capture")

    def _on_open_folder(self) -> None:
        """Opens session folder in Windows Explorer."""
        if self.ctx.session_paths and self.ctx.session_paths.session_dir.exists():
            try:
                os.startfile(str(self.ctx.session_paths.jpg_dir))
            except Exception as e:
                logger.error("Could not open explorer: %s", e)
