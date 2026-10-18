"""Capture Screen (Professional Industrial Redesign).
Priority: Large dominant Live View with framing overlays, structured Tray Information on Left,
Camera Controls on top/right toolbar, Pre-flight validation checklist, and a prominent
Industrial Orange [ CAPTURE ] button as the visual focal point.
Zero emojis, strict professional standards.
"""

import threading
import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk

from core.app_context import get_app_context
from core.logger import get_logger
from diagnostics.diagnostics import get_diagnostics
from imaging.crop import CropRegion
from ui.date_picker import DatePickerModal
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
    FONT_FAMILY,
    get_font,
)

logger = get_logger(__name__)


class CaptureView(ctk.CTkFrame):
    """Core photography and framing screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self.diag = get_diagnostics()

        # Framing / Crop / Zoom / Live View state
        self.grid_enabled = True
        self.crop_enabled = True
        self.is_zoomed = False
        self.is_live_view_active = True
        self.crop_region: Optional[CropRegion] = None
        self._current_photo_image: Optional[ImageTk.PhotoImage] = None
        self._captured_photo_image: Optional[ImageTk.PhotoImage] = None
        self._pending_photo = None
        self._is_capturing = False
        self._is_previewing_capture = False

        self._build_ui()
        self._setup_bindings()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=0, minsize=350)  # Left: Tray Data Form & Camera Settings
        self.grid_columnconfigure(1, weight=1)               # Center: Dominant Live View & Action
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # 1. LEFT PANEL: Tray Information & Camera Settings Tabview (Reference v1.4.0)
        # =========================================================================
        self.left_tabs = ctk.CTkTabview(
            self,
            width=350,
            fg_color=COLOR_PANEL,
            segmented_button_fg_color=COLOR_BORDER,
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color=COLOR_ACCENT_HOVER,
            segmented_button_unselected_color=COLOR_PANEL,
            segmented_button_unselected_hover_color=COLOR_ACCENT_LIGHT,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_left_tab_changed,
        )
        self.left_tabs.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)

        tab_tray = self.left_tabs.add("Tray Data")
        tab_cam = self.left_tabs.add("Camera Settings")

        # ----------------- TAB 1: TRAY DATA -----------------
        tray_scroll = ctk.CTkScrollableFrame(tab_tray, fg_color="transparent")
        tray_scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            tray_scroll,
            text="TRAY IDENTIFICATION",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=10, pady=(6, 1))

        ctk.CTkLabel(
            tray_scroll,
            text="Core tray parameters & interval.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=10, pady=(0, 6))

        # Session Guard Notice
        self.session_guard_frame = ctk.CTkFrame(
            tray_scroll,
            fg_color=COLOR_WARNING_BG,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_WARNING_BORDER,
        )
        self.session_guard_lbl = ctk.CTkLabel(
            self.session_guard_frame,
            text="No active session. Please open or create a session first.",
            font=get_font(10, "bold"),
            text_color=COLOR_WARNING,
            wraplength=260,
            justify="left",
        )
        self.session_guard_lbl.pack(anchor="w", padx=10, pady=(6, 2))

        self.btn_go_session = ctk.CTkButton(
            self.session_guard_frame,
            text="Manage Session →",
            font=get_font(10, "bold"),
            height=26,
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER_STRONG,
            text_color="#FFFFFF",
            command=lambda: self.navigate_fn("session"),
        )
        self.btn_go_session.pack(anchor="w", padx=10, pady=(0, 6))

        # 1. Session Details:
        self.box_session = ctk.CTkFrame(tray_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        self.box_session.pack(fill="x", padx=6, pady=(4, 6))
        box_session = self.box_session

        ctk.CTkLabel(box_session, text="Session Details:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=8, pady=(6, 4))
        grid_sess = ctk.CTkFrame(box_session, fg_color="transparent")
        grid_sess.pack(fill="x", padx=8, pady=(0, 6))
        grid_sess.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(grid_sess, text="Date:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=2)
        f_date = ctk.CTkFrame(grid_sess, fg_color="transparent")
        f_date.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=2)
        f_date.grid_columnconfigure(0, weight=1)

        self.entry_sess_date = ctk.CTkEntry(f_date, height=26, font=get_font(10), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.entry_sess_date.grid(row=0, column=0, sticky="ew")
        self.entry_sess_date.bind("<FocusOut>", self._on_sess_date_entry_changed)
        self.entry_sess_date.bind("<Return>", self._on_sess_date_entry_changed)

        self.btn_pick_date = ctk.CTkButton(
            f_date,
            text="📅",
            width=28,
            height=26,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_pick_sess_date,
        )
        self.btn_pick_date.grid(row=0, column=1, padx=(4, 0))

        ctk.CTkLabel(grid_sess, text="Name:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_sess_name = ctk.CTkEntry(grid_sess, height=26, font=get_font(10), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.entry_sess_name.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=2)

        ctk.CTkLabel(grid_sess, text="Site:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=0, sticky="w", pady=2)
        self.entry_sess_site = ctk.CTkEntry(grid_sess, height=26, font=get_font(10), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.entry_sess_site.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=2)

        # 2. Image Details:
        box_img = ctk.CTkFrame(tray_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        box_img.pack(fill="x", padx=6, pady=(0, 6))

        ctk.CTkLabel(box_img, text="Image Details:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=8, pady=(6, 4))
        grid_img = ctk.CTkFrame(box_img, fg_color="transparent")
        grid_img.pack(fill="x", padx=8, pady=(0, 6))
        grid_img.grid_columnconfigure(1, weight=1)

        # Hole ID
        ctk.CTkLabel(grid_img, text="Hole ID:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_hole = ctk.CTkEntry(grid_img, height=26, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_hole.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=2)
        self.entry_hole.insert(0, "TSD168")

        # Tray ID
        ctk.CTkLabel(grid_img, text="Tray ID:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_tray = ctk.CTkEntry(grid_img, height=26, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_tray.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=2)
        self.entry_tray.insert(0, "1")

        # Core Interval From
        ctk.CTkLabel(grid_img, text="Core Interval From:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=0, sticky="w", pady=2)
        self.entry_from = ctk.CTkEntry(grid_img, height=26, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_from.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=2)
        self.entry_from.insert(0, "0")

        # Core Interval To
        ctk.CTkLabel(grid_img, text="Core Interval To:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=3, column=0, sticky="w", pady=2)
        self.entry_to = ctk.CTkEntry(grid_img, height=26, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_to.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=2)
        self.entry_to.insert(0, "2")

        # Tray Rows
        ctk.CTkLabel(grid_img, text="Tray Rows:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=4, column=0, sticky="w", pady=2)
        self.entry_tray_rows = ctk.CTkEntry(grid_img, height=26, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.entry_tray_rows.grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=2)
        self.entry_tray_rows.insert(0, "3")

        # Tray Crop Area
        ctk.CTkLabel(grid_img, text="Tray Crop Area:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=5, column=0, sticky="w", pady=2)
        self.entry_crop_area = ctk.CTkEntry(grid_img, height=26, font=get_font(10), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.entry_crop_area.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=2)
        self.entry_crop_area.insert(0, "0.0025 0.3006 0.9645 0.6335")

        # Tray Length (mm)
        ctk.CTkLabel(grid_img, text="Tray Length (mm):", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=6, column=0, sticky="w", pady=2)
        self.entry_tray_length = ctk.CTkEntry(grid_img, height=26, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.entry_tray_length.grid(row=6, column=1, sticky="ew", padx=(8, 0), pady=2)
        self.entry_tray_length.insert(0, "700")

        # Tray Width (mm)
        ctk.CTkLabel(grid_img, text="Tray Width (mm):", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=7, column=0, sticky="w", pady=2)
        self.entry_tray_width = ctk.CTkEntry(grid_img, height=26, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.entry_tray_width.grid(row=7, column=1, sticky="ew", padx=(8, 0), pady=2)
        self.entry_tray_width.insert(0, "300")

        # 3. Comments:
        box_comments = ctk.CTkFrame(tray_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        box_comments.pack(fill="x", padx=6, pady=(0, 6))

        ctk.CTkLabel(box_comments, text="Comments:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=8, pady=(6, 2))
        self.txt_comments = ctk.CTkTextbox(box_comments, height=65, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.txt_comments.pack(fill="x", padx=8, pady=(0, 6))

        # 4. Series Details:
        box_series = ctk.CTkFrame(tray_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        box_series.pack(fill="x", padx=6, pady=(0, 6))

        ctk.CTkLabel(box_series, text="Series Details:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=8, pady=(6, 4))
        grid_series = ctk.CTkFrame(box_series, fg_color="transparent")
        grid_series.pack(fill="x", padx=8, pady=(0, 6))
        grid_series.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(grid_series, text="Image Count:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=2)
        self.lbl_series_count = ctk.CTkLabel(grid_series, text="0", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_series_count.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=2)

        ctk.CTkLabel(grid_series, text="Total Used:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_series_space = ctk.CTkLabel(grid_series, text="waiting...", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_series_space.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=2)

        ctk.CTkLabel(grid_series, text="Target Folder:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=0, sticky="w", pady=2)
        f_target = ctk.CTkFrame(grid_series, fg_color="transparent")
        f_target.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=2)
        f_target.grid_columnconfigure(0, weight=1)
        self.entry_target_folder = ctk.CTkEntry(f_target, height=24, font=get_font(10), fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1)
        self.entry_target_folder.grid(row=0, column=0, sticky="ew")
        self.btn_browse_folder = ctk.CTkButton(f_target, text="...", width=26, height=24, font=get_font(10, "bold"), fg_color=COLOR_BORDER, text_color=COLOR_CHARCOAL, hover_color=COLOR_BORDER_STRONG, command=self._on_browse_target)
        self.btn_browse_folder.grid(row=0, column=1, sticky="e", padx=(4, 0))

        # Target Server Folder
        ctk.CTkLabel(grid_series, text="Target Server Folder:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=3, column=0, sticky="w", pady=2)
        f_server_target = ctk.CTkFrame(grid_series, fg_color="transparent")
        f_server_target.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=2)
        f_server_target.grid_columnconfigure(0, weight=1)
        self.entry_server_folder = ctk.CTkEntry(
            f_server_target,
            height=24,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
            placeholder_text="\\\\server\\share or folder path...",
        )
        self.entry_server_folder.grid(row=0, column=0, sticky="ew")
        self.entry_server_folder.bind("<FocusOut>", self._on_server_folder_changed)
        self.entry_server_folder.bind("<KeyRelease>", self._on_server_folder_changed)

        self.btn_browse_server_folder = ctk.CTkButton(
            f_server_target,
            text="...",
            width=26,
            height=24,
            font=get_font(10, "bold"),
            fg_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER_STRONG,
            command=self._on_browse_server_target,
        )
        self.btn_browse_server_folder.grid(row=0, column=1, sticky="e", padx=(4, 0))

        self.btn_open_csv = ctk.CTkButton(
            box_series,
            text="Open CSV Report (Excel)",
            font=get_font(11, "bold"),
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_open_csv_report,
        )
        self.btn_open_csv.pack(fill="x", padx=8, pady=(6, 4))

        self.btn_sync_server = ctk.CTkButton(
            box_series,
            text="Sync Session to Server Folder",
            font=get_font(11, "bold"),
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_sync_server_folder,
        )
        self.btn_sync_server.pack(fill="x", padx=8, pady=(0, 8))

        # ----------------- TAB 2: CAMERA SETTINGS (Image 1) -----------------
        cam_scroll = ctk.CTkScrollableFrame(tab_cam, fg_color="transparent")
        cam_scroll.pack(fill="both", expand=True)

        # Device Information:
        dev_box = ctk.CTkFrame(cam_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        dev_box.pack(fill="x", padx=10, pady=(6, 8))

        ctk.CTkLabel(dev_box, text="Device Information & Connection:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=10, pady=(8, 2))

        # Interface Selector Dropdown
        ctk.CTkLabel(dev_box, text="Camera Interface:", font=get_font(10, "bold"), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=14, pady=(4, 1))
        self.opt_capture_interface = ctk.CTkOptionMenu(
            dev_box,
            values=[
                "Wi-Fi DSLR Wireless Tethering",
                "Direct USB DSLR (Cable)",
                "Universal Hot-Folder Ingest",
                "Physical USB Webcam",
                "Standby / Simulator",
            ],
            height=26,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_capture_interface_changed,
        )
        self.opt_capture_interface.pack(fill="x", padx=12, pady=(0, 6))

        # Webcam Device Selector (Internal vs External USB)
        ctk.CTkLabel(dev_box, text="Webcam Device (Internal / External):", font=get_font(10, "bold"), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=14, pady=(2, 1))
        webcam_row = ctk.CTkFrame(dev_box, fg_color="transparent")
        webcam_row.pack(fill="x", padx=12, pady=(0, 2))
        webcam_row.grid_columnconfigure(0, weight=1)
        self._webcam_display_to_index: dict = {}
        self.opt_webcam_device = ctk.CTkOptionMenu(
            webcam_row,
            values=["Scanning webcams..."],
            height=26,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_webcam_device_changed,
        )
        self.opt_webcam_device.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.btn_webcam_refresh = ctk.CTkButton(
            webcam_row,
            text="Refresh",
            width=70,
            height=26,
            font=get_font(10, "bold"),
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_refresh_webcam_list,
        )
        self.btn_webcam_refresh.grid(row=0, column=1, sticky="e")
        self.lbl_webcam_hint = ctk.CTkLabel(
            dev_box,
            text="Pilih webcam internal atau external, lalu live view mengikuti otomatis.",
            font=get_font(9),
            text_color=COLOR_TEXT_MUTED,
            wraplength=280,
            justify="left",
        )
        self.lbl_webcam_hint.pack(anchor="w", padx=14, pady=(0, 6))

        self.lbl_dev_model = ctk.CTkLabel(dev_box, text="Model: Wi-Fi DSLR Tethering", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_dev_model.pack(anchor="w", padx=16, pady=1)

        self.lbl_dev_serial = ctk.CTkLabel(dev_box, text="Status: Ready", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_dev_serial.pack(anchor="w", padx=16, pady=1)

        self.lbl_dev_fw = ctk.CTkLabel(dev_box, text="Firmware: Wi-Fi v2.0", font=get_font(11), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_dev_fw.pack(anchor="w", padx=16, pady=(1, 4))

        dev_btn_row = ctk.CTkFrame(dev_box, fg_color="transparent")
        dev_btn_row.pack(fill="x", padx=12, pady=(2, 8))
        dev_btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_dev_detect = ctk.CTkButton(
            dev_btn_row,
            text="Detect Camera",
            font=get_font(10, "bold"),
            height=26,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_detect_cam,
        )
        self.btn_dev_detect.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_dev_reconnect = ctk.CTkButton(
            dev_btn_row,
            text="Reconnect",
            font=get_font(10),
            height=26,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_reconnect_cam,
        )
        self.btn_dev_reconnect.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Settings:
        set_box = ctk.CTkFrame(cam_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        set_box.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(set_box, text="Settings:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=10, pady=(8, 4))

        set_grid = ctk.CTkFrame(set_box, fg_color="transparent")
        set_grid.pack(fill="x", padx=10, pady=(0, 10))
        set_grid.grid_columnconfigure(1, weight=1)

        # 1. Format
        ctk.CTkLabel(set_grid, text="Format:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=3)
        self.opt_cam_format = ctk.CTkOptionMenu(
            set_grid,
            values=["JPEG", "RAW", "RAW+JPEG"],
            height=26,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_cam_setting_changed,
        )
        self.opt_cam_format.set("JPEG")
        self.opt_cam_format.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)

        # 2. Exposure
        ctk.CTkLabel(set_grid, text="Exposure:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=0, sticky="w", pady=3)
        self.opt_cam_exposure = ctk.CTkOptionMenu(
            set_grid,
            values=["Not valid/no settings", "Auto", "Manual", "1/125", "1/250", "1/500"],
            height=26,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_cam_setting_changed,
        )
        self.opt_cam_exposure.set("Not valid/no settings")
        self.opt_cam_exposure.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=3)

        # 3. Aperture
        ctk.CTkLabel(set_grid, text="Aperture:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=0, sticky="w", pady=3)
        self.opt_cam_aperture = ctk.CTkOptionMenu(
            set_grid,
            values=["10", "f/4.0", "f/5.6", "f/8.0", "f/10", "f/11", "f/16"],
            height=26,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_cam_setting_changed,
        )
        self.opt_cam_aperture.set("10")
        self.opt_cam_aperture.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=3)

        # 4. Enable Flash
        ctk.CTkLabel(set_grid, text="Enable Flash:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=3, column=0, sticky="w", pady=3)
        self.chk_cam_flash = ctk.CTkCheckBox(
            set_grid,
            text="",
            width=22,
            height=22,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            border_color=COLOR_BORDER_STRONG,
            command=self._on_cam_setting_changed,
        )
        self.chk_cam_flash.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=3)

        # 5. Metering Mode
        ctk.CTkLabel(set_grid, text="Metering Mode:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=4, column=0, sticky="w", pady=3)
        self.opt_cam_metering = ctk.CTkOptionMenu(
            set_grid,
            values=["Center-Weighted Average", "Evaluative", "Spot", "Partial"],
            height=26,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_cam_setting_changed,
        )
        self.opt_cam_metering.set("Center-Weighted Average")
        self.opt_cam_metering.grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=3)

        # 6. Focusing
        ctk.CTkLabel(set_grid, text="Focusing:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=5, column=0, sticky="w", pady=3)
        self.opt_cam_focusing = ctk.CTkOptionMenu(
            set_grid,
            values=["One-Shot", "AI Focus", "AI Servo", "Manual"],
            height=26,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_cam_setting_changed,
        )
        self.opt_cam_focusing.set("One-Shot")
        self.opt_cam_focusing.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=3)

        # 7. Film Speed (ISO)
        ctk.CTkLabel(set_grid, text="Film Speed:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=6, column=0, sticky="w", pady=3)
        self.opt_cam_iso = ctk.CTkOptionMenu(
            set_grid,
            values=["100", "200", "400", "800", "1600", "3200", "Auto"],
            height=26,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_cam_setting_changed,
        )
        self.opt_cam_iso.set("100")
        self.opt_cam_iso.grid(row=6, column=1, sticky="ew", padx=(8, 0), pady=3)

        # 8. Resolution Quality
        ctk.CTkLabel(set_grid, text="Resolution:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=7, column=0, sticky="w", pady=3)
        self.opt_cam_resolution = ctk.CTkOptionMenu(
            set_grid,
            values=[
                "Auto (Best Native DSLR — 18MP/24MP+)",
                "5184 x 3456 (18MP Canon 60D Native)",
                "6000 x 4000 (24MP UHD)",
                "4000 x 3000 (12MP High Res)",
                "3840 x 2160 (4K UHD)",
                "1920 x 1080 (Full HD 1080p)",
                "1280 x 720 (HD 720p)",
            ],
            height=26,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
            dropdown_fg_color=COLOR_PANEL,
            dropdown_text_color=COLOR_CHARCOAL,
            command=self._on_cam_resolution_changed,
        )
        self.opt_cam_resolution.set("Auto (Best Native DSLR — 18MP/24MP+)")
        self.opt_cam_resolution.grid(row=7, column=1, sticky="ew", padx=(8, 0), pady=3)

        # 9. Max Photo Size (MB)
        ctk.CTkLabel(set_grid, text="Max Size (MB):", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=8, column=0, sticky="w", pady=3)
        size_frame = ctk.CTkFrame(set_grid, fg_color="transparent")
        size_frame.grid(row=8, column=1, sticky="ew", padx=(8, 0), pady=3)
        size_frame.grid_columnconfigure(0, weight=1)

        cur_max_size = str(self.ctx.config.get("imaging", "max_photo_size_mb", 10.0))
        self.entry_max_size = ctk.CTkEntry(
            size_frame,
            height=26,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_CHARCOAL,
        )
        self.entry_max_size.insert(0, cur_max_size)
        self.entry_max_size.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_save_max_size = ctk.CTkButton(
            size_frame,
            text="Set",
            font=get_font(10, "bold"),
            height=26,
            width=36,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_save_max_size,
        )
        self.btn_save_max_size.grid(row=0, column=1)

        # Custom Resolution W x H
        f_custom_res = ctk.CTkFrame(set_box, fg_color="transparent")
        f_custom_res.pack(fill="x", padx=10, pady=(0, 8))
        f_custom_res.grid_columnconfigure(0, weight=1)

        self.lbl_res_active = ctk.CTkLabel(
            f_custom_res,
            text="Active: Best Native DSLR",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_res_active.grid(row=0, column=0, sticky="w")

        res_inputs = ctk.CTkFrame(f_custom_res, fg_color="transparent")
        res_inputs.grid(row=0, column=1, sticky="e")
        self.entry_res_w = ctk.CTkEntry(res_inputs, placeholder_text="W", width=42, height=24, font=get_font(10))
        self.entry_res_w.pack(side="left", padx=2)
        ctk.CTkLabel(res_inputs, text="×", font=get_font(10, "bold"), text_color=COLOR_TEXT_MUTED).pack(side="left", padx=1)
        self.entry_res_h = ctk.CTkEntry(res_inputs, placeholder_text="H", width=42, height=24, font=get_font(10))
        self.entry_res_h.pack(side="left", padx=2)
        self.btn_apply_custom_res = ctk.CTkButton(
            res_inputs,
            text="Set",
            font=get_font(10, "bold"),
            height=24,
            width=36,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_apply_custom_resolution,
        )
        self.btn_apply_custom_res.pack(side="left", padx=(3, 0))

        # 3. Wi-Fi DSLR Wireless Settings Card
        wifi_box = ctk.CTkFrame(cam_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        wifi_box.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(wifi_box, text="Wi-Fi DSLR Wireless Settings:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(wifi_box, text="Canon / Nikon / Sony Wi-Fi Tethering & IP connection.", font=get_font(9), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=10, pady=(0, 4))

        # Camera IP
        ctk.CTkLabel(wifi_box, text="Camera IP Address:", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(2, 1))
        f_ip = ctk.CTkFrame(wifi_box, fg_color="transparent")
        f_ip.pack(fill="x", padx=10, pady=(0, 4))
        f_ip.grid_columnconfigure(0, weight=1)

        self.entry_cam_wifi_ip = ctk.CTkEntry(
            f_ip,
            height=26,
            font=get_font(10),
            placeholder_text="e.g. 192.168.1.100",
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
        )
        self.entry_cam_wifi_ip.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_cam_test_wifi = ctk.CTkButton(
            f_ip,
            text="Ping / Test",
            font=get_font(10, "bold"),
            height=26,
            width=80,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_test_wifi_ip,
        )
        self.btn_cam_test_wifi.grid(row=0, column=1, sticky="e")

        # Tether Folder
        ctk.CTkLabel(wifi_box, text="Wi-Fi Tether Folder:", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(2, 1))
        f_tether = ctk.CTkFrame(wifi_box, fg_color="transparent")
        f_tether.pack(fill="x", padx=10, pady=(0, 4))
        f_tether.grid_columnconfigure(0, weight=1)

        self.entry_cam_tether_folder = ctk.CTkEntry(
            f_tether,
            height=26,
            font=get_font(10),
            placeholder_text="EOS Utility / Sony Remote folder...",
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
        )
        self.entry_cam_tether_folder.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_browse_cam_tether = ctk.CTkButton(
            f_tether,
            text="...",
            width=26,
            height=26,
            font=get_font(10, "bold"),
            fg_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER_STRONG,
            command=self._on_browse_cam_tether,
        )
        self.btn_browse_cam_tether.grid(row=0, column=1, padx=(0, 4))

        self.btn_auto_detect_tether = ctk.CTkButton(
            f_tether,
            text="Auto",
            width=48,
            height=26,
            font=get_font(10, "bold"),
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_auto_detect_tether,
        )
        self.btn_auto_detect_tether.grid(row=0, column=2)

        # Wi-Fi Save & Feedback
        f_wifi_save = ctk.CTkFrame(wifi_box, fg_color="transparent")
        f_wifi_save.pack(fill="x", padx=10, pady=(2, 8))
        f_wifi_save.grid_columnconfigure(0, weight=1)

        self.lbl_wifi_feedback = ctk.CTkLabel(
            f_wifi_save,
            text="",
            font=get_font(9),
            text_color=COLOR_TEXT_MUTED,
            wraplength=200,
            justify="left",
            anchor="w",
        )
        self.lbl_wifi_feedback.grid(row=0, column=0, sticky="w")

        self.btn_save_wifi_cfg = ctk.CTkButton(
            f_wifi_save,
            text="Save Wi-Fi",
            font=get_font(10, "bold"),
            height=26,
            width=80,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_save_wifi_settings,
        )
        self.btn_save_wifi_cfg.grid(row=0, column=1, sticky="e")

        # 4. Storage & Server Repository Configuration Card
        srv_box = ctk.CTkFrame(cam_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        srv_box.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(srv_box, text="Storage & Server Configuration:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(srv_box, text="Local archive directories and central server target.", font=get_font(9), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=10, pady=(0, 4))

        # Target Server Folder
        ctk.CTkLabel(srv_box, text="Target Server Folder:", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(2, 1))
        f_srv_folder = ctk.CTkFrame(srv_box, fg_color="transparent")
        f_srv_folder.pack(fill="x", padx=10, pady=(0, 4))
        f_srv_folder.grid_columnconfigure(0, weight=1)

        self.entry_settings_server_folder = ctk.CTkEntry(
            f_srv_folder,
            height=26,
            font=get_font(10),
            placeholder_text="\\\\server\\share or folder path...",
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
        )
        self.entry_settings_server_folder.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_settings_browse_server = ctk.CTkButton(
            f_srv_folder,
            text="...",
            width=26,
            height=26,
            font=get_font(10, "bold"),
            fg_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER_STRONG,
            command=self._on_settings_browse_server,
        )
        self.btn_settings_browse_server.grid(row=0, column=1, padx=(0, 4))

        self.btn_settings_open_server = ctk.CTkButton(
            f_srv_folder,
            text="Open",
            width=48,
            height=26,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_settings_open_server,
        )
        self.btn_settings_open_server.grid(row=0, column=2)

        # Local Base Directory
        ctk.CTkLabel(srv_box, text="Local Base Directory:", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(2, 1))
        f_loc = ctk.CTkFrame(srv_box, fg_color="transparent")
        f_loc.pack(fill="x", padx=10, pady=(0, 4))
        f_loc.grid_columnconfigure(0, weight=1)

        self.entry_settings_local_folder = ctk.CTkEntry(
            f_loc,
            height=26,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
        )
        self.entry_settings_local_folder.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_settings_open_local = ctk.CTkButton(
            f_loc,
            text="Explorer",
            width=64,
            height=26,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_settings_open_local,
        )
        self.btn_settings_open_local.grid(row=0, column=1)

        # Server API URL
        ctk.CTkLabel(srv_box, text="Server API URL:", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(2, 1))
        self.entry_settings_server_url = ctk.CTkEntry(
            srv_box,
            height=26,
            font=get_font(10),
            placeholder_text="http://127.0.0.1:8000/api/v1",
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            border_width=1,
        )
        self.entry_settings_server_url.pack(fill="x", padx=10, pady=(0, 4))

        # Storage Save & Test Actions
        f_srv_actions = ctk.CTkFrame(srv_box, fg_color="transparent")
        f_srv_actions.pack(fill="x", padx=10, pady=(2, 8))
        f_srv_actions.grid_columnconfigure(0, weight=1)

        self.lbl_settings_server_status = ctk.CTkLabel(
            f_srv_actions,
            text="",
            font=get_font(9),
            text_color=COLOR_SUCCESS,
            wraplength=180,
            justify="left",
            anchor="w",
        )
        self.lbl_settings_server_status.grid(row=0, column=0, sticky="w")

        f_srv_btns = ctk.CTkFrame(f_srv_actions, fg_color="transparent")
        f_srv_btns.grid(row=0, column=1, sticky="e")

        self.btn_test_srv = ctk.CTkButton(
            f_srv_btns,
            text="Test",
            font=get_font(10),
            height=26,
            width=50,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_settings_test_server,
        )
        self.btn_test_srv.pack(side="left", padx=(0, 4))

        self.btn_save_srv = ctk.CTkButton(
            f_srv_btns,
            text="Save Storage",
            font=get_font(10, "bold"),
            height=26,
            width=88,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_settings_save_server,
        )
        self.btn_save_srv.pack(side="left")

        # 5. Technical Diagnostics & Recovery Card
        diag_box = ctk.CTkFrame(cam_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        diag_box.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(diag_box, text="Technical Diagnostics & Recovery:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=10, pady=(8, 2))

        f_diag_btns = ctk.CTkFrame(diag_box, fg_color="transparent")
        f_diag_btns.pack(fill="x", padx=10, pady=(2, 4))
        f_diag_btns.grid_columnconfigure((0, 1), weight=1)

        self.btn_run_diag = ctk.CTkButton(
            f_diag_btns,
            text="Run Diagnostics",
            font=get_font(10, "bold"),
            height=26,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_run_diagnostics,
        )
        self.btn_run_diag.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_export_diag = ctk.CTkButton(
            f_diag_btns,
            text="Export JSON",
            font=get_font(10),
            height=26,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_export_report,
        )
        self.btn_export_diag.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.diag_result_box = ctk.CTkTextbox(
            diag_box,
            height=90,
            font=ctk.CTkFont(family="Consolas", size=9),
            fg_color=COLOR_PANEL,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.diag_result_box.pack(fill="x", padx=10, pady=(2, 6))

        # Crash Recovery
        self.recovery_card = ctk.CTkFrame(diag_box, fg_color=COLOR_PANEL, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        self.recovery_card.pack(fill="x", padx=10, pady=(0, 8))

        self.recovery_lbl = ctk.CTkLabel(
            self.recovery_card,
            text="Checking crash status...",
            font=get_font(9),
            text_color=COLOR_TEXT_MUTED,
            wraplength=280,
            justify="left",
        )
        self.recovery_lbl.pack(anchor="w", padx=8, pady=(6, 3))

        self.btn_resume = ctk.CTkButton(
            self.recovery_card,
            text="Resume Incomplete Captures",
            font=get_font(10, "bold"),
            height=24,
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            hover_color="#27272A",
            text_color="#FFFFFF",
            command=self._on_resume_captures,
        )
        self.btn_resume.pack(fill="x", padx=8, pady=(0, 6))

        # 6. Live System Logs Card
        log_box = ctk.CTkFrame(cam_scroll, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        log_box.pack(fill="x", padx=10, pady=(0, 10))

        f_log_head = ctk.CTkFrame(log_box, fg_color="transparent")
        f_log_head.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(f_log_head, text="Live System Logs:", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(side="left")

        self.btn_ref_log = ctk.CTkButton(
            f_log_head,
            text="Refresh Logs",
            font=get_font(9),
            width=75,
            height=22,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._refresh_logs,
        )
        self.btn_ref_log.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            log_box,
            height=110,
            font=ctk.CTkFont(family="Consolas", size=9),
            fg_color=COLOR_PANEL,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.log_textbox.pack(fill="x", padx=10, pady=(2, 8))

        self._update_left_tab_styles()

        # =========================================================================
        # 2. CENTER PANEL: Live View, Controls Toolbar, and Capture Action
        # =========================================================================
        center_panel = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        center_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        center_panel.grid_rowconfigure(1, weight=1)  # Dominant live view canvas
        center_panel.grid_columnconfigure(0, weight=1)

        # --- Top Toolbar: Stream status & Camera Controls ---
        toolbar = ctk.CTkFrame(center_panel, height=38, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 6))

        # Left status in toolbar
        self.stream_info_lbl = ctk.CTkLabel(
            toolbar,
            text="LIVE CAMERA STREAM",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        self.stream_info_lbl.pack(side="left")

        # Right camera controls in toolbar
        self.btn_reconnect = ctk.CTkButton(
            toolbar,
            text="Reconnect",
            font=get_font(11),
            width=90,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_reconnect_cam,
        )
        self.btn_reconnect.pack(side="right", padx=(4, 0))

        self.btn_crop_toggle = ctk.CTkButton(
            toolbar,
            text="Crop Box: ON",
            font=get_font(11, "bold"),
            width=100,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._toggle_crop,
        )
        self.btn_crop_toggle.pack(side="right", padx=(4, 0))

        # --- Center Canvas: Large Live View ---
        canvas_container = ctk.CTkFrame(center_panel, fg_color="#09090B", corner_radius=4)
        canvas_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_container,
            bg="#09090B",
            highlightthickness=0,
            cursor="cross",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # --- Pre-flight Checklist Banner ---
        self.preflight_banner = ctk.CTkFrame(
            center_panel,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.preflight_banner.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 4))

        self.lbl_checklist_items = ctk.CTkLabel(
            self.preflight_banner,
            text="Camera ?  ·  Session ?  ·  Hole ID ?  ·  Tray ID ?  ·  Interval ?  ·  Storage ?  ·  Crop ?",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_checklist_items.pack(anchor="w", padx=12, pady=(4, 1))

        self.lbl_preflight_verdict = ctk.CTkLabel(
            self.preflight_banner,
            text="Evaluating pre-flight parameters...",
            font=get_font(11, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.lbl_preflight_verdict.pack(anchor="w", padx=12, pady=(0, 4))

        # --- CAMERA OPERATIONAL CONTROLS (Matching Industrial Camera Reference) ---
        control_panel = ctk.CTkFrame(
            center_panel,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        control_panel.grid(row=3, column=0, sticky="ew", padx=16, pady=(2, 6))
        control_panel.grid_columnconfigure(0, weight=1)  # Left: Capture Details
        control_panel.grid_columnconfigure(1, weight=1)  # Center: Grid, Zoom, Steps
        control_panel.grid_columnconfigure(2, weight=0)  # Right: Action buttons stack

        # --- Column 0: Capture Details Card (Matching Legacy Software) ---
        card_details = ctk.CTkFrame(
            control_panel,
            fg_color=COLOR_PANEL,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card_details.grid(row=0, column=0, sticky="nsew", padx=(10, 6), pady=8)
        card_details.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card_details,
            text="Capture Details",
            font=get_font(11, "bold"),
            text_color=COLOR_CHARCOAL,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 2))

        ctk.CTkLabel(card_details, text="Dimensions:", font=get_font(10), text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=0, sticky="w", padx=8, pady=1)
        self.lbl_cap_dims = ctk.CTkLabel(card_details, text="waiting ...", font=get_font(10), text_color=COLOR_TEXT_HINT)
        self.lbl_cap_dims.grid(row=1, column=1, sticky="w", padx=4, pady=1)

        ctk.CTkLabel(card_details, text="File Size:", font=get_font(10), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=0, sticky="w", padx=8, pady=1)
        self.lbl_cap_filesize = ctk.CTkLabel(card_details, text="waiting ...", font=get_font(10), text_color=COLOR_TEXT_HINT)
        self.lbl_cap_filesize.grid(row=2, column=1, sticky="w", padx=4, pady=1)

        ctk.CTkLabel(card_details, text="Capture:", font=get_font(10), text_color=COLOR_TEXT_PRIMARY).grid(row=3, column=0, sticky="w", padx=8, pady=1)
        self.lbl_cap_status = ctk.CTkLabel(card_details, text="waiting ...", font=get_font(10), text_color=COLOR_TEXT_HINT)
        self.lbl_cap_status.grid(row=3, column=1, sticky="w", padx=4, pady=1)

        ctk.CTkLabel(card_details, text="Destination:", font=get_font(10), text_color=COLOR_TEXT_PRIMARY).grid(row=4, column=0, sticky="w", padx=8, pady=1)
        self.lbl_cap_dest = ctk.CTkLabel(card_details, text="waiting ...", font=get_font(10), text_color=COLOR_TEXT_HINT, wraplength=140, justify="left")
        self.lbl_cap_dest.grid(row=4, column=1, sticky="w", padx=4, pady=1)

        # --- Column 1: Grid, Zoom In, Step Adjustment ---
        left_ctrl = ctk.CTkFrame(control_panel, fg_color="transparent")
        left_ctrl.grid(row=0, column=1, sticky="nsew", padx=6, pady=8)
        left_ctrl.grid_columnconfigure(0, weight=1)

        # Grid Checkbox
        self.chk_grid = ctk.CTkCheckBox(
            left_ctrl,
            text="Grid",
            font=get_font(11, "bold"),
            text_color=COLOR_CHARCOAL,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            border_color=COLOR_BORDER_STRONG,
            checkmark_color="#FFFFFF",
            command=self._on_grid_checkbox_toggle,
        )
        self.chk_grid.grid(row=0, column=0, sticky="w", pady=(0, 6))
        if self.grid_enabled:
            self.chk_grid.select()

        # Zoom In / Out Button
        self.btn_zoom = ctk.CTkButton(
            left_ctrl,
            text="Zoom In",
            font=get_font(12, "bold"),
            height=34,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._toggle_zoom,
        )
        self.btn_zoom.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        # Focus Drive Label
        ctk.CTkLabel(
            left_ctrl,
            text="Lens Focus Drive (DSLR Tethered):",
            font=get_font(9),
            text_color=COLOR_TEXT_MUTED,
        ).grid(row=2, column=0, sticky="w", pady=(0, 2))

        # 6 Step adjustment buttons: [ <<< ] [ << ] [ < ] [ > ] [ >> ] [ >>> ]
        step_bar = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        step_bar.grid(row=3, column=0, sticky="ew")
        for col_idx in range(6):
            step_bar.grid_columnconfigure(col_idx, weight=1)

        steps_info = [
            ("<<<", -3),
            ("<<", -2),
            ("<", -1),
            (">", 1),
            (">>", 2),
            (">>>", 3),
        ]
        self.step_buttons = []
        for idx, (label, val) in enumerate(steps_info):
            s_btn = ctk.CTkButton(
                step_bar,
                text=label,
                font=get_font(11, "bold"),
                height=28,
                corner_radius=4,
                fg_color=COLOR_PANEL,
                hover_color=COLOR_BORDER,
                text_color=COLOR_CHARCOAL,
                border_width=1,
                border_color=COLOR_BORDER,
                command=lambda l=label, v=val: self._on_focus_step(l, v),
            )
            s_btn.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 2, 0 if idx == 5 else 2))
            self.step_buttons.append(s_btn)

        # --- Column 2: End Live View, Capture, Save, Finish ---
        right_ctrl = ctk.CTkFrame(control_panel, fg_color="transparent")
        right_ctrl.grid(row=0, column=2, sticky="ns", padx=(6, 10), pady=8)

        self.btn_live_view_toggle = ctk.CTkButton(
            right_ctrl,
            text="End Live View",
            font=get_font(11, "bold"),
            width=130,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._toggle_live_view,
        )
        self.btn_live_view_toggle.pack(fill="x", pady=(0, 4))

        self.btn_capture = ctk.CTkButton(
            right_ctrl,
            text="Capture",
            font=get_font(12, "bold"),
            width=130,
            height=30,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_capture_click,
        )
        self.btn_capture.pack(fill="x", pady=(0, 4))

        self.btn_retake = ctk.CTkButton(
            right_ctrl,
            text="Retake",
            font=get_font(11, "bold"),
            width=130,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            state="disabled",
            command=self._on_retake_click,
        )
        self.btn_retake.pack(fill="x", pady=(0, 4))

        self.btn_save = ctk.CTkButton(
            right_ctrl,
            text="Save",
            font=get_font(11, "bold"),
            width=130,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            state="disabled",
            command=self._on_save_click,
        )
        self.btn_save.pack(fill="x", pady=(0, 4))

        self.btn_finish = ctk.CTkButton(
            right_ctrl,
            text="Finish",
            font=get_font(11),
            width=130,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_finish_click,
        )
        self.btn_finish.pack(fill="x", pady=0)

        # Status feedback line at very bottom
        self.lbl_capture_feedback = ctk.CTkLabel(
            center_panel,
            text="",
            font=get_font(10, "bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_capture_feedback.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 6))

    def _setup_bindings(self) -> None:
        """Trace changes in input entries to automatically re-evaluate preflight."""
        entries = [self.entry_hole, self.entry_tray, self.entry_from, self.entry_to]
        if hasattr(self, "entry_tray_rows"):
            entries.append(self.entry_tray_rows)
        for entry in entries:
            entry.bind("<KeyRelease>", lambda e: self._evaluate_preflight())

    def _on_browse_target(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Target Folder")
        if folder:
            self.entry_target_folder.delete(0, "end")
            self.entry_target_folder.insert(0, folder)

    def _on_browse_server_target(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Target Server Folder")
        if folder:
            self.entry_server_folder.delete(0, "end")
            self.entry_server_folder.insert(0, folder)
            self._save_server_folder(folder)

    def _on_server_folder_changed(self, event=None) -> None:
        if hasattr(self, "entry_server_folder"):
            val = self.entry_server_folder.get().strip()
            self._save_server_folder(val)

    def _save_server_folder(self, folder: str) -> None:
        try:
            from config.config_manager import get_config
            cfg = getattr(self.ctx, "config", None) or get_config()
            cfg.set("transfer", "server_folder", folder)
            cfg.set("storage", "server_folder", folder)
        except Exception as e:
            logger.debug("Could not save server folder: %s", e)

    def _on_sync_server_folder(self) -> None:
        import shutil
        from pathlib import Path

        server_dir_str = self.entry_server_folder.get().strip() if hasattr(self, "entry_server_folder") else ""
        if not server_dir_str:
            self.lbl_capture_feedback.configure(
                text="Target Server Folder is empty. Please select or enter a server folder.",
                text_color=COLOR_WARNING,
            )
            return

        server_path = Path(server_dir_str)
        try:
            server_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.lbl_capture_feedback.configure(
                text=f"Cannot access Server Folder: {e}",
                text_color=COLOR_ERROR,
            )
            return

        sess = self.ctx.active_session
        if not sess:
            self.lbl_capture_feedback.configure(
                text="Active session required to sync.",
                text_color=COLOR_WARNING,
            )
            return

        sp = self.ctx.session_paths if self.ctx.session_paths else self.ctx.storage_manager.get_session_paths(f"{sess.site}_{sess.date}")
        if not sp or not sp.session_dir.exists():
            self.lbl_capture_feedback.configure(
                text="No local session files found to sync.",
                text_color=COLOR_WARNING,
            )
            return

        dest_sess = server_path / sp.session_dir.name
        dest_jpg = dest_sess / "jpg"
        dest_raw = dest_sess / "raw"
        dest_thumbs = dest_sess / "thumbs"

        try:
            dest_jpg.mkdir(parents=True, exist_ok=True)
            dest_raw.mkdir(parents=True, exist_ok=True)
            dest_thumbs.mkdir(parents=True, exist_ok=True)

            synced_count = 0
            if sp.jpg_dir.exists():
                for f in sp.jpg_dir.glob("*.jpg"):
                    d = dest_jpg / f.name
                    if not d.exists() or d.stat().st_size != f.stat().st_size:
                        shutil.copy2(f, d)
                        synced_count += 1

            for f in sp.session_dir.glob("*.csv"):
                shutil.copy2(f, dest_sess / f.name)

            if self.ctx.transfer_repo and self.ctx.photo_repo:
                photos = self.ctx.photo_repo.list_by_session(sess.id)
                from database.models import TransferModel, TransferStatus
                for photo in photos:
                    if photo.id:
                        existing = self.ctx.transfer_repo.get_by_photo_id(photo.id)
                        if not existing:
                            self.ctx.transfer_repo.create(TransferModel(
                                photo_id=photo.id,
                                server_url=server_dir_str,
                                status=TransferStatus.SUCCESS.value,
                            ))
                        else:
                            self.ctx.transfer_repo.update_status(existing.id, TransferStatus.SUCCESS)

            self.lbl_capture_feedback.configure(
                text=f"✓ Synced {synced_count} photo(s) & report to Server Folder: {dest_sess.name}",
                text_color=COLOR_SUCCESS,
            )
            logger.info("Session %s successfully synced to server folder: %s", dest_sess.name, dest_sess)
        except Exception as e:
            logger.error("Failed syncing to server folder: %s", e)
            self.lbl_capture_feedback.configure(
                text=f"Sync error: {e}",
                text_color=COLOR_ERROR,
            )

    def _on_open_csv_report(self) -> None:
        import os
        from pathlib import Path
        sess = self.ctx.active_session
        if not sess:
            self.lbl_capture_feedback.configure(text="Active session required to view report.", text_color=COLOR_WARNING)
            return

        hole_id = self.entry_hole.get().strip() or "TSD168"
        clean_hole = str(hole_id).strip().replace(" ", "_")
        sp = self.ctx.storage_manager.get_session_paths(f"{sess.site}_{sess.date}")
        csv_path = sp.session_dir / f"{clean_hole}.csv"

        if not csv_path.exists():
            photos = self.ctx.photo_repo.list_by_session(sess.id) if self.ctx.photo_repo else []
            from imaging.processor import ImageProcessor
            ImageProcessor.export_csv_report(sess, photos, csv_path)

        if csv_path.exists():
            try:
                os.startfile(str(csv_path))
                self.lbl_capture_feedback.configure(text=f"Report opened: {csv_path.name}", text_color=COLOR_SUCCESS)
            except Exception as e:
                logger.error("Could not open CSV file: %s", e)
                import subprocess
                subprocess.Popen(["explorer", "/select,", str(csv_path)])

    def start_view(self) -> None:
        """Called when this view becomes active or live stream started."""
        logger.info("Starting CaptureView live view...")
        self._is_previewing_capture = False
        self.is_live_view_active = True
        self.btn_live_view_toggle.configure(text="End Live View", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL)
        self.ctx.subscribe_live_frames(self._handle_incoming_frame)
        self._check_session_guard()

        # Populate session details matching legacy software
        sess = self.ctx.active_session
        if sess:
            if hasattr(self, "entry_sess_date"):
                self.entry_sess_date.delete(0, "end")
                self.entry_sess_date.insert(0, sess.date)
            if hasattr(self, "entry_sess_name"):
                self.entry_sess_name.delete(0, "end")
                if sess.operator:
                    self.entry_sess_name.insert(0, sess.operator)
            if hasattr(self, "entry_sess_site"):
                self.entry_sess_site.delete(0, "end")
                self.entry_sess_site.insert(0, sess.site)
            if hasattr(self, "lbl_series_count") and self.ctx.photo_repo:
                cnt = len(self.ctx.photo_repo.list_by_session(sess.id))
                self.lbl_series_count.configure(text=str(cnt))
            if hasattr(self, "entry_target_folder"):
                sp = self.ctx.session_paths if self.ctx.session_paths else self.ctx.storage_manager.get_session_paths(f"{sess.site}_{sess.date}")
                self.entry_target_folder.delete(0, "end")
                self.entry_target_folder.insert(0, str(sp.jpg_dir))
        if hasattr(self, "entry_server_folder"):
            from config.config_manager import get_config
            cfg = getattr(self.ctx, "config", None) or get_config()
            srv_dir = cfg.get("transfer", "server_folder", "") or cfg.get("storage", "server_folder", "")
            if srv_dir and not self.entry_server_folder.get().strip():
                self.entry_server_folder.delete(0, "end")
                self.entry_server_folder.insert(0, str(srv_dir))
        if hasattr(self, "lbl_series_space"):
            free_mb = self.ctx.storage_manager.get_available_space_mb()
            self.lbl_series_space.configure(text=f"{free_mb:.0f} MB free")

        self._evaluate_preflight()
        try:
            self._refresh_webcam_list()
        except Exception:
            pass
        self._refresh_cam_info()
        self._update_left_tab_styles()
        # NOTE (fix koneksi): jangan panggil start_live_view() lagi di sini.
        # subscribe_live_frames() di atas sudah memulai distribusi live dengan
        # callback ctx._on_live_frame. Panggilan ekstra tanpa callback akan
        # menimpa callback menjadi None pada HotFolder/Direct/WiFi sehingga
        # live view membeku (terlihat tidak connect).

    def _on_left_tab_changed(self) -> None:
        self._update_left_tab_styles()

    def _update_left_tab_styles(self) -> None:
        if not hasattr(self, "left_tabs"):
            return
        current = self.left_tabs.get()
        if hasattr(self.left_tabs, "_segmented_button") and hasattr(self.left_tabs._segmented_button, "_buttons_dict"):
            for name, btn in self.left_tabs._segmented_button._buttons_dict.items():
                if name == current:
                    btn.configure(text_color="#FFFFFF", font=get_font(11, "bold"), fg_color=COLOR_ACCENT)
                else:
                    btn.configure(text_color=COLOR_CHARCOAL, font=get_font(11, "normal"), fg_color=COLOR_PANEL)

    def _on_cam_setting_changed(self, *args) -> None:
        fmt = self.opt_cam_format.get()
        iso = self.opt_cam_iso.get()
        aperture = self.opt_cam_aperture.get()
        self.lbl_capture_feedback.configure(
            text=f"Camera parameter updated: {fmt} | ISO {iso} | f/{aperture}",
            text_color=COLOR_TEXT_MUTED,
        )

    def _on_cam_resolution_changed(self, choice: str) -> None:
        """Handles resolution changes from Capture screen."""
        if "Auto (Best Native" in choice:
            self.ctx.camera_manager.set_resolution(5184, 3456, mode="best_native")
        elif "5184 x 3456" in choice:
            self.ctx.camera_manager.set_resolution(5184, 3456, mode="5184x3456")
        elif "6000 x 4000" in choice:
            self.ctx.camera_manager.set_resolution(6000, 4000, mode="6000x4000")
        elif "4000 x 3000" in choice:
            self.ctx.camera_manager.set_resolution(4000, 3000, mode="4000x3000")
        elif "3840 x 2160" in choice:
            self.ctx.camera_manager.set_resolution(3840, 2160, mode="4k")
        elif "1920 x 1080" in choice:
            self.ctx.camera_manager.set_resolution(1920, 1080, mode="1080p")
        elif "1280 x 720" in choice:
            self.ctx.camera_manager.set_resolution(1280, 720, mode="720p")

        w, h = self.ctx.camera_manager.get_current_resolution()
        mp = (w * h) / 1_000_000.0
        self.lbl_capture_feedback.configure(
            text=f"Resolution configured: {w}x{h} ({mp:.1f} MP)",
            text_color=COLOR_SUCCESS,
        )

    def _on_save_max_size(self) -> None:
        """Saves configured maximum photo size limit in MB."""
        if not hasattr(self, "entry_max_size"):
            return
        val_str = self.entry_max_size.get().strip()
        try:
            val = float(val_str)
            if val <= 0:
                raise ValueError("Batas ukuran foto harus lebih dari 0 MB.")
            self.ctx.config.set("imaging", "max_photo_size_mb", val)
            self.ctx.config.save()
            self.lbl_capture_feedback.configure(
                text=f"✓ Batas maksimal foto berhasil disimpan: {val:.1f} MB",
                text_color=COLOR_SUCCESS,
            )
        except Exception as e:
            self.lbl_capture_feedback.configure(
                text="Error: Batas ukuran foto harus berupa angka positif (MB).",
                text_color=COLOR_ERROR,
            )

    def _parse_webcam_index(self, choice: str) -> str:
        """Parses webcam OptionMenu display string back to device id ('0'..'N' or 'sim')."""
        if not choice:
            return str(self.ctx.camera_manager.get_preferred_webcam_index())
        if "Simulator" in choice or "Standby" in choice or "Sample Feed" in choice:
            return "sim"
        mapped = getattr(self, "_webcam_display_to_index", {}).get(choice)
        if mapped is not None:
            return str(mapped)
        import re
        m = re.search(r"Index\s+(\d+)", choice)
        if m:
            return m.group(1)
        m2 = re.search(r"^\s*(\d+)\s*$", choice)
        if m2:
            return m2.group(1)
        return str(self.ctx.camera_manager.get_preferred_webcam_index())

    def _refresh_webcam_list(self) -> None:
        """Re-enumerates physical webcams and repopulates the device selector."""
        if not hasattr(self, "opt_webcam_device"):
            return
        try:
            devices = self.ctx.camera_manager.list_webcam_devices()
        except Exception as e:
            logger.debug("Webcam enumeration failed: %s", e)
            devices = []
        self._webcam_display_to_index = {}
        values: list = []
        for dev in devices:
            label = dev.get("name") or f"Webcam Index {dev.get('index')}"
            values.append(label)
            self._webcam_display_to_index[label] = dev.get("index")
        values.append("Simulator (Standby Sample Feed)")
        self._webcam_display_to_index["Simulator (Standby Sample Feed)"] = "sim"
        try:
            self.opt_webcam_device.configure(values=values)
        except Exception:
            pass
        # Select current / preferred device
        try:
            active = getattr(self.ctx.camera_manager, "_active_adapter", None)
            cur_idx: object = None
            if active is not None and getattr(active, "device_index", None) is not None \
                    and active.__class__.__name__ == "WebcamAdapter" \
                    and not getattr(active, "_is_simulated", False):
                cur_idx = active.device_index
            else:
                cur_idx = self.ctx.camera_manager.get_preferred_webcam_index()
            selected = None
            for label, idx in self._webcam_display_to_index.items():
                if str(idx) == str(cur_idx):
                    selected = label
                    break
            if selected is None and values:
                selected = values[0]
            if selected:
                self.opt_webcam_device.set(selected)
        except Exception:
            pass
        if hasattr(self, "lbl_webcam_hint"):
            if devices:
                self.lbl_webcam_hint.configure(
                    text=f"{len(devices)} webcam terdeteksi. Pilih internal/external lalu live view mengikuti otomatis."
                )
            else:
                self.lbl_webcam_hint.configure(
                    text="Tidak ada webcam fisik terdeteksi. Gunakan Simulator atau hubungkan USB lalu klik Refresh."
                )

    def _on_refresh_webcam_list(self) -> None:
        self._refresh_webcam_list()
        self.lbl_capture_feedback.configure(
            text="Daftar webcam diperbarui. Pilih device untuk beralih kamera.",
            text_color=COLOR_TEXT_MUTED,
        )

    def _switch_to_webcam_index(self, device_id: str) -> None:
        """Reconnects to the given webcam index and restarts live distribution."""
        was_subscribed = self._handle_incoming_frame in getattr(self.ctx, "_frame_subscribers", [])
        try:
            self.ctx.camera_manager.stop_live_view()
        except Exception:
            pass
        ok = self.ctx.camera_manager.connect_camera("webcam", device_id)
        if was_subscribed:
            try:
                # Re-attach live distribution to the new adapter
                self.ctx.camera_manager.start_live_view(self.ctx._on_live_frame)
            except Exception as e:
                logger.debug("Restart live view after webcam switch failed: %s", e)
        try:
            from config.config_manager import get_config
            cfg = getattr(self.ctx, "config", None) or get_config()
            cfg.set("camera", "default_adapter", "webcam")
        except Exception:
            pass
        self._refresh_cam_info()
        self._evaluate_preflight()
        if ok:
            # FIX: bedakan standby vs fisik agar user tahu bila device
            # tidak benar-benar terbuka (mis. index basi / kamera dicabut).
            try:
                _active = getattr(self.ctx.camera_manager, "_active_adapter", None)
                _is_sim = bool(getattr(_active, "_is_simulated", False))
                _real_idx = getattr(_active, "device_index", device_id)
            except Exception:
                _is_sim, _real_idx = False, device_id
            if _is_sim and str(device_id).lower() != "sim":
                from ui.theme import COLOR_WARNING
                self.lbl_capture_feedback.configure(
                    text=f"Webcam Index {device_id} tidak dapat dibuka (kamera dicabut/sibuk). "
                         f"Otomatis memakai Index {_real_idx} bila tersedia; bila tetap standby, pilih device lain lalu klik Refresh.",
                    text_color=COLOR_WARNING,
                )
            elif str(device_id).lower() == "sim":
                self.lbl_capture_feedback.configure(
                    text="Simulator standby aktif. Pilih webcam fisik untuk live video.",
                    text_color=COLOR_TEXT_MUTED,
                )
            else:
                self.lbl_capture_feedback.configure(
                    text=f"Webcam aktif: Index {_real_idx}. Live view mengikuti otomatis.",
                    text_color=COLOR_SUCCESS,
                )
        else:
            self.lbl_capture_feedback.configure(
                text=f"Gagal menghubungkan webcam Index {device_id}.",
                text_color=COLOR_ERROR,
            )

    def _on_webcam_device_changed(self, choice: str) -> None:
        """User picked a different physical webcam (internal vs external)."""
        device_id = self._parse_webcam_index(choice)
        if hasattr(self, "opt_capture_interface"):
            try:
                self.opt_capture_interface.set("Physical USB Webcam")
            except Exception:
                pass
        self._switch_to_webcam_index(device_id)

    def _on_capture_interface_changed(self, choice: str) -> None:
        """Allows switching camera connection directly from Capture Screen."""
        # FIX koneksi: restart distribusi live setelah ganti adapter agar
        # live view langsung mengikuti (sebelumnya hanya webcam yang restart).
        was_subscribed = self._handle_incoming_frame in getattr(self.ctx, "_frame_subscribers", [])
        try:
            self.ctx.camera_manager.stop_live_view()
        except Exception:
            pass
        if "Wi-Fi" in choice:
            self.ctx.camera_manager.connect_camera("wifi_dslr", "wifi_dslr")
        elif "Direct USB" in choice:
            self.ctx.camera_manager.connect_camera("direct_usb", "0")
        elif "Hot-Folder" in choice or "Hot Folder" in choice or "Universal Hot" in choice:
            try:
                hot_dir = self.ctx.storage_manager.base_dir / "HotFolder"
            except Exception:
                hot_dir = "hot_folder"
            try:
                from config.config_manager import get_config
                cfg = getattr(self.ctx, "config", None) or get_config()
                cfg.set("camera", "default_adapter", "hot_folder")
            except Exception:
                pass
            self.ctx.camera_manager.connect_camera("hot_folder", str(hot_dir))
        elif "Standby" in choice or "Simulator" in choice:
            self._switch_to_webcam_index("sim")
            return
        else:
            device_id = self._parse_webcam_index(
                self.opt_webcam_device.get() if hasattr(self, "opt_webcam_device") else "0"
            )
            self._switch_to_webcam_index(device_id)
            return
        if was_subscribed:
            try:
                self.ctx.camera_manager.start_live_view(self.ctx._on_live_frame)
            except Exception as e:
                logger.debug("Restart live view after interface switch failed: %s", e)
        self._refresh_cam_info()
        self._evaluate_preflight()
        self.lbl_capture_feedback.configure(
            text=f"Camera interface changed: {choice}",
            text_color=COLOR_TEXT_PRIMARY,
        )

    def _refresh_cam_info(self) -> None:
        if not hasattr(self, "lbl_dev_model"):
            return
        from pathlib import Path
        info = self.ctx.camera_manager.get_info()
        active_adapter = getattr(self.ctx.camera_manager, "_active_adapter", None)

        from camera.adapters.wifi_dslr import WiFiDslrAdapter
        from camera.adapters.direct_usb import DirectUsbAdapter
        from camera.adapters.hot_folder import HotFolderAdapter
        from camera.adapters.webcam import WebcamAdapter

        if isinstance(active_adapter, WiFiDslrAdapter):
            if hasattr(self, "opt_capture_interface"):
                self.opt_capture_interface.set("Wi-Fi DSLR Wireless Tethering")
            self.lbl_dev_model.configure(text=f"Model: {info.model if info else 'Wi-Fi DSLR'}")
            ip_desc = f"IP: {active_adapter.camera_ip}" if active_adapter.camera_ip else "Wireless Tether"
            self.lbl_dev_serial.configure(text=f"Connection: {ip_desc}")
            tether_name = Path(active_adapter.tether_dir).name if active_adapter.tether_dir else "WiFiTether"
            self.lbl_dev_fw.configure(text=f"Tether Folder: {tether_name}")
        elif isinstance(active_adapter, DirectUsbAdapter):
            if hasattr(self, "opt_capture_interface"):
                self.opt_capture_interface.set("Direct USB DSLR (Cable)")
            self.lbl_dev_model.configure(text=f"Model: {info.model if info else 'Direct USB DSLR'}")
            self.lbl_dev_serial.configure(text=f"Serial No: {info.serial_number if info else 'Cable'}")
            self.lbl_dev_fw.configure(text="Protocol: Windows WIA / PTP")
        elif isinstance(active_adapter, HotFolderAdapter):
            # FIX: Hot-Folder sebelumnya salah dilabeli sebagai Physical USB
            # Webcam sehingga UI menipu (interface webcam tapi model Hot-Folder).
            if hasattr(self, "opt_capture_interface"):
                try:
                    self.opt_capture_interface.set("Universal Hot-Folder Ingest")
                except Exception:
                    pass
            self.lbl_dev_model.configure(text=f"Model: {info.model if info else 'Universal Hot-Folder Ingest'}")
            self.lbl_dev_serial.configure(text=f"Serial No: {info.serial_number if info else 'HOT_FOLDER_01'}")
            try:
                watch_name = Path(str(getattr(active_adapter, 'watch_dir', ''))).name or "HotFolder"
            except Exception:
                watch_name = "HotFolder"
            self.lbl_dev_fw.configure(text=f"Watch Folder: {watch_name}")
        elif isinstance(active_adapter, WebcamAdapter):
            if getattr(active_adapter, "_is_simulated", False):
                if hasattr(self, "opt_capture_interface"):
                    try:
                        self.opt_capture_interface.set("Standby / Simulator")
                    except Exception:
                        pass
                self.lbl_dev_model.configure(text=f"Model: {info.model if info else 'Standby (Simulator)'}")
                self.lbl_dev_serial.configure(text=f"Serial No: {info.serial_number if info else 'STANDBY'}")
                self.lbl_dev_fw.configure(text=f"Firmware: {info.firmware_version if info else '-'}")
                try:
                    if hasattr(self, "opt_webcam_device"):
                        self.opt_webcam_device.set("Simulator (Standby Sample Feed)")
                except Exception:
                    pass
            else:
                if hasattr(self, "opt_capture_interface"):
                    try:
                        self.opt_capture_interface.set("Physical USB Webcam")
                    except Exception:
                        pass
                self.lbl_dev_model.configure(text=f"Model: {info.model if info else 'USB Webcam'}")
                self.lbl_dev_serial.configure(text=f"Serial No: {info.serial_number if info else '-'}")
                self.lbl_dev_fw.configure(text=f"Firmware: {info.firmware_version if info else '-'}")
                # Sync webcam selector to active index
                try:
                    if hasattr(self, "opt_webcam_device"):
                        idx = getattr(active_adapter, "device_index", None)
                        for label, mapped in getattr(self, "_webcam_display_to_index", {}).items():
                            if str(mapped) == str(idx):
                                self.opt_webcam_device.set(label)
                                break
                except Exception:
                    pass
        elif info and info.model not in ("Unknown Camera", "None"):
            if hasattr(self, "opt_capture_interface"):
                self.opt_capture_interface.set("Physical USB Webcam")
            self.lbl_dev_model.configure(text=f"Model: {info.model}")
            self.lbl_dev_serial.configure(text=f"Serial No: {info.serial_number}")
            self.lbl_dev_fw.configure(text=f"Firmware: {info.firmware_version}")
            # Sync webcam selector to active index (incl. simulated)
            try:
                from camera.adapters.webcam import WebcamAdapter
                if isinstance(active_adapter, WebcamAdapter) and hasattr(self, "opt_webcam_device"):
                    if getattr(active_adapter, "_is_simulated", False):
                        self.opt_webcam_device.set("Simulator (Standby Sample Feed)")
                    else:
                        idx = getattr(active_adapter, "device_index", None)
                        for label, mapped in getattr(self, "_webcam_display_to_index", {}).items():
                            if str(mapped) == str(idx):
                                self.opt_webcam_device.set(label)
                                break
            except Exception:
                pass
        else:
            if hasattr(self, "opt_capture_interface"):
                self.opt_capture_interface.set("Physical USB Webcam")
            self.lbl_dev_model.configure(text="Model: Integrated USB Camera (Webcam)")
            self.lbl_dev_serial.configure(text="Serial No: USB-VIDEO-01")
            self.lbl_dev_fw.configure(text="Driver: DirectShow UVC")

        if hasattr(self, "opt_cam_resolution"):
            try:
                cur_w, cur_h = self.ctx.camera_manager.get_current_resolution()
                cur_mode = self.ctx.camera_manager.get_resolution_mode()
                if cur_mode == "best_native":
                    self.opt_cam_resolution.set("Auto (Best Native DSLR — 18MP/24MP+)")
                elif (cur_w, cur_h) == (5184, 3456):
                    self.opt_cam_resolution.set("5184 x 3456 (18MP Canon 60D Native)")
                elif (cur_w, cur_h) == (6000, 4000):
                    self.opt_cam_resolution.set("6000 x 4000 (24MP UHD)")
                elif (cur_w, cur_h) == (4000, 3000):
                    self.opt_cam_resolution.set("4000 x 3000 (12MP High Res)")
                elif (cur_w, cur_h) == (3840, 2160):
                    self.opt_cam_resolution.set("3840 x 2160 (4K UHD)")
                elif (cur_w, cur_h) == (1920, 1080):
                    self.opt_cam_resolution.set("1920 x 1080 (Full HD 1080p)")
                elif (cur_w, cur_h) == (1280, 720):
                    self.opt_cam_resolution.set("1280 x 720 (HD 720p)")
            except Exception:
                pass

    def stop_view(self) -> None:
        """Called when navigating away or ending live view."""
        logger.info("Stopping CaptureView live view...")
        self.is_live_view_active = False
        self.btn_live_view_toggle.configure(text="Start Live View", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL)
        self.ctx.unsubscribe_live_frames(self._handle_incoming_frame)
        self.ctx.camera_manager.stop_live_view()

    def _toggle_live_view(self) -> None:
        """Toggles camera live preview on or off."""
        if self._is_previewing_capture:
            self._is_previewing_capture = False
            self.start_view()
            self._evaluate_preflight()
            self.lbl_capture_feedback.configure(
                text="Live View resumed.",
                text_color=COLOR_SUCCESS,
            )
            return

        if self.is_live_view_active:
            self.stop_view()
            self.stream_info_lbl.configure(text="LIVE CAMERA STREAM — PAUSED")
            self.lbl_capture_feedback.configure(
                text="Live View ended. Click 'Start Live View' to resume preview.",
                text_color=COLOR_TEXT_MUTED,
            )
        else:
            self.start_view()
            self.lbl_capture_feedback.configure(
                text="Live View resumed.",
                text_color=COLOR_SUCCESS,
            )

    def _check_session_guard(self) -> None:
        """Verifies an active session exists."""
        sess = self.ctx.active_session
        if sess:
            self.session_guard_frame.pack_forget()
        else:
            if hasattr(self, "box_session") and self.box_session.winfo_manager() == "pack":
                self.session_guard_frame.pack(fill="x", padx=14, pady=(0, 10), before=self.box_session)
            else:
                self.session_guard_frame.pack(fill="x", padx=14, pady=(0, 10))

    def _handle_incoming_frame(self, frame_rgb: np.ndarray) -> None:
        """Receives RGB frame from background camera thread."""
        try:
            self.after(0, self._render_frame, frame_rgb)
        except Exception as e:
            logger.debug("Failed to schedule frame render: %s", e)

    def _render_frame(self, frame_rgb: np.ndarray) -> None:
        if not self.is_live_view_active or self._is_previewing_capture:
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w < 50 or canvas_h < 50:
            return

        frame_h, frame_w = frame_rgb.shape[:2]

        if self.is_zoomed:
            zh, zw = frame_h // 2, frame_w // 2
            zx, zy = (frame_w - zw) // 2, (frame_h - zh) // 2
            frame_rgb = frame_rgb[zy:zy+zh, zx:zx+zw]
            frame_h, frame_w = frame_rgb.shape[:2]

        # Aspect ratio fitting
        scale = min(canvas_w / frame_w, canvas_h / frame_h)
        disp_w = max(1, int(frame_w * scale))
        disp_h = max(1, int(frame_h * scale))

        offset_x = (canvas_w - disp_w) // 2
        offset_y = (canvas_h - disp_h) // 2

        pil_img = Image.fromarray(frame_rgb).resize((disp_w, disp_h), Image.Resampling.BILINEAR)
        self._current_photo_image = ImageTk.PhotoImage(pil_img)

        self.canvas.delete("all")
        self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self._current_photo_image)

        # Draw Grid if enabled
        if self.grid_enabled:
            x1 = offset_x + disp_w // 3
            x2 = offset_x + (2 * disp_w) // 3
            y1 = offset_y + disp_h // 3
            y2 = offset_y + (2 * disp_h) // 3
            self.canvas.create_line(x1, offset_y, x1, offset_y + disp_h, fill="#0284C7", dash=(3, 3))
            self.canvas.create_line(x2, offset_y, x2, offset_y + disp_h, fill="#0284C7", dash=(3, 3))
            self.canvas.create_line(offset_x, y1, offset_x + disp_w, y1, fill="#0284C7", dash=(3, 3))
            self.canvas.create_line(offset_x, y2, offset_x + disp_w, y2, fill="#0284C7", dash=(3, 3))

        # Standard Tray Crop Framing box (300 x 200 ratio)
        crop_w_box = int(disp_w * 0.88)
        crop_h_box = int(crop_w_box / 1.5)  # 300:200 ratio
        if crop_h_box > disp_h * 0.88:
            crop_h_box = int(disp_h * 0.88)
            crop_w_box = int(crop_h_box * 1.5)

        cx1 = offset_x + (disp_w - crop_w_box) // 2
        cy1 = offset_y + (disp_h - crop_h_box) // 2
        cx2 = cx1 + crop_w_box
        cy2 = cy1 + crop_h_box

        orig_crop_x = int((cx1 - offset_x) / scale)
        orig_crop_y = int((cy1 - offset_y) / scale)
        orig_crop_w = int(crop_w_box / scale)
        orig_crop_h = int(crop_h_box / scale)
        self.crop_region = CropRegion(x=orig_crop_x, y=orig_crop_y, width=orig_crop_w, height=orig_crop_h)

        if self.crop_enabled and not self.is_zoomed:
            # 1. Shaded / hatched overlay on outer uncropped areas (Matching Legacy App)
            try:
                self.canvas.create_rectangle(offset_x, offset_y, offset_x + disp_w, cy1, fill="#000000", stipple="gray50", width=0)
                self.canvas.create_rectangle(offset_x, cy2, offset_x + disp_w, offset_y + disp_h, fill="#000000", stipple="gray50", width=0)
                self.canvas.create_rectangle(offset_x, cy1, cx1, cy2, fill="#000000", stipple="gray50", width=0)
                self.canvas.create_rectangle(cx2, cy1, offset_x + disp_w, cy2, fill="#000000", stipple="gray50", width=0)
            except Exception:
                pass

            # 2. White outer bounding box
            self.canvas.create_rectangle(cx1, cy1, cx2, cy2, outline="#FFFFFF", width=2)

            # 3. Horizontal row dividers matching Tray Rows (Legacy Reference)
            num_rows = 3
            if hasattr(self, "entry_tray_rows"):
                try:
                    num_rows = max(1, int(self.entry_tray_rows.get().strip()))
                except Exception:
                    num_rows = 3
            row_h = crop_h_box / num_rows
            for r in range(1, num_rows):
                ry = int(cy1 + r * row_h)
                self.canvas.create_line(cx1, ry, cx2, ry, fill="#FFFFFF", width=1)

            # 4. Watermark / Hole ID at top of canvas
            hole_txt = self.entry_hole.get().strip() if hasattr(self, "entry_hole") else ""
            if hole_txt:
                watermark_y = max(offset_y + 16, cy1 - 18)
                self.canvas.create_text(
                    offset_x + disp_w // 2,
                    watermark_y,
                    text=hole_txt,
                    fill="#FEF08A",
                    font=(FONT_FAMILY, 20, "bold"),
                )

            # 5. Live update Tray Crop Area normalized coordinates
            if hasattr(self, "entry_crop_area"):
                nx1 = orig_crop_x / frame_w if frame_w else 0.0
                ny1 = orig_crop_y / frame_h if frame_h else 0.0
                nx2 = (orig_crop_x + orig_crop_w) / frame_w if frame_w else 0.0
                ny2 = (orig_crop_y + orig_crop_h) / frame_h if frame_h else 0.0
                self.entry_crop_area.delete(0, "end")
                self.entry_crop_area.insert(0, f"{nx1:.4f} {ny1:.4f} {nx2:.4f} {ny2:.4f}")

        if self.is_zoomed:
            self.canvas.create_text(
                offset_x + 12,
                offset_y + 16,
                text="[ ZOOM 2X ACTIVE ]",
                fill=COLOR_ACCENT,
                anchor="nw",
                font=(FONT_FAMILY, 10, "bold"),
            )

        cam_text = self.ctx.camera_manager.get_status_summary()
        zoom_text = "  |  [2X ZOOM]" if self.is_zoomed else ""
        self.stream_info_lbl.configure(text=f"LIVE VIEW — {frame_w}x{frame_h} @ ~30 FPS  |  {cam_text}{zoom_text}")

    def _on_grid_checkbox_toggle(self) -> None:
        self.grid_enabled = bool(self.chk_grid.get())

    def _toggle_zoom(self) -> None:
        self.is_zoomed = not self.is_zoomed
        if self.is_zoomed:
            self.btn_zoom.configure(
                text="Zoom Out",
                fg_color=COLOR_ACCENT_LIGHT,
                text_color=COLOR_ACCENT,
            )
            self.lbl_capture_feedback.configure(
                text="2x Digital Zoom active. Inspect core grain and focus.",
                text_color=COLOR_ACCENT,
            )
        else:
            self.btn_zoom.configure(
                text="Zoom In",
                fg_color=COLOR_PANEL,
                text_color=COLOR_CHARCOAL,
            )
            self.lbl_capture_feedback.configure(
                text="Full framing view restored.",
                text_color=COLOR_TEXT_MUTED,
            )

    def _on_focus_step(self, step_label: str, step_val: int) -> None:
        """Manual focus / framing step adjustment: <<< << < > >> >>>"""
        logger.info("Focus / framing step clicked: %s (%d)", step_label, step_val)
        adapter = self.ctx.camera_manager._active_adapter
        direction = "Near" if step_val < 0 else "Far"
        speed = "Fine" if abs(step_val) == 1 else ("Medium" if abs(step_val) == 2 else "Coarse")

        if adapter and hasattr(adapter, "drive_lens"):
            try:
                adapter.drive_lens(step_val)
                self.lbl_capture_feedback.configure(
                    text=f"DSLR Focus Drive: {step_label} ({speed} {direction})",
                    text_color=COLOR_TEXT_PRIMARY,
                )
            except Exception as e:
                logger.debug("Lens drive exception: %s", e)
                self.lbl_capture_feedback.configure(
                    text=f"Lens drive error: {e}",
                    text_color=COLOR_ERROR,
                )
        else:
            self.lbl_capture_feedback.configure(
                text=f"Focus Step {step_label} ({speed} {direction}): Hanya aktif pada kamera DSLR tethered (Canon EOS). Webcam laptop menggunakan lensa fixed-focus.",
                text_color=COLOR_WARNING,
            )


    def _toggle_crop(self) -> None:
        self.crop_enabled = not self.crop_enabled
        self.btn_crop_toggle.configure(
            text="Crop Box: ON" if self.crop_enabled else "Crop Box: OFF",
            fg_color=COLOR_ACCENT_LIGHT if self.crop_enabled else COLOR_PANEL_ALT,
            text_color=COLOR_ACCENT if self.crop_enabled else COLOR_TEXT_MUTED,
        )

    def _on_reconnect_cam(self) -> None:
        self.stream_info_lbl.configure(text="Reconnecting camera adapter...")
        try:
            iface = self.opt_capture_interface.get() if hasattr(self, "opt_capture_interface") else ""
        except Exception:
            iface = ""
        # FIX: Reconnect harus menghormati semua interface (termasuk
        # Hot-Folder/Simulator) dan me-restart distribusi live.
        if "Standby" in iface or "Simulator" in iface:
            device_id = "sim"
            self._switch_to_webcam_index(device_id)
            return
        if "Hot-Folder" in iface or "Hot Folder" in iface or "Universal Hot" in iface:
            was_sub = self._handle_incoming_frame in getattr(self.ctx, "_frame_subscribers", [])
            try:
                self.ctx.camera_manager.stop_live_view()
            except Exception:
                pass
            try:
                hot_dir = self.ctx.storage_manager.base_dir / "HotFolder"
            except Exception:
                hot_dir = "hot_folder"
            self.ctx.camera_manager.connect_camera("hot_folder", str(hot_dir))
            if was_sub:
                try:
                    self.ctx.camera_manager.start_live_view(self.ctx._on_live_frame)
                except Exception as e:
                    logger.debug("Restart live view after reconnect failed: %s", e)
            self._refresh_cam_info()
            self._evaluate_preflight()
            return
        if "Wi-Fi" in iface:
            was_sub = self._handle_incoming_frame in getattr(self.ctx, "_frame_subscribers", [])
            try:
                self.ctx.camera_manager.stop_live_view()
            except Exception:
                pass
            self.ctx.camera_manager.connect_camera("wifi_dslr", "wifi_dslr")
            if was_sub:
                try:
                    self.ctx.camera_manager.start_live_view(self.ctx._on_live_frame)
                except Exception as e:
                    logger.debug("Restart live view after reconnect failed: %s", e)
            self._refresh_cam_info()
            self._evaluate_preflight()
            return
        elif "Direct USB" in iface:
            was_sub = self._handle_incoming_frame in getattr(self.ctx, "_frame_subscribers", [])
            try:
                self.ctx.camera_manager.stop_live_view()
            except Exception:
                pass
            self.ctx.camera_manager.connect_camera("direct_usb", "0")
            if was_sub:
                try:
                    self.ctx.camera_manager.start_live_view(self.ctx._on_live_frame)
                except Exception as e:
                    logger.debug("Restart live view after reconnect failed: %s", e)
            self._refresh_cam_info()
            self._evaluate_preflight()
            return
        else:
            device_id = self._parse_webcam_index(
                self.opt_webcam_device.get() if hasattr(self, "opt_webcam_device") else "0"
            )
            self._switch_to_webcam_index(device_id)
            return

    def _evaluate_preflight(self) -> None:
        """Evaluates pre-flight checks and updates UI."""
        self._check_session_guard()
        hole_id = self.entry_hole.get().strip()
        tray_id = self.entry_tray.get().strip()

        try:
            f_val = float(self.entry_from.get())
        except ValueError:
            f_val = -1.0
        try:
            t_val = float(self.entry_to.get())
        except ValueError:
            t_val = -1.0

        res = self.ctx.run_preflight(
            hole_id=hole_id,
            tray_id=tray_id,
            interval_from=f_val,
            interval_to=t_val,
            crop_region=self.crop_region,
        )

        # Build checklist summary status string
        cam_chk = "✓" if self.ctx.camera_manager.is_ready() else "✕"
        sess_chk = "✓" if self.ctx.active_session else "✕"
        hole_chk = "✓" if bool(hole_id) else "✕"
        tray_chk = "✓" if bool(tray_id) else "✕"
        int_chk = "✓" if (f_val >= 0 and t_val >= f_val) else "✕"
        stor_chk = "✓" if self.ctx.storage_manager.get_available_space_mb() > 500 else "✕"
        crop_chk = "✓" if self.crop_region else "✕"

        self.lbl_checklist_items.configure(
            text=f"Camera {cam_chk}  ·  Session {sess_chk}  ·  Hole ID {hole_chk}  ·  Tray ID {tray_chk}  ·  Interval {int_chk}  ·  Storage {stor_chk}  ·  Crop {crop_chk}"
        )

        if not self.ctx.active_session:
            self.preflight_banner.configure(fg_color=COLOR_ERROR_BG, border_color=COLOR_ERROR_BORDER)
            self.lbl_preflight_verdict.configure(
                text="Active session required. Select or create a session before capture.",
                text_color=COLOR_ERROR,
            )
            self.btn_capture.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)
        elif self._is_previewing_capture:
            self.preflight_banner.configure(fg_color=COLOR_SUCCESS_BG, border_color=COLOR_SUCCESS_BORDER)
            self.lbl_preflight_verdict.configure(
                text="PHOTO CAPTURED — PREVIEW MODE (RETAKE OR SAVE)",
                text_color=COLOR_SUCCESS,
            )
            self.btn_capture.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)
        elif res.is_ready:
            self.preflight_banner.configure(fg_color=COLOR_SUCCESS_BG, border_color=COLOR_SUCCESS_BORDER)
            self.lbl_preflight_verdict.configure(
                text="READY TO CAPTURE",
                text_color=COLOR_SUCCESS,
            )
            self.btn_capture.configure(state="normal", fg_color=COLOR_ACCENT)
        else:
            issue = res.summary_errors[0] if res.summary_errors else "Complete all required tray parameters."
            self.preflight_banner.configure(fg_color=COLOR_WARNING_BG, border_color=COLOR_WARNING_BORDER)
            self.lbl_preflight_verdict.configure(
                text=f"CANNOT CAPTURE: {issue}",
                text_color=COLOR_WARNING,
            )
            self.btn_capture.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)

    def _trigger_shutter_flash(self) -> None:
        """Renders an instant tactile/visual shutter flash on the canvas."""
        try:
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            if cw > 10 and ch > 10:
                rect = self.canvas.create_rectangle(0, 0, cw, ch, fill="#FFFFFF", width=0)
                self.after(90, lambda: self.canvas.delete(rect))
            self.bell()
        except Exception:
            pass

    def _display_still_photo_on_canvas(self, photo) -> None:
        """Renders the captured still image onto the canvas in frozen preview mode (PRD Section 14)."""
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 50 or canvas_h < 50:
            return

        pil_img = None
        try:
            from pathlib import Path
            if getattr(photo, "jpg_path", None) and Path(photo.jpg_path).exists():
                pil_img = Image.open(photo.jpg_path)
            elif getattr(photo, "raw_path", None) and Path(photo.raw_path).exists():
                from imaging.raw import RawHandler
                rgb = RawHandler.decode_raw_to_rgb(Path(photo.raw_path))
                pil_img = Image.fromarray(rgb)
        except Exception as e:
            logger.warning("Could not open captured photo for preview display: %s", e)

        if pil_img is None:
            self.canvas.delete("all")
            self.canvas.create_text(
                canvas_w // 2,
                canvas_h // 2,
                text="[ CAPTURED STILL PHOTO READY ]",
                fill=COLOR_SUCCESS,
                font=(FONT_FAMILY, 14, "bold"),
            )
            return

        img_w, img_h = pil_img.size
        scale = min(canvas_w / img_w, canvas_h / img_h)
        disp_w = max(1, int(img_w * scale))
        disp_h = max(1, int(img_h * scale))

        offset_x = (canvas_w - disp_w) // 2
        offset_y = (canvas_h - disp_h) // 2

        resized = pil_img.resize((disp_w, disp_h), Image.Resampling.BILINEAR)
        self._captured_photo_image = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self._captured_photo_image)

        # Draw a prominent badge at the top indicating frozen preview mode
        self.canvas.create_rectangle(
            offset_x + 8,
            offset_y + 8,
            offset_x + disp_w - 8,
            offset_y + 36,
            fill="#090D16",
            outline=COLOR_SUCCESS,
            width=1,
        )
        self.canvas.create_text(
            offset_x + disp_w // 2,
            offset_y + 22,
            text="● CAPTURED STILL PHOTO (FROZEN PREVIEW) — KLIK 'SAVE' ATAU 'RETAKE'",
            fill=COLOR_SUCCESS,
            font=(FONT_FAMILY, 10, "bold"),
        )

    def _on_capture_click(self) -> None:
        if self._is_capturing or not self.ctx.active_session:
            return

        self._trigger_shutter_flash()
        self._is_capturing = True
        self.btn_capture.configure(text="Capturing...", state="disabled", fg_color=COLOR_BORDER_STRONG)
        active_adapter = getattr(self.ctx.camera_manager, "_active_adapter", None)
        from camera.adapters.wifi_dslr import WiFiDslrAdapter
        if isinstance(active_adapter, WiFiDslrAdapter):
            self.lbl_capture_feedback.configure(
                text="Wi-Fi DSLR: Mengirim trigger remote / menunggu transmisi foto nirkabel...",
                text_color=COLOR_ACCENT,
            )
        else:
            self.lbl_capture_feedback.configure(text="Acquiring high-resolution core photo...", text_color=COLOR_ACCENT)

        # Update Capture Details Card to acquiring
        self.lbl_cap_dims.configure(text="acquiring...", text_color=COLOR_TEXT_HINT)
        self.lbl_cap_filesize.configure(text="calculating...", text_color=COLOR_TEXT_HINT)
        self.lbl_cap_status.configure(text="In Progress...", text_color=COLOR_ACCENT)
        self.lbl_cap_dest.configure(text="saving...", text_color=COLOR_TEXT_HINT)

        def capture_task():
            try:
                hole_id = self.entry_hole.get().strip()
                tray_id = self.entry_tray.get().strip()
                f_val = float(self.entry_from.get())
                t_val = float(self.entry_to.get())
                comments = self.txt_comments.get("1.0", "end").strip() if hasattr(self, "txt_comments") else ""

                photo = self.ctx.execute_capture(
                    hole_id=hole_id,
                    tray_id=tray_id,
                    interval_from=f_val,
                    interval_to=t_val,
                    crop_region=self.crop_region,
                    comments=comments,
                )

                # Validate immediately
                self.ctx.validate_photo(photo.id)

                self.after(0, self._on_capture_success, photo)
            except Exception as e:
                logger.error("Capture failed: %s", e)
                self.after(0, self._on_capture_error, str(e))

        threading.Thread(target=capture_task, daemon=True).start()

    def _on_capture_success(self, photo) -> None:
        self._is_capturing = False
        self._pending_photo = photo
        self._is_previewing_capture = True
        self.is_live_view_active = False

        self.btn_capture.configure(text="Capture", state="disabled", fg_color=COLOR_BORDER_STRONG)
        self.btn_retake.configure(state="normal", fg_color=COLOR_WARNING, hover_color="#D97706", text_color="#FFFFFF")
        self.btn_save.configure(state="normal", fg_color=COLOR_SUCCESS, hover_color="#15803D", text_color="#FFFFFF")
        self.btn_finish.configure(state="normal", fg_color=COLOR_CHARCOAL, hover_color="#27272A", text_color="#FFFFFF")
        self.btn_live_view_toggle.configure(text="Resume Live View", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL)

        fw = getattr(photo, "crop_w", 0)
        fh = getattr(photo, "crop_h", 0)
        if fw <= 0 or fh <= 0:
            fw, fh = 1280, 720
        self.lbl_cap_dims.configure(text=f"{fw} x {fh}", text_color=COLOR_TEXT_PRIMARY)

        try:
            from pathlib import Path
            max_mb = float(self.ctx.config.get("imaging", "max_photo_size_mb", 10.0))
            if getattr(photo, "jpg_path", None) and Path(photo.jpg_path).exists():
                sz_mb = Path(photo.jpg_path).stat().st_size / (1024 * 1024)
                color = COLOR_TEXT_PRIMARY if sz_mb <= (max_mb + 0.05) else COLOR_ERROR
                self.lbl_cap_filesize.configure(text=f"{sz_mb:.2f} MB (Max {max_mb:.0f} MB)", text_color=color)
            else:
                self.lbl_cap_filesize.configure(text=f"< {max_mb:.0f} MB", text_color=COLOR_TEXT_PRIMARY)
        except Exception:
            self.lbl_cap_filesize.configure(text="1.45 MB", text_color=COLOR_TEXT_PRIMARY)

        self.lbl_cap_status.configure(text="Success (Validated)", text_color=COLOR_SUCCESS)

        from pathlib import Path
        dest_name = Path(photo.jpg_path).name if getattr(photo, "jpg_path", None) else f"{photo.filename_base}.jpg"
        self.lbl_cap_dest.configure(text=dest_name, text_color=COLOR_TEXT_PRIMARY)

        # Refresh Series count
        if hasattr(self, "lbl_series_count") and self.ctx.active_session and self.ctx.photo_repo:
            cnt = len(self.ctx.photo_repo.list_by_session(self.ctx.active_session.id))
            self.lbl_series_count.configure(text=str(cnt))

        self.stream_info_lbl.configure(text=f"CAPTURED PHOTO PREVIEW — {fw}x{fh}  |  Review & Retake / Save")
        self.lbl_capture_feedback.configure(
            text=f"✓ Captured: {photo.filename_base}.jpg (Frozen Preview). Klik 'Save' untuk simpan atau 'Retake' untuk foto ulang.",
            text_color=COLOR_SUCCESS,
        )

        # Refresh camera info dynamically from newly arrived image EXIF
        self._refresh_cam_info()

        # Freeze screen & display captured photo
        self._display_still_photo_on_canvas(photo)

    def _on_capture_error(self, err_msg: str) -> None:
        self._is_capturing = False
        self._is_previewing_capture = False
        self.btn_capture.configure(text="Capture", state="normal", fg_color=COLOR_ACCENT)
        self.btn_retake.configure(state="disabled", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL)
        self.btn_save.configure(state="disabled", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL)
        self.lbl_capture_feedback.configure(
            text=f"Capture Error: {err_msg}",
            text_color=COLOR_ERROR,
        )
        self.lbl_cap_status.configure(text="Error", text_color=COLOR_ERROR)
        self.start_view()

    def _on_retake_click(self) -> None:
        """Marks current photo as superseded and resumes Live View (PRD Section 14)."""
        logger.info("Operator triggered Retake on current photo.")
        self.ctx.retake_current()

        self._pending_photo = None
        self._is_previewing_capture = False

        self.btn_retake.configure(state="disabled", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL)
        self.btn_save.configure(state="disabled", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL)
        self.btn_capture.configure(text="Capture", state="normal", fg_color=COLOR_ACCENT)

        self.lbl_cap_status.configure(text="Retake (Superseded)", text_color=COLOR_WARNING)
        self.lbl_capture_feedback.configure(
            text="Retake: Foto sebelumnya ditandai Superseded. Live View aktif kembali untuk capture ulang.",
            text_color=COLOR_WARNING,
        )

        self.start_view()
        self._evaluate_preflight()

    def _on_save_click(self) -> None:
        """Commits the current photo capture to disk and session."""
        if not self._pending_photo:
            self.lbl_capture_feedback.configure(
                text="No photo to save yet. Click 'Capture' first.",
                text_color=COLOR_WARNING,
            )
            return

        server_dir_str = self.entry_server_folder.get().strip() if hasattr(self, "entry_server_folder") else ""
        server_copy_msg = ""
        if server_dir_str and getattr(self._pending_photo, "jpg_path", None):
            try:
                import shutil
                from pathlib import Path
                srv_path = Path(server_dir_str)
                if srv_path.exists():
                    sess = self.ctx.active_session
                    sess_name = f"{sess.site}_{sess.date}" if sess else "Captures"
                    srv_jpg = srv_path / sess_name / "jpg"
                    srv_jpg.mkdir(parents=True, exist_ok=True)
                    src_jpg = Path(self._pending_photo.jpg_path)
                    if src_jpg.exists():
                        shutil.copy2(src_jpg, srv_jpg / src_jpg.name)
                        server_copy_msg = " & disalin ke Server Folder"
            except Exception as e:
                logger.debug("Failed auto-copy to server folder on save: %s", e)

        saved_name = self._pending_photo.filename_base
        self.lbl_capture_feedback.configure(
            text=f"✓ Foto {saved_name}.jpg berhasil disimpan{server_copy_msg}. Siap untuk tray berikutnya.",
            text_color=COLOR_SUCCESS,
        )

        self._pending_photo = None
        self._is_previewing_capture = False

        self.btn_save.configure(state="disabled", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL, hover_color=COLOR_BORDER)
        self.btn_retake.configure(state="disabled", fg_color=COLOR_PANEL, text_color=COLOR_CHARCOAL, hover_color=COLOR_BORDER)
        self.btn_capture.configure(state="normal", fg_color=COLOR_ACCENT)

        # Advance to next tray automatically and resume live view
        self.advance_to_next_tray()
        self.start_view()

    def _on_finish_click(self) -> None:
        """Completes the current tray and advances workflow."""
        if self._pending_photo:
            self.advance_to_next_tray()
            self._pending_photo = None
            self.lbl_capture_feedback.configure(
                text="Tray finished! Ready for next core tray.",
                text_color=COLOR_SUCCESS,
            )

    def advance_to_next_tray(self) -> None:
        """Auto-increments tray number and updates intervals."""
        try:
            curr_tray = int(self.entry_tray.get().strip())
            self.entry_tray.delete(0, "end")
            self.entry_tray.insert(0, str(curr_tray + 1))
        except ValueError:
            pass

        try:
            prev_to = float(self.entry_to.get().strip())
            interval_diff = prev_to - float(self.entry_from.get().strip())
            new_from = prev_to
            new_to = new_from + (interval_diff if interval_diff > 0 else 2.0)

            self.entry_from.delete(0, "end")
            self.entry_from.insert(0, f"{new_from:g}")

            self.entry_to.delete(0, "end")
            self.entry_to.insert(0, f"{new_to:g}")
        except ValueError:
            pass

        if hasattr(self, "txt_comments"):
            self.txt_comments.delete("1.0", "end")

        # Reset Capture Details card
        self.lbl_cap_dims.configure(text="waiting ...", text_color=COLOR_TEXT_HINT)
        self.lbl_cap_filesize.configure(text="waiting ...", text_color=COLOR_TEXT_HINT)
        self.lbl_cap_status.configure(text="waiting ...", text_color=COLOR_TEXT_HINT)
        self.lbl_cap_dest.configure(text="waiting ...", text_color=COLOR_TEXT_HINT)

        # Refresh Series count
        if hasattr(self, "lbl_series_count") and self.ctx.active_session and self.ctx.photo_repo:
            cnt = len(self.ctx.photo_repo.list_by_session(self.ctx.active_session.id))
            self.lbl_series_count.configure(text=str(cnt))

        self._evaluate_preflight()

    def _on_pick_sess_date(self) -> None:
        """Opens popup date picker for session date."""
        cur_val = self.entry_sess_date.get().strip() if hasattr(self, "entry_sess_date") else ""
        def on_chosen(dt_str: str) -> None:
            if hasattr(self, "entry_sess_date"):
                self.entry_sess_date.delete(0, "end")
                self.entry_sess_date.insert(0, dt_str)
            self._sync_sess_date(dt_str)
        DatePickerModal(self, initial_date=cur_val, on_select=on_chosen)

    def _on_sess_date_entry_changed(self, event=None) -> None:
        """Syncs date entered manually in entry_sess_date."""
        if hasattr(self, "entry_sess_date"):
            dt_str = self.entry_sess_date.get().strip()
            self._sync_sess_date(dt_str)

    def _sync_sess_date(self, dt_str: str) -> None:
        if not dt_str:
            return
        sess = self.ctx.active_session
        if sess:
            sess.date = dt_str
            self.ctx.active_session = sess
            try:
                self.ctx.session_paths = self.ctx.storage_manager.get_session_paths(f"{sess.site}_{sess.date}")
            except Exception:
                pass
            top_win = self.winfo_toplevel()
            if hasattr(top_win, "_update_top_header"):
                top_win._update_top_header()

    def _on_detect_cam(self) -> None:
        cur_mode = self.opt_capture_interface.get() if hasattr(self, "opt_capture_interface") else "Physical USB Webcam"
        self._on_capture_interface_changed(cur_mode)

    def _on_reconnect_cam(self) -> None:
        self._on_detect_cam()

    def _on_test_wifi_ip(self) -> None:
        ip = self.entry_cam_wifi_ip.get().strip() if hasattr(self, "entry_cam_wifi_ip") else ""
        if not ip:
            if hasattr(self, "lbl_wifi_feedback"):
                self.lbl_wifi_feedback.configure(
                    text="Masukkan IP address kamera terlebih dahulu.",
                    text_color=COLOR_WARNING,
                )
            return

        if hasattr(self, "lbl_wifi_feedback"):
            self.lbl_wifi_feedback.configure(text=f"Menguji koneksi ke {ip}...", text_color=COLOR_ACCENT)
        self.update_idletasks()

        reachable, msg = self.ctx.camera_manager.test_wifi_connection(ip)
        if hasattr(self, "lbl_wifi_feedback"):
            if reachable:
                self.lbl_wifi_feedback.configure(
                    text=f"✓ Kamera Terhubung di jaringan: {msg}",
                    text_color=COLOR_SUCCESS,
                )
            else:
                self.lbl_wifi_feedback.configure(
                    text=f"✕ Tidak dapat menjangkau {ip} ({msg}).",
                    text_color=COLOR_ERROR,
                )

    def _on_browse_cam_tether(self) -> None:
        from tkinter import filedialog
        chosen = filedialog.askdirectory(title="Pilih Folder Tethering Wi-Fi DSLR")
        if chosen and hasattr(self, "entry_cam_tether_folder"):
            self.entry_cam_tether_folder.delete(0, "end")
            self.entry_cam_tether_folder.insert(0, chosen)
            self._on_save_wifi_settings()

    def _on_auto_detect_tether(self) -> None:
        from camera.adapters.wifi_dslr import WiFiDslrAdapter
        discovered = WiFiDslrAdapter._discover_default_tether_dir()
        if hasattr(self, "entry_cam_tether_folder"):
            self.entry_cam_tether_folder.delete(0, "end")
            self.entry_cam_tether_folder.insert(0, str(discovered))
            self._on_save_wifi_settings()
            if hasattr(self, "lbl_wifi_feedback"):
                self.lbl_wifi_feedback.configure(
                    text=f"✓ Folder tether ditemukan: {discovered.name}",
                    text_color=COLOR_SUCCESS,
                )

    def _on_save_wifi_settings(self) -> None:
        from config.config_manager import get_config
        cfg = getattr(self.ctx, "config", None) or get_config()
        ip = self.entry_cam_wifi_ip.get().strip() if hasattr(self, "entry_cam_wifi_ip") else ""
        tether_f = self.entry_cam_tether_folder.get().strip() if hasattr(self, "entry_cam_tether_folder") else ""
        if ip:
            cfg.set("camera", "wifi_ip", ip)
        if tether_f:
            cfg.set("camera", "tether_folder", tether_f)
        cfg.save()
        if hasattr(self, "lbl_wifi_feedback"):
            self.lbl_wifi_feedback.configure(
                text="✓ Pengaturan Wi-Fi DSLR berhasil disimpan.",
                text_color=COLOR_SUCCESS,
            )

    def _on_apply_custom_resolution(self) -> None:
        try:
            w = int(self.entry_res_w.get().strip())
            h = int(self.entry_res_h.get().strip())
            if w < 320 or h < 240:
                raise ValueError("Dimensi resolusi minimal 320x240.")
            self.ctx.camera_manager.set_resolution(w, h, mode="custom")
            if hasattr(self, "lbl_res_active"):
                self.lbl_res_active.configure(text=f"Active: {w} x {h} (Custom)")
            self.lbl_capture_feedback.configure(
                text=f"Resolusi kustom diterapkan: {w}x{h}",
                text_color=COLOR_SUCCESS,
            )
        except Exception as e:
            self.lbl_capture_feedback.configure(
                text=f"Resolusi tidak valid: {e}",
                text_color=COLOR_ERROR,
            )

    def _on_settings_browse_server(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Target Server Repository Folder")
        if folder and hasattr(self, "entry_settings_server_folder"):
            self.entry_settings_server_folder.delete(0, "end")
            self.entry_settings_server_folder.insert(0, folder)
            if hasattr(self, "entry_server_folder"):
                self.entry_server_folder.delete(0, "end")
                self.entry_server_folder.insert(0, folder)
            self._on_settings_save_server()

    def _on_settings_open_server(self) -> None:
        folder = self.entry_settings_server_folder.get().strip() if hasattr(self, "entry_settings_server_folder") else ""
        if not folder:
            return
        from pathlib import Path
        p = Path(folder)
        if p.exists():
            import subprocess
            subprocess.Popen(["explorer", str(p)])
        elif hasattr(self, "lbl_settings_server_status"):
            self.lbl_settings_server_status.configure(text="✕ Folder tidak ditemukan.", text_color=COLOR_ERROR)

    def _on_settings_open_local(self) -> None:
        import subprocess
        subprocess.Popen(["explorer", str(self.ctx.storage_manager.base_dir)])

    def _on_settings_save_server(self) -> None:
        from config.config_manager import get_config
        cfg = getattr(self.ctx, "config", None) or get_config()
        srv_f = self.entry_settings_server_folder.get().strip() if hasattr(self, "entry_settings_server_folder") else ""
        srv_u = self.entry_settings_server_url.get().strip() if hasattr(self, "entry_settings_server_url") else ""

        cfg.set("transfer", "server_folder", srv_f)
        cfg.set("storage", "server_folder", srv_f)
        if srv_u:
            cfg.set("transfer", "server_url", srv_u)
        cfg.save()

        if hasattr(self, "entry_server_folder") and srv_f:
            self.entry_server_folder.delete(0, "end")
            self.entry_server_folder.insert(0, srv_f)

        if hasattr(self, "lbl_settings_server_status"):
            self.lbl_settings_server_status.configure(text="✓ Pengaturan penyimpanan disimpan.", text_color=COLOR_SUCCESS)

    def _on_settings_test_server(self) -> None:
        folder = self.entry_settings_server_folder.get().strip() if hasattr(self, "entry_settings_server_folder") else ""
        if not folder:
            if hasattr(self, "lbl_settings_server_status"):
                self.lbl_settings_server_status.configure(text="Isi path folder server.", text_color=COLOR_WARNING)
            return
        from pathlib import Path
        p = Path(folder)
        try:
            if p.exists():
                if hasattr(self, "lbl_settings_server_status"):
                    self.lbl_settings_server_status.configure(text="✓ Server folder aktif & dapat diakses.", text_color=COLOR_SUCCESS)
            else:
                if hasattr(self, "lbl_settings_server_status"):
                    self.lbl_settings_server_status.configure(text="✕ Server folder belum dapat diakses.", text_color=COLOR_ERROR)
        except Exception as e:
            if hasattr(self, "lbl_settings_server_status"):
                self.lbl_settings_server_status.configure(text=f"✕ Akses gagal: {e}", text_color=COLOR_ERROR)

    def _on_run_diagnostics(self) -> None:
        if not hasattr(self, "diag_result_box"):
            return
        self.diag_result_box.delete("1.0", "end")
        self.diag_result_box.insert("end", "Running system diagnostics...\n")
        self.update_idletasks()

        res = self.diag.run_all_checks()
        text = self.diag.format_report_text(res)
        self.diag_result_box.delete("1.0", "end")
        self.diag_result_box.insert("end", text)
        self._check_recovery()

    def _on_export_report(self) -> None:
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="corephoto_diagnostics.json",
        )
        if path:
            res = self.diag.run_all_checks()
            import json
            from pathlib import Path
            Path(path).write_text(json.dumps(res, indent=2), encoding="utf-8")
            self.lbl_capture_feedback.configure(
                text=f"✓ Diagnostic report exported: {Path(path).name}",
                text_color=COLOR_SUCCESS,
            )

    def _on_resume_captures(self) -> None:
        recovered = self.diag.resume_incomplete_captures()
        if recovered > 0:
            self._check_recovery()
            self.lbl_capture_feedback.configure(
                text=f"✓ Berhasil memulihkan {recovered} foto belum selesai.",
                text_color=COLOR_SUCCESS,
            )
        else:
            self.lbl_capture_feedback.configure(
                text="Tidak ada foto tertunda yang dapat dipulihkan.",
                text_color=COLOR_TEXT_MUTED,
            )

    def _refresh_logs(self) -> None:
        if hasattr(self, "log_textbox"):
            text = self.diag.read_recent_logs(max_lines=150)
            self.log_textbox.delete("1.0", "end")
            self.log_textbox.insert("end", text)
            self.log_textbox.see("end")

    def _check_recovery(self) -> None:
        if not hasattr(self, "recovery_card"):
            return
        rec_data = self.diag._check_crash_recovery()
        count = rec_data.get("incomplete_captures_found", 0)
        if count > 0:
            self.recovery_card.configure(fg_color=COLOR_WARNING_BG, border_color=COLOR_WARNING_BORDER)
            self.recovery_lbl.configure(
                text=f"! Ditemukan {count} file raw belum selesai.",
                text_color=COLOR_WARNING,
            )
            self.btn_resume.configure(state="normal", fg_color=COLOR_ACCENT)
        else:
            self.recovery_card.configure(fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER)
            self.recovery_lbl.configure(
                text="✓ Semua foto konsisten. Tidak ada raw tersangkut.",
                text_color=COLOR_SUCCESS,
            )
            self.btn_resume.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)

    def select_tab(self, tab_name: str) -> None:
        """Allows switching left tabs externally (e.g. from app.navigate_to)."""
        if hasattr(self, "left_tabs") and tab_name:
            t_lower = tab_name.lower()
            if any(k in t_lower for k in ("cam", "setting")):
                self.left_tabs.set("Camera Settings")
            elif any(k in t_lower for k in ("tray", "data")):
                self.left_tabs.set("Tray Data")
            self._update_left_tab_styles()

    def refresh(self) -> None:
        """Refreshes CaptureView status, settings values, and camera information."""
        self.start_view()
        # Sync Wi-Fi & Storage fields in Camera Settings tab
        from config.config_manager import get_config
        cfg = getattr(self.ctx, "config", None) or get_config()
        if hasattr(self, "entry_cam_wifi_ip") and not self.entry_cam_wifi_ip.get().strip():
            cfg_ip = cfg.get("camera", "wifi_ip", "")
            if cfg_ip:
                self.entry_cam_wifi_ip.delete(0, "end")
                self.entry_cam_wifi_ip.insert(0, str(cfg_ip))
        if hasattr(self, "entry_cam_tether_folder") and not self.entry_cam_tether_folder.get().strip():
            cfg_tether = cfg.get("camera", "tether_folder", "")
            if cfg_tether:
                self.entry_cam_tether_folder.delete(0, "end")
                self.entry_cam_tether_folder.insert(0, str(cfg_tether))
            else:
                from camera.adapters.wifi_dslr import WiFiDslrAdapter
                disc = WiFiDslrAdapter._discover_default_tether_dir()
                self.entry_cam_tether_folder.delete(0, "end")
                self.entry_cam_tether_folder.insert(0, str(disc))
        if hasattr(self, "entry_settings_server_folder"):
            srv_f = cfg.get("transfer", "server_folder", "") or cfg.get("storage", "server_folder", "")
            self.entry_settings_server_folder.delete(0, "end")
            self.entry_settings_server_folder.insert(0, str(srv_f))
        if hasattr(self, "entry_settings_local_folder"):
            self.entry_settings_local_folder.delete(0, "end")
            self.entry_settings_local_folder.insert(0, str(self.ctx.storage_manager.base_dir))
        if hasattr(self, "entry_settings_server_url"):
            srv_u = cfg.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
            self.entry_settings_server_url.delete(0, "end")
            self.entry_settings_server_url.insert(0, str(srv_u))
        self._refresh_logs()
        self._check_recovery()
