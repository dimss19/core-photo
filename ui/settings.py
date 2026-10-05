"""Settings & Diagnostics Screen (Professional Industrial Redesign).
Segmented into:
- GENERAL (Application profile, Storage path and capacity)
- CAMERA (Camera status, model, Detect / Reconnect buttons; no SDK leaks)
- SERVER (Server URL, Auth credentials, connection tester)
- SYSTEM (Diagnostics, Crash Recovery, Live Log inspector)
Zero emojis, strict professional industrial standards.
"""

from pathlib import Path
from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from diagnostics.diagnostics import get_diagnostics
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_ACCENT_LIGHT,
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


class SettingsView(ctk.CTkFrame):
    """Settings and Technical Diagnostics screen."""

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
            text="SYSTEM SETTINGS & DIAGNOSTICS",
            font=get_font(16, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="General parameters, hardware adapters, server endpoints, crash recovery, and operational logs.",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # ----------------- Tabbed Sections -----------------
        self.tabs = ctk.CTkTabview(
            self,
            fg_color=COLOR_PANEL,
            segmented_button_fg_color=COLOR_PANEL_ALT,
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color=COLOR_ACCENT_HOVER,
            segmented_button_unselected_color=COLOR_PANEL_ALT,
            segmented_button_unselected_hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))

        tab_general = self.tabs.add("GENERAL")
        tab_camera = self.tabs.add("CAMERA")
        tab_server = self.tabs.add("SERVER")
        tab_system = self.tabs.add("SYSTEM")

        self._build_general_tab(tab_general)
        self._build_camera_tab(tab_camera)
        self._build_server_tab(tab_server)
        self._build_system_tab(tab_system)

    # =========================================================================
    # 1. GENERAL TAB
    # =========================================================================
    def _build_general_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure((0, 1), weight=1)

        # Application Profile
        app_box = ctk.CTkFrame(parent, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        app_box.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        ctk.CTkLabel(app_box, text="APPLICATION PROFILE", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(16, 2))
        ctk.CTkLabel(app_box, text="Name: Core Photo Desktop Industrial", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(app_box, text="Version: 1.0.0 (Windows Native)", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(app_box, text="Theme: Light Mode (Industrial High Contrast)", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(app_box, text="Database: SQLite (WAL mode, offline-first)", font=get_font(11), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 16))

        # Storage Management
        stor_box = ctk.CTkFrame(parent, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        stor_box.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)

        ctk.CTkLabel(stor_box, text="STORAGE CONFIGURATION", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(16, 2))
        base_dir = str(self.ctx.storage_manager.base_dir)
        ctk.CTkLabel(stor_box, text=f"Archive Directory:\n{base_dir}", font=get_font(11), text_color=COLOR_TEXT_PRIMARY, justify="left").pack(anchor="w", padx=16, pady=2)

        free_gb = self.ctx.storage_manager.get_available_space_mb() / 1024.0
        self.lbl_storage_space = ctk.CTkLabel(stor_box, text=f"Available Space: {free_gb:.1f} GB", font=get_font(11, "bold"), text_color=COLOR_SUCCESS)
        self.lbl_storage_space.pack(anchor="w", padx=16, pady=(4, 16))

    # =========================================================================
    # 2. CAMERA TAB (Clean operator view, no raw technical leaks)
    # =========================================================================
    def _build_camera_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)

        cam_box = ctk.CTkFrame(parent, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        cam_box.pack(fill="x", padx=12, pady=12)

        ctk.CTkLabel(cam_box, text="CAMERA INTERFACE", font=get_font(13, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(cam_box, text="Connected imaging hardware status and detection controls.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 10))

        # Status & Model Card
        card = ctk.CTkFrame(cam_box, fg_color=COLOR_PANEL, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", padx=18, pady=4)

        self.lbl_cam_tab_status = ctk.CTkLabel(card, text="Camera: ● Checking...", font=get_font(12, "bold"), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_cam_tab_status.pack(anchor="w", padx=14, pady=(12, 2))

        self.lbl_cam_tab_model = ctk.CTkLabel(card, text="Model: USB Video Device (WebcamAdapter)", font=get_font(11), text_color=COLOR_TEXT_MUTED)
        self.lbl_cam_tab_model.pack(anchor="w", padx=14, pady=(0, 12))

        # Buttons Row: [ Detect Camera ] [ Reconnect ]
        btn_box = ctk.CTkFrame(cam_box, fg_color="transparent")
        btn_box.pack(fill="x", padx=18, pady=(10, 16))

        btn_detect = ctk.CTkButton(
            btn_box,
            text="Detect Camera",
            font=get_font(11, "bold"),
            height=34,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_detect_camera,
        )
        btn_detect.pack(side="left", padx=(0, 8))

        btn_reconnect = ctk.CTkButton(
            btn_box,
            text="Reconnect",
            font=get_font(11),
            height=34,
            corner_radius=4,
            fg_color=COLOR_PANEL,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_reconnect_camera,
        )
        btn_reconnect.pack(side="left")

        self.lbl_cam_feedback = ctk.CTkLabel(cam_box, text="", font=get_font(11, "bold"), text_color=COLOR_TEXT_MUTED)
        self.lbl_cam_feedback.pack(anchor="w", padx=18, pady=(0, 10))

    # =========================================================================
    # 3. SERVER TAB
    # =========================================================================
    def _build_server_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)

        srv_box = ctk.CTkFrame(parent, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        srv_box.pack(fill="x", padx=12, pady=12)

        ctk.CTkLabel(srv_box, text="CENTRAL SERVER REPOSITORY", font=get_font(13, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(srv_box, text="Configuration for secure batch uploads.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=18, pady=(0, 10))

        server_url = self.ctx.config_manager.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
        ctk.CTkLabel(srv_box, text="Endpoint URL:", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(2, 1))
        self.entry_srv_url = ctk.CTkEntry(srv_box, height=34, font=get_font(11), fg_color=COLOR_PANEL, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_srv_url.insert(0, server_url)
        self.entry_srv_url.pack(fill="x", padx=18, pady=(0, 8))

        api_key = self.ctx.config_manager.get("transfer", "api_key", "")
        ctk.CTkLabel(srv_box, text="API Key / Auth Token (Optional):", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(2, 1))
        self.entry_srv_key = ctk.CTkEntry(srv_box, height=34, font=get_font(11), show="*", fg_color=COLOR_PANEL, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_srv_key.insert(0, api_key)
        self.entry_srv_key.pack(fill="x", padx=18, pady=(0, 14))

        btn_save = ctk.CTkButton(
            srv_box,
            text="Save Server Settings",
            font=get_font(11, "bold"),
            height=34,
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            hover_color="#27272A",
            text_color="#FFFFFF",
            command=self._on_save_server_cfg,
        )
        btn_save.pack(anchor="w", padx=18, pady=(0, 16))

        self.lbl_srv_feedback = ctk.CTkLabel(srv_box, text="", font=get_font(11, "bold"), text_color=COLOR_TEXT_MUTED)
        self.lbl_srv_feedback.pack(anchor="w", padx=18, pady=(0, 10))

    # =========================================================================
    # 4. SYSTEM / DIAGNOSTICS TAB
    # =========================================================================
    def _build_system_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure((0, 1), weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Left: Diagnostics & Crash Recovery
        left_col = ctk.CTkFrame(parent, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        ctk.CTkLabel(left_col, text="TECHNICAL DIAGNOSTICS", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(16, 2))
        ctk.CTkLabel(left_col, text="Hardware adapters, SDK status, and database checks.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 8))

        diag_btns = ctk.CTkFrame(left_col, fg_color="transparent")
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
            left_col,
            height=130,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLOR_PANEL,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.diag_result_box.pack(fill="both", expand=True, padx=16, pady=(6, 8))

        # Crash Recovery
        ctk.CTkLabel(left_col, text="CRASH RECOVERY", font=get_font(11, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(6, 2))
        self.recovery_card = ctk.CTkFrame(left_col, fg_color=COLOR_PANEL, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        self.recovery_card.pack(fill="x", padx=16, pady=(0, 16))

        self.recovery_lbl = ctk.CTkLabel(self.recovery_card, text="Checking crash status...", font=get_font(10), text_color=COLOR_TEXT_MUTED, wraplength=260, justify="left")
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

        # Right: Live System Logs
        right_col = ctk.CTkFrame(parent, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        right_col.grid_rowconfigure(1, weight=1)
        right_col.grid_columnconfigure(0, weight=1)

        log_head = ctk.CTkFrame(right_col, fg_color="transparent")
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
            right_col,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLOR_PANEL,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

    def refresh(self) -> None:
        """Refreshes camera status, logs, and storage."""
        cam_ready = self.ctx.camera_manager.is_ready()
        if cam_ready:
            self.lbl_cam_tab_status.configure(text="Camera: ● Connected", text_color=COLOR_SUCCESS)
            self.lbl_cam_tab_model.configure(text=f"Model: {self.ctx.camera_manager.get_status_summary()}")
        else:
            self.lbl_cam_tab_status.configure(text="Camera: ● Disconnected", text_color=COLOR_ERROR)
            self.lbl_cam_tab_model.configure(text="No active camera adapter recognized")

        free_gb = self.ctx.storage_manager.get_available_space_mb() / 1024.0
        self.lbl_storage_space.configure(text=f"Available Space: {free_gb:.1f} GB")

        self._refresh_logs()
        self._check_recovery()

    def _on_detect_camera(self) -> None:
        self.lbl_cam_feedback.configure(text="Scanning video devices...", text_color=COLOR_TEXT_MUTED)
        self.ctx.camera_manager.connect_camera("webcam", "0")
        self.refresh()
        if self.ctx.camera_manager.is_ready():
            self.lbl_cam_feedback.configure(text="✓ Camera detected and connected successfully.", text_color=COLOR_SUCCESS)
        else:
            self.lbl_cam_feedback.configure(text="✕ Camera detected but not responding. Check connection.", text_color=COLOR_ERROR)

    def _on_reconnect_camera(self) -> None:
        self._on_detect_camera()

    def _on_save_server_cfg(self) -> None:
        url = self.entry_srv_url.get().strip()
        key = self.entry_srv_key.get().strip()
        self.ctx.config_manager.set("transfer", "server_url", url, auto_save=False)
        self.ctx.config_manager.set("transfer", "api_key", key, auto_save=True)
        self.lbl_srv_feedback.configure(text="✓ Server settings updated.", text_color=COLOR_SUCCESS)

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
            self.recovery_card.configure(fg_color=COLOR_PANEL, border_color=COLOR_BORDER)
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
