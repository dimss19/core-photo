"""Diagnostics and Settings UI (PRD Section 24 & 25).
Provides technicians with hardware diagnostics, crash recovery, and live log inspection.
"""

from pathlib import Path
from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from diagnostics.diagnostics import get_diagnostics

logger = get_logger(__name__)


class SettingsView(ctk.CTkFrame):
    """Settings and Technical Diagnostics screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self.diag = get_diagnostics()

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 10))

        title = ctk.CTkLabel(header, text="Pengaturan & Diagnostik Sistem", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Menu teknisi untuk pemecahan masalah (troubleshooting), pemulihan crash, dan pengecekan hardware.",
            font=ctk.CTkFont(size=13),
            text_color="gray70"
        )
        subtitle.pack(anchor="w")

        # ----------------- Left: Diagnostics & Recovery -----------------
        left_panel = ctk.CTkScrollableFrame(self, corner_radius=12)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=(10, 20))

        ctk.CTkLabel(left_panel, text="Pemeriksaan Diagnostik", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=14, pady=(12, 6))

        btn_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=6)
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_run_diag = ctk.CTkButton(
            btn_row,
            text="🔍  Jalankan Tes Diagnostik",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            command=self._on_run_diagnostics
        )
        self.btn_run_diag.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_export = ctk.CTkButton(
            btn_row,
            text="📁  Ekspor Laporan",
            font=ctk.CTkFont(size=13),
            height=36,
            fg_color="#333333",
            command=self._on_export_report
        )
        self.btn_export.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Result box
        self.diag_result_box = ctk.CTkTextbox(left_panel, height=220, font=ctk.CTkFont(family="Consolas", size=11))
        self.diag_result_box.pack(fill="x", padx=14, pady=10)

        # Crash Recovery Section (PRD Section 19)
        ctk.CTkLabel(left_panel, text="Pemulihan Crash (Crash Recovery)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=14, pady=(14, 4))

        self.recovery_lbl = ctk.CTkLabel(
            left_panel,
            text="Memeriksa keberadaan file RAW yang belum selesai diproses...",
            font=ctk.CTkFont(size=12),
            wraplength=320,
            justify="left"
        )
        self.recovery_lbl.pack(anchor="w", padx=14, pady=4)

        self.btn_resume = ctk.CTkButton(
            left_panel,
            text="🛡️  Pulihkan Pekerjaan (Resume Processing)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#2CC985",
            hover_color="#229965",
            command=self._on_resume_captures
        )
        self.btn_resume.pack(fill="x", padx=14, pady=(8, 14))

        # ----------------- Right: Settings & Log Viewer -----------------
        right_panel = ctk.CTkFrame(self, corner_radius=12)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=(10, 20))
        right_panel.grid_rowconfigure(2, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Theme settings
        theme_bar = ctk.CTkFrame(right_panel, fg_color="transparent")
        theme_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(theme_bar, text="Tema Tampilan UI:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            theme_bar,
            values=["dark", "light", "system"],
            command=self._on_change_theme,
            width=120
        )
        self.theme_menu.pack(side="right")
        self.theme_menu.set(self.ctx.config_manager.get("app", "theme", "dark"))

        # Log viewer
        log_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        log_header.grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 4))

        ctk.CTkLabel(log_header, text="Log Sistem (Live Log Viewer)", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_refresh_log = ctk.CTkButton(
            log_header,
            text="Segarkan Log",
            width=100,
            height=28,
            fg_color="#333333",
            command=self._refresh_logs
        )
        btn_refresh_log.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(right_panel, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_textbox.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))

    def refresh(self) -> None:
        self._refresh_logs()
        self._check_recovery()

    def _refresh_logs(self) -> None:
        text = self.diag.read_recent_logs(max_lines=150)
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.insert("end", text)
        self.log_textbox.see("end")

    def _check_recovery(self) -> None:
        rec_data = self.diag._check_crash_recovery()
        count = rec_data.get("incomplete_captures_found", 0)
        if count > 0:
            self.recovery_lbl.configure(
                text=f"Ditemukan {count} file foto RAW yang belum selesai diproses setelah penutupan aplikasi. Klik tombol di bawah untuk memproses otomatis tanpa perlu capture ulang.",
                text_color="#E5A93C"
            )
            self.btn_resume.configure(state="normal")
        else:
            self.recovery_lbl.configure(
                text="Seluruh pekerjaan capture berada dalam kondisi konsisten. Tidak ada proses yang tertunda.",
                text_color="#2CC985"
            )
            self.btn_resume.configure(state="disabled")

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
        recovered = self.diag.resume_incomplete_captures()
        self._check_recovery()
        self._refresh_logs()

    def _on_change_theme(self, theme_val: str) -> None:
        ctk.set_appearance_mode(theme_val)
        self.ctx.config_manager.set("app", "theme", theme_val)
