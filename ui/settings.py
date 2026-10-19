"""Settings & Diagnostics Screen (Professional Industrial Redesign).
Unified Single-Page View:
- Application Profile & Storage Configuration
- Camera Hardware Interface (Status & Connection Controls)
- Technical Diagnostics & Crash Recovery
- Live System Logs
Zero emojis, strict professional industrial standards.
"""

from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from diagnostics.diagnostics import get_diagnostics
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
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    COLOR_WARNING_BG,
    COLOR_WARNING_BORDER,
    get_font,
)

logger = get_logger(__name__)


class SettingsView(ctk.CTkFrame):
    """Settings and Technical Diagnostics screen (unified single-page layout)."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self.diag = get_diagnostics()

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------- Top Header -----------------
        header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            title_box,
            text="SETTINGS",
            font=get_font(16, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Camera hardware interface, crash recovery, and operational diagnostic logs.",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # ----------------- Unified Scrollable Dashboard -----------------
        scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        scroll_body.grid_columnconfigure((0, 1), weight=1)

        # =====================================================================
        # 1. CAMERA HARDWARE INTERFACE (Row 0, Full Width)
        # =====================================================================
        cam_box = ctk.CTkFrame(scroll_body, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        cam_box.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        cam_head = ctk.CTkFrame(cam_box, fg_color="transparent")
        cam_head.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(cam_head, text="CAMERA HARDWARE INTERFACE", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w")
        ctk.CTkLabel(cam_head, text="Connected imaging hardware status and detection controls.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(1, 0))

        cam_content = ctk.CTkFrame(cam_box, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        cam_content.pack(fill="x", padx=16, pady=(0, 8))
        cam_content.grid_columnconfigure(0, weight=1)
        cam_content.grid_columnconfigure(1, weight=0)

        cam_info = ctk.CTkFrame(cam_content, fg_color="transparent")
        cam_info.grid(row=0, column=0, sticky="w", padx=14, pady=10)

        self.lbl_cam_tab_status = ctk.CTkLabel(cam_info, text="Camera: ● Checking...", font=get_font(12, "bold"), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_cam_tab_status.pack(anchor="w")

        self.lbl_cam_tab_model = ctk.CTkLabel(cam_info, text="Model: USB Video Device (WebcamAdapter)", font=get_font(11), text_color=COLOR_TEXT_MUTED)
        self.lbl_cam_tab_model.pack(anchor="w", pady=(2, 0))

        self.lbl_cam_feedback = ctk.CTkLabel(cam_info, text="", font=get_font(10, "bold"), text_color=COLOR_TEXT_MUTED)
        self.lbl_cam_feedback.pack(anchor="w", pady=(2, 0))

        cam_btns = ctk.CTkFrame(cam_content, fg_color="transparent")
        cam_btns.grid(row=0, column=1, sticky="e", padx=14, pady=10)

        self.opt_adapter_mode = ctk.CTkOptionMenu(
            cam_btns,
            values=[
                "Direct USB DSLR (Canon/Nikon/Sony)",
                "Physical USB / Webcam",
            ],
            command=self._on_adapter_mode_changed,
            height=32,
            width=280,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
        )
        self.opt_adapter_mode.pack(side="left", padx=(0, 8))

        btn_detect = ctk.CTkButton(
            cam_btns,
            text="Detect Camera",
            font=get_font(11, "bold"),
            height=32,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_detect_camera,
        )
        btn_detect.pack(side="left", padx=(0, 8))

        btn_reconnect = ctk.CTkButton(
            cam_btns,
            text="Reconnect",
            font=get_font(11),
            height=32,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_reconnect_camera,
        )
        btn_reconnect.pack(side="left")

        # Physical Webcam Device Selector (Internal vs External USB)
        webcam_box = ctk.CTkFrame(cam_box, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        webcam_box.pack(fill="x", padx=16, pady=(0, 8))
        webcam_box.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(webcam_box, text="Physical Webcam Device (Internal / External USB):", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(webcam_box, text="Pilih webcam internal laptop atau external USB. Berlaku untuk mode Physical USB / Webcam.", font=get_font(10), text_color=COLOR_TEXT_MUTED).grid(row=1, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 4))
        ctk.CTkLabel(webcam_box, text="Webcam Device:", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=0, sticky="w", padx=(14, 8), pady=3)
        f_webcam = ctk.CTkFrame(webcam_box, fg_color="transparent")
        f_webcam.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=3)
        f_webcam.grid_columnconfigure(0, weight=1)
        self._webcam_display_to_index = {}
        self.opt_settings_webcam = ctk.CTkOptionMenu(
            f_webcam,
            values=["Scanning webcams..."],
            command=self._on_settings_webcam_changed,
            height=28,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
        )
        self.opt_settings_webcam.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.btn_settings_webcam_refresh = ctk.CTkButton(
            f_webcam,
            text="Refresh",
            width=80,
            height=28,
            font=get_font(10, "bold"),
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_refresh_settings_webcam,
        )
        self.btn_settings_webcam_refresh.grid(row=0, column=1, sticky="e")
        self.lbl_settings_webcam_hint = ctk.CTkLabel(
            webcam_box,
            text="",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_settings_webcam_hint.grid(row=3, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 8))

        # Resolution Controls & Quality Panel
        res_content = ctk.CTkFrame(cam_box, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        res_content.pack(fill="x", padx=16, pady=(0, 14))
        res_content.grid_columnconfigure(0, weight=1)
        res_content.grid_columnconfigure(1, weight=0)

        res_info = ctk.CTkFrame(res_content, fg_color="transparent")
        res_info.grid(row=0, column=0, sticky="w", padx=14, pady=10)

        ctk.CTkLabel(res_info, text="Capture Resolution Quality:", font=get_font(12, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w")
        self.lbl_res_active = ctk.CTkLabel(
            res_info,
            text="Active: 5184 x 3456 (18.0 MP · Best DSLR Native)",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_res_active.pack(anchor="w", pady=(2, 0))

        res_btns = ctk.CTkFrame(res_content, fg_color="transparent")
        res_btns.grid(row=0, column=1, sticky="e", padx=14, pady=10)

        self.opt_resolution = ctk.CTkOptionMenu(
            res_btns,
            values=[
                "Auto (Best Native DSLR — 18MP/24MP+)",
                "5184 x 3456 (18MP Canon 60D Native)",
                "6000 x 4000 (24MP Ultra High Res)",
                "4000 x 3000 (12MP High Res)",
                "3840 x 2160 (4K UHD)",
                "1920 x 1080 (Full HD 1080p)",
                "1280 x 720 (HD 720p)",
                "Custom Resolution...",
            ],
            command=self._on_resolution_changed,
            height=32,
            width=240,
            font=get_font(10),
            fg_color=COLOR_PANEL,
            text_color=COLOR_CHARCOAL,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BORDER_STRONG,
        )
        self.opt_resolution.pack(side="left", padx=(0, 6))

        self.entry_res_w = ctk.CTkEntry(res_btns, placeholder_text="W", width=50, height=32, font=get_font(10))
        self.entry_res_w.pack(side="left", padx=2)

        ctk.CTkLabel(res_btns, text="×", font=get_font(11, "bold"), text_color=COLOR_TEXT_MUTED).pack(side="left", padx=2)

        self.entry_res_h = ctk.CTkEntry(res_btns, placeholder_text="H", width=50, height=32, font=get_font(10))
        self.entry_res_h.pack(side="left", padx=2)

        self.btn_apply_custom_res = ctk.CTkButton(
            res_btns,
            text="Set",
            font=get_font(11, "bold"),
            height=32,
            width=42,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_apply_custom_resolution,
        )
        self.btn_apply_custom_res.pack(side="left", padx=(4, 0))

        # =====================================================================
        # 2. DIAGNOSTICS & LIVE LOGS (Row 1, 2 Columns)
        # =====================================================================
        diag_box = ctk.CTkFrame(scroll_body, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        diag_box.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))

        ctk.CTkLabel(diag_box, text="TECHNICAL DIAGNOSTICS", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(16, 2))
        ctk.CTkLabel(diag_box, text="Hardware adapters, SDK status, and database checks.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 8))

        diag_btns = ctk.CTkFrame(diag_box, fg_color="transparent")
        diag_btns.pack(fill="x", padx=16, pady=4)
        diag_btns.grid_columnconfigure((0, 1), weight=1)

        btn_run = ctk.CTkButton(
            diag_btns,
            text="Run Diagnostics",
            font=get_font(11, "bold"),
            height=32,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_run_diagnostics,
        )
        btn_run.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        btn_export = ctk.CTkButton(
            diag_btns,
            text="Export JSON",
            font=get_font(11),
            height=32,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_export_report,
        )
        btn_export.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.diag_result_box = ctk.CTkTextbox(
            diag_box,
            height=130,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLOR_PANEL_ALT,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.diag_result_box.pack(fill="both", expand=True, padx=16, pady=(6, 8))

        # Crash Recovery
        ctk.CTkLabel(diag_box, text="CRASH RECOVERY", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(6, 2))
        self.recovery_card = ctk.CTkFrame(diag_box, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        self.recovery_card.pack(fill="x", padx=16, pady=(0, 16))

        self.recovery_lbl = ctk.CTkLabel(self.recovery_card, text="Checking crash status...", font=get_font(10), text_color=COLOR_TEXT_MUTED, wraplength=280, justify="left")
        self.recovery_lbl.pack(anchor="w", padx=12, pady=(8, 4))

        self.btn_resume = ctk.CTkButton(
            self.recovery_card,
            text="Resume Incomplete Captures",
            font=get_font(10, "bold"),
            height=28,
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            hover_color="#27272A",
            text_color="#FFFFFF",
            command=self._on_resume_captures,
        )
        self.btn_resume.pack(fill="x", padx=12, pady=(0, 8))

        # Live Logs (Right)
        log_box = ctk.CTkFrame(scroll_body, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        log_box.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        log_box.grid_rowconfigure(1, weight=1)
        log_box.grid_columnconfigure(0, weight=1)

        log_head = ctk.CTkFrame(log_box, fg_color="transparent")
        log_head.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))

        ctk.CTkLabel(log_head, text="LIVE SYSTEM LOGS", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(side="left")

        btn_ref_log = ctk.CTkButton(
            log_head,
            text="Refresh Logs",
            font=get_font(10),
            width=80,
            height=26,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._refresh_logs,
        )
        btn_ref_log.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            log_box,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLOR_PANEL_ALT,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

        # =====================================================================
        # 3. STORAGE & SERVER CONFIGURATION (Row 2, Full Width)
        # =====================================================================
        srv_box = ctk.CTkFrame(scroll_body, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        srv_box.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        srv_head = ctk.CTkFrame(srv_box, fg_color="transparent")
        srv_head.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(srv_head, text="STORAGE & SERVER REPOSITORY CONFIGURATION", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w")
        ctk.CTkLabel(srv_head, text="Local file directory sandbox and remote network target server folder for centralized archiving.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(1, 0))

        srv_content = ctk.CTkFrame(srv_box, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        srv_content.pack(fill="x", padx=16, pady=(0, 14))
        srv_content.grid_columnconfigure(1, weight=1)

        # 1. Target Server Folder
        ctk.CTkLabel(srv_content, text="Target Server Folder:", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        f_srv_input = ctk.CTkFrame(srv_content, fg_color="transparent")
        f_srv_input.grid(row=0, column=1, sticky="ew", padx=14, pady=(12, 4))
        f_srv_input.grid_columnconfigure(0, weight=1)

        self.entry_settings_server_folder = ctk.CTkEntry(
            f_srv_input,
            height=30,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            placeholder_text="\\\\192.168.x.x\\Share or Z:\\CorePhotoServer",
        )
        self.entry_settings_server_folder.grid(row=0, column=0, sticky="ew")

        btn_browse_srv = ctk.CTkButton(
            f_srv_input,
            text="Browse...",
            font=get_font(10, "bold"),
            height=30,
            width=75,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_settings_browse_server,
        )
        btn_browse_srv.grid(row=0, column=1, padx=(6, 0))

        btn_open_srv = ctk.CTkButton(
            f_srv_input,
            text="Open Folder",
            font=get_font(10),
            height=30,
            width=85,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_settings_open_server,
        )
        btn_open_srv.grid(row=0, column=2, padx=(4, 0))

        # 2. Local Base Storage Directory
        ctk.CTkLabel(srv_content, text="Local Base Directory:", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=0, sticky="w", padx=14, pady=(4, 4))
        f_loc_input = ctk.CTkFrame(srv_content, fg_color="transparent")
        f_loc_input.grid(row=1, column=1, sticky="ew", padx=14, pady=(4, 4))
        f_loc_input.grid_columnconfigure(0, weight=1)

        self.entry_settings_local_folder = ctk.CTkEntry(
            f_loc_input,
            height=30,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
        )
        self.entry_settings_local_folder.grid(row=0, column=0, sticky="ew")

        btn_open_loc = ctk.CTkButton(
            f_loc_input,
            text="Open in Explorer",
            font=get_font(10),
            height=30,
            width=110,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_settings_open_local,
        )
        btn_open_loc.grid(row=0, column=1, padx=(6, 0))

        # 3. Server API URL
        ctk.CTkLabel(srv_content, text="Server API URL:", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=2, column=0, sticky="w", padx=14, pady=(4, 12))
        f_api_input = ctk.CTkFrame(srv_content, fg_color="transparent")
        f_api_input.grid(row=2, column=1, sticky="ew", padx=14, pady=(4, 12))
        f_api_input.grid_columnconfigure(0, weight=1)

        self.entry_settings_server_url = ctk.CTkEntry(
            f_api_input,
            height=30,
            font=get_font(11),
            fg_color=COLOR_PANEL,
            border_color=COLOR_BORDER,
            placeholder_text="http://127.0.0.1:8000/api/v1",
        )
        self.entry_settings_server_url.grid(row=0, column=0, sticky="ew")

        # Action Buttons & Status feedback
        srv_actions = ctk.CTkFrame(srv_box, fg_color="transparent")
        srv_actions.pack(fill="x", padx=16, pady=(0, 14))

        self.lbl_settings_server_status = ctk.CTkLabel(srv_actions, text="", font=get_font(10, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_settings_server_status.pack(side="left")

        btn_test_srv = ctk.CTkButton(
            srv_actions,
            text="Check Server Access",
            font=get_font(11),
            height=32,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_settings_test_server,
        )
        btn_test_srv.pack(side="right", padx=(6, 0))

        btn_save_srv = ctk.CTkButton(
            srv_actions,
            text="Save Storage & Server Settings",
            font=get_font(11, "bold"),
            height=32,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_settings_save_server,
        )
        btn_save_srv.pack(side="right")

    def select_tab(self, tab_name: str = "") -> None:
        """Compatibility method for external callers navigating to settings."""
        pass

    def refresh(self) -> None:
        """Refreshes camera status, logs, and storage."""
        cam_ready = self.ctx.camera_manager.is_ready()
        if cam_ready:
            self.lbl_cam_tab_status.configure(text="Camera: ● Connected", text_color=COLOR_SUCCESS)
            self.lbl_cam_tab_model.configure(text=f"Model: {self.ctx.camera_manager.get_status_summary()}")
        else:
            self.lbl_cam_tab_status.configure(text="Camera: ● Disconnected", text_color=COLOR_ERROR)
            self.lbl_cam_tab_model.configure(text="No active camera adapter recognized")

        # Update resolution display
        try:
            cur_w, cur_h = self.ctx.camera_manager.get_current_resolution()
            cur_mode = self.ctx.camera_manager.get_resolution_mode()
            mp = (cur_w * cur_h) / 1_000_000.0
            mode_desc = "Best DSLR Native" if cur_mode == "best_native" else "Custom / Configured"
            self.lbl_res_active.configure(
                text=f"Active: {cur_w} x {cur_h} ({mp:.1f} MP · {mode_desc})"
            )

            if cur_mode == "best_native":
                self.opt_resolution.set("Auto (Best Native DSLR — 18MP/24MP+)")
            elif (cur_w, cur_h) == (5184, 3456):
                self.opt_resolution.set("5184 x 3456 (18MP Canon 60D Native)")
            elif (cur_w, cur_h) == (6000, 4000):
                self.opt_resolution.set("6000 x 4000 (24MP Ultra High Res)")
            elif (cur_w, cur_h) == (4000, 3000):
                self.opt_resolution.set("4000 x 3000 (12MP High Res)")
            elif (cur_w, cur_h) == (3840, 2160):
                self.opt_resolution.set("3840 x 2160 (4K UHD)")
            elif (cur_w, cur_h) == (1920, 1080):
                self.opt_resolution.set("1920 x 1080 (Full HD 1080p)")
            elif (cur_w, cur_h) == (1280, 720):
                self.opt_resolution.set("1280 x 720 (HD 720p)")
            else:
                self.opt_resolution.set("Custom Resolution...")
                self.entry_res_w.delete(0, "end")
                self.entry_res_w.insert(0, str(cur_w))
                self.entry_res_h.delete(0, "end")
                self.entry_res_h.insert(0, str(cur_h))
        except Exception as e:
            logger.debug("Resolution UI sync exception: %s", e)

        # Synchronize adapter dropdown with active adapter + webcam list
        try:
            self._refresh_settings_webcam_list()
        except Exception:
            pass
        active_adapter = getattr(self.ctx.camera_manager, "_active_adapter", None)
        if hasattr(self, "opt_adapter_mode") and active_adapter:
            from camera.adapters.direct_usb import DirectUsbAdapter
            from camera.adapters.webcam import WebcamAdapter
            if isinstance(active_adapter, DirectUsbAdapter):
                self.opt_adapter_mode.set("Direct USB DSLR (Canon/Nikon/Sony)")
            else:
                self.opt_adapter_mode.set("Physical USB / Webcam")

        # Update Storage & Server Configuration fields
        if hasattr(self, "entry_settings_server_folder"):
            from config.config_manager import get_config
            cfg = getattr(self.ctx, "config", None) or get_config()
            srv_f = cfg.get("transfer", "server_folder", "") or cfg.get("storage", "server_folder", "")
            self.entry_settings_server_folder.delete(0, "end")
            self.entry_settings_server_folder.insert(0, str(srv_f))

            loc_f = self.ctx.storage_manager.base_dir
            self.entry_settings_local_folder.delete(0, "end")
            self.entry_settings_local_folder.insert(0, str(loc_f))

            srv_u = cfg.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
            self.entry_settings_server_url.delete(0, "end")
            self.entry_settings_server_url.insert(0, str(srv_u))

        self._refresh_logs()
        self._check_recovery()

    def _on_adapter_mode_changed(self, mode: str) -> None:
        """Switches active camera adapter between Direct USB DSLR and Physical USB Webcam."""
        from config.config_manager import get_config
        cfg = getattr(self.ctx, "config", None) or get_config()

        if "Direct USB" in mode:
            cfg.set("camera", "default_adapter", "direct_usb")
            cfg.save()
            self.ctx.camera_manager.connect_camera("direct_usb", "0")
            if self.ctx.camera_manager.is_ready():
                info = self.ctx.camera_manager.get_info()
                self.lbl_cam_feedback.configure(
                    text=f"✓ Direct USB Active: {info.model if info else 'Ready'}",
                    text_color=COLOR_SUCCESS,
                )
            else:
                self.lbl_cam_feedback.configure(
                    text="✓ Direct USB Active: Connect camera with USB cable",
                    text_color=COLOR_TEXT_PRIMARY,
                )
        else:
            cfg.set("camera", "default_adapter", "webcam")
            cfg.save()
            device_id = self._parse_settings_webcam_index(
                self.opt_settings_webcam.get() if hasattr(self, "opt_settings_webcam") else None
            )
            self.ctx.camera_manager.connect_camera("webcam", device_id)
            if self.ctx.camera_manager.is_ready():
                info = self.ctx.camera_manager.get_info()
                self.lbl_cam_feedback.configure(
                    text=f"✓ Physical USB Camera connected: {info.model if info else device_id}.",
                    text_color=COLOR_SUCCESS,
                )
            else:
                self.lbl_cam_feedback.configure(text=f"✕ No physical video camera detected on USB index {device_id}.", text_color=COLOR_ERROR)
        self.refresh()

    def _parse_settings_webcam_index(self, choice=None) -> str:
        """Parses Settings webcam selector back to device id."""
        if choice:
            mapped = getattr(self, "_webcam_display_to_index", {}).get(choice)
            if mapped is not None:
                return str(mapped)
            import re
            m = re.search(r"Index\s+(\d+)", choice)
            if m:
                return m.group(1)
        try:
            return str(self.ctx.camera_manager.get_preferred_webcam_index())
        except Exception:
            return "0"

    def _refresh_settings_webcam_list(self) -> None:
        """Enumerates webcams for Settings selector (no auto-connect)."""
        if not hasattr(self, "opt_settings_webcam"):
            return
        try:
            devices = self.ctx.camera_manager.list_webcam_devices()
        except Exception:
            devices = []
        self._webcam_display_to_index = {}
        values: list = []
        for dev in devices:
            label = dev.get("name") or f"Webcam Index {dev.get('index')}"
            values.append(label)
            self._webcam_display_to_index[label] = dev.get("index")
        try:
            self.opt_settings_webcam.configure(values=values)
        except Exception:
            pass
        try:
            active = getattr(self.ctx.camera_manager, "_active_adapter", None)
            cur = None
            if active is not None and active.__class__.__name__ == "WebcamAdapter" \
                    and not getattr(active, "_is_simulated", False):
                cur = getattr(active, "device_index", None)
            else:
                cur = self.ctx.camera_manager.get_preferred_webcam_index()
            selected = None
            for label, idx in self._webcam_display_to_index.items():
                if str(idx) == str(cur):
                    selected = label
                    break
            if selected is None and values:
                selected = values[0]
            if selected:
                self.opt_settings_webcam.set(selected)
        except Exception:
            pass
        if hasattr(self, "lbl_settings_webcam_hint"):
            if devices:
                self.lbl_settings_webcam_hint.configure(
                    text=f"{len(devices)} webcam terdeteksi — pilih lalu klik Detect Camera."
                )
            else:
                self.lbl_settings_webcam_hint.configure(
                    text="Tidak ada webcam fisik terdeteksi."
                )

    def _on_refresh_settings_webcam(self) -> None:
        self._refresh_settings_webcam_list()
        self.lbl_cam_feedback.configure(
            text="Daftar webcam diperbarui.",
            text_color=COLOR_TEXT_MUTED,
        )

    def _on_settings_webcam_changed(self, choice: str) -> None:
        """User picked webcam in Settings: switch immediately if in webcam mode."""
        try:
            cur_mode = self.opt_adapter_mode.get() if hasattr(self, "opt_adapter_mode") else "Physical USB / Webcam"
        except Exception:
            cur_mode = "Physical USB / Webcam"
        if "Physical" in cur_mode or "Webcam" in cur_mode:
            self._on_adapter_mode_changed(cur_mode)
        else:
            # Just persist preference for next time
            try:
                from config.config_manager import get_config
                cfg = getattr(self.ctx, "config", None) or get_config()
                device_id = self._parse_settings_webcam_index(choice)
                if device_id != "sim":
                    cfg.set("camera", "preferred_index", int(device_id))
                    cfg.set("camera", "device_id", str(device_id))
            except Exception:
                pass

    def _on_detect_camera(self) -> None:
        cur_mode = self.opt_adapter_mode.get() if hasattr(self, "opt_adapter_mode") else "Physical USB / Webcam"
        self._on_adapter_mode_changed(cur_mode)

    def _on_reconnect_camera(self) -> None:
        self._on_detect_camera()

    def _refresh_logs(self) -> None:
        text = self.diag.read_recent_logs(max_lines=150)
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.insert("end", text)
        self.log_textbox.see("end")

    def _check_recovery(self) -> None:
        rec_data = self.diag._check_crash_recovery()
        count = rec_data.get("incomplete_captures_found", 0)
        if count > 0:
            self.recovery_card.configure(fg_color=COLOR_WARNING_BG, border_color=COLOR_WARNING_BORDER)
            self.recovery_lbl.configure(
                text=f"! Found {count} incomplete capture raw files after shutdown. Click below to resume without retaking.",
                text_color=COLOR_WARNING,
            )
            self.btn_resume.configure(state="normal", fg_color=COLOR_ACCENT)
        else:
            self.recovery_card.configure(fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER)
            self.recovery_lbl.configure(
                text="✓ All captures consistent. No orphaned raw files.",
                text_color=COLOR_SUCCESS,
            )
            self.btn_resume.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)

    def _on_run_diagnostics(self) -> None:
        res = self.diag.run_all_checks()
        import json
        pretty_json = json.dumps(res, indent=2)
        self.diag_result_box.delete("1.0", "end")
        self.diag_result_box.insert("end", pretty_json)
        self._check_recovery()

    def _on_export_report(self) -> None:
        dest = self.ctx.storage_manager.base_dir / "diagnostics_report.json"
        self.diag.export_report(dest)
        self._refresh_logs()

    def _on_resume_captures(self) -> None:
        self.diag.resume_incomplete_captures()
        self._check_recovery()
        self._refresh_logs()

    def _on_resolution_changed(self, choice: str) -> None:
        """Handles resolution option selection."""
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
        elif "Custom" in choice:
            cur_w, cur_h = self.ctx.camera_manager.get_current_resolution()
            self.entry_res_w.delete(0, "end")
            self.entry_res_w.insert(0, str(cur_w))
            self.entry_res_h.delete(0, "end")
            self.entry_res_h.insert(0, str(cur_h))
            return
        self.refresh()

    def _on_apply_custom_resolution(self) -> None:
        """Applies custom width and height resolution values."""
        try:
            w_str = self.entry_res_w.get().strip()
            h_str = self.entry_res_h.get().strip()
            if not w_str or not h_str:
                return
            w = int(w_str)
            h = int(h_str)
            if w < 320 or h < 240:
                return
            self.ctx.camera_manager.set_resolution(w, h, mode="custom")
            self.refresh()
        except Exception as e:
            logger.error("Failed applying custom resolution: %s", e)

    def _on_settings_browse_server(self) -> None:
        """Opens folder dialog to pick a remote or network server target directory."""
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Target Server Folder")
        if folder:
            self.entry_settings_server_folder.delete(0, "end")
            self.entry_settings_server_folder.insert(0, folder)
            self._on_settings_save_server()

    def _on_settings_open_server(self) -> None:
        """Opens configured server folder in Windows File Explorer if accessible."""
        import os
        from pathlib import Path
        path_str = self.entry_settings_server_folder.get().strip()
        if path_str and Path(path_str).exists():
            try:
                os.startfile(str(Path(path_str)))
            except Exception as e:
                self.lbl_settings_server_status.configure(text=f"Failed opening folder: {e}", text_color=COLOR_ERROR)
        else:
            self.lbl_settings_server_status.configure(text="Server folder path does not exist or is unreachable.", text_color=COLOR_WARNING)

    def _on_settings_open_local(self) -> None:
        """Opens local storage base directory in Windows File Explorer."""
        import os
        loc = self.ctx.storage_manager.base_dir
        if loc.exists():
            try:
                os.startfile(str(loc))
            except Exception as e:
                logger.error("Failed opening local folder: %s", e)

    def _on_settings_save_server(self) -> None:
        """Persists storage and server folder configuration."""
        srv_folder = self.entry_settings_server_folder.get().strip()
        srv_url = self.entry_settings_server_url.get().strip()
        from config.config_manager import get_config
        cfg = getattr(self.ctx, "config", None) or get_config()
        cfg.set("transfer", "server_folder", srv_folder)
        cfg.set("storage", "server_folder", srv_folder)
        if srv_url:
            cfg.set("transfer", "server_url", srv_url)
        self.lbl_settings_server_status.configure(text="✓ Storage & Server settings saved successfully.", text_color=COLOR_SUCCESS)

    def _on_settings_test_server(self) -> None:
        """Verifies if the specified target server directory is accessible."""
        from pathlib import Path
        srv_folder = self.entry_settings_server_folder.get().strip()
        if not srv_folder:
            self.lbl_settings_server_status.configure(text="Server folder is not configured.", text_color=COLOR_WARNING)
            return
        try:
            p = Path(srv_folder)
            if p.exists():
                self.lbl_settings_server_status.configure(text=f"✓ Target Server Folder accessible: {p}", text_color=COLOR_SUCCESS)
            else:
                self.lbl_settings_server_status.configure(text="! Folder does not exist yet. Will be created upon sync.", text_color=COLOR_WARNING)
        except Exception as e:
            self.lbl_settings_server_status.configure(text=f"✕ Error checking server folder: {e}", text_color=COLOR_ERROR)


