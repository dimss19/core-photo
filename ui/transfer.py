"""Transfer UI Screen (PRD Section 22, 23 & 24).
Provides server settings, connectivity testing, transfer queue execution,
and progress monitoring with offline tolerance.
"""

import threading
from typing import Callable, List
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from transfer.uploader import TransferUploader

logger = get_logger(__name__)


class TransferView(ctk.CTkFrame):
    """Data transfer orchestration screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self.uploader = TransferUploader(
            photo_repo=self.ctx.photo_repo,
            transfer_repo=self.ctx.transfer_repo
        )
        self._is_transferring = False

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 10))

        title = ctk.CTkLabel(header, text="Transfer Data ke Server", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Kirim foto drill core dan metadata ke server pusat. Seluruh file tetap tersimpan aman di disk lokal.",
            font=ctk.CTkFont(size=13),
            text_color="gray70"
        )
        subtitle.pack(anchor="w", pady=(2, 6))

        # ----------------- Left: Server Configuration -----------------
        cfg_card = ctk.CTkFrame(self, corner_radius=12)
        cfg_card.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=10)

        ctk.CTkLabel(cfg_card, text="Konfigurasi Server Tujuan", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(14, 10))

        ctk.CTkLabel(cfg_card, text="URL Endpoint Server:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=16, pady=(4, 2))
        server_url = self.ctx.config_manager.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
        self.entry_url = ctk.CTkEntry(cfg_card, height=36)
        self.entry_url.insert(0, server_url)
        self.entry_url.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(cfg_card, text="API Key / Auth Token (Opsional):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=16, pady=(4, 2))
        api_key = self.ctx.config_manager.get("transfer", "api_key", "")
        self.entry_key = ctk.CTkEntry(cfg_card, placeholder_text="Masukkan API key jika diperlukan", height=36, show="*")
        self.entry_key.insert(0, api_key)
        self.entry_key.pack(fill="x", padx=16, pady=(0, 14))

        btn_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=4)
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_save_cfg = ctk.CTkButton(btn_row, text="Simpan Pengaturan", height=36, command=self._on_save_config)
        self.btn_save_cfg.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_test_conn = ctk.CTkButton(
            btn_row,
            text="Uji Koneksi Server",
            height=36,
            fg_color="#333333",
            hover_color="#444444",
            command=self._on_test_connection
        )
        self.btn_test_conn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.conn_feedback_lbl = ctk.CTkLabel(cfg_card, text="", font=ctk.CTkFont(size=12), wraplength=340)
        self.conn_feedback_lbl.pack(anchor="w", padx=16, pady=(8, 12))

        # ----------------- Right: Transfer Execution & Progress -----------------
        exec_card = ctk.CTkFrame(self, corner_radius=12)
        exec_card.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=10)

        ctk.CTkLabel(exec_card, text="Antrean Transfer Sesi", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(14, 10))

        self.queue_info_lbl = ctk.CTkLabel(exec_card, text="Memeriksa foto...", font=ctk.CTkFont(size=13))
        self.queue_info_lbl.pack(anchor="w", padx=16, pady=4)

        self.progress_bar = ctk.CTkProgressBar(exec_card, height=12)
        self.progress_bar.pack(fill="x", padx=16, pady=(12, 6))
        self.progress_bar.set(0)

        self.btn_start_transfer = ctk.CTkButton(
            exec_card,
            text="📤  Mulai Transfer Seluruh Foto",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color="#2CC985",
            hover_color="#229965",
            command=self._on_start_transfer
        )
        self.btn_start_transfer.pack(fill="x", padx=16, pady=(10, 14))

        # ----------------- Bottom: Transfer Log -----------------
        log_panel = ctk.CTkFrame(self, corner_radius=12)
        log_panel.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=24, pady=(10, 20))
        log_panel.grid_rowconfigure(1, weight=1)
        log_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_panel, text="Log Aktivitas Transfer", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(10, 4))

        self.log_textbox = ctk.CTkTextbox(log_panel, height=140, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))

    def refresh(self) -> None:
        """Refreshes queue stats."""
        self.uploader.photo_repo = self.ctx.photo_repo
        self.uploader.transfer_repo = self.ctx.transfer_repo

        if not self.ctx.active_session or not self.ctx.photo_repo:
            self.queue_info_lbl.configure(text="Tidak ada sesi aktif.")
            self.btn_start_transfer.configure(state="disabled")
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        pending = [p for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFER_FAILED")]
        transferred = [p for p in photos if p.status == "TRANSFERRED"]

        self.queue_info_lbl.configure(
            text=f"Total: {len(photos)} Foto | Menunggu: {len(pending)} | Terkirim: {len(transferred)}"
        )
        self.btn_start_transfer.configure(state="normal" if pending else "disabled")

    def _append_log(self, text: str) -> None:
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")

    def _on_save_config(self) -> None:
        url = self.entry_url.get().strip()
        key = self.entry_key.get().strip()

        self.ctx.config_manager.set("transfer", "server_url", url, auto_save=False)
        self.ctx.config_manager.set("transfer", "api_key", key, auto_save=True)
        self.conn_feedback_lbl.configure(text="Pengaturan server berhasil disimpan.", text_color="#2CC985")

    def _on_test_connection(self) -> None:
        url = self.entry_url.get().strip()
        self.conn_feedback_lbl.configure(text="Menguji koneksi ke server...", text_color="#3B8ED0")

        def test_task():
            ok, msg = self.uploader.check_server_connectivity(url)
            color = "#2CC985" if ok else "#E5A93C"
            self.after(0, lambda: self.conn_feedback_lbl.configure(text=msg, text_color=color))

        threading.Thread(target=test_task, daemon=True).start()

    def _on_start_transfer(self) -> None:
        if self._is_transferring or not self.ctx.active_session or not self.ctx.photo_repo:
            return

        self._is_transferring = True
        self.btn_start_transfer.configure(state="disabled", text="Sedang mentransfer...")
        self.progress_bar.set(0)

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        pending = [p for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFER_FAILED")]

        if not pending:
            self._append_log("Tidak ada foto yang perlu ditransfer.")
            self._is_transferring = False
            self.btn_start_transfer.configure(state="normal", text="📤  Mulai Transfer Seluruh Foto")
            return

        def transfer_worker():
            total = len(pending)
            self._append_log(f"--- Memulai proses transfer {total} foto ke {self.entry_url.get().strip()} ---")

            success_count = 0
            for idx, photo in enumerate(pending):
                self._append_log(f"Mengunggah [{idx+1}/{total}]: {photo.filename_base}...")
                ok, msg = self.uploader.upload_photo(photo, server_url=self.entry_url.get().strip())
                if ok:
                    success_count += 1
                    self._append_log(f"  -> Sukses: {msg}")
                else:
                    self._append_log(f"  -> Gagal: {msg}")

                progress = (idx + 1) / total
                self.after(0, lambda p=progress: self.progress_bar.set(p))

            self._append_log(f"--- Selesai: {success_count}/{total} foto berhasil diunggah ---")
            self.after(0, self._on_transfer_done)

        threading.Thread(target=transfer_worker, daemon=True).start()

    def _on_transfer_done(self) -> None:
        self._is_transferring = False
        self.btn_start_transfer.configure(state="normal", text="📤  Mulai Transfer Seluruh Foto")
        self.refresh()
