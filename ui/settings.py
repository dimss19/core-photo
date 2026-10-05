"""Diagnostics and Settings UI (PRD Section 24 & 25).
Provides technicians with hardware diagnostics, crash recovery, and live log inspection.
Designed with Light Mode aesthetics, clear descriptions, and responsive actions.
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
        super().__init__(master, fg_color="#F8FAFC", **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self.diag = get_diagnostics()

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------- Header -----------------
        header = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=(14, 12))

        ctk.CTkLabel(
            title_box,
            text="⚙️ Pengaturan & Diagnostik Sistem",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Panel teknisi dan geologis untuk pemecahan masalah (troubleshooting), pemulihan crash otomatis, dan inspeksi log aktivitas.",
            font=ctk.CTkFont(size=12),
            text_color="#64748B",
            wraplength=950,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # ----------------- Left: Diagnostics & Recovery -----------------
        left_panel = ctk.CTkScrollableFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E2E8F0"
        )
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 16))

        ctk.CTkLabel(
            left_panel,
            text="🔍 Pemeriksaan Diagnostik",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=16, pady=(14, 2))

        ctk.CTkLabel(
            left_panel,
            text="Verifikasi kamera, integritas database SQLite, dan ruang disk.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        ).pack(anchor="w", padx=16, pady=(0, 8))

        btn_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=4)
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_run_diag = ctk.CTkButton(
            btn_row,
            text="Jalankan Diagnostik",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=6,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            command=self._on_run_diagnostics
        )
        self.btn_run_diag.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_export = ctk.CTkButton(
            btn_row,
            text="Ekspor Laporan JSON",
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=6,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            command=self._on_export_report
        )
        self.btn_export.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Result box
        self.diag_result_box = ctk.CTkTextbox(
            left_panel,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#F8FAFC",
            border_width=1,
            border_color="#CBD5E1",
            text_color="#334155"
        )
        self.diag_result_box.pack(fill="x", padx=16, pady=8)

        # Crash Recovery Section (PRD Section 19)
        ctk.CTkLabel(
            left_panel,
            text="🛡️ Pemulihan Crash (Crash Recovery)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=16, pady=(16, 2))

        ctk.CTkLabel(
            left_panel,
            text="Memeriksa keberadaan file RAW yang belum selesai diproses saat aplikasi tertutup tiba-tiba.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=380,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self.recovery_card = ctk.CTkFrame(left_panel, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color="#E2E8F0")
        self.recovery_card.pack(fill="x", padx=16, pady=4)

        self.recovery_lbl = ctk.CTkLabel(
            self.recovery_card,
            text="Memeriksa status crash recovery...",
            font=ctk.CTkFont(size=12),
            wraplength=360,
            justify="left",
            text_color="#334155"
        )
        self.recovery_lbl.pack(anchor="w", padx=12, pady=(10, 8))

        self.btn_resume = ctk.CTkButton(
            self.recovery_card,
            text="Pulihkan Pekerjaan Tertunda (Resume Processing)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=6,
            fg_color="#059669",
            hover_color="#047857",
            command=self._on_resume_captures
        )
        self.btn_resume.pack(fill="x", padx=12, pady=(0, 10))

        # ----------------- Right: Settings & Log Viewer -----------------
        right_panel = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 16))
        right_panel.grid_rowconfigure(2, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Mode Info Bar
        info_bar = ctk.CTkFrame(right_panel, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color="#E2E8F0")
        info_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(info_bar, text="🎨 Mode Tampilan:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#1E293B").pack(side="left", padx=12, pady=10)
        ctk.CTkLabel(info_bar, text="Light Mode (Aktif Standar)", font=ctk.CTkFont(size=12), text_color="#059669").pack(side="left", pady=10)

        # Log viewer Header
        log_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        log_header.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 4))

        ctk.CTkLabel(
            log_header,
            text="📋 Log Sistem Terkini (Live Log)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")

        btn_refresh_log = ctk.CTkButton(
            log_header,
            text="Segarkan Log",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            corner_radius=6,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            command=self._refresh_logs
        )
        btn_refresh_log.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            right_panel,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#F8FAFC",
            border_width=1,
            border_color="#CBD5E1",
            text_color="#334155"
        )
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
            self.recovery_card.configure(fg_color="#FFFBEB", border_color="#FCD34D")
            self.recovery_lbl.configure(
                text=f"⚠️ Ditemukan {count} file foto RAW yang belum selesai diproses setelah penutupan aplikasi. Klik tombol di bawah untuk memproses otomatis tanpa perlu capture ulang.",
                text_color="#B45309"
            )
            self.btn_resume.configure(state="normal", fg_color="#059669")
        else:
            self.recovery_card.configure(fg_color="#ECFDF5", border_color="#A7F3D0")
            self.recovery_lbl.configure(
                text="✅ Seluruh pekerjaan capture berada dalam kondisi konsisten. Tidak ada proses yang tertunda.",
                text_color="#065F46"
            )
            self.btn_resume.configure(state="disabled", fg_color="#94A3B8")

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
