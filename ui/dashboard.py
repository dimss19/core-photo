"""Dashboard Screen (PRD Section 5.3 & 6).
Provides high-level system overview, workflow guide, quick action cards, and camera status.
Optimized for clean, intuitive Light Mode design with supporting instructions.
"""

from typing import Callable, Optional
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger

logger = get_logger(__name__)


class DashboardView(ctk.CTkFrame):
    """Main dashboard overview screen with guided workflow."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color="#F8FAFC", **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ----------------- 1. Hero & Guided Step Indicator -----------------
        hero_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        hero_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))
        hero_frame.grid_columnconfigure(0, weight=1)

        # Title & Welcome
        title_box = ctk.CTkFrame(hero_frame, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=(16, 6))

        title = ctk.CTkLabel(
            title_box,
            text="Core Photo — Alur Kerja Lapangan",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#1E293B"
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Sistem foto drill core otomatis dengan validasi data 10-titik dan pengarsipan aman.",
            font=ctk.CTkFont(size=13),
            text_color="#64748B"
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Workflow Steps Bar
        steps_container = ctk.CTkFrame(hero_frame, fg_color="#F1F5F9", corner_radius=8)
        steps_container.pack(fill="x", padx=20, pady=(8, 16))
        steps_container.grid_columnconfigure((0, 1, 2, 3), weight=1)

        steps = [
            ("1. Sesi Foto", "Tentukan Site & Operator", "#1D4ED8"),
            ("2. Ambil Foto", "Framing & Capture RAW", "#0284C7"),
            ("3. Review Foto", "Periksa & Validasi Tray", "#059669"),
            ("4. Transfer Data", "Kirim ke Server Pusat", "#7C3AED"),
        ]

        for idx, (step_title, step_desc, step_color) in enumerate(steps):
            col_frame = ctk.CTkFrame(steps_container, fg_color="transparent")
            col_frame.grid(row=0, column=idx, padx=12, pady=10, sticky="ew")

            st_lbl = ctk.CTkLabel(
                col_frame,
                text=step_title,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=step_color
            )
            st_lbl.pack(anchor="w")

            sd_lbl = ctk.CTkLabel(
                col_frame,
                text=step_desc,
                font=ctk.CTkFont(size=11),
                text_color="#64748B"
            )
            sd_lbl.pack(anchor="w")

        # ----------------- 2. Status Overview Cards -----------------
        self.status_container = ctk.CTkFrame(self, fg_color="transparent")
        self.status_container.grid(row=1, column=0, sticky="ew", padx=20, pady=6)
        self.status_container.grid_columnconfigure((0, 1, 2), weight=1)

        # Card 1: Camera Status
        self.cam_card = ctk.CTkFrame(self.status_container, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E2E8F0")
        self.cam_card.grid(row=0, column=0, sticky="nsew", padx=6, pady=4)

        ctk.CTkLabel(self.cam_card, text="📷 Status Kamera", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1E293B").pack(anchor="w", padx=16, pady=(12, 4))
        self.cam_status_lbl = ctk.CTkLabel(self.cam_card, text="Mengecek koneksi...", font=ctk.CTkFont(size=13, weight="bold"), text_color="#0284C7")
        self.cam_status_lbl.pack(anchor="w", padx=16, pady=(0, 2))
        self.cam_sub_lbl = ctk.CTkLabel(self.cam_card, text="Webcam / USB Camera", font=ctk.CTkFont(size=11), text_color="#64748B")
        self.cam_sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # Card 2: Active Session
        self.session_card = ctk.CTkFrame(self.status_container, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E2E8F0")
        self.session_card.grid(row=0, column=1, sticky="nsew", padx=6, pady=4)

        ctk.CTkLabel(self.session_card, text="📁 Sesi Aktif", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1E293B").pack(anchor="w", padx=16, pady=(12, 4))
        self.session_status_lbl = ctk.CTkLabel(self.session_card, text="Belum ada sesi", font=ctk.CTkFont(size=13, weight="bold"), text_color="#D97706")
        self.session_status_lbl.pack(anchor="w", padx=16, pady=(0, 2))
        self.session_sub_lbl = ctk.CTkLabel(self.session_card, text="Buat sesi baru untuk mulai", font=ctk.CTkFont(size=11), text_color="#64748B")
        self.session_sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # Card 3: Storage Health
        self.storage_card = ctk.CTkFrame(self.status_container, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E2E8F0")
        self.storage_card.grid(row=0, column=2, sticky="nsew", padx=6, pady=4)

        ctk.CTkLabel(self.storage_card, text="💾 Penyimpanan Lokal", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1E293B").pack(anchor="w", padx=16, pady=(12, 4))
        self.storage_status_lbl = ctk.CTkLabel(self.storage_card, text="Memeriksa...", font=ctk.CTkFont(size=13, weight="bold"), text_color="#059669")
        self.storage_status_lbl.pack(anchor="w", padx=16, pady=(0, 2))
        self.storage_sub_lbl = ctk.CTkLabel(self.storage_card, text="Format folder terstandarisasi", font=ctk.CTkFont(size=11), text_color="#64748B")
        self.storage_sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # ----------------- 3. Action Panel & Session Stats -----------------
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(6, 16))
        content_frame.grid_columnconfigure(0, weight=3)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)

        # Quick Actions (Left)
        actions_panel = ctk.CTkFrame(content_frame, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        actions_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=6)

        ctk.CTkLabel(
            actions_panel,
            text="Aksi Langsung",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            actions_panel,
            text="Pilih menu utama di bawah untuk melanjutkan aktivitas kerja Anda:",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).pack(anchor="w", padx=20, pady=(0, 12))

        # Context-Aware Primary Action Button
        self.primary_cta_btn = ctk.CTkButton(
            actions_panel,
            text="📁  Mulai Sesi Baru Terlebih Dahulu",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            corner_radius=8,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            command=self._on_primary_cta_click
        )
        self.primary_cta_btn.pack(fill="x", padx=20, pady=(4, 2))

        self.primary_cta_hint = ctk.CTkLabel(
            actions_panel,
            text="💡 Anda harus membuat atau memilih sesi foto aktif sebelum mengambil foto.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        self.primary_cta_hint.pack(anchor="w", padx=20, pady=(0, 10))

        # Secondary Actions
        btn_session = ctk.CTkButton(
            actions_panel,
            text="📁  Kelola Sesi (Ganti atau Buka Sesi Tersimpan)",
            font=ctk.CTkFont(size=13, weight="normal"),
            height=38,
            corner_radius=8,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            command=lambda: self.navigate_fn("session")
        )
        btn_session.pack(fill="x", padx=20, pady=4)

        btn_browser = ctk.CTkButton(
            actions_panel,
            text="🔍  Buka Photo Browser (Galeri & Filter Hole ID)",
            font=ctk.CTkFont(size=13, weight="normal"),
            height=38,
            corner_radius=8,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            command=lambda: self.navigate_fn("browser")
        )
        btn_browser.pack(fill="x", padx=20, pady=4)

        btn_transfer = ctk.CTkButton(
            actions_panel,
            text="📤  Transfer Data ke Server (Upload Batch)",
            font=ctk.CTkFont(size=13, weight="normal"),
            height=38,
            corner_radius=8,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            command=lambda: self.navigate_fn("transfer")
        )
        btn_transfer.pack(fill="x", padx=20, pady=4)

        # Quick Stats Panel (Right)
        stats_panel = ctk.CTkFrame(content_frame, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        stats_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=6)

        ctk.CTkLabel(
            stats_panel,
            text="Statistik Sesi Aktif",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            stats_panel,
            text="Ringkasan foto dan status verifikasi:",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).pack(anchor="w", padx=20, pady=(0, 12))

        # Stat Items in Light Cards
        stat_box = ctk.CTkFrame(stats_panel, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color="#E2E8F0")
        stat_box.pack(fill="x", padx=20, pady=6)

        self.stat_photos_lbl = ctk.CTkLabel(stat_box, text="Total Foto: 0 Tray", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1E293B")
        self.stat_photos_lbl.pack(anchor="w", padx=16, pady=(10, 4))

        self.stat_valid_lbl = ctk.CTkLabel(stat_box, text="✅ Tervalidasi Penuh: 0", font=ctk.CTkFont(size=13), text_color="#059669")
        self.stat_valid_lbl.pack(anchor="w", padx=16, pady=2)

        self.stat_pending_lbl = ctk.CTkLabel(stat_box, text="⏳ Siap Dikirim: 0", font=ctk.CTkFont(size=13), text_color="#D97706")
        self.stat_pending_lbl.pack(anchor="w", padx=16, pady=(2, 10))

        # Quick Info Tip
        tip_frame = ctk.CTkFrame(stats_panel, fg_color="#EFF6FF", corner_radius=8, border_width=1, border_color="#BFDBFE")
        tip_frame.pack(fill="x", padx=20, pady=(12, 16))

        ctk.CTkLabel(
            tip_frame,
            text="Petunjuk Singkat:\nSetiap kali selesai mengambil foto, sistem otomatis memotong ke rasio standar 300x200 dan menghitung hash integritas MD5.",
            font=ctk.CTkFont(size=11),
            text_color="#1E40AF",
            justify="left",
            wraplength=260
        ).pack(padx=12, pady=10)

    def _on_primary_cta_click(self) -> None:
        if self.ctx.active_session:
            self.navigate_fn("capture")
        else:
            self.navigate_fn("session")

    def refresh(self) -> None:
        """Refreshes status indicators and statistics in Light Mode."""
        # 1. Camera Status
        cam_ready = self.ctx.camera_manager.is_ready()
        cam_summary = self.ctx.camera_manager.get_status_summary()
        self.cam_status_lbl.configure(
            text=cam_summary,
            text_color="#059669" if cam_ready else "#D97706"
        )
        self.cam_sub_lbl.configure(
            text="Kamera siap untuk capture" if cam_ready else "Hubungkan webcam melalui USB"
        )

        # 2. Session Status & Primary CTA Configuration
        sess = self.ctx.active_session
        if sess:
            self.session_status_lbl.configure(
                text=f"{sess.site} ({sess.date})",
                text_color="#047857"
            )
            self.session_sub_lbl.configure(
                text=f"Operator: {sess.operator}"
            )
            self.primary_cta_btn.configure(
                text="📷  Lanjutkan Pengambilan Foto (Capture)",
                fg_color="#059669",
                hover_color="#047857"
            )
            self.primary_cta_hint.configure(
                text=f"Sesi aktif terpasang: {sess.id}. Klik untuk mengambil tray foto berikutnya.",
                text_color="#047857"
            )
        else:
            self.session_status_lbl.configure(
                text="Belum ada sesi aktif",
                text_color="#D97706"
            )
            self.session_sub_lbl.configure(
                text="Klik tombol aksi untuk membuat sesi"
            )
            self.primary_cta_btn.configure(
                text="📁  1. Buat Sesi Baru Terlebih Dahulu",
                fg_color="#1D4ED8",
                hover_color="#1E40AF"
            )
            self.primary_cta_hint.configure(
                text="Langkah 1: Tentukan lokasi pit/site dan nama operator untuk memulai.",
                text_color="#64748B"
            )

        # 3. Storage
        free_mb = self.ctx.storage_manager.get_available_space_mb()
        free_gb = free_mb / 1024.0
        self.storage_status_lbl.configure(
            text=f"{free_gb:.1f} GB Bebas",
            text_color="#059669" if free_gb > 1.0 else "#DC2626"
        )
        self.storage_sub_lbl.configure(
            text="Ruang disk lokal mencukupi" if free_gb > 1.0 else "PERINGATAN: Ruang disk menipis!"
        )

        # 4. Stats
        if sess and self.ctx.photo_repo:
            photos = self.ctx.photo_repo.list_by_session(sess.id, active_only=True)
            total = len(photos)
            valid = sum(1 for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFERRED"))
            ready = sum(1 for p in photos if p.status in ("VALID", "PROCESSED"))
            self.stat_photos_lbl.configure(text=f"Total Foto: {total} Tray")
            self.stat_valid_lbl.configure(text=f"✅ Tervalidasi Penuh: {valid}")
            self.stat_pending_lbl.configure(text=f"⏳ Siap Dikirim: {ready}")
        else:
            self.stat_photos_lbl.configure(text="Total Foto: 0 Tray")
            self.stat_valid_lbl.configure(text="✅ Tervalidasi Penuh: 0")
            self.stat_pending_lbl.configure(text="⏳ Siap Dikirim: 0")
