"""Main Desktop Application Entry Point for Core Photo (PRD Section 1, 5, 27 & 28).
Windows desktop application using CustomTkinter with clean navigation,
thread-safe camera management, and offline-first workflows.
"""

import sys
import tkinter as tk
from typing import Dict
import customtkinter as ctk

from config.config_manager import get_config
from core.app_context import get_app_context
from core.logger import get_logger, setup_logging
from ui.browser import BrowserView
from ui.capture import CaptureView
from ui.dashboard import DashboardView
from ui.review import ReviewView
from ui.session import SessionView
from ui.settings import SettingsView
from ui.transfer import TransferView
from ui.validation import ValidationView

logger = get_logger(__name__)


class CorePhotoApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.config = get_config()
        theme = self.config.get("app", "theme", "dark")
        color_theme = self.config.get("app", "color_theme", "blue")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Core Photo — Sistem Pengambilan Foto Drill Core")
        self.geometry("1300x820")
        self.minsize(1100, 700)

        # Set Application Window Icon (PRD Section 1 & UI Branding)
        from pathlib import Path
        from PIL import Image, ImageTk
        self.icon_dir = Path(__file__).parent / "assets"
        ico_file = self.icon_dir / "icon.ico"
        png_file = self.icon_dir / "icon.png"

        if ico_file.exists():
            try:
                self.iconbitmap(default=str(ico_file))
            except Exception as e:
                logger.debug("Failed setting iconbitmap: %s", e)
        if png_file.exists():
            try:
                self._app_icon_photo = ImageTk.PhotoImage(file=str(png_file))
                self.iconphoto(True, self._app_icon_photo)
            except Exception as e:
                logger.debug("Failed setting iconphoto: %s", e)

        self.ctx = get_app_context()
        self.current_view_name = "dashboard"
        self.views: Dict[str, ctk.CTkFrame] = {}

        self._build_layout()
        self._init_views()
        self.navigate_to("dashboard")

        # Automatically connect camera in background on startup (PRD Section 8)
        self.after(300, self._startup_camera_init)

        # Handle clean window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------- Top Header Bar (Light Mode) -----------------
        self.header_bar = ctk.CTkFrame(self, height=54, corner_radius=0, fg_color="#FFFFFF", border_width=1, border_color="#E5E7EB")
        self.header_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header_bar.grid_columnconfigure(1, weight=1)

        # Logo text & sub-badge
        logo_frame = ctk.CTkFrame(self.header_bar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=(16, 16), pady=8, sticky="w")

        # Display App Icon Image in Header
        png_file = self.icon_dir / "icon.png"
        if png_file.exists():
            try:
                from PIL import Image
                pil_logo = Image.open(png_file)
                self.logo_ctk_image = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(32, 32))
                self.logo_icon_lbl = ctk.CTkLabel(logo_frame, image=self.logo_ctk_image, text="")
                self.logo_icon_lbl.pack(side="left", padx=(0, 10))
            except Exception as e:
                logger.debug("Could not load header logo image: %s", e)

        self.logo_lbl = ctk.CTkLabel(
            logo_frame,
            text="CORE PHOTO",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#1E293B"
        )
        self.logo_lbl.pack(side="left")

        # Top System Status Indicators (Light mode contrast)
        status_frame = ctk.CTkFrame(self.header_bar, fg_color="transparent")
        status_frame.grid(row=0, column=1, sticky="e", padx=20)

        self.top_session_lbl = ctk.CTkLabel(
            status_frame,
            text="Sesi: [Belum Ada]",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#D97706"
        )
        self.top_session_lbl.pack(side="left", padx=10)

        self.top_cam_lbl = ctk.CTkLabel(
            status_frame,
            text="Kamera: Disconnected",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280"
        )
        self.top_cam_lbl.pack(side="left", padx=10)

        self.top_storage_lbl = ctk.CTkLabel(
            status_frame,
            text="Storage: OK",
            font=ctk.CTkFont(size=12),
            text_color="#059669"
        )
        self.top_storage_lbl.pack(side="left", padx=10)

        # ----------------- Left Navigation Sidebar (Light Mode) -----------------
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color="#F8FAFC", border_width=1, border_color="#E2E8F0")
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(20, weight=1)

        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        nav_groups = [
            ("ALUR KERJA UTAMA", [
                ("dashboard", "📊  Dashboard", "Halaman Utama & Status"),
                ("session", "📁  Sesi Foto", "Pilih / Buat Sesi Baru"),
                ("capture", "📷  Capture Foto", "Live View & Ambil Foto"),
                ("review", "👁️  Review Foto", "Inspeksi & Simpan Tray"),
            ]),
            ("DATA & DISTRIBUSI", [
                ("browser", "🔍  Photo Browser", "Galeri & Filter Foto"),
                ("validation", "✅  Validasi Data", "Audit & Integritas"),
                ("transfer", "📤  Transfer Server", "Kirim Data ke Server"),
                ("settings", "⚙️  Pengaturan", "Diagnostik & Recovery"),
            ])
        ]

        current_row = 0
        for group_title, items in nav_groups:
            grp_lbl = ctk.CTkLabel(
                self.sidebar,
                text=group_title,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#94A3B8"
            )
            grp_lbl.grid(row=current_row, column=0, padx=16, pady=(14 if current_row > 0 else 10, 4), sticky="w")
            current_row += 1

            for route, label, tooltip in items:
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=label,
                    anchor="w",
                    font=ctk.CTkFont(size=13, weight="normal"),
                    height=38,
                    corner_radius=8,
                    fg_color="transparent",
                    text_color="#334155",
                    hover_color="#E2E8F0",
                    command=lambda r=route: self.navigate_to(r)
                )
                btn.grid(row=current_row, column=0, padx=10, pady=2, sticky="ew")
                self.nav_buttons[route] = btn
                current_row += 1

        # Version stamp
        v_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        v_frame.grid(row=21, column=0, padx=12, pady=16, sticky="s")

        v_lbl = ctk.CTkLabel(
            v_frame,
            text="Core Photo v1.0.0\nOffline-Ready",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            justify="center"
        )
        v_lbl.pack()

        # ----------------- Main Content Area (Light Mode) -----------------
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="#F1F5F9")
        self.content_area.grid(row=1, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

    def _init_views(self) -> None:
        """Instantiates all application screen frames."""
        capture_view = CaptureView(self.content_area, navigate_fn=self.navigate_to)
        self.views["capture"] = capture_view

        self.views["dashboard"] = DashboardView(self.content_area, navigate_fn=self.navigate_to)
        self.views["session"] = SessionView(self.content_area, navigate_fn=self.navigate_to)
        self.views["review"] = ReviewView(
            self.content_area,
            navigate_fn=self.navigate_to,
            advance_tray_fn=capture_view.advance_to_next_tray
        )
        self.views["browser"] = BrowserView(self.content_area, navigate_fn=self.navigate_to)
        self.views["validation"] = ValidationView(self.content_area, navigate_fn=self.navigate_to)
        self.views["transfer"] = TransferView(self.content_area, navigate_fn=self.navigate_to)
        self.views["settings"] = SettingsView(self.content_area, navigate_fn=self.navigate_to)

    def navigate_to(self, route: str) -> None:
        """Navigates smoothly between screens."""
        logger.info("Navigating to view: %s", route)

        # Handle view lifecycle transitions
        if self.current_view_name == "capture" and route != "capture":
            self.views["capture"].stop_view()

        # Update button highlights for Light Mode
        for r, btn in self.nav_buttons.items():
            if r == route:
                btn.configure(fg_color="#EBF5FF", hover_color="#DBEAFE", text_color="#1D4ED8", font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", hover_color="#E2E8F0", text_color="#475569", font=ctk.CTkFont(size=13, weight="normal"))

        # Hide current view
        if self.current_view_name in self.views:
            self.views[self.current_view_name].grid_forget()

        # Show target view
        target_view = self.views.get(route)
        if target_view:
            target_view.grid(row=0, column=0, sticky="nsew")
            if hasattr(target_view, "refresh"):
                target_view.refresh()
            if route == "capture":
                target_view.start_view()

        self.current_view_name = route
        self._update_top_header()

    def _update_top_header(self) -> None:
        """Refreshes status in top bar for light mode."""
        sess = self.ctx.active_session
        if sess:
            self.top_session_lbl.configure(text=f"Sesi Aktif: {sess.site} ({sess.date})", text_color="#047857")
        else:
            self.top_session_lbl.configure(text="Sesi: [Belum Ada]", text_color="#D97706")

        cam_summary = self.ctx.camera_manager.get_status_summary()
        self.top_cam_lbl.configure(
            text=cam_summary,
            text_color="#059669" if self.ctx.camera_manager.is_ready() else "#D97706"
        )

        free_gb = self.ctx.storage_manager.get_available_space_mb() / 1024.0
        self.top_storage_lbl.configure(
            text=f"Storage: {free_gb:.1f} GB Bebas",
            text_color="#059669" if free_gb > 1.0 else "#DC2626"
        )

    def _startup_camera_init(self) -> None:
        """Initializes camera connection on app start (PRD Section 8)."""
        logger.info("Initializing camera on startup...")
        self.ctx.camera_manager.connect_camera("webcam", "0")
        self._update_top_header()
        if self.current_view_name in self.views and hasattr(self.views[self.current_view_name], "refresh"):
            self.views[self.current_view_name].refresh()

    def _on_close(self) -> None:
        """Gracefully release camera resources and exit."""
        logger.info("Closing application...")
        try:
            if "capture" in self.views:
                self.views["capture"].stop_view()
            self.ctx.camera_manager.disconnect_camera()
        except Exception as e:
            logger.error("Error during teardown: %s", e)
        self.destroy()


def main():
    setup_logging()
    logger.info("Starting Core Photo Application...")
    app = CorePhotoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
