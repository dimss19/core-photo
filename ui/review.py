"""Review and Retake Screen (Professional Industrial Redesign).
Enables the operator to inspect the captured drill core photo, view metadata and MD5 checksums,
and immediately choose to [ SAVE PHOTO ] and advance or [ RETAKE ].
Zero emojis, strict professional standards.
"""

import os
from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk
from PIL import Image

from core.app_context import get_app_context
from core.logger import get_logger
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_BORDER_STRONG,
    COLOR_CHARCOAL,
    COLOR_ERROR,
    COLOR_PANEL,
    COLOR_PANEL_ALT,
    COLOR_SUCCESS,
    COLOR_SUCCESS_BG,
    COLOR_SUCCESS_BORDER,
    COLOR_TEXT_HINT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    COLOR_WARNING_BG,
    COLOR_WARNING_BORDER,
    get_font,
)

logger = get_logger(__name__)


class ReviewView(ctk.CTkFrame):
    """Post-capture inspection and decision screen."""

    def __init__(
        self,
        master,
        navigate_fn: Callable[[str], None],
        advance_tray_fn: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.advance_tray_fn = advance_tray_fn
        self.ctx = get_app_context()
        self._ctk_image: Optional[ctk.CTkImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=3)  # Left: Large photo inspection
        self.grid_columnconfigure(1, weight=2)  # Right: Metadata & Decision
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # 1. LEFT PANEL: Large Photo Preview
        # =========================================================================
        preview_panel = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        preview_panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        preview_panel.grid_rowconfigure(1, weight=1)
        preview_panel.grid_columnconfigure(0, weight=1)

        # Header
        header_box = ctk.CTkFrame(preview_panel, fg_color="transparent")
        header_box.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(
            header_box,
            text="PHOTO INSPECTION",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_box,
            text="Inspect standardized crop framing (300:200 aspect ratio) and optical clarity.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Preview Container
        self.img_container = ctk.CTkFrame(
            preview_panel,
            fg_color="#09090B",
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.img_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=6)
        self.img_container.grid_rowconfigure(0, weight=1)
        self.img_container.grid_columnconfigure(0, weight=1)

        self.img_label = ctk.CTkLabel(
            self.img_container,
            text="No captured photo loaded.",
            font=get_font(12),
            text_color=COLOR_TEXT_HINT,
        )
        self.img_label.grid(row=0, column=0)

        # Filename Banner Footer
        self.filename_banner = ctk.CTkLabel(
            preview_panel,
            text="",
            font=get_font(11, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        self.filename_banner.grid(row=2, column=0, sticky="w", padx=16, pady=(6, 14))

        # =========================================================================
        # 2. RIGHT PANEL: Metadata & Clear Decision Actions
        # =========================================================================
        right_panel = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        ctk.CTkLabel(
            right_panel,
            text="METADATA & VALIDATION",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            right_panel,
            text="Image verification records and checksum integrity.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Metadata Card
        meta_card = ctk.CTkFrame(
            right_panel,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        meta_card.pack(fill="x", padx=14, pady=4)

        self.lbl_meta_hole = ctk.CTkLabel(meta_card, text="Hole ID: -", font=get_font(12, "bold"), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_meta_hole.pack(anchor="w", padx=14, pady=(10, 2))

        self.lbl_meta_tray = ctk.CTkLabel(meta_card, text="Tray Number: -", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_meta_tray.pack(anchor="w", padx=14, pady=2)

        self.lbl_meta_interval = ctk.CTkLabel(meta_card, text="Depth Interval: -", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_meta_interval.pack(anchor="w", padx=14, pady=2)

        self.lbl_meta_timestamp = ctk.CTkLabel(meta_card, text="Timestamp: -", font=get_font(11), text_color=COLOR_TEXT_MUTED)
        self.lbl_meta_timestamp.pack(anchor="w", padx=14, pady=2)

        self.lbl_meta_camera = ctk.CTkLabel(meta_card, text="Camera: -", font=get_font(11), text_color=COLOR_TEXT_MUTED)
        self.lbl_meta_camera.pack(anchor="w", padx=14, pady=2)

        self.lbl_meta_md5 = ctk.CTkLabel(
            meta_card,
            text="MD5: -",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLOR_TEXT_HINT,
            justify="left",
        )
        self.lbl_meta_md5.pack(anchor="w", padx=14, pady=(4, 10))

        # Validation Status Indicator
        self.validation_badge = ctk.CTkFrame(
            right_panel,
            fg_color=COLOR_SUCCESS_BG,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_SUCCESS_BORDER,
        )
        self.validation_badge.pack(fill="x", padx=14, pady=10)

        self.validation_badge_lbl = ctk.CTkLabel(
            self.validation_badge,
            text="STATUS: VALIDATED",
            font=get_font(11, "bold"),
            text_color=COLOR_SUCCESS,
        )
        self.validation_badge_lbl.pack(pady=8)

        # Operational Decision Actions
        ctk.CTkLabel(
            right_panel,
            text="OPERATOR DECISION",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            right_panel,
            text="Approve the photo to advance or retake immediately.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(0, 8))

        # 1. Primary: [ SAVE PHOTO ]
        self.btn_save_next = ctk.CTkButton(
            right_panel,
            text="SAVE PHOTO",
            font=get_font(13, "bold"),
            height=44,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_save_next,
        )
        self.btn_save_next.pack(fill="x", padx=14, pady=(2, 2))

        ctk.CTkLabel(
            right_panel,
            text="Confirms tray documentation, increments tray index, and returns to capture.",
            font=get_font(10),
            text_color=COLOR_TEXT_HINT,
            wraplength=270,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # 2. Secondary: [ RETAKE ] (Immediately visible, prominent)
        self.btn_retake = ctk.CTkButton(
            right_panel,
            text="RETAKE PHOTO",
            font=get_font(12, "bold"),
            height=38,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_ERROR,
            border_width=1,
            border_color=COLOR_ERROR,
            command=self._on_retake,
        )
        self.btn_retake.pack(fill="x", padx=14, pady=(2, 2))

        ctk.CTkLabel(
            right_panel,
            text="Discards this frame and immediately returns to live framing with same tray parameters.",
            font=get_font(10),
            text_color=COLOR_TEXT_HINT,
            wraplength=270,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # 3. Explorer Folder Action
        self.btn_open_folder = ctk.CTkButton(
            right_panel,
            text="Open Folder in Explorer",
            font=get_font(11),
            height=32,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_open_folder,
        )
        self.btn_open_folder.pack(fill="x", padx=14, pady=4)

    def refresh(self) -> None:
        """Loads last captured photo details."""
        photo = self.ctx.last_photo
        if not photo:
            self.img_label.configure(text="No photo available.\nCapture a photo from the Capture screen.")
            self.filename_banner.configure(text="")
            self.lbl_meta_hole.configure(text="Hole ID: -")
            self.lbl_meta_tray.configure(text="Tray Number: -")
            self.lbl_meta_interval.configure(text="Depth Interval: -")
            self.lbl_meta_timestamp.configure(text="Timestamp: -")
            self.lbl_meta_camera.configure(text="Camera: -")
            self.lbl_meta_md5.configure(text="MD5: -")
            self.btn_save_next.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)
            self.btn_retake.configure(state="disabled", text_color=COLOR_TEXT_HINT, border_color=COLOR_BORDER_STRONG)
            return

        self.btn_save_next.configure(state="normal", fg_color=COLOR_ACCENT)
        self.btn_retake.configure(state="normal", text_color=COLOR_ERROR, border_color=COLOR_ERROR)

        self.filename_banner.configure(text=f"File: {photo.filename_base}.jpg")
        self.lbl_meta_hole.configure(text=f"Hole ID: {photo.hole_id}")
        self.lbl_meta_tray.configure(text=f"Tray Number: {photo.tray_number}")
        self.lbl_meta_interval.configure(text=f"Depth Interval: {photo.interval_from:.2f} m - {photo.interval_to:.2f} m")
        self.lbl_meta_timestamp.configure(text=f"Timestamp: {photo.timestamp}")
        self.lbl_meta_camera.configure(text=f"Camera Model: {photo.camera_model}")
        self.lbl_meta_md5.configure(text=f"RAW MD5: {photo.md5_raw[:16]}...\nJPG MD5: {photo.md5_jpg[:16]}...")

        # Update validation status
        if photo.status == "VALID":
            self.validation_badge.configure(fg_color=COLOR_SUCCESS_BG, border_color=COLOR_SUCCESS_BORDER)
            self.validation_badge_lbl.configure(text="STATUS: VALIDATED (PASS)", text_color=COLOR_SUCCESS)
        else:
            self.validation_badge.configure(fg_color=COLOR_WARNING_BG, border_color=COLOR_WARNING_BORDER)
            self.validation_badge_lbl.configure(text=f"STATUS: {photo.status}", text_color=COLOR_WARNING)

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
                self.img_label.configure(text="Error loading image file.")
        else:
            self.img_label.configure(text="JPG file missing on storage disk.")

    def _on_save_next(self) -> None:
        """Saves current capture as accepted, advances tray, and returns to capture."""
        if self.advance_tray_fn:
            self.advance_tray_fn()
        self.navigate_fn("capture")

    def _on_retake(self) -> None:
        """Marks current capture as superseded and returns to capture for retake."""
        logger.info("Operator triggered Retake for last photo.")
        self.ctx.retake_current()
        self.navigate_fn("capture")

    def _on_open_folder(self) -> None:
        photo = self.ctx.last_photo
        if photo and photo.jpg_path:
            folder = str(Path(photo.jpg_path).parent)
            try:
                os.startfile(folder)
            except Exception as e:
                logger.error("Failed opening folder %s: %s", folder, e)
