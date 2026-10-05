"""Validation Results & Audit Screen (Professional Industrial Redesign).
Audits data integrity: filename schemas, MD5 checksum consistency, interval sequences, and file existence.
Zero emojis, strict professional standards.
"""

from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
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


class ValidationView(ctk.CTkFrame):
    """Validation report and integrity check screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------- Top Header -----------------
        header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=(16, 6))

        ctk.CTkLabel(
            title_box,
            text="DATA VALIDATION & INTEGRITY AUDIT",
            font=get_font(16, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Automated compliance audit: naming structure, MD5 checksum integrity, metadata consistency, and depth intervals.",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Toolbar & Summary Bar
        summary_bar = ctk.CTkFrame(header, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        summary_bar.pack(fill="x", padx=20, pady=(6, 16))

        self.summary_lbl = ctk.CTkLabel(
            summary_bar,
            text="Loading validation report...",
            font=get_font(11, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.summary_lbl.pack(side="left", padx=14, pady=8)

        self.btn_run_all = ctk.CTkButton(
            summary_bar,
            text="RUN RE-VALIDATION AUDIT",
            font=get_font(11, "bold"),
            height=32,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_rerun_validation,
        )
        self.btn_run_all.pack(side="right", padx=10, pady=6)

        # ----------------- Scrollable List of Findings -----------------
        self.results_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.results_scroll.grid_columnconfigure(0, weight=1)

    def refresh(self) -> None:
        """Loads all validation findings for current session."""
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        if not self.ctx.active_session or not self.ctx.photo_repo or not self.ctx.validation_repo:
            ctk.CTkLabel(
                self.results_scroll,
                text="No active session found. Please initialize a session first.",
                font=get_font(12),
                text_color=COLOR_TEXT_HINT,
            ).pack(pady=60)
            self.summary_lbl.configure(text="Session: [None]")
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        total = len(photos)
        valid_count = sum(1 for p in photos if p.status == "VALID")
        invalid_count = total - valid_count

        verdict_color = COLOR_SUCCESS if invalid_count == 0 else COLOR_WARNING
        self.summary_lbl.configure(
            text=f"Total: {total} Trays  ·  ✓ Validated: {valid_count}  ·  ! Issues: {invalid_count}",
            text_color=verdict_color,
        )

        if not photos:
            ctk.CTkLabel(
                self.results_scroll,
                text="No core photos captured in this session yet.\nPerform tray captures to generate validation audits.",
                font=get_font(12),
                text_color=COLOR_TEXT_HINT,
                justify="center",
            ).pack(pady=60)
            return

        for photo in photos:
            is_valid = (photo.status == "VALID")
            card_border = COLOR_BORDER if is_valid else COLOR_WARNING_BORDER

            card = ctk.CTkFrame(
                self.results_scroll,
                fg_color=COLOR_PANEL_ALT,
                corner_radius=4,
                border_width=1,
                border_color=card_border,
            )
            card.pack(fill="x", padx=8, pady=6)

            card_top = ctk.CTkFrame(card, fg_color="transparent")
            card_top.pack(fill="x", padx=14, pady=(10, 4))

            title_text = f"Photo #{photo.id} — {photo.filename_base}.jpg  ({photo.hole_id}, Tray {photo.tray_number})"
            ctk.CTkLabel(
                card_top,
                text=title_text,
                font=get_font(12, "bold"),
                text_color=COLOR_CHARCOAL,
            ).pack(side="left")

            badge_text = " VALID " if is_valid else f" {photo.status} "
            badge_fg = COLOR_SUCCESS_BG if is_valid else COLOR_WARNING_BG
            badge_tc = COLOR_SUCCESS if is_valid else COLOR_WARNING
            badge_border = COLOR_SUCCESS_BORDER if is_valid else COLOR_WARNING_BORDER

            badge = ctk.CTkLabel(
                card_top,
                text=badge_text,
                font=get_font(10, "bold"),
                text_color=badge_tc,
                fg_color=badge_fg,
                corner_radius=2,
            )
            badge.pack(side="right")

            # Load validation checks for this photo
            checks = self.ctx.validation_repo.get_for_target("photo", str(photo.id))
            if checks:
                has_error = False
                for chk in checks:
                    chk_frame = ctk.CTkFrame(card, fg_color="transparent")
                    chk_frame.pack(fill="x", padx=16, pady=1)

                    mark = "✓" if chk.is_valid else "✕"
                    mark_color = COLOR_SUCCESS if chk.is_valid else COLOR_ERROR

                    ctk.CTkLabel(
                        chk_frame,
                        text=f"{mark}  {chk.rule_name}: {chk.message}",
                        font=get_font(11),
                        text_color=mark_color,
                    ).pack(anchor="w")

                    if not chk.is_valid:
                        has_error = True

                if has_error:
                    btn_fix = ctk.CTkButton(
                        card,
                        text="FIX ISSUE (REVIEW PHOTO)",
                        font=get_font(10, "bold"),
                        height=26,
                        width=160,
                        corner_radius=4,
                        fg_color=COLOR_WARNING,
                        hover_color="#B45309",
                        text_color="#FFFFFF",
                        command=lambda p=photo: self._on_fix_issue(p),
                    )
                    btn_fix.pack(anchor="e", padx=16, pady=(4, 10))
            else:
                ctk.CTkLabel(
                    card,
                    text="Validation pending. Click 'Run Re-Validation Audit'.",
                    font=get_font(11),
                    text_color=COLOR_TEXT_HINT,
                ).pack(anchor="w", padx=16, pady=(2, 8))

    def _on_fix_issue(self, photo) -> None:
        self.ctx.last_photo = photo
        self.navigate_fn("review")

    def _on_rerun_validation(self) -> None:
        """Re-runs validation across all photos in active session."""
        if not self.ctx.active_session or not self.ctx.photo_repo:
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        for photo in photos:
            self.ctx.validate_photo(photo.id)

        self.refresh()
