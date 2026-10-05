"""Photo Browser Screen (Professional Industrial Redesign).
Provides fast browsing, structured search (Hole ID, Tray, Interval, Status),
compact thumbnail grid, and instant deep inspector (Large Preview, Metadata, Validation, Transfer).
Zero emojis, strict professional standards.
"""

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


class BrowserView(ctk.CTkFrame):
    """Photo gallery and inspection browser."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self._thumb_cache: List[ctk.CTkImage] = []
        self._selected_photo: Optional[PhotoModel] = None
        self._preview_ctk_img: Optional[ctk.CTkImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=3)  # Thumbnail gallery
        self.grid_columnconfigure(1, weight=2)  # Inspector details
        self.grid_rowconfigure(1, weight=1)

        # =========================================================================
        # 1. TOP FILTER BAR
        # =========================================================================
        filter_bar = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        filter_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 10))

        title_box = ctk.CTkFrame(filter_bar, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            title_box,
            text="PHOTO BROWSER",
            font=get_font(14, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Filter and inspect core photography archives.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w")

        # Search & Filter inputs
        controls_box = ctk.CTkFrame(filter_bar, fg_color="transparent")
        controls_box.pack(side="right", padx=16, pady=10)

        self.search_entry = ctk.CTkEntry(
            controls_box,
            placeholder_text="Filter Hole ID or Tray...",
            width=210,
            height=32,
            font=get_font(11),
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        self.status_filter = ctk.CTkOptionMenu(
            controls_box,
            values=["All Statuses", "VALID", "PROCESSED", "INVALID", "TRANSFERRED"],
            command=lambda v: self.refresh(),
            height=32,
            width=130,
            font=get_font(11),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
        )
        self.status_filter.pack(side="left", padx=4)

        btn_refresh = ctk.CTkButton(
            controls_box,
            text="Refresh",
            width=70,
            height=32,
            font=get_font(11, "bold"),
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            hover_color="#27272A",
            text_color="#FFFFFF",
            command=self.refresh,
        )
        btn_refresh.pack(side="left", padx=4)

        btn_export = ctk.CTkButton(
            controls_box,
            text="Export CSV Report",
            width=135,
            height=32,
            font=get_font(11, "bold"),
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_export_csv,
        )
        btn_export.pack(side="left", padx=4)

        # =========================================================================
        # 2. LEFT: Scrollable Thumbnail Grid
        # =========================================================================
        self.grid_container = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.grid_container.grid(row=1, column=0, sticky="nsew", padx=(20, 8), pady=(0, 16))
        self.grid_container.grid_columnconfigure((0, 1, 2), weight=1)

        # =========================================================================
        # 3. RIGHT: Photo Inspector Panel
        # =========================================================================
        self.detail_panel = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.detail_panel.grid(row=1, column=1, sticky="nsew", padx=(8, 20), pady=(0, 16))

        ctk.CTkLabel(
            self.detail_panel,
            text="SELECTED PHOTO INSPECTOR",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=16, pady=(14, 2))

        ctk.CTkLabel(
            self.detail_panel,
            text="Click any photo in the catalog to inspect details.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Large Preview Canvas
        preview_card = ctk.CTkFrame(
            self.detail_panel,
            fg_color="#09090B",
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        preview_card.pack(fill="x", padx=16, pady=4)

        self.detail_img_lbl = ctk.CTkLabel(
            preview_card,
            text="Select a photo from the gallery",
            font=get_font(11),
            text_color=COLOR_TEXT_HINT,
        )
        self.detail_img_lbl.pack(padx=8, pady=16)

        # Inspector Metadata Card
        self.meta_card = ctk.CTkFrame(
            self.detail_panel,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.meta_card.pack(fill="x", padx=16, pady=10)

        self.lbl_insp_title = ctk.CTkLabel(self.meta_card, text="File: -", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_insp_title.pack(anchor="w", padx=12, pady=(10, 2))

        self.lbl_insp_interval = ctk.CTkLabel(self.meta_card, text="Interval: -", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_insp_interval.pack(anchor="w", padx=12, pady=2)

        self.lbl_insp_status = ctk.CTkLabel(self.meta_card, text="Validation Status: -", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_insp_status.pack(anchor="w", padx=12, pady=2)

        self.lbl_insp_transfer = ctk.CTkLabel(self.meta_card, text="Transfer Status: -", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_insp_transfer.pack(anchor="w", padx=12, pady=2)

        self.lbl_insp_hashes = ctk.CTkLabel(
            self.meta_card,
            text="MD5: -",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=COLOR_TEXT_HINT,
            justify="left",
        )
        self.lbl_insp_hashes.pack(anchor="w", padx=12, pady=(4, 10))

    def refresh(self) -> None:
        """Reloads photos from database matching active search filters."""
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self._thumb_cache.clear()

        if not self.ctx.photo_repo or not self.ctx.active_session:
            empty_lbl = ctk.CTkLabel(
                self.grid_container,
                text="No active session or photo archive found.\nCreate a session and capture photos to view the catalog.",
                font=get_font(11),
                text_color=COLOR_TEXT_HINT,
                justify="center",
            )
            empty_lbl.grid(row=0, column=0, columnspan=3, pady=60)
            return

        query = self.search_entry.get().strip()
        status_sel = self.status_filter.get()
        status_param = None if status_sel == "All Statuses" else status_sel

        photos = self.ctx.photo_repo.search(
            hole_id=query if query else None,
            tray_number=query if query else None,
            status=status_param,
        )

        if not photos:
            empty_lbl = ctk.CTkLabel(
                self.grid_container,
                text="No photos match the current filter criteria.",
                font=get_font(11),
                text_color=COLOR_TEXT_HINT,
            )
            empty_lbl.grid(row=0, column=0, columnspan=3, pady=60)
            return

        col_count = 3
        for idx, photo in enumerate(photos):
            row = idx // col_count
            col = idx % col_count

            card = ctk.CTkFrame(
                self.grid_container,
                fg_color=COLOR_PANEL_ALT,
                corner_radius=4,
                border_width=1,
                border_color=COLOR_BORDER,
                cursor="hand2",
            )
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Load thumbnail
            thumb_path = Path(photo.thumbnail_path) if photo.thumbnail_path else None
            if thumb_path and thumb_path.exists():
                try:
                    pil_thumb = Image.open(thumb_path)
                    ctk_thumb = ctk.CTkImage(light_image=pil_thumb, dark_image=pil_thumb, size=(110, 74))
                    self._thumb_cache.append(ctk_thumb)
                    thumb_lbl = ctk.CTkLabel(card, image=ctk_thumb, text="")
                    thumb_lbl.pack(padx=6, pady=(6, 3))
                except Exception:
                    ctk.CTkLabel(card, text="[No Thumb]", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(pady=16)
            else:
                ctk.CTkLabel(card, text="[No Thumb]", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(pady=16)

            title_lbl = ctk.CTkLabel(
                card,
                text=f"{photo.hole_id} (Tray {photo.tray_number})",
                font=get_font(11, "bold"),
                text_color=COLOR_TEXT_PRIMARY,
            )
            title_lbl.pack(padx=4, pady=1)

            sub_lbl = ctk.CTkLabel(
                card,
                text=f"{photo.interval_from:.2f} - {photo.interval_to:.2f} m",
                font=get_font(10),
                text_color=COLOR_TEXT_MUTED,
            )
            sub_lbl.pack(padx=4, pady=1)

            # Status Indicator
            is_valid = photo.status in ("VALID", "TRANSFERRED")
            status_color = COLOR_SUCCESS if is_valid else COLOR_WARNING
            status_bg = COLOR_SUCCESS_BG if is_valid else COLOR_WARNING_BG

            pill = ctk.CTkLabel(
                card,
                text=f" {photo.status} ",
                font=get_font(9, "bold"),
                text_color=status_color,
                fg_color=status_bg,
                corner_radius=2,
            )
            pill.pack(padx=4, pady=(2, 6))

            # Click binding to inspect
            for widget in [card, title_lbl, sub_lbl, pill]:
                widget.bind("<Button-1>", lambda e, p=photo: self._inspect_photo(p))

        # Select first photo by default if none selected
        if not self._selected_photo and photos:
            self._inspect_photo(photos[0])

    def _inspect_photo(self, photo: PhotoModel) -> None:
        self._selected_photo = photo
        jpg_path = Path(photo.jpg_path) if photo.jpg_path else None

        if jpg_path and jpg_path.exists():
            try:
                pil_img = Image.open(jpg_path)
                self._preview_ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(300, 200))
                self.detail_img_lbl.configure(image=self._preview_ctk_img, text="")
            except Exception as e:
                logger.error("Error opening image %s: %s", jpg_path, e)
                self.detail_img_lbl.configure(image="", text="Error rendering image.")
        else:
            self.detail_img_lbl.configure(image="", text="File missing on disk.")

        self.lbl_insp_title.configure(text=f"File: {photo.filename_base}.jpg")
        self.lbl_insp_interval.configure(text=f"Hole: {photo.hole_id}  ·  Tray: {photo.tray_number}  ·  {photo.interval_from:.2f} m - {photo.interval_to:.2f} m")
        self.lbl_insp_status.configure(text=f"Validation Status: {photo.status}")
        self.lbl_insp_transfer.configure(text=f"Transfer Status: {'TRANSFERRED' if photo.status == 'TRANSFERRED' else 'LOCAL ONLY'}")
        self.lbl_insp_hashes.configure(
            text=f"RAW MD5: {photo.md5_raw}\nJPG MD5: {photo.md5_jpg}\nCamera: {photo.camera_model}"
        )

    def _on_export_csv(self) -> None:
        import os
        from tkinter import filedialog
        sess = self.ctx.active_session
        if not sess:
            return

        photos = self.ctx.photo_repo.get_by_session_id(sess.id) if self.ctx.photo_repo else []
        hole_id = "TSD168"
        if photos and photos[0].hole_id:
            hole_id = photos[0].hole_id

        dest = filedialog.asksaveasfilename(
            title="Export Geological Report CSV",
            initialfile=f"{hole_id}.csv",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")]
        )
        if dest:
            from imaging.processor import ImageProcessor
            out_path = ImageProcessor.export_csv_report(sess, photos, Path(dest))
            try:
                os.startfile(str(out_path))
            except Exception:
                pass
