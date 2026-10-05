"""Review and Retake Screen (PRD Section 14).
Enables the operator to review captured JPG/RAW, inspect validation status,
and choose to either Save & advance to Next Tray or Retake.
"""

import os
import subprocess
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
        super().__init__(master, **kwargs)
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
        preview_panel = ctk.CTkFrame(self, corner_radius=12)
        preview_panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        preview_panel.grid_rowconfigure(1, weight=1)
        preview_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_panel,
            text="Hasil Foto (Review Preview - 300x200 Cropped)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        self.img_container = ctk.CTkFrame(preview_panel, fg_color="#141414", corner_radius=8)
        self.img_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=6)
        self.img_container.grid_rowconfigure(0, weight=1)
        self.img_container.grid_columnconfigure(0, weight=1)

        self.img_label = ctk.CTkLabel(self.img_container, text="Memuat foto...")
        self.img_label.grid(row=0, column=0)

        self.filename_banner = ctk.CTkLabel(
            preview_panel,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2CC985"
        )
        self.filename_banner.grid(row=2, column=0, sticky="w", padx=16, pady=(6, 12))

        # ----------------- Right: Metadata & Decision -----------------
        right_panel = ctk.CTkScrollableFrame(self, corner_radius=12)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        ctk.CTkLabel(
            right_panel,
            text="Rincian & Validasi Foto",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=10, pady=(6, 12))

        # Metadata Card
        meta_card = ctk.CTkFrame(right_panel, fg_color="#222222", corner_radius=8)
        meta_card.pack(fill="x", padx=10, pady=6)

        self.lbl_meta_hole = ctk.CTkLabel(meta_card, text="Hole ID: -", font=ctk.CTkFont(size=13))
        self.lbl_meta_hole.pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_meta_tray = ctk.CTkLabel(meta_card, text="Tray No: -", font=ctk.CTkFont(size=13))
        self.lbl_meta_tray.pack(anchor="w", padx=12, pady=2)

        self.lbl_meta_interval = ctk.CTkLabel(meta_card, text="Interval: -", font=ctk.CTkFont(size=13))
        self.lbl_meta_interval.pack(anchor="w", padx=12, pady=2)

        self.lbl_meta_md5 = ctk.CTkLabel(meta_card, text="MD5 RAW: -", font=ctk.CTkFont(size=11), text_color="gray70")
        self.lbl_meta_md5.pack(anchor="w", padx=12, pady=(4, 8))

        # Validation Status Badge
        self.validation_badge = ctk.CTkFrame(right_panel, fg_color="#2CC985", corner_radius=6, height=36)
        self.validation_badge.pack(fill="x", padx=10, pady=10)
        self.validation_badge_lbl = ctk.CTkLabel(
            self.validation_badge,
            text="STATUS: TERVALIDASI (VALID)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#000000"
        )
        self.validation_badge_lbl.pack(pady=6)

        # Decision Actions (PRD Section 14)
        ctk.CTkLabel(
            right_panel,
            text="Tindakan Operator:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(16, 6))

        # 1. Save and Next Tray
        self.btn_save_next = ctk.CTkButton(
            right_panel,
            text="✅  Simpan & Lanjut Tray Berikutnya",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            fg_color="#2CC985",
            hover_color="#229965",
            command=self._on_save_next
        )
        self.btn_save_next.pack(fill="x", padx=10, pady=8)

        # 2. Retake
        self.btn_retake = ctk.CTkButton(
            right_panel,
            text="🔄  Ambil Ulang (Retake)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color="#D9534F",
            hover_color="#C0392B",
            command=self._on_retake
        )
        self.btn_retake.pack(fill="x", padx=10, pady=8)

        # 3. Open Folder
        self.btn_open_folder = ctk.CTkButton(
            right_panel,
            text="📂  Buka Folder Foto",
            font=ctk.CTkFont(size=13),
            height=36,
            fg_color="#333333",
            hover_color="#444444",
            command=self._on_open_folder
        )
        self.btn_open_folder.pack(fill="x", padx=10, pady=8)

    def refresh(self) -> None:
        """Loads last captured photo details."""
        photo = self.ctx.last_photo
        if not photo:
            self.img_label.configure(text="Belum ada foto yang diambil.")
            self.filename_banner.configure(text="")
            return

        self.filename_banner.configure(text=f"File: {photo.filename_base}.jpg")
        self.lbl_meta_hole.configure(text=f"Hole ID: {photo.hole_id}")
        self.lbl_meta_tray.configure(text=f"Tray No: {photo.tray_number}")
        self.lbl_meta_interval.configure(text=f"Interval: {photo.interval_from:.2f} m - {photo.interval_to:.2f} m")
        self.lbl_meta_md5.configure(text=f"MD5 RAW: {photo.md5_raw[:16]}... | JPG: {photo.md5_jpg[:16]}...")

        # Update validation badge
        if photo.status == "VALID":
            self.validation_badge.configure(fg_color="#2CC985")
            self.validation_badge_lbl.configure(text="STATUS: TERVALIDASI (VALID)", text_color="#000000")
        else:
            self.validation_badge.configure(fg_color="#E5A93C")
            self.validation_badge_lbl.configure(text=f"STATUS: {photo.status}", text_color="#000000")

        # Load image
        jpg_path = Path(photo.jpg_path)
        if jpg_path.exists():
            try:
                pil_img = Image.open(jpg_path)
                # Display large preview keeping 300:200 aspect ratio
                disp_w = 480
                disp_h = 320
                self._ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(disp_w, disp_h))
                self.img_label.configure(image=self._ctk_image, text="")
            except Exception as e:
                logger.error("Error loading preview image %s: %s", jpg_path, e)
                self.img_label.configure(text="Gagal memuat file gambar.")
        else:
            self.img_label.configure(text="File JPG belum tersedia.")

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
