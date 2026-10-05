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
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme(color_theme)

        self.title("Core Photo — Sistem Pengambilan Foto Drill Core")
        self.geometry("1300x820")
        self.minsize(1100, 700)

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

        # ----------------- Top Header Bar -----------------
        self.header_bar = ctk.CTkFrame(self, height=48, corner_radius=0, fg_color="#1F1F1F")
        self.header_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header_bar.grid_columnconfigure(1, weight=1)

        # Logo text
        self.logo_lbl = ctk.CTkLabel(
            self.header_bar,
            text="CORE PHOTO",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3B8ED0"
        )
        self.logo_lbl.grid(row=0, column=0, padx=(20, 16), pady=8)

        # Top System Status Indicators
        status_frame = ctk.CTkFrame(self.header_bar, fg_color="transparent")
        status_frame.grid(row=0, column=1, sticky="e", padx=20)

        self.top_session_lbl = ctk.CTkLabel(
            status_frame,
            text="Sesi: [Belum Ada]",
            font=ctk.CTkFont(size=12),
            text_color="gray75"
        )
        self.top_session_lbl.pack(side="left", padx=12)

        self.top_cam_lbl = ctk.CTkLabel(
            status_frame,
            text="Kamera: Disconnected",
            font=ctk.CTkFont(size=12),
            text_color="#E5A93C"
        )
        self.top_cam_lbl.pack(side="left", padx=12)

        self.top_storage_lbl = ctk.CTkLabel(
            status_frame,
            text="Storage: OK",
            font=ctk.CTkFont(size=12),
            text_color="#2CC985"
        )
        self.top_storage_lbl.pack(side="left", padx=12)

        # ----------------- Left Navigation Sidebar -----------------
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#181818")
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)

        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("session", "📁  Sesi (Session)"),
            ("capture", "📷  Capture Foto"),
            ("review", "👁️  Review Foto"),
            ("browser", "🔍  Photo Browser"),
            ("validation", "✅  Validasi Data"),
            ("transfer", "📤  Transfer Server"),
            ("settings", "⚙️  Pengaturan & Tes"),
        ]

        for idx, (route, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="normal"),
                height=40,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#282828",
                command=lambda r=route: self.navigate_to(r)
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[route] = btn

        # Version stamp
        v_lbl = ctk.CTkLabel(
            self.sidebar,
            text="Core Photo v1.0.0\nDesktop Offline-Ready",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            justify="center"
        )
        v_lbl.grid(row=10, column=0, padx=12, pady=16)

        # ----------------- Main Content Area -----------------
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="#121212")
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

        # Update button highlights
        for r, btn in self.nav_buttons.items():
            if r == route:
                btn.configure(fg_color="#3B8ED0", hover_color="#2E75B6", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", hover_color="#282828", text_color="#DCE4EE")

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
        """Refreshes status in top bar."""
        sess = self.ctx.active_session
        if sess:
            self.top_session_lbl.configure(text=f"Sesi: {sess.site} ({sess.date})", text_color="#E0E0E0")
        else:
            self.top_session_lbl.configure(text="Sesi: [Belum Ada]", text_color="#E5A93C")

        cam_summary = self.ctx.camera_manager.get_status_summary()
        self.top_cam_lbl.configure(
            text=cam_summary,
            text_color="#2CC985" if self.ctx.camera_manager.is_ready() else "#E5A93C"
        )

        free_gb = self.ctx.storage_manager.get_available_space_mb() / 1024.0
        self.top_storage_lbl.configure(
            text=f"Storage: {free_gb:.1f} GB Bebas",
            text_color="#2CC985" if free_gb > 1.0 else "#D9534F"
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
