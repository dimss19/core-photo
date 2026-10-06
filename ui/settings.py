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
        cam_content.pack(fill="x", padx=16, pady=(0, 14))
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
                "Universal Hot-Folder (All DSLRs)",
                "Physical USB / Webcam",
                "Standby / Simulator",
            ],
            command=self._on_adapter_mode_changed,
            height=32,
            width=240,
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

        self._refresh_logs()
        self._check_recovery()

    def _on_adapter_mode_changed(self, mode: str) -> None:
        """Switches active camera adapter between Direct USB, Hot-Folder, USB, and Standby."""
        if "Direct USB" in mode:
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
        elif "Hot-Folder" in mode:
            hot_dir = self.ctx.storage_manager.base_dir / "HotFolder"
            self.ctx.camera_manager.connect_camera("hot_folder", str(hot_dir))
            self.lbl_cam_feedback.configure(
                text=f"✓ Universal Hot-Folder Active: Watching {hot_dir.name}",
                text_color=COLOR_SUCCESS,
            )
        elif "Standby" in mode:
            self.ctx.camera_manager.connect_camera("webcam", "sim")
            self.lbl_cam_feedback.configure(
                text="✓ Standby Simulator Pattern Active.",
                text_color=COLOR_TEXT_MUTED,
            )
        else:
            self.ctx.camera_manager.connect_camera("webcam", "0")
            if self.ctx.camera_manager.is_ready():
                self.lbl_cam_feedback.configure(text="✓ Physical USB Camera connected.", text_color=COLOR_SUCCESS)
            else:
                self.lbl_cam_feedback.configure(text="✕ No physical video camera detected on USB index 0.", text_color=COLOR_ERROR)
        self.refresh()

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
