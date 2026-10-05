"""Transfer UI Screen (Professional Industrial Redesign).
Provides server configuration, connectivity testing, idempotent batch uploads,
and progress monitoring with offline tolerance. Local archives are never deleted.
Zero emojis, strict professional standards.
"""

import threading
from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from transfer.uploader import TransferUploader
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


class TransferView(ctk.CTkFrame):
    """Data transfer orchestration screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self.uploader = TransferUploader(
            photo_repo=self.ctx.photo_repo,
            transfer_repo=self.ctx.transfer_repo,
        )
        self._is_transferring = False

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ----------------- Header -----------------
        header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            title_box,
            text="CENTRAL SERVER DATA TRANSFER",
            font=get_font(16, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Synchronize validated drill core archives (RAW, JPG, metadata JSON) to central server. Local files are never deleted.",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # ----------------- Left: Server Configuration -----------------
        cfg_card = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        cfg_card.grid(row=1, column=0, sticky="nsew", padx=(24, 8), pady=(0, 10))

        ctk.CTkLabel(
            cfg_card,
            text="SERVER ENDPOINT SETTINGS",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=18, pady=(16, 2))

        ctk.CTkLabel(
            cfg_card,
            text="Configure central repository REST API destination.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(0, 10))

        # Server URL
        ctk.CTkLabel(cfg_card, text="Server API URL *", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(2, 1))
        server_url = self.ctx.config_manager.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
        self.entry_url = ctk.CTkEntry(
            cfg_card,
            placeholder_text="http://127.0.0.1:8000/api/v1",
            height=34,
            font=get_font(12),
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.entry_url.insert(0, server_url)
        self.entry_url.pack(fill="x", padx=18, pady=(0, 6))

        # API Key
        ctk.CTkLabel(cfg_card, text="Bearer Auth Token / API Key (Optional)", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(2, 1))
        api_key = self.ctx.config_manager.get("transfer", "api_key", "")
        self.entry_key = ctk.CTkEntry(
            cfg_card,
            placeholder_text="Optional authorization token",
            height=34,
            font=get_font(12),
            show="*",
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.entry_key.insert(0, api_key)
        self.entry_key.pack(fill="x", padx=18, pady=(0, 10))

        # Button Row
        btn_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=2)
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_save_cfg = ctk.CTkButton(
            btn_row,
            text="Save Settings",
            font=get_font(11, "bold"),
            height=34,
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            hover_color="#27272A",
            text_color="#FFFFFF",
            command=self._on_save_config,
        )
        self.btn_save_cfg.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_test_conn = ctk.CTkButton(
            btn_row,
            text="Test Connection",
            font=get_font(11),
            height=34,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_test_connection,
        )
        self.btn_test_conn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.conn_feedback_lbl = ctk.CTkLabel(cfg_card, text="", font=get_font(11, "bold"), wraplength=340)
        self.conn_feedback_lbl.pack(anchor="w", padx=18, pady=(6, 12))

        # ----------------- Right: Transfer Execution & Status -----------------
        exec_card = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        exec_card.grid(row=1, column=1, sticky="nsew", padx=(8, 24), pady=(0, 10))

        ctk.CTkLabel(
            exec_card,
            text="TRANSFER BATCH QUEUE",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=18, pady=(16, 2))

        ctk.CTkLabel(
            exec_card,
            text="Transfer status: READY · UPLOADING · VERIFYING · TRANSFERRED",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(0, 10))

        # Queue Status Headline
        self.queue_info_lbl = ctk.CTkLabel(
            exec_card,
            text="Checking queue...",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        self.queue_info_lbl.pack(anchor="w", padx=18, pady=2)

        self.transfer_state_lbl = ctk.CTkLabel(
            exec_card,
            text="READY",
            font=get_font(11, "bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        self.transfer_state_lbl.pack(anchor="w", padx=18, pady=(0, 6))

        self.progress_bar = ctk.CTkProgressBar(
            exec_card,
            height=10,
            corner_radius=2,
            fg_color=COLOR_PANEL_ALT,
            progress_color=COLOR_ACCENT,
        )
        self.progress_bar.pack(fill="x", padx=18, pady=(4, 8))
        self.progress_bar.set(0)

        # Primary Orange [ TRANSFER ] Action
        self.btn_start_transfer = ctk.CTkButton(
            exec_card,
            text="TRANSFER PHOTOS",
            font=get_font(13, "bold"),
            height=44,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_start_transfer,
        )
        self.btn_start_transfer.pack(fill="x", padx=18, pady=(4, 6))

        ctk.CTkLabel(
            exec_card,
            text="Idempotent upload: successfully transferred photos are automatically skipped.",
            font=get_font(10),
            text_color=COLOR_TEXT_HINT,
            wraplength=340,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        # ----------------- Bottom: Transfer Log -----------------
        log_panel = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        log_panel.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=24, pady=(0, 20))
        log_panel.grid_rowconfigure(1, weight=1)
        log_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_panel,
            text="TRANSFER ACTIVITY LOG",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(12, 4))

        self.log_textbox = ctk.CTkTextbox(
            log_panel,
            height=130,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLOR_PANEL_ALT,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 14))

    def refresh(self) -> None:
        """Refreshes queue stats."""
        self.uploader.photo_repo = self.ctx.photo_repo
        self.uploader.transfer_repo = self.ctx.transfer_repo

        if not self.ctx.active_session or not self.ctx.photo_repo:
            self.queue_info_lbl.configure(text="No active session selected.")
            self.transfer_state_lbl.configure(text="SESSION REQUIRED", text_color=COLOR_WARNING)
            self.btn_start_transfer.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        pending = [p for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFER_FAILED")]
        transferred = [p for p in photos if p.status == "TRANSFERRED"]

        self.queue_info_lbl.configure(
            text=f"{len(pending)} photos ready to transfer ({len(transferred)} already synced)"
        )
        if pending:
            self.transfer_state_lbl.configure(text="READY", text_color=COLOR_SUCCESS)
            self.btn_start_transfer.configure(state="normal", fg_color=COLOR_ACCENT)
        else:
            self.transfer_state_lbl.configure(text="TRANSFERRED (ALL SYNCED)", text_color=COLOR_SUCCESS)
            self.btn_start_transfer.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)

    def _append_log(self, text: str) -> None:
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")

    def _on_save_config(self) -> None:
        url = self.entry_url.get().strip()
        key = self.entry_key.get().strip()

        self.ctx.config_manager.set("transfer", "server_url", url, auto_save=False)
        self.ctx.config_manager.set("transfer", "api_key", key, auto_save=True)
        self.conn_feedback_lbl.configure(text="✓ Server configuration saved.", text_color=COLOR_SUCCESS)

    def _on_test_connection(self) -> None:
        url = self.entry_url.get().strip()
        self.conn_feedback_lbl.configure(text="Testing server endpoint...", text_color=COLOR_TEXT_MUTED)

        def test_task():
            ok, msg = self.uploader.check_server_connectivity(url)
            color = COLOR_SUCCESS if ok else COLOR_ERROR
            prefix = "✓ " if ok else "✕ "
            self.after(0, lambda: self.conn_feedback_lbl.configure(text=f"{prefix}{msg}", text_color=color))

        threading.Thread(target=test_task, daemon=True).start()

    def _on_start_transfer(self) -> None:
        if self._is_transferring or not self.ctx.active_session or not self.ctx.photo_repo:
            return

        self._is_transferring = True
        self.btn_start_transfer.configure(state="disabled", text="TRANSFERRING...", fg_color=COLOR_BORDER_STRONG)
        self.transfer_state_lbl.configure(text="UPLOADING", text_color=COLOR_ACCENT)
        self.progress_bar.set(0)

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        pending = [p for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFER_FAILED")]

        if not pending:
            self._append_log("No photos pending transfer.")
            self._is_transferring = False
            self.btn_start_transfer.configure(state="normal", text="TRANSFER PHOTOS", fg_color=COLOR_ACCENT)
            return

        def transfer_worker():
            total = len(pending)
            self._append_log(f"--- Transfer session started: {total} photos to {self.entry_url.get().strip()} ---")

            success_count = 0
            for idx, photo in enumerate(pending):
                self.after(
                    0,
                    lambda i=idx+1, t=total: self.transfer_state_lbl.configure(
                        text=f"Uploading {i} / {t}", text_color=COLOR_ACCENT
                    ),
                )
                self._append_log(f"Uploading [{idx+1}/{total}]: {photo.filename_base}...")
                ok, msg = self.uploader.upload_photo(photo, server_url=self.entry_url.get().strip())
                if ok:
                    success_count += 1
                    self._append_log(f"  -> Success: {msg}")
                else:
                    self._append_log(f"  -> Error: {msg}")

                progress = (idx + 1) / total
                self.after(0, lambda p=progress: self.progress_bar.set(p))

            self._append_log(f"--- Completed: {success_count}/{total} photos synced ---")
            self.after(0, lambda: self._on_transfer_done(success_count, total))

        threading.Thread(target=transfer_worker, daemon=True).start()

    def _on_transfer_done(self, success: int, total: int) -> None:
        self._is_transferring = False
        self.btn_start_transfer.configure(state="normal", text="TRANSFER PHOTOS", fg_color=COLOR_ACCENT)
        if success == total:
            self.transfer_state_lbl.configure(text="✓ Transfer completed", text_color=COLOR_SUCCESS)
        else:
            self.transfer_state_lbl.configure(text=f"FAILED ({total - success} issues)", text_color=COLOR_ERROR)
        self.refresh()
