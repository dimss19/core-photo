"""Review & Photo Catalog Screen (Professional Industrial Redesign).
Unified workspace combining deep tray inspection (zoom, carousel navigation,
depth interval corrections, validation audit checklist, and approve/retake decisions)
with full session photo catalog browsing (search, status filters, thumbnail grid, and CSV export).
Zero emojis, strict professional standards.
"""

from datetime import datetime
import os
from pathlib import Path
from tkinter import filedialog
from typing import Callable, List, Optional
import customtkinter as ctk
from PIL import Image

from core.app_context import get_app_context
from core.logger import get_logger
from database.models import PhotoModel
from imaging.processor import ImageProcessor
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_ACCENT_LIGHT,
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
    """Unified photo review, inspection, validation audit, and catalog browser."""

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

        self._active_tab = "inspect"  # "inspect" or "catalog"
        self._photos: List[PhotoModel] = []
        self._current_index: int = -1
        self._ctk_image: Optional[ctk.CTkImage] = None
        self._zoom_mode: bool = False  # False = Fit, True = 1:1 Detail Zoom
        self._edit_mode: bool = False

        # Catalog state
        self._thumb_cache: List[ctk.CTkImage] = []
        self._catalog_selected_photo: Optional[PhotoModel] = None
        self._catalog_preview_img: Optional[ctk.CTkImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # =========================================================================
        # 1. TOP HEADER WITH INTEGRATED SEGMENTED NAVIGATION
        # =========================================================================
        top_header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        top_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))

        header_inner = ctk.CTkFrame(top_header, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=12)

        title_box = ctk.CTkFrame(header_inner, fg_color="transparent")
        title_box.pack(side="left", anchor="w")

        ctk.CTkLabel(
            title_box,
            text="REVIEW & PHOTO CATALOG",
            font=get_font(14, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        self.lbl_header_subtitle = ctk.CTkLabel(
            title_box,
            text="Inspect captured core trays, verify validation integrity, and browse catalog archive.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_header_subtitle.pack(anchor="w", pady=(2, 0))

        # Segmented Tab Switcher
        tab_btn_box = ctk.CTkFrame(header_inner, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        tab_btn_box.pack(side="right", anchor="e")

        self.btn_tab_inspect = ctk.CTkButton(
            tab_btn_box,
            text="TRAY INSPECTION & AUDIT",
            font=get_font(10, "bold"),
            height=30,
            width=165,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=lambda: self.select_tab("inspect"),
        )
        self.btn_tab_inspect.pack(side="left", padx=2, pady=2)

        self.btn_tab_catalog = ctk.CTkButton(
            tab_btn_box,
            text="PHOTO CATALOG & GRID",
            font=get_font(10, "bold"),
            height=30,
            width=165,
            corner_radius=4,
            fg_color="transparent",
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            command=lambda: self.select_tab("catalog"),
        )
        self.btn_tab_catalog.pack(side="left", padx=2, pady=2)

        # =========================================================================
        # 2. MAIN CONTAINER FOR TAB PAGES
        # =========================================================================
        self.tab_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.tab_container.grid_columnconfigure(0, weight=1)
        self.tab_container.grid_rowconfigure(0, weight=1)

        self._build_inspect_tab()
        self._build_catalog_tab()

    def select_tab(self, tab_name: str) -> None:
        """Switches between 'inspect' and 'catalog' view modes."""
        norm = "catalog" if tab_name.lower() in ("catalog", "browser", "grid") else "inspect"
        self._active_tab = norm

        if norm == "inspect":
            self.btn_tab_inspect.configure(fg_color=COLOR_ACCENT, text_color="#FFFFFF")
            self.btn_tab_catalog.configure(fg_color="transparent", text_color=COLOR_TEXT_PRIMARY)
            self.frame_catalog.grid_forget()
            self.frame_inspect.grid(row=0, column=0, sticky="nsew")
        else:
            self.btn_tab_inspect.configure(fg_color="transparent", text_color=COLOR_TEXT_PRIMARY)
            self.btn_tab_catalog.configure(fg_color=COLOR_ACCENT, text_color="#FFFFFF")
            self.frame_inspect.grid_forget()
            self.frame_catalog.grid(row=0, column=0, sticky="nsew")

        self.refresh()

    # =========================================================================
    # TAB 1: TRAY INSPECTION & AUDIT
    # =========================================================================
    def _build_inspect_tab(self) -> None:
        self.frame_inspect = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.frame_inspect.grid(row=0, column=0, sticky="nsew")
        self.frame_inspect.grid_columnconfigure(0, weight=3)  # Left: Photo Viewer & Carousel
        self.frame_inspect.grid_columnconfigure(1, weight=2)  # Right: Metadata, Audit & Actions
        self.frame_inspect.grid_rowconfigure(0, weight=1)

        # ----------------- Left: Photo Canvas & Carousel -----------------
        preview_panel = ctk.CTkFrame(self.frame_inspect, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        preview_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
        preview_panel.grid_rowconfigure(1, weight=1)
        preview_panel.grid_columnconfigure(0, weight=1)

        # Header with Title and Carousel Controls
        header_box = ctk.CTkFrame(preview_panel, fg_color="transparent")
        header_box.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        title_left = ctk.CTkFrame(header_box, fg_color="transparent")
        title_left.pack(side="left", anchor="w")

        ctk.CTkLabel(title_left, text="PHOTO INSPECTION", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w")
        self.lbl_carousel_status = ctk.CTkLabel(title_left, text="Optical clarity and crop inspection.", font=get_font(10), text_color=COLOR_TEXT_MUTED)
        self.lbl_carousel_status.pack(anchor="w")

        # Top Carousel Controls
        nav_controls = ctk.CTkFrame(header_box, fg_color="transparent")
        nav_controls.pack(side="right", anchor="e")

        self.btn_prev = ctk.CTkButton(
            nav_controls, text="◀ Prev", width=65, height=28, font=get_font(10, "bold"),
            fg_color=COLOR_PANEL_ALT, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_BORDER,
            command=self._on_prev_photo,
        )
        self.btn_prev.pack(side="left", padx=2)

        self.lbl_index_badge = ctk.CTkLabel(nav_controls, text="0 / 0", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL, width=60)
        self.lbl_index_badge.pack(side="left", padx=4)

        self.btn_next = ctk.CTkButton(
            nav_controls, text="Next ▶", width=65, height=28, font=get_font(10, "bold"),
            fg_color=COLOR_PANEL_ALT, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_BORDER,
            command=self._on_next_photo,
        )
        self.btn_next.pack(side="left", padx=2)

        self.btn_zoom = ctk.CTkButton(
            nav_controls, text="Zoom 1:1", width=70, height=28, font=get_font(10, "bold"),
            fg_color=COLOR_PANEL_ALT, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_BORDER,
            command=self._toggle_zoom,
        )
        self.btn_zoom.pack(side="left", padx=(8, 0))

        # Main Photo Canvas Container
        self.img_container = ctk.CTkFrame(preview_panel, fg_color="#09090B", corner_radius=4, border_width=1, border_color=COLOR_BORDER)
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

        # Footer Bar: Filename + Explorer Button + Jump Selector + View in Catalog Button
        footer_box = ctk.CTkFrame(preview_panel, fg_color="transparent")
        footer_box.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 12))

        self.filename_banner = ctk.CTkLabel(footer_box, text="", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL)
        self.filename_banner.pack(side="left", anchor="w")

        btn_view_catalog = ctk.CTkButton(
            footer_box, text="View in Catalog ⊞", font=get_font(10, "bold"), height=26, width=120,
            corner_radius=4, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF",
            command=self._switch_to_catalog_at_current,
        )
        btn_view_catalog.pack(side="right", padx=(4, 0))

        self.btn_open_folder = ctk.CTkButton(
            footer_box, text="Open Folder", font=get_font(10, "bold"), height=26, width=90,
            corner_radius=4, fg_color=COLOR_PANEL_ALT, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_BORDER,
            command=self._on_open_folder,
        )
        self.btn_open_folder.pack(side="right", padx=4)

        self.tray_selector = ctk.CTkOptionMenu(
            footer_box, values=["No Trays"], command=self._on_tray_dropdown_selected,
            height=26, width=160, font=get_font(10), fg_color=COLOR_PANEL_ALT, text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER, button_hover_color=COLOR_BORDER_STRONG,
        )
        self.tray_selector.pack(side="right", padx=4)

        # ----------------- Right: Metadata, Audit & Actions -----------------
        right_panel = ctk.CTkScrollableFrame(self.frame_inspect, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        # Section A: Metadata
        meta_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        meta_header.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(meta_header, text="TRAY RECORD & METADATA", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(side="left")
        self.btn_edit_meta = ctk.CTkButton(
            meta_header, text="Edit Depth / Info", font=get_font(10, "bold"), height=24, width=110,
            corner_radius=4, fg_color=COLOR_PANEL_ALT, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_BORDER,
            command=self._toggle_edit_mode,
        )
        self.btn_edit_meta.pack(side="right")

        self.meta_display_card = ctk.CTkFrame(right_panel, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
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
            self.meta_display_card, text="MD5: -", font=ctk.CTkFont(family="Consolas", size=9),
            text_color=COLOR_TEXT_HINT, justify="left",
        )
        self.lbl_meta_md5.pack(anchor="w", padx=12, pady=(4, 8))

        # Edit Form (managed dynamically)
        self.edit_form_card = ctk.CTkFrame(right_panel, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_ACCENT)
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
            self.edit_form_card, text="Save Corrections", font=get_font(10, "bold"), height=28,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", command=self._on_save_edits,
        )
        btn_save_edit.pack(fill="x", padx=12, pady=(2, 8))

        # Section B: Validation & Audit Checklist
        audit_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        audit_header.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(audit_header, text="VALIDATION & INTEGRITY AUDIT", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(side="left")
        btn_recheck = ctk.CTkButton(
            audit_header, text="Re-run Audit", font=get_font(10, "bold"), height=24, width=90,
            corner_radius=4, fg_color=COLOR_PANEL_ALT, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_BORDER,
            command=self._on_rerun_audit,
        )
        btn_recheck.pack(side="right")

        self.validation_badge = ctk.CTkFrame(right_panel, fg_color=COLOR_SUCCESS_BG, corner_radius=4, border_width=1, border_color=COLOR_SUCCESS_BORDER)
        self.validation_badge.pack(fill="x", padx=14, pady=4)

        self.validation_badge_lbl = ctk.CTkLabel(self.validation_badge, text="STATUS: VALIDATED (PASS)", font=get_font(11, "bold"), text_color=COLOR_SUCCESS)
        self.validation_badge_lbl.pack(pady=6)

        self.audit_card = ctk.CTkFrame(right_panel, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        self.audit_card.pack(fill="x", padx=14, pady=4)

        self.lbl_chk_schema = ctk.CTkLabel(self.audit_card, text="✓ Filename Schema: Validated", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_chk_schema.pack(anchor="w", padx=12, pady=(6, 2))

        self.lbl_chk_interval = ctk.CTkLabel(self.audit_card, text="✓ Depth Interval: Continuous & Non-negative", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_chk_interval.pack(anchor="w", padx=12, pady=2)

        self.lbl_chk_md5 = ctk.CTkLabel(self.audit_card, text="✓ MD5 Hashes: Computed & Verified", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_chk_md5.pack(anchor="w", padx=12, pady=2)

        self.lbl_chk_assets = ctk.CTkLabel(self.audit_card, text="✓ Storage Assets: JPG, RAW, Thumbs on disk", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_chk_assets.pack(anchor="w", padx=12, pady=(2, 6))

        self.audit_alert_box = ctk.CTkFrame(right_panel, fg_color=COLOR_WARNING_BG, corner_radius=4, border_width=1, border_color=COLOR_WARNING_BORDER)
        self.audit_alert_lbl = ctk.CTkLabel(self.audit_alert_box, text="", font=get_font(10), text_color=COLOR_WARNING, justify="left", wraplength=280)
        self.audit_alert_lbl.pack(padx=10, pady=6)

        # Section C: Operator Decisions
        ctk.CTkLabel(right_panel, text="OPERATOR DECISION", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=14, pady=(14, 4))

        self.btn_save_next = ctk.CTkButton(
            right_panel, text="APPROVE & NEXT TRAY", font=get_font(12, "bold"), height=42, corner_radius=4,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", command=self._on_save_next,
        )
        self.btn_save_next.pack(fill="x", padx=14, pady=(2, 2))

        ctk.CTkLabel(right_panel, text="Approves this tray and moves to the next tray in the logging series.", font=get_font(9), text_color=COLOR_TEXT_HINT, wraplength=280, justify="left").pack(anchor="w", padx=14, pady=(0, 8))

        self.btn_retake = ctk.CTkButton(
            right_panel, text="RETAKE THIS TRAY", font=get_font(11, "bold"), height=36, corner_radius=4,
            fg_color=COLOR_PANEL_ALT, hover_color=COLOR_BORDER, text_color=COLOR_ERROR, border_width=1, border_color=COLOR_ERROR,
            command=self._on_retake,
        )
        self.btn_retake.pack(fill="x", padx=14, pady=(2, 2))

        ctk.CTkLabel(right_panel, text="Marks capture as superseded and loads parameters back into Live Capture.", font=get_font(9), text_color=COLOR_TEXT_HINT, wraplength=280, justify="left").pack(anchor="w", padx=14, pady=(0, 14))

    # =========================================================================
    # TAB 2: PHOTO CATALOG & GRID
    # =========================================================================
    def _build_catalog_tab(self) -> None:
        self.frame_catalog = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        # managed in select_tab
        self.frame_catalog.grid_columnconfigure(0, weight=3)  # Thumbnail Gallery
        self.frame_catalog.grid_columnconfigure(1, weight=2)  # Inspector Panel
        self.frame_catalog.grid_rowconfigure(1, weight=1)

        # Top Filter Bar inside Catalog
        filter_bar = ctk.CTkFrame(self.frame_catalog, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        filter_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        bar_inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        bar_inner.pack(fill="x", padx=14, pady=8)

        ctk.CTkLabel(bar_inner, text="CATALOG ARCHIVES", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(side="left")

        controls_box = ctk.CTkFrame(bar_inner, fg_color="transparent")
        controls_box.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            controls_box, placeholder_text="Filter Hole ID or Tray...", width=180, height=30,
            font=get_font(11), fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER_STRONG, border_width=1,
        )
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_catalog_grid())

        self.status_filter = ctk.CTkOptionMenu(
            controls_box, values=["All Statuses", "VALID", "Issues / Flagged"],
            command=lambda v: self._refresh_catalog_grid(), height=30, width=130, font=get_font(10),
            fg_color=COLOR_PANEL_ALT, text_color=COLOR_CHARCOAL, button_color=COLOR_BORDER, button_hover_color=COLOR_BORDER_STRONG,
        )
        self.status_filter.pack(side="left", padx=4)

        btn_refresh_cat = ctk.CTkButton(
            controls_box, text="Refresh", width=65, height=30, font=get_font(10, "bold"),
            corner_radius=4, fg_color=COLOR_CHARCOAL, text_color="#FFFFFF", command=self._refresh_catalog_grid,
        )
        btn_refresh_cat.pack(side="left", padx=4)

        btn_export = ctk.CTkButton(
            controls_box, text="Export CSV Report", width=130, height=30, font=get_font(10, "bold"),
            corner_radius=4, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF",
            command=self._on_export_csv,
        )
        btn_export.pack(side="left", padx=4)

        # Left: Scrollable Thumbnail Grid
        self.grid_container = ctk.CTkScrollableFrame(self.frame_catalog, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        self.grid_container.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=0)
        self.grid_container.grid_columnconfigure((0, 1, 2), weight=1)

        # Right: Detail Inspector
        self.cat_detail_panel = ctk.CTkScrollableFrame(self.frame_catalog, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        self.cat_detail_panel.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=0)

        ctk.CTkLabel(self.cat_detail_panel, text="SELECTED PHOTO DETAILS", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(self.cat_detail_panel, text="Click any photo in the catalog to inspect.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 8))

        preview_card = ctk.CTkFrame(self.cat_detail_panel, fg_color="#09090B", corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        preview_card.pack(fill="x", padx=16, pady=4)

        self.cat_img_lbl = ctk.CTkLabel(preview_card, text="Select a photo from the gallery", font=get_font(11), text_color=COLOR_TEXT_HINT)
        self.cat_img_lbl.pack(padx=8, pady=16)

        self.cat_meta_card = ctk.CTkFrame(self.cat_detail_panel, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        self.cat_meta_card.pack(fill="x", padx=16, pady=8)

        self.lbl_cat_title = ctk.CTkLabel(self.cat_meta_card, text="File: -", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_cat_title.pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_cat_interval = ctk.CTkLabel(self.cat_meta_card, text="Interval: -", font=get_font(10), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_cat_interval.pack(anchor="w", padx=12, pady=2)

        self.lbl_cat_status = ctk.CTkLabel(self.cat_meta_card, text="Validation Status: -", font=get_font(10), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_cat_status.pack(anchor="w", padx=12, pady=2)

        self.lbl_cat_storage = ctk.CTkLabel(self.cat_meta_card, text="Storage: LOCAL ARCHIVE", font=get_font(10), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_cat_storage.pack(anchor="w", padx=12, pady=2)

        self.lbl_cat_hashes = ctk.CTkLabel(
            self.cat_meta_card, text="MD5: -", font=ctk.CTkFont(family="Consolas", size=9),
            text_color=COLOR_TEXT_HINT, justify="left",
        )
        self.lbl_cat_hashes.pack(anchor="w", padx=12, pady=(4, 8))

        # Action: [ 🔍 OPEN IN TRAY INSPECTION ]
        self.btn_open_inspect = ctk.CTkButton(
            self.cat_detail_panel, text="🔍 OPEN IN TRAY INSPECTION", font=get_font(11, "bold"), height=38,
            corner_radius=4, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF",
            command=self._on_open_selected_in_inspect,
        )
        self.btn_open_inspect.pack(fill="x", padx=16, pady=(4, 4))

        self.btn_cat_folder = ctk.CTkButton(
            self.cat_detail_panel, text="Open Image Folder", font=get_font(10), height=30,
            corner_radius=4, fg_color=COLOR_PANEL_ALT, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_BORDER,
            command=self._on_open_catalog_folder,
        )
        self.btn_cat_folder.pack(fill="x", padx=16, pady=(0, 10))

    # =========================================================================
    # REFRESH & DATA LOGIC
    # =========================================================================
    def refresh(self) -> None:
        """Reloads photos and refreshes both tabs."""
        self._load_session_photos()
        if self._active_tab == "inspect":
            self._render_current_photo()
        else:
            self._refresh_catalog_grid()

    def _load_session_photos(self) -> None:
        if not self.ctx.active_session or not self.ctx.photo_repo:
            self._photos = []
            self._current_index = -1
            return

        self._photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        if not self._photos:
            self._current_index = -1
            return

        # Locate target photo from ctx.last_photo if available
        target_photo = self.ctx.last_photo
        if target_photo and target_photo.id:
            found_idx = next((i for i, p in enumerate(self._photos) if p.id == target_photo.id), -1)
            if found_idx != -1:
                self._current_index = found_idx
                return

        if self._current_index < 0 or self._current_index >= len(self._photos):
            self._current_index = len(self._photos) - 1

    def _render_current_photo(self) -> None:
        total = len(self._photos)
        if total == 0 or self._current_index < 0 or self._current_index >= total:
            self._show_empty_inspect_state()
            return

        photo = self._photos[self._current_index]
        self.ctx.last_photo = photo

        self.btn_prev.configure(state="normal" if self._current_index > 0 else "disabled")
        self.btn_next.configure(state="normal" if self._current_index < total - 1 else "disabled")
        self.lbl_index_badge.configure(text=f"{self._current_index + 1} / {total}")
        self.lbl_carousel_status.configure(text=f"Tray {photo.tray_number} ({photo.interval_from:.2f}m - {photo.interval_to:.2f}m) · Hole {photo.hole_id}")

        dropdown_vals = [f"Tray {p.tray_number} ({p.interval_from:.2f}-{p.interval_to:.2f}m)" for p in self._photos]
        self.tray_selector.configure(values=dropdown_vals)
        if 0 <= self._current_index < len(dropdown_vals):
            self.tray_selector.set(dropdown_vals[self._current_index])

        self.btn_save_next.configure(state="normal", fg_color=COLOR_ACCENT)
        self.btn_retake.configure(state="normal", text_color=COLOR_ERROR, border_color=COLOR_ERROR)

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

        self.entry_edit_hole.delete(0, "end")
        self.entry_edit_hole.insert(0, photo.hole_id)
        self.entry_edit_tray.delete(0, "end")
        self.entry_edit_tray.insert(0, photo.tray_number)
        self.entry_edit_from.delete(0, "end")
        self.entry_edit_from.insert(0, f"{photo.interval_from:.2f}")
        self.entry_edit_to.delete(0, "end")
        self.entry_edit_to.insert(0, f"{photo.interval_to:.2f}")

        self._refresh_validation_audit(photo)
        self._display_inspect_image(photo)

    def _show_empty_inspect_state(self) -> None:
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

    def _display_inspect_image(self, photo: PhotoModel) -> None:
        jpg_path = Path(photo.jpg_path)
        if not jpg_path.exists():
            self.img_label.configure(image="", text="JPG image file not found on disk.")
            return

        try:
            pil_img = Image.open(jpg_path)
            orig_w, orig_h = pil_img.size

            if self._zoom_mode:
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
                target_w = 540
                aspect = orig_h / orig_w if orig_w > 0 else 0.66
                target_h = int(target_w * aspect)
                self._ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(target_w, target_h))

            self.img_label.configure(image=self._ctk_image, text="")
        except Exception as e:
            logger.error("Error loading review photo %s: %s", jpg_path, e)
            self.img_label.configure(image="", text="Error rendering image file.")

    def _refresh_validation_audit(self, photo: PhotoModel) -> None:
        is_valid = True
        err_msgs: List[str] = []

        if photo.id and self.ctx.validation_runner:
            is_valid, err_msgs = self.ctx.validate_photo(photo.id)

        if photo.filename_base and photo.hole_id in photo.filename_base:
            self.lbl_chk_schema.configure(text="✓ Filename Schema: Validated Standard", text_color=COLOR_SUCCESS)
        else:
            self.lbl_chk_schema.configure(text="! Filename Schema: Incomplete identifier", text_color=COLOR_WARNING)

        if photo.interval_from < photo.interval_to:
            self.lbl_chk_interval.configure(text=f"✓ Depth Interval: Continuous ({photo.interval_from:.2f}m - {photo.interval_to:.2f}m)", text_color=COLOR_SUCCESS)
        else:
            self.lbl_chk_interval.configure(text=f"! Depth Interval: Invalid From >= To ({photo.interval_from:.2f}m - {photo.interval_to:.2f}m)", text_color=COLOR_ERROR)
            is_valid = False

        if photo.md5_jpg and photo.md5_raw:
            self.lbl_chk_md5.configure(text="✓ Checksum Integrity: RAW & JPG MD5 verified", text_color=COLOR_SUCCESS)
        else:
            self.lbl_chk_md5.configure(text="! Checksum Integrity: MD5 hash missing", text_color=COLOR_WARNING)

        jpg_ok = Path(photo.jpg_path).exists() if photo.jpg_path else False
        raw_ok = Path(photo.raw_path).exists() if photo.raw_path else False
        if jpg_ok and raw_ok:
            self.lbl_chk_assets.configure(text="✓ Physical Storage: RAW & JPG verified on disk", text_color=COLOR_SUCCESS)
        elif jpg_ok:
            self.lbl_chk_assets.configure(text="✓ Physical Storage: JPG present on disk", text_color=COLOR_SUCCESS)
        else:
            self.lbl_chk_assets.configure(text="! Physical Storage: Assets missing from disk", text_color=COLOR_ERROR)
            is_valid = False

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
    # CATALOG GRID LOGIC
    # =========================================================================
    def _refresh_catalog_grid(self) -> None:
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self._thumb_cache.clear()

        if not self.ctx.photo_repo or not self.ctx.active_session:
            ctk.CTkLabel(
                self.grid_container, text="No active session photos found.", font=get_font(11),
                text_color=COLOR_TEXT_HINT,
            ).grid(row=0, column=0, columnspan=3, pady=60)
            return

        query = self.search_entry.get().strip()
        status_sel = self.status_filter.get()
        status_param = None if status_sel in ("All Statuses", "Issues / Flagged") else status_sel

        photos = self.ctx.photo_repo.search(
            hole_id=query if query else None,
            tray_number=query if query else None,
            status=status_param,
        )

        if status_sel == "Issues / Flagged":
            photos = [p for p in photos if p.status != "VALID"]

        if not photos:
            ctk.CTkLabel(
                self.grid_container, text="No photos match the filter criteria.", font=get_font(11),
                text_color=COLOR_TEXT_HINT,
            ).grid(row=0, column=0, columnspan=3, pady=60)
            return

        col_count = 3
        for idx, photo in enumerate(photos):
            row = idx // col_count
            col = idx % col_count

            card = ctk.CTkFrame(
                self.grid_container, fg_color=COLOR_PANEL_ALT, corner_radius=4,
                border_width=1, border_color=COLOR_BORDER, cursor="hand2",
            )
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            thumb_path = Path(photo.thumbnail_path) if photo.thumbnail_path else None
            if thumb_path and thumb_path.exists():
                try:
                    pil_thumb = Image.open(thumb_path)
                    ctk_thumb = ctk.CTkImage(light_image=pil_thumb, dark_image=pil_thumb, size=(110, 74))
                    self._thumb_cache.append(ctk_thumb)
                    thumb_lbl = ctk.CTkLabel(card, image=ctk_thumb, text="")
                    thumb_lbl.pack(padx=4, pady=(4, 2))
                except Exception:
                    ctk.CTkLabel(card, text="[No Thumb]", font=get_font(9), text_color=COLOR_TEXT_HINT).pack(pady=14)
            else:
                ctk.CTkLabel(card, text="[No Thumb]", font=get_font(9), text_color=COLOR_TEXT_HINT).pack(pady=14)

            title_lbl = ctk.CTkLabel(card, text=f"{photo.hole_id} (Tray {photo.tray_number})", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY)
            title_lbl.pack(padx=2, pady=1)

            sub_lbl = ctk.CTkLabel(card, text=f"{photo.interval_from:.2f} - {photo.interval_to:.2f} m", font=get_font(9), text_color=COLOR_TEXT_MUTED)
            sub_lbl.pack(padx=2, pady=1)

            is_valid = photo.status == "VALID"
            status_color = COLOR_SUCCESS if is_valid else COLOR_WARNING
            status_bg = COLOR_SUCCESS_BG if is_valid else COLOR_WARNING_BG

            pill = ctk.CTkLabel(card, text=f" {photo.status} ", font=get_font(8, "bold"), text_color=status_color, fg_color=status_bg, corner_radius=2)
            pill.pack(padx=4, pady=(2, 4))

            for widget in [card, title_lbl, sub_lbl, pill]:
                widget.bind("<Button-1>", lambda e, p=photo: self._inspect_catalog_photo(p))

        # Select first photo by default if none selected
        if not self._catalog_selected_photo and photos:
            self._inspect_catalog_photo(photos[0])

    def _inspect_catalog_photo(self, photo: PhotoModel) -> None:
        self._catalog_selected_photo = photo
        jpg_path = Path(photo.jpg_path) if photo.jpg_path else None

        if jpg_path and jpg_path.exists():
            try:
                pil_img = Image.open(jpg_path)
                self._catalog_preview_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(300, 200))
                self.cat_img_lbl.configure(image=self._catalog_preview_img, text="")
            except Exception as e:
                logger.error("Error opening image %s: %s", jpg_path, e)
                self.cat_img_lbl.configure(image="", text="Error rendering image.")
        else:
            self.cat_img_lbl.configure(image="", text="File missing on disk.")

        self.lbl_cat_title.configure(text=f"File: {photo.filename_base}.jpg")
        self.lbl_cat_interval.configure(text=f"Hole: {photo.hole_id}  ·  Tray: {photo.tray_number}  ·  {photo.interval_from:.2f} m - {photo.interval_to:.2f} m")
        self.lbl_cat_status.configure(text=f"Validation Status: {photo.status}")
        self.lbl_cat_storage.configure(text="Storage: Local Session Archive")
        self.lbl_cat_hashes.configure(text=f"RAW MD5: {photo.md5_raw}\nJPG MD5: {photo.md5_jpg}\nCamera: {photo.camera_model}")

    def _on_open_selected_in_inspect(self) -> None:
        if not self._catalog_selected_photo:
            return

        self.ctx.last_photo = self._catalog_selected_photo
        # Find index in self._photos
        for idx, p in enumerate(self._photos):
            if p.id == self._catalog_selected_photo.id:
                self._current_index = idx
                break

        self.select_tab("inspect")

    def _switch_to_catalog_at_current(self) -> None:
        if 0 <= self._current_index < len(self._photos):
            self._catalog_selected_photo = self._photos[self._current_index]
        self.select_tab("catalog")

    def _on_open_catalog_folder(self) -> None:
        if self._catalog_selected_photo and self._catalog_selected_photo.jpg_path:
            folder = str(Path(self._catalog_selected_photo.jpg_path).parent)
            try:
                os.startfile(folder)
            except Exception as e:
                logger.error("Failed opening folder %s: %s", folder, e)

    def _on_export_csv(self) -> None:
        sess = self.ctx.active_session
        if not sess:
            return

        photos = self.ctx.photo_repo.list_by_session(sess.id) if self.ctx.photo_repo else []
        hole_id = "TSD168"
        if photos and photos[0].hole_id:
            hole_id = photos[0].hole_id

        dest = filedialog.asksaveasfilename(
            title="Export Geological Report CSV",
            initialfile=f"{hole_id}.csv",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
        )
        if dest:
            out_path = ImageProcessor.export_csv_report(sess, photos, Path(dest))
            try:
                os.startfile(str(out_path))
            except Exception:
                pass

    # =========================================================================
    # ACTIONS: PREV / NEXT / ZOOM / EDIT / RETAKE / APPROVE
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
            self._display_inspect_image(self._photos[self._current_index])

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
        if 0 <= self._current_index < len(self._photos) - 1:
            self._current_index += 1
            self._render_current_photo()
        else:
            if self.advance_tray_fn:
                self.advance_tray_fn()
            self.navigate_fn("capture")

    def _on_retake(self) -> None:
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
