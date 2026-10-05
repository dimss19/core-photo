"""Dashboard Screen (PRD Section 5.3 & 6).
Provides high-level system overview, quick action cards, and camera status.
"""

from typing import Callable, Optional
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger

logger = get_logger(__name__)


class DashboardView(ctk.CTkFrame):
    """Main dashboard overview screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Title
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="Core Photo Dashboard",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Sistem Pengambilan Foto Drill Core Terstruktur & Otomatis",
            font=ctk.CTkFont(size=14),
            text_color="gray70"
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Status Cards Grid
        self.status_container = ctk.CTkFrame(self, fg_color="transparent")
        self.status_container.grid(row=1, column=0, sticky="ew", padx=24, pady=10)
        self.status_container.grid_columnconfigure((0, 1, 2), weight=1)

        # 1. Camera Card
        self.cam_card = ctk.CTkFrame(self.status_container, corner_radius=12)
        self.cam_card.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(self.cam_card, text="Status Kamera", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        self.cam_status_lbl = ctk.CTkLabel(self.cam_card, text="Mengecek...", font=ctk.CTkFont(size=13), text_color="#3B8ED0")
        self.cam_status_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # 2. Session Card
        self.session_card = ctk.CTkFrame(self.status_container, corner_radius=12)
        self.session_card.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(self.session_card, text="Sesi Saat Ini", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        self.session_status_lbl = ctk.CTkLabel(self.session_card, text="Belum ada sesi", font=ctk.CTkFont(size=13), text_color="gray70")
        self.session_status_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # 3. Storage Card
        self.storage_card = ctk.CTkFrame(self.status_container, corner_radius=12)
        self.storage_card.grid(row=0, column=2, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(self.storage_card, text="Penyimpanan", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        self.storage_status_lbl = ctk.CTkLabel(self.storage_card, text="Memeriksa...", font=ctk.CTkFont(size=13), text_color="gray70")
        self.storage_status_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # Action & Stats Area
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=10)
        content_frame.grid_columnconfigure(0, weight=3)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)

        # Quick Actions
        actions_panel = ctk.CTkFrame(content_frame, corner_radius=12)
        actions_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=6)

        ctk.CTkLabel(
            actions_panel,
            text="Menu Utama",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(16, 12))

        self.btn_capture = ctk.CTkButton(
            actions_panel,
            text="📷  Mulai Pengambilan Foto (Capture)",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            command=lambda: self.navigate_fn("capture")
        )
        self.btn_capture.pack(fill="x", padx=20, pady=8)

        btn_session = ctk.CTkButton(
            actions_panel,
            text="📁  Kelola Sesi (New / Continue Session)",
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#2B2B2B",
            hover_color="#3A3A3A",
            command=lambda: self.navigate_fn("session")
        )
        btn_session.pack(fill="x", padx=20, pady=8)

        btn_browser = ctk.CTkButton(
            actions_panel,
            text="🔍  Buka Photo Browser",
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#2B2B2B",
            hover_color="#3A3A3A",
            command=lambda: self.navigate_fn("browser")
        )
        btn_browser.pack(fill="x", padx=20, pady=8)

        btn_transfer = ctk.CTkButton(
            actions_panel,
            text="📤  Transfer Data ke Server",
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#2B2B2B",
            hover_color="#3A3A3A",
            command=lambda: self.navigate_fn("transfer")
        )
        btn_transfer.pack(fill="x", padx=20, pady=8)

        # Quick Stats Panel
        stats_panel = ctk.CTkFrame(content_frame, corner_radius=12)
        stats_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=6)

        ctk.CTkLabel(
            stats_panel,
            text="Statistik Sesi",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(16, 12))

        self.stat_photos_lbl = ctk.CTkLabel(stats_panel, text="Total Foto: 0", font=ctk.CTkFont(size=14))
        self.stat_photos_lbl.pack(anchor="w", padx=20, pady=6)

        self.stat_valid_lbl = ctk.CTkLabel(stats_panel, text="Tervalidasi: 0", font=ctk.CTkFont(size=14), text_color="#2CC985")
        self.stat_valid_lbl.pack(anchor="w", padx=20, pady=6)

        self.stat_pending_lbl = ctk.CTkLabel(stats_panel, text="Siap Transfer: 0", font=ctk.CTkFont(size=14), text_color="#E5A93C")
        self.stat_pending_lbl.pack(anchor="w", padx=20, pady=6)

    def refresh(self) -> None:
        """Refreshes status indicators and statistics."""
        # 1. Camera Status
        cam_summary = self.ctx.camera_manager.get_status_summary()
        self.cam_status_lbl.configure(text=cam_summary)
        if self.ctx.camera_manager.is_ready():
            self.cam_status_lbl.configure(text_color="#2CC985")
        else:
            self.cam_status_lbl.configure(text_color="#D9534F")

        # 2. Session Status
        sess = self.ctx.active_session
        if sess:
            self.session_status_lbl.configure(
                text=f"{sess.site} ({sess.date})\nOp: {sess.operator}",
                text_color="#E0E0E0"
            )
        else:
            self.session_status_lbl.configure(
                text="Tidak ada sesi aktif.\nKlik 'Kelola Sesi' untuk memulai.",
                text_color="#E5A93C"
            )

        # 3. Storage
        free_mb = self.ctx.storage_manager.get_available_space_mb()
        free_gb = free_mb / 1024.0
        self.storage_status_lbl.configure(
            text=f"{free_gb:.1f} GB Bebas",
            text_color="#2CC985" if free_gb > 1.0 else "#D9534F"
        )

        # 4. Stats
        if sess and self.ctx.photo_repo:
            photos = self.ctx.photo_repo.list_by_session(sess.id, active_only=True)
            total = len(photos)
            valid = sum(1 for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFERRED"))
            ready = sum(1 for p in photos if p.status in ("VALID", "PROCESSED"))
            self.stat_photos_lbl.configure(text=f"Total Foto: {total}")
            self.stat_valid_lbl.configure(text=f"Tervalidasi: {valid}")
            self.stat_pending_lbl.configure(text=f"Siap Transfer: {ready}")
        else:
            self.stat_photos_lbl.configure(text="Total Foto: 0")
            self.stat_valid_lbl.configure(text="Tervalidasi: 0")
            self.stat_pending_lbl.configure(text="Siap Transfer: 0")
