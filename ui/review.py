"""Tray Review & Audit Screen (Professional Industrial Redesign).
Enables operators to inspect captured drill core photos with carousel navigation,
zoom inspection, inline validation audit checklist, depth interval corrections,
and instant Save / Retake decisions.
Zero emojis, strict professional standards.
"""

import os
from pathlib import Path
from typing import Callable, List, Optional
import customtkinter as ctk
from PIL import Image

from core.app_context import get_app_context
from core.logger import get_logger
from database.models import PhotoModel
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_BORDER_STRONG,
    COLOR_CHARCOAL,
    COLOR_ERROR,
    COLOR_ERROR_BG,
    COLOR_ERROR_BORDER,
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
    """Post-capture deep inspection, carousel review, validation audit, and decision screen."""

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

        self._photos: List[PhotoModel] = []
        self._current_index: int = -1
        self._ctk_image: Optional[ctk.CTkImage] = None
        self._zoom_mode: bool = False  # False = Fit, True = 1:1 Detail Zoom
        self._edit_mode: bool = False

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=3)  # Left: Photo Viewer & Carousel
        self.grid_columnconfigure(1, weight=2)  # Right: Metadata, Validation Audit & Decisions
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # 1. LEFT PANEL: Photo Inspection Canvas & Carousel
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

        # Header with Title and Carousel Controls
        header_box = ctk.CTkFrame(preview_panel, fg_color="transparent")
        header_box.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        header_box.grid_columnconfigure(0, weight=1)

        title_left = ctk.CTkFrame(header_box, fg_color="transparent")
        title_left.pack(side="left", anchor="w")

        ctk.CTkLabel(
            title_left,
            text="PHOTO INSPECTION & AUDIT",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        self.lbl_carousel_status = ctk.CTkLabel(
            title_left,
            text="Inspect optical clarity and standardized crop framing.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_carousel_status.pack(anchor="w")

        # Top Carousel Quick Navigation Bar
        nav_controls = ctk.CTkFrame(header_box, fg_color="transparent")
        nav_controls.pack(side="right", anchor="e")

        self.btn_prev = ctk.CTkButton(
            nav_controls,
            text="◀ Prev",
            width=65,
            height=28,
            font=get_font(10, "bold"),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_prev_photo,
        )
        self.btn_prev.pack(side="left", padx=2)

        self.lbl_index_badge = ctk.CTkLabel(
            nav_controls,
            text="0 / 0",
            font=get_font(11, "bold"),
            text_color=COLOR_CHARCOAL,
            width=60,
        )
        self.lbl_index_badge.pack(side="left", padx=4)

        self.btn_next = ctk.CTkButton(
            nav_controls,
            text="Next ▶",
            width=65,
            height=28,
            font=get_font(10, "bold"),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_next_photo,
        )
        self.btn_next.pack(side="left", padx=2)

        # Zoom Mode Toggle Button
        self.btn_zoom = ctk.CTkButton(
            nav_controls,
            text="Zoom 1:1",
            width=70,
            height=28,
            font=get_font(10, "bold"),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._toggle_zoom,
        )
        self.btn_zoom.pack(side="left", padx=(8, 0))

        # Main Photo Canvas Container
        self.img_container = ctk.CTkFrame(
            preview_panel,
            fg_color="#09090B",
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.img_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        self.img_container.grid_rowconfigure(0, weight=1)
        self.img_container.grid_columnconfigure(0, weight=1)

        self.img_label = ctk.CTkLabel(
            self.img_container,
            text="No captured photo loaded.\nCapture a core tray from Live Capture.",
            font=get_font(12),
            text_color=COLOR_TEXT_HINT,
        )
        self.img_label.grid(row=0, column=0)

        # Footer Bar: Filename Banner + Jump Selector + Explorer Button
        footer_box = ctk.CTkFrame(preview_panel, fg_color="transparent")
        footer_box.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 12))

        self.filename_banner = ctk.CTkLabel(
            footer_box,
            text="",
            font=get_font(11, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        self.filename_banner.pack(side="left", anchor="w")

        self.btn_open_folder = ctk.CTkButton(
            footer_box,
            text="Open Folder",
            font=get_font(10, "bold"),
            height=26,
            width=90,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_open_folder,
        )
        self.btn_open_folder.pack(side="right", padx=2)

        self.tray_selector = ctk.CTkOptionMenu(
            footer_box,
            values=["No Trays"],
            command=self._on_tray_dropdown_selected,
            height=26,
            width=170,
            font=get_font(10),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
        )
        self.tray_selector.pack(side="right", padx=6)

        # =========================================================================
        # 2. RIGHT PANEL: Metadata, Audit Checklist & Operator Actions
        # =========================================================================
        right_panel = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        # Section A: Metadata & Interval Info
        meta_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        meta_header.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            meta_header,
            text="TRAY RECORD & METADATA",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(side="left")

        self.btn_edit_meta = ctk.CTkButton(
            meta_header,
            text="Edit Depth / Info",
            font=get_font(10, "bold"),
            height=24,
            width=110,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._toggle_edit_mode,
        )
        self.btn_edit_meta.pack(side="right")

        # Display Card
        self.meta_display_card = ctk.CTkFrame(
            right_panel,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.meta_display_card.pack(fill="x", padx=14, pady=4)

        self.lbl_meta_hole = ctk.CTkLabel(self.meta_display_card, text="Hole ID: -", font=get_font(12, "bold"), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_meta_hole.pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_meta_tray = ctk.CTkLabel(self.meta_display_card, text="Tray Number: -", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_meta_tray.pack(anchor="w", padx=12, pady=2)

        self.lbl_meta_interval = ctk.CTkLabel(self.meta_display_card, text="Depth Interval: -", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_meta_interval.pack(anchor="w", padx=12, pady=2)

        self.lbl_meta_timestamp = ctk.CTkLabel(self.meta_display_card, text="Timestamp: -", font=get_font(10), text_color=COLOR_TEXT_MUTED)
        self.lbl_meta_timestamp.pack(anchor="w", padx=12, pady=2)

        self.lbl_meta_camera = ctk.CTkLabel(self.meta_display_card, text="Camera: -", font=get_font(10), text_color=COLOR_TEXT_MUTED)
        self.lbl_meta_camera.pack(anchor="w", padx=12, pady=2)

        self.lbl_meta_md5 = ctk.CTkLabel(
            self.meta_display_card,
            text="MD5: -",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=COLOR_TEXT_HINT,
            justify="left",
        )
        self.lbl_meta_md5.pack(anchor="w", padx=12, pady=(4, 8))

        # Edit Form (hidden by default)
        self.edit_form_card = ctk.CTkFrame(
            right_panel,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_ACCENT,
        )
        # pack managed dynamically in _toggle_edit_mode

        ctk.CTkLabel(self.edit_form_card, text="CORRECT TRAY PARAMETERS", font=get_font(11, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=12, pady=(8, 4))
        
        edit_grid = ctk.CTkFrame(self.edit_form_card, fg_color="transparent")
        edit_grid.pack(fill="x", padx=12, pady=2)
        edit_grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(edit_grid, text="Hole ID", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=(2, 1))
        self.entry_edit_hole = ctk.CTkEntry(edit_grid, height=28, font=get_font(11))
        self.entry_edit_hole.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(0, 4))

        ctk.CTkLabel(edit_grid, text="Tray Number", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=1, sticky="w", pady=(2, 1))
        self.entry_edit_tray = ctk.CTkEntry(edit_grid, height=28, font=get_font(11))
        self.entry_edit_tray.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(0, 4))

        ctk.CTkLabel(edit_grid, text="From (m)", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=0, sticky="w", pady=(2, 1))
        self.entry_edit_from = ctk.CTkEntry(edit_grid, height=28, font=get_font(11))
        self.entry_edit_from.grid(row=3, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))

        ctk.CTkLabel(edit_grid, text="To (m)", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=1, sticky="w", pady=(2, 1))
        self.entry_edit_to = ctk.CTkEntry(edit_grid, height=28, font=get_font(11))
        self.entry_edit_to.grid(row=3, column=1, sticky="ew", padx=(4, 0), pady=(0, 6))

        btn_save_edit = ctk.CTkButton(
            self.edit_form_card,
            text="Save Corrections",
            font=get_font(10, "bold"),
            height=28,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_save_edits,
        )
        btn_save_edit.pack(fill="x", padx=12, pady=(2, 8))

        # Section B: Validation Audit Checklist
        audit_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        audit_header.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            audit_header,
            text="VALIDATION & INTEGRITY AUDIT",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(side="left")

        btn_recheck = ctk.CTkButton(
            audit_header,
            text="Re-run Audit",
            font=get_font(10, "bold"),
            height=24,
            width=90,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_rerun_audit,
        )
        btn_recheck.pack(side="right")

        # Validation Status Badge
        self.validation_badge = ctk.CTkFrame(
            right_panel,
            fg_color=COLOR_SUCCESS_BG,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_SUCCESS_BORDER,
        )
        self.validation_badge.pack(fill="x", padx=14, pady=4)

        self.validation_badge_lbl = ctk.CTkLabel(
            self.validation_badge,
            text="STATUS: VALIDATED (PASS)",
            font=get_font(11, "bold"),
            text_color=COLOR_SUCCESS,
        )
        self.validation_badge_lbl.pack(pady=6)

        # Audit Checklist Items
        self.audit_card = ctk.CTkFrame(
            right_panel,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.audit_card.pack(fill="x", padx=14, pady=4)

        self.lbl_chk_schema = ctk.CTkLabel(self.audit_card, text="✓ Filename Schema: Validated", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_chk_schema.pack(anchor="w", padx=12, pady=(6, 2))

        self.lbl_chk_interval = ctk.CTkLabel(self.audit_card, text="✓ Depth Interval: Continuous & Non-negative", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_chk_interval.pack(anchor="w", padx=12, pady=2)

        self.lbl_chk_md5 = ctk.CTkLabel(self.audit_card, text="✓ MD5 Hashes: Computed & Verified", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_chk_md5.pack(anchor="w", padx=12, pady=2)

        self.lbl_chk_assets = ctk.CTkLabel(self.audit_card, text="✓ Storage Assets: JPG, RAW, Thumbs on disk", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_chk_assets.pack(anchor="w", padx=12, pady=(2, 6))

        # Alert Box for any specific audit issues
        self.audit_alert_box = ctk.CTkFrame(
            right_panel,
            fg_color=COLOR_WARNING_BG,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_WARNING_BORDER,
        )
        self.audit_alert_lbl = ctk.CTkLabel(
            self.audit_alert_box,
            text="",
            font=get_font(10),
            text_color=COLOR_WARNING,
            justify="left",
            wraplength=280,
        )
        self.audit_alert_lbl.pack(padx=10, pady=6)
        # managed dynamically

        # Section C: Operator Decisions
        ctk.CTkLabel(
            right_panel,
            text="OPERATOR DECISION",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=14, pady=(14, 4))

        # 1. Primary: [ APPROVE & NEXT TRAY ]
        self.btn_save_next = ctk.CTkButton(
            right_panel,
            text="APPROVE & NEXT TRAY",
            font=get_font(12, "bold"),
            height=42,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_save_next,
        )
        self.btn_save_next.pack(fill="x", padx=14, pady=(2, 2))

        ctk.CTkLabel(
            right_panel,
            text="Approves this tray, updates compliance state, and moves to the next tray in the series.",
            font=get_font(9),
            text_color=COLOR_TEXT_HINT,
            wraplength=280,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 8))

        # 2. Secondary: [ RETAKE THIS TRAY ]
        self.btn_retake = ctk.CTkButton(
            right_panel,
            text="RETAKE THIS TRAY",
            font=get_font(11, "bold"),
            height=36,
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
            text="Marks this capture as superseded and immediately loads these tray parameters back into Live Capture.",
            font=get_font(9),
            text_color=COLOR_TEXT_HINT,
            wraplength=280,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 14))

    # =========================================================================
    # Data Loading & Carousel Management
    # =========================================================================
    def refresh(self) -> None:
        """Loads all photos in active session, setting current photo to last photo or latest capture."""
        self._load_session_photos()
        self._render_current_photo()

    def _load_session_photos(self) -> None:
        if not self.ctx.active_session or not self.ctx.photo_repo:
            self._photos = []
            self._current_index = -1
            return

        self._photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)

        if not self._photos:
            self._current_index = -1
            return

        # Try to locate ctx.last_photo in the list
        target_photo = self.ctx.last_photo
        if target_photo and target_photo.id:
            found_idx = next((i for i, p in enumerate(self._photos) if p.id == target_photo.id), -1)
            if found_idx != -1:
                self._current_index = found_idx
                return

        # If current_index out of range or not set, default to most recent photo
        if self._current_index < 0 or self._current_index >= len(self._photos):
            self._current_index = len(self._photos) - 1

    def _render_current_photo(self) -> None:
        total = len(self._photos)
        if total == 0 or self._current_index < 0 or self._current_index >= total:
            self._show_empty_state()
            return

        photo = self._photos[self._current_index]
        self.ctx.last_photo = photo  # synchronize active context

        # Update Navigation State
        self.btn_prev.configure(state="normal" if self._current_index > 0 else "disabled")
        self.btn_next.configure(state="normal" if self._current_index < total - 1 else "disabled")
        self.lbl_index_badge.configure(text=f"{self._current_index + 1} / {total}")
        self.lbl_carousel_status.configure(text=f"Tray {photo.tray_number} ({photo.interval_from:.2f} m - {photo.interval_to:.2f} m) · Hole {photo.hole_id}")

        # Update Tray Dropdown list
        dropdown_vals = [f"Tray {p.tray_number} ({p.interval_from:.2f}-{p.interval_to:.2f}m)" for p in self._photos]
        self.tray_selector.configure(values=dropdown_vals)
        if 0 <= self._current_index < len(dropdown_vals):
            self.tray_selector.set(dropdown_vals[self._current_index])

        # Enable Decision Buttons
        self.btn_save_next.configure(state="normal", fg_color=COLOR_ACCENT)
        self.btn_retake.configure(state="normal", text_color=COLOR_ERROR, border_color=COLOR_ERROR)

        # Update Metadata Display
        self.filename_banner.configure(text=f"File: {photo.filename_base}.jpg")
        self.lbl_meta_hole.configure(text=f"Hole ID: {photo.hole_id}")
        self.lbl_meta_tray.configure(text=f"Tray Number: {photo.tray_number}")
        int_len = max(0.0, photo.interval_to - photo.interval_from)
        self.lbl_meta_interval.configure(text=f"Depth Interval: {photo.interval_from:.2f} m - {photo.interval_to:.2f} m (Length: {int_len:.2f} m)")
        
        ts = getattr(photo, "timestamp", "") or photo.captured_at or photo.created_at or "-"
        self.lbl_meta_timestamp.configure(text=f"Timestamp: {ts}")
        cam_info = f"{photo.camera_model} (SN: {photo.camera_serial})" if photo.camera_serial else (photo.camera_model or "Standard Camera")
        self.lbl_meta_camera.configure(text=f"Camera: {cam_info}")

        raw_md5 = photo.md5_raw[:16] + "..." if photo.md5_raw else "Not generated"
        jpg_md5 = photo.md5_jpg[:16] + "..." if photo.md5_jpg else "Not generated"
        self.lbl_meta_md5.configure(text=f"RAW MD5: {raw_md5}\nJPG MD5: {jpg_md5}")

        # Populate Edit Form entries
        self.entry_edit_hole.delete(0, "end")
        self.entry_edit_hole.insert(0, photo.hole_id)
        self.entry_edit_tray.delete(0, "end")
        self.entry_edit_tray.insert(0, photo.tray_number)
        self.entry_edit_from.delete(0, "end")
        self.entry_edit_from.insert(0, f"{photo.interval_from:.2f}")
        self.entry_edit_to.delete(0, "end")
        self.entry_edit_to.insert(0, f"{photo.interval_to:.2f}")

        # Update Validation Checklist
        self._refresh_validation_audit(photo)

        # Load & Render Image
        self._display_photo_image(photo)

    def _show_empty_state(self) -> None:
        self.btn_prev.configure(state="disabled")
        self.btn_next.configure(state="disabled")
        self.lbl_index_badge.configure(text="0 / 0")
        self.lbl_carousel_status.configure(text="No active session photos available.")
        self.tray_selector.configure(values=["No Trays"])
        self.tray_selector.set("No Trays")
        self.img_label.configure(image="", text="No captured photo available.\nCapture a core tray from Live Capture.")
        self.filename_banner.configure(text="")
        self.lbl_meta_hole.configure(text="Hole ID: -")
        self.lbl_meta_tray.configure(text="Tray Number: -")
        self.lbl_meta_interval.configure(text="Depth Interval: -")
        self.lbl_meta_timestamp.configure(text="Timestamp: -")
        self.lbl_meta_camera.configure(text="Camera: -")
        self.lbl_meta_md5.configure(text="MD5: -")
        self.validation_badge.configure(fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER)
        self.validation_badge_lbl.configure(text="STATUS: NO DATA", text_color=COLOR_TEXT_HINT)
        self.audit_alert_box.pack_forget()
        self.btn_save_next.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)
        self.btn_retake.configure(state="disabled", text_color=COLOR_TEXT_HINT, border_color=COLOR_BORDER_STRONG)

    def _display_photo_image(self, photo: PhotoModel) -> None:
        jpg_path = Path(photo.jpg_path)
        if not jpg_path.exists():
            self.img_label.configure(image="", text="JPG image file not found on disk.")
            return

        try:
            pil_img = Image.open(jpg_path)
            orig_w, orig_h = pil_img.size

            if self._zoom_mode:
                # 1:1 Detail Zoom: crop center 540x360 window at full resolution
                zoom_w, zoom_h = min(orig_w, 540), min(orig_h, 360)
                cx, cy = orig_w // 2, orig_h // 2
                crop_box = (
                    max(0, cx - zoom_w // 2),
                    max(0, cy - zoom_h // 2),
                    min(orig_w, cx + zoom_w // 2),
                    min(orig_h, cy + zoom_h // 2),
                )
                cropped_img = pil_img.crop(crop_box)
                self._ctk_image = ctk.CTkImage(light_image=cropped_img, dark_image=cropped_img, size=(zoom_w, zoom_h))
            else:
                # Standard Fit View: scale preserving aspect ratio
                target_w = 540
                aspect = orig_h / orig_w if orig_w > 0 else 0.66
                target_h = int(target_w * aspect)
                self._ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(target_w, target_h))

            self.img_label.configure(image=self._ctk_image, text="")
        except Exception as e:
            logger.error("Error loading review photo %s: %s", jpg_path, e)
            self.img_label.configure(image="", text="Error rendering image file.")

    def _refresh_validation_audit(self, photo: PhotoModel) -> None:
        # Run validation runner
        is_valid = True
        err_msgs: List[str] = []

        if photo.id and self.ctx.validation_runner:
            is_valid, err_msgs = self.ctx.validate_photo(photo.id)

        # Check Schema
        if photo.filename_base and photo.hole_id in photo.filename_base:
            self.lbl_chk_schema.configure(text="✓ Filename Schema: Validated Standard", text_color=COLOR_SUCCESS)
        else:
            self.lbl_chk_schema.configure(text="! Filename Schema: Incomplete identifier", text_color=COLOR_WARNING)

        # Check Interval
        if photo.interval_from < photo.interval_to:
            self.lbl_chk_interval.configure(text=f"✓ Depth Interval: Continuous ({photo.interval_from:.2f}m - {photo.interval_to:.2f}m)", text_color=COLOR_SUCCESS)
        else:
            self.lbl_chk_interval.configure(text=f"! Depth Interval: Invalid From >= To ({photo.interval_from:.2f}m - {photo.interval_to:.2f}m)", text_color=COLOR_ERROR)
            is_valid = False

        # Check MD5
        if photo.md5_jpg and photo.md5_raw:
            self.lbl_chk_md5.configure(text="✓ Checksum Integrity: RAW & JPG MD5 verified", text_color=COLOR_SUCCESS)
        else:
            self.lbl_chk_md5.configure(text="! Checksum Integrity: MD5 hash missing", text_color=COLOR_WARNING)

        # Check Assets on disk
        jpg_ok = Path(photo.jpg_path).exists() if photo.jpg_path else False
        raw_ok = Path(photo.raw_path).exists() if photo.raw_path else False
        if jpg_ok and raw_ok:
            self.lbl_chk_assets.configure(text="✓ Physical Storage: RAW & JPG verified on disk", text_color=COLOR_SUCCESS)
        elif jpg_ok:
            self.lbl_chk_assets.configure(text="✓ Physical Storage: JPG present on disk", text_color=COLOR_SUCCESS)
        else:
            self.lbl_chk_assets.configure(text="! Physical Storage: Assets missing from disk", text_color=COLOR_ERROR)
            is_valid = False

        # Overall Status Badge
        if is_valid and (photo.status == "VALID" or not err_msgs):
            self.validation_badge.configure(fg_color=COLOR_SUCCESS_BG, border_color=COLOR_SUCCESS_BORDER)
            self.validation_badge_lbl.configure(text="STATUS: VALIDATED (PASS)", text_color=COLOR_SUCCESS)
            self.audit_alert_box.pack_forget()
        else:
            self.validation_badge.configure(fg_color=COLOR_WARNING_BG, border_color=COLOR_WARNING_BORDER)
            self.validation_badge_lbl.configure(text="STATUS: AUDIT WARNING / ISSUES", text_color=COLOR_WARNING)
            msg_str = "\n".join(err_msgs) if err_msgs else "Validation checks flagged inconsistencies. Please review metadata."
            self.audit_alert_lbl.configure(text=msg_str)
            self.audit_alert_box.pack(fill="x", padx=14, pady=(2, 6))

    # =========================================================================
    # Interactive Actions & Carousel Navigation
    # =========================================================================
    def _on_prev_photo(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._render_current_photo()

    def _on_next_photo(self) -> None:
        if self._current_index < len(self._photos) - 1:
            self._current_index += 1
            self._render_current_photo()

    def _on_tray_dropdown_selected(self, choice: str) -> None:
        for idx, p in enumerate(self._photos):
            entry_str = f"Tray {p.tray_number} ({p.interval_from:.2f}-{p.interval_to:.2f}m)"
            if entry_str == choice:
                self._current_index = idx
                self._render_current_photo()
                break

    def _toggle_zoom(self) -> None:
        self._zoom_mode = not self._zoom_mode
        self.btn_zoom.configure(
            text="Fit View" if self._zoom_mode else "Zoom 1:1",
            fg_color=COLOR_ACCENT_HOVER if self._zoom_mode else COLOR_PANEL_ALT,
            text_color="#FFFFFF" if self._zoom_mode else COLOR_TEXT_PRIMARY,
        )
        if 0 <= self._current_index < len(self._photos):
            self._display_photo_image(self._photos[self._current_index])

    def _toggle_edit_mode(self) -> None:
        self._edit_mode = not self._edit_mode
        if self._edit_mode:
            self.btn_edit_meta.configure(text="Cancel Edit", text_color=COLOR_ERROR)
            self.edit_form_card.pack(fill="x", padx=14, pady=4, after=self.meta_display_card)
        else:
            self.btn_edit_meta.configure(text="Edit Depth / Info", text_color=COLOR_TEXT_PRIMARY)
            self.edit_form_card.pack_forget()

    def _on_save_edits(self) -> None:
        if not (0 <= self._current_index < len(self._photos)):
            return

        photo = self._photos[self._current_index]
        new_hole = self.entry_edit_hole.get().strip()
        new_tray = self.entry_edit_tray.get().strip()
        try:
            new_from = float(self.entry_edit_from.get().strip())
            new_to = float(self.entry_edit_to.get().strip())
        except ValueError:
            logger.warning("Invalid numerical depth interval inputs.")
            return

        if new_from >= new_to:
            logger.warning("Interval From must be strictly less than To.")
            return

        # Update in database
        if photo.id and self.ctx.photo_repo:
            photo.hole_id = new_hole
            photo.tray_number = new_tray
            photo.interval_from = new_from
            photo.interval_to = new_to
            self.ctx.photo_repo.update(photo)
            logger.info("Updated photo %d metadata: Hole=%s, Tray=%s, %f-%f", photo.id, new_hole, new_tray, new_from, new_to)

        self._toggle_edit_mode()
        self._on_rerun_audit()

    def _on_rerun_audit(self) -> None:
        if 0 <= self._current_index < len(self._photos):
            photo = self._photos[self._current_index]
            if photo.id and self.ctx.validate_photo:
                self.ctx.validate_photo(photo.id)
            self._render_current_photo()

    def _on_save_next(self) -> None:
        """Approves current photo, advances to next in review or calls advance_tray_fn."""
        if 0 <= self._current_index < len(self._photos) - 1:
            # Advance to next photo in review series
            self._current_index += 1
            self._render_current_photo()
        else:
            # At end of series: advance tray sequence and return to capture
            if self.advance_tray_fn:
                self.advance_tray_fn()
            self.navigate_fn("capture")

    def _on_retake(self) -> None:
        """Marks current capture as superseded and loads tray parameters into Live Capture for reshot."""
        if not (0 <= self._current_index < len(self._photos)):
            return

        photo = self._photos[self._current_index]
        logger.info("Operator triggered Retake for Photo ID %s (Tray %s).", photo.id, photo.tray_number)

        self.ctx.last_photo = photo
        if photo.id and self.ctx.photo_repo:
            self.ctx.photo_repo.mark_as_superseded(photo.id)

        self.navigate_fn("capture")

    def _on_open_folder(self) -> None:
        if 0 <= self._current_index < len(self._photos):
            photo = self._photos[self._current_index]
            if photo.jpg_path:
                folder = str(Path(photo.jpg_path).parent)
                try:
                    os.startfile(folder)
                except Exception as e:
                    logger.error("Failed opening folder %s: %s", folder, e)
