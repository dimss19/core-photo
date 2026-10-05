"""Transfer UI Screen (PRD Section 22, 23 & 24).
Provides server settings, connectivity testing, transfer queue execution,
and progress monitoring with offline tolerance.
Designed with Light Mode aesthetics, clear field guides, and activity log.
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
        super().__init__(master, fg_color="#F8FAFC", **kwargs)
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

        # ----------------- Header -----------------
        header = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=(14, 12))

        ctk.CTkLabel(
            title_box,
            text="📤 Transfer Data ke Server Pusat",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Kirim file foto drill core (RAW & JPG) beserta berkas metadata JSON ke server pusat. Seluruh file asli tetap tersimpan aman di disk lokal.",
            font=ctk.CTkFont(size=12),
            text_color="#64748B",
            wraplength=950,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # ----------------- Left: Server Configuration -----------------
        cfg_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        cfg_card.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 10))

        ctk.CTkLabel(
            cfg_card,
            text="Konfigurasi Server Tujuan",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=16, pady=(14, 2))

        ctk.CTkLabel(
            cfg_card,
            text="Tentukan alamat endpoint REST API server pusat.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Server URL
        ctk.CTkLabel(cfg_card, text="URL Endpoint Server *", font=ctk.CTkFont(size=12, weight="bold"), text_color="#334155").pack(anchor="w", padx=16, pady=(2, 1))
        server_url = self.ctx.config_manager.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
        self.entry_url = ctk.CTkEntry(
            cfg_card,
            placeholder_text="Contoh: https://core-api.perusahaan.com/api/v1",
            height=36,
            fg_color="#F8FAFC",
            border_color="#CBD5E1"
        )
        self.entry_url.insert(0, server_url)
        self.entry_url.pack(fill="x", padx=16, pady=(0, 2))
        ctk.CTkLabel(cfg_card, text="Pastikan koneksi internet atau LAN terhubung ke host server.", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w", padx=16, pady=(0, 8))

        # API Key
        ctk.CTkLabel(cfg_card, text="API Key / Auth Token (Opsional):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#334155").pack(anchor="w", padx=16, pady=(2, 1))
        api_key = self.ctx.config_manager.get("transfer", "api_key", "")
        self.entry_key = ctk.CTkEntry(
            cfg_card,
            placeholder_text="Masukkan API key jika diperlukan otorisasi",
            height=36,
            show="*",
            fg_color="#F8FAFC",
            border_color="#CBD5E1"
        )
        self.entry_key.insert(0, api_key)
        self.entry_key.pack(fill="x", padx=16, pady=(0, 2))
        ctk.CTkLabel(cfg_card, text="Token autentikasi Bearer header.", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w", padx=16, pady=(0, 12))

        # Button Row
        btn_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=2)
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_save_cfg = ctk.CTkButton(
            btn_row,
            text="Simpan Pengaturan",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=6,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            command=self._on_save_config
        )
        self.btn_save_cfg.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_test_conn = ctk.CTkButton(
            btn_row,
            text="Uji Koneksi Server",
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=6,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            command=self._on_test_connection
        )
        self.btn_test_conn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.conn_feedback_lbl = ctk.CTkLabel(cfg_card, text="", font=ctk.CTkFont(size=12, weight="bold"), wraplength=340)
        self.conn_feedback_lbl.pack(anchor="w", padx=16, pady=(8, 12))

        # ----------------- Right: Transfer Execution & Progress -----------------
        exec_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        exec_card.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 10))

        ctk.CTkLabel(
            exec_card,
            text="Antrean Transfer Sesi Aktif",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=16, pady=(14, 2))

        ctk.CTkLabel(
            exec_card,
            text="Proses upload batch foto yang telah tervalidasi.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        self.queue_info_lbl = ctk.CTkLabel(
            exec_card,
            text="Memeriksa antrean foto...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1E293B"
        )
        self.queue_info_lbl.pack(anchor="w", padx=16, pady=4)

        self.progress_bar = ctk.CTkProgressBar(exec_card, height=14, corner_radius=7, fg_color="#F1F5F9", progress_color="#059669")
        self.progress_bar.pack(fill="x", padx=16, pady=(10, 6))
        self.progress_bar.set(0)

        self.btn_start_transfer = ctk.CTkButton(
            exec_card,
            text="📤  Mulai Transfer Seluruh Foto",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            corner_radius=8,
            fg_color="#059669",
            hover_color="#047857",
            command=self._on_start_transfer
        )
        self.btn_start_transfer.pack(fill="x", padx=16, pady=(10, 6))

        ctk.CTkLabel(
            exec_card,
            text="💡 Pengiriman bersifat idempoten: foto yang sudah berhasil dikirim tidak akan diunggah ulang.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=340,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # ----------------- Bottom: Transfer Log -----------------
        log_panel = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        log_panel.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 16))
        log_panel.grid_rowconfigure(1, weight=1)
        log_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_panel,
            text="Log Aktivitas Pengunggahan (Real-time Uploader Log)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1E293B"
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(10, 4))

        self.log_textbox = ctk.CTkTextbox(
            log_panel,
            height=140,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#F8FAFC",
            border_width=1,
            border_color="#E2E8F0",
            text_color="#334155"
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))

    def refresh(self) -> None:
        """Refreshes queue stats."""
        self.uploader.photo_repo = self.ctx.photo_repo
        self.uploader.transfer_repo = self.ctx.transfer_repo

        if not self.ctx.active_session or not self.ctx.photo_repo:
            self.queue_info_lbl.configure(text="Belum ada sesi aktif.")
            self.btn_start_transfer.configure(state="disabled", fg_color="#94A3B8")
            return

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        pending = [p for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFER_FAILED")]
        transferred = [p for p in photos if p.status == "TRANSFERRED"]

        self.queue_info_lbl.configure(
            text=f"Total: {len(photos)} Foto  |  Menunggu Unggah: {len(pending)}  |  Terkirim: {len(transferred)}"
        )
        if pending:
            self.btn_start_transfer.configure(state="normal", fg_color="#059669")
        else:
            self.btn_start_transfer.configure(state="disabled", fg_color="#94A3B8")

    def _append_log(self, text: str) -> None:
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")

    def _on_save_config(self) -> None:
        url = self.entry_url.get().strip()
        key = self.entry_key.get().strip()

        self.ctx.config_manager.set("transfer", "server_url", url, auto_save=False)
        self.ctx.config_manager.set("transfer", "api_key", key, auto_save=True)
        self.conn_feedback_lbl.configure(text="✅ Pengaturan server berhasil disimpan.", text_color="#059669")

    def _on_test_connection(self) -> None:
        url = self.entry_url.get().strip()
        self.conn_feedback_lbl.configure(text="Menguji koneksi ke server...", text_color="#1D4ED8")

        def test_task():
            ok, msg = self.uploader.check_server_connectivity(url)
            color = "#059669" if ok else "#DC2626"
            self.after(0, lambda: self.conn_feedback_lbl.configure(text=msg, text_color=color))

        threading.Thread(target=test_task, daemon=True).start()

    def _on_start_transfer(self) -> None:
        if self._is_transferring or not self.ctx.active_session or not self.ctx.photo_repo:
            return

        self._is_transferring = True
        self.btn_start_transfer.configure(state="disabled", text="Sedang mentransfer...", fg_color="#94A3B8")
        self.progress_bar.set(0)

        photos = self.ctx.photo_repo.list_by_session(self.ctx.active_session.id, active_only=True)
        pending = [p for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFER_FAILED")]

        if not pending:
            self._append_log("Tidak ada foto yang perlu ditransfer.")
            self._is_transferring = False
            self.btn_start_transfer.configure(state="normal", text="📤  Mulai Transfer Seluruh Foto", fg_color="#059669")
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
        self.btn_start_transfer.configure(state="normal", text="📤  Mulai Transfer Seluruh Foto", fg_color="#059669")
        self.refresh()
