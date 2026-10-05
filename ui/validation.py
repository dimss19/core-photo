"""Validation Results & Audit Screen (PRD Section 20).
Displays comprehensive data integrity audit results and enables re-running validation.
"""

from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger

logger = get_logger(__name__)


class ValidationView(ctk.CTkFrame):
    """Validation report and integrity check screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))

        title = ctk.CTkLabel(header, text="Pusat Validasi & Integritas Data", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Pemeriksaan otomatis kelengkapan data, konvensi nama, hash MD5, dan konsistensi file lokal.",
            font=ctk.CTkFont(size=13),
            text_color="gray70"
        )
        subtitle.pack(anchor="w", pady=(2, 10))

        # Toolbar & Summary
        summary_bar = ctk.CTkFrame(header, fg_color="transparent")
        summary_bar.pack(fill="x")

        self.summary_lbl = ctk.CTkLabel(
            summary_bar,
            text="Memuat status validasi...",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.summary_lbl.pack(side="left")

        self.btn_run_all = ctk.CTkButton(
            summary_bar,
            text="🔄  Jalankan Validasi Ulang Sesi",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            command=self._on_rerun_validation
        )
        self.btn_run_all.pack(side="right")

        # Scrollable list of validation findings
        self.results_scroll = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.results_scroll.grid_columnconfigure(0, weight=1)

    def refresh(self) -> None:
        """Loads all validation findings for current session."""
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        if not self.ctx.active_session or not self.ctx.photo_repo or not self.ctx.validation_repo:
            ctk.CTkLabel(self.results_scroll, text="Tidak ada sesi aktif.", text_color="gray60").pack(pady=40)
            self.summary_lbl.configure(text="Sesi: Tidak ada")
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        total = len(photos)
        valid_count = sum(1 for p in photos if p.status == "VALID")
        invalid_count = total - valid_count

        self.summary_lbl.configure(
            text=f"Total: {total} Foto  |  ✅ Tervalidasi: {valid_count}  |  ⚠️ Memerlukan Perhatian: {invalid_count}",
            text_color="#2CC985" if invalid_count == 0 else "#E5A93C"
        )

        if not photos:
            ctk.CTkLabel(self.results_scroll, text="Belum ada foto dalam sesi ini.", text_color="gray60").pack(pady=40)
            return

        for photo in photos:
            card = ctk.CTkFrame(self.results_scroll, corner_radius=8)
            card.pack(fill="x", padx=10, pady=6)

            card_top = ctk.CTkFrame(card, fg_color="transparent")
            card_top.pack(fill="x", padx=12, pady=(10, 4))

            title_text = f"Foto ID #{photo.id} — {photo.filename_base}.jpg"
            ctk.CTkLabel(card_top, text=title_text, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

            status_color = "#2CC985" if photo.status == "VALID" else "#D9534F"
            badge = ctk.CTkLabel(card_top, text=f" {photo.status} ", font=ctk.CTkFont(size=12, weight="bold"), text_color=status_color)
            badge.pack(side="right")

            # Load validation checks for this photo
            checks = self.ctx.validation_repo.get_for_target("photo", str(photo.id))
            if checks:
                for chk in checks:
                    chk_frame = ctk.CTkFrame(card, fg_color="transparent")
                    chk_frame.pack(fill="x", padx=16, pady=1)

                    icon = "✅" if chk.is_valid else "❌"
                    color = "#E0E0E0" if chk.is_valid else "#D9534F"
                    ctk.CTkLabel(
                        chk_frame,
                        text=f"{icon}  [{chk.rule_name}] {chk.message}",
                        font=ctk.CTkFont(size=12),
                        text_color=color
                    ).pack(anchor="w")
            else:
                ctk.CTkLabel(card, text="Pemeriksaan belum dijalankan.", font=ctk.CTkFont(size=12), text_color="gray60").pack(anchor="w", padx=16, pady=4)

    def _on_rerun_validation(self) -> None:
        """Re-runs validation across all photos in active session."""
        if not self.ctx.active_session or not self.ctx.photo_repo:
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        for photo in photos:
            self.ctx.validate_photo(photo.id)

        self.refresh()
