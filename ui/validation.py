"""Validation Results & Audit Screen (PRD Section 20).
Displays comprehensive data integrity audit results and enables re-running validation.
Designed with Light Mode aesthetics, clear audit badges, and informative explanations.
"""

from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger

logger = get_logger(__name__)


class ValidationView(ctk.CTkFrame):
    """Validation report and integrity check screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color="#F8FAFC", **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------- Header -----------------
        header = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E2E8F0")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 8))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            title_box,
            text="✅ Pusat Validasi & Integritas Data",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Sistem melakukan audit kepatuhan otomatis: format penamaan file, keutuhan checksum MD5, kelengkapan metadata, dan validitas rentang interval.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=950,
            justify="left"
        )
        subtitle.pack(anchor="w", pady=(2, 4))

        # Toolbar & Summary Bar
        summary_bar = ctk.CTkFrame(header, fg_color="#F1F5F9", corner_radius=8)
        summary_bar.pack(fill="x", padx=16, pady=(4, 12))

        self.summary_lbl = ctk.CTkLabel(
            summary_bar,
            text="Memuat status validasi...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1E293B"
        )
        self.summary_lbl.pack(side="left", padx=14, pady=8)

        self.btn_run_all = ctk.CTkButton(
            summary_bar,
            text="🔄  Jalankan Validasi Ulang Sesi",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            corner_radius=6,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            command=self._on_rerun_validation
        )
        self.btn_run_all.pack(side="right", padx=10, pady=6)

        # ----------------- Scrollable List of Findings -----------------
        self.results_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E2E8F0"
        )
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.results_scroll.grid_columnconfigure(0, weight=1)

    def refresh(self) -> None:
        """Loads all validation findings for current session."""
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        if not self.ctx.active_session or not self.ctx.photo_repo or not self.ctx.validation_repo:
            ctk.CTkLabel(
                self.results_scroll,
                text="Tidak ada sesi aktif. Buat sesi di menu Sesi Foto terlebih dahulu.",
                font=ctk.CTkFont(size=13),
                text_color="#94A3B8"
            ).pack(pady=60)
            self.summary_lbl.configure(text="Sesi: Belum Ada Sesi Aktif")
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        total = len(photos)
        valid_count = sum(1 for p in photos if p.status == "VALID")
        invalid_count = total - valid_count

        self.summary_lbl.configure(
            text=f"Total: {total} Foto Tray  |  ✅ Tervalidasi Penuh: {valid_count}  |  ⚠️ Perlu Perhatian: {invalid_count}",
            text_color="#059669" if invalid_count == 0 else "#D97706"
        )

        if not photos:
            ctk.CTkLabel(
                self.results_scroll,
                text="Belum ada foto yang diambil dalam sesi aktif ini.\nAmbil foto di menu Capture untuk melihat hasil audit.",
                font=ctk.CTkFont(size=13),
                text_color="#94A3B8",
                justify="center"
            ).pack(pady=60)
            return

        for photo in photos:
            card = ctk.CTkFrame(self.results_scroll, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color="#E2E8F0")
            card.pack(fill="x", padx=12, pady=6)

            card_top = ctk.CTkFrame(card, fg_color="transparent")
            card_top.pack(fill="x", padx=14, pady=(10, 4))

            title_text = f"Foto ID #{photo.id} — {photo.filename_base}.jpg"
            ctk.CTkLabel(card_top, text=title_text, font=ctk.CTkFont(size=13, weight="bold"), text_color="#1E293B").pack(side="left")

            is_valid = photo.status == "VALID"
            status_color = "#059669" if is_valid else "#DC2626"
            status_bg = "#ECFDF5" if is_valid else "#FEF2F2"

            badge = ctk.CTkLabel(
                card_top,
                text=f" {photo.status} ",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=status_color,
                fg_color=status_bg,
                corner_radius=4
            )
            badge.pack(side="right")

            # Load validation checks for this photo
            checks = self.ctx.validation_repo.get_for_target("photo", str(photo.id))
            if checks:
                for chk in checks:
                    chk_frame = ctk.CTkFrame(card, fg_color="transparent")
                    chk_frame.pack(fill="x", padx=16, pady=2)

                    icon = "✅" if chk.is_valid else "❌"
                    color = "#047857" if chk.is_valid else "#DC2626"
                    ctk.CTkLabel(
                        chk_frame,
                        text=f"{icon}  [{chk.rule_name}] {chk.message}",
                        font=ctk.CTkFont(size=12),
                        text_color=color
                    ).pack(anchor="w")
            else:
                ctk.CTkLabel(card, text="Pemeriksaan belum dijalankan. Klik 'Jalankan Validasi Ulang'.", font=ctk.CTkFont(size=12), text_color="#94A3B8").pack(anchor="w", padx=16, pady=4)

    def _on_rerun_validation(self) -> None:
        """Re-runs validation across all photos in active session."""
        if not self.ctx.active_session or not self.ctx.photo_repo:
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        for photo in photos:
            self.ctx.validate_photo(photo.id)

        self.refresh()
