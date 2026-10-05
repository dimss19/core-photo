"""Main Desktop Application Entry Point for Core Photo.
Professional Industrial Desktop Application for geological drill core photography.
Window layout: TopBar (branding & subtle status) + Left compact Sidebar + Main Content Canvas + Bottom Status Bar.
Zero emojis, strict industrial palette (Orange accent, Dark Charcoal, Off-white canvas).
"""

import sys
import tkinter as tk
from pathlib import Path
from typing import Dict, Optional
import customtkinter as ctk
from PIL import Image, ImageTk

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
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_ACCENT_LIGHT,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_BORDER_STRONG,
    COLOR_CHARCOAL,
    COLOR_ERROR,
    COLOR_PANEL,
    COLOR_PANEL_ALT,
    COLOR_SUCCESS,
    COLOR_TEXT_HINT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    FONT_FAMILY,
    get_font,
)

logger = get_logger(__name__)


class CorePhotoApp(ctk.CTk):
    """Main application window adhering to industrial desktop standards."""

    def __init__(self):
        super().__init__()

        self.config = get_config()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Core Photo — Drill Core Photography System")
        self.geometry("1340x840")
        self.minsize(1120, 720)
        self.configure(fg_color=COLOR_BG)

        # Window icon configuration
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

        # Automatically connect camera in background on startup
        self.after(300, self._startup_camera_init)

        # Handle clean window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # =========================================================================
        # 1. TOP BAR (Clean, subtle status, not headline heavy)
        # =========================================================================
        self.top_bar = ctk.CTkFrame(
            self,
            height=44,
            corner_radius=0,
            fg_color=COLOR_PANEL,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.top_bar.grid_columnconfigure(1, weight=1)

        # Brand / Logo Section (Left)
        brand_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=(16, 12), pady=6, sticky="w")

        png_file = self.icon_dir / "icon.png"
        if png_file.exists():
            try:
                pil_logo = Image.open(png_file)
                self.logo_ctk_image = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(22, 22))
                self.logo_icon_lbl = ctk.CTkLabel(brand_frame, image=self.logo_ctk_image, text="")
                self.logo_icon_lbl.pack(side="left", padx=(0, 8))
            except Exception as e:
                logger.debug("Could not load header logo image: %s", e)

        self.brand_title_lbl = ctk.CTkLabel(
            brand_frame,
            text="CORE PHOTO",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        self.brand_title_lbl.pack(side="left")

        # Subtle System Status Indicators (Right)
        status_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        status_frame.grid(row=0, column=1, sticky="e", padx=16, pady=6)

        # Session status
        self.top_session_lbl = ctk.CTkLabel(
            status_frame,
            text="Session: [None]",
            font=get_font(11, "bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        self.top_session_lbl.pack(side="left", padx=(0, 16))

        # Divider
        ctk.CTkLabel(status_frame, text="|", font=get_font(11), text_color=COLOR_BORDER_STRONG).pack(side="left", padx=(0, 16))

        # Camera status
        self.top_cam_indicator = ctk.CTkLabel(
            status_frame,
            text="● Disconnected",
            font=get_font(11, "bold"),
            text_color=COLOR_ERROR,
        )
        self.top_cam_indicator.pack(side="left", padx=(0, 16))

        # Divider
        ctk.CTkLabel(status_frame, text="|", font=get_font(11), text_color=COLOR_BORDER_STRONG).pack(side="left", padx=(0, 16))

        # Storage status
        self.top_storage_lbl = ctk.CTkLabel(
            status_frame,
            text="Storage: Checking...",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.top_storage_lbl.pack(side="left")

        # =========================================================================
        # 2. LEFT SIDEBAR (Compact, strictly grouped, zero emojis)
        # =========================================================================
        self.sidebar = ctk.CTkFrame(
            self,
            width=200,
            corner_radius=0,
            fg_color=COLOR_PANEL,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(25, weight=1)

        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        nav_structure = [
            ("MAIN", [
                ("dashboard", "Dashboard"),
                ("capture", "Capture"),
            ]),
            ("REVIEW", [
                ("review", "Review"),
                ("browser", "Photo Browser"),
                ("validation", "Validation"),
            ]),
            ("DATA", [
                ("transfer", "Transfer"),
                ("session", "Session"),
            ]),
            ("SYSTEM", [
                ("settings", "Settings"),
                ("diagnostics", "Diagnostics"),
            ]),
        ]

        current_row = 0
        for group_title, items in nav_structure:
            grp_lbl = ctk.CTkLabel(
                self.sidebar,
                text=group_title,
                font=get_font(10, "bold"),
                text_color=COLOR_TEXT_HINT,
            )
            grp_lbl.grid(row=current_row, column=0, padx=16, pady=(12 if current_row > 0 else 10, 3), sticky="w")
            current_row += 1

            for route_key, label in items:
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=label,
                    anchor="w",
                    font=get_font(12, "normal"),
                    height=32,
                    corner_radius=4,
                    fg_color="transparent",
                    text_color=COLOR_TEXT_PRIMARY,
                    hover_color=COLOR_PANEL_ALT,
                    command=lambda r=route_key: self.navigate_to(r),
                )
                btn.grid(row=current_row, column=0, padx=8, pady=1, sticky="ew")
                self.nav_buttons[route_key] = btn
                current_row += 1

        # Sidebar footer
        side_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        side_footer.grid(row=26, column=0, padx=12, pady=12, sticky="s")

        lbl_version = ctk.CTkLabel(
            side_footer,
            text="Core Photo v1.0.0\nIndustrial Edition",
            font=get_font(10),
            text_color=COLOR_TEXT_HINT,
            justify="center",
        )
        lbl_version.pack()

        # =========================================================================
        # 3. MAIN CONTENT CONTAINER (Off-white industrial canvas)
        # =========================================================================
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        self.content_area.grid(row=1, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # =========================================================================
        # 4. BOTTOM STATUS BAR (Industrial status & operational metadata)
        # =========================================================================
        self.bottom_bar = ctk.CTkFrame(
            self,
            height=26,
            corner_radius=0,
            fg_color=COLOR_PANEL,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.bottom_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.bottom_bar.grid_columnconfigure(1, weight=1)

        self.bottom_status_lbl = ctk.CTkLabel(
            self.bottom_bar,
            text="System Ready  |  WebcamAdapter Active",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        )
        self.bottom_status_lbl.grid(row=0, column=0, padx=16, pady=2, sticky="w")

        self.bottom_info_lbl = ctk.CTkLabel(
            self.bottom_bar,
            text="Offline-Ready  |  SQLite Database OK",
            font=get_font(10),
            text_color=COLOR_TEXT_HINT,
        )
        self.bottom_info_lbl.grid(row=0, column=1, padx=16, pady=2, sticky="e")

    def _init_views(self) -> None:
        """Instantiates all application screen frames."""
        capture_view = CaptureView(self.content_area, navigate_fn=self.navigate_to)
        self.views["capture"] = capture_view

        self.views["dashboard"] = DashboardView(self.content_area, navigate_fn=self.navigate_to)
        self.views["session"] = SessionView(self.content_area, navigate_fn=self.navigate_to)
        self.views["review"] = ReviewView(
            self.content_area,
            navigate_fn=self.navigate_to,
            advance_tray_fn=capture_view.advance_to_next_tray,
        )
        self.views["browser"] = BrowserView(self.content_area, navigate_fn=self.navigate_to)
        self.views["validation"] = ValidationView(self.content_area, navigate_fn=self.navigate_to)
        self.views["transfer"] = TransferView(self.content_area, navigate_fn=self.navigate_to)
        self.views["settings"] = SettingsView(self.content_area, navigate_fn=self.navigate_to)

    def navigate_to(self, route: str) -> None:
        """Navigates smoothly between screens."""
        logger.info("Navigating to view: %s", route)

        # Handle 'diagnostics' routing to settings view
        effective_route = "settings" if route == "diagnostics" else route

        # Handle view lifecycle transitions
        if self.current_view_name == "capture" and effective_route != "capture":
            self.views["capture"].stop_view()

        # Update button highlights for Industrial Orange active indicator
        for r, btn in self.nav_buttons.items():
            if r == route or (route == "diagnostics" and r == "diagnostics"):
                btn.configure(
                    fg_color=COLOR_ACCENT_LIGHT,
                    hover_color=COLOR_ACCENT_LIGHT,
                    text_color=COLOR_ACCENT,
                    font=get_font(12, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=COLOR_PANEL_ALT,
                    text_color=COLOR_TEXT_PRIMARY,
                    font=get_font(12, "normal"),
                )

        # Hide current view
        if self.current_view_name in self.views:
            self.views[self.current_view_name].grid_forget()

        # Show target view
        target_view = self.views.get(effective_route)
        if target_view:
            target_view.grid(row=0, column=0, sticky="nsew")
            if hasattr(target_view, "refresh"):
                target_view.refresh()
            if effective_route == "capture":
                target_view.start_view()

        self.current_view_name = effective_route
        self._update_top_header()

    def _update_top_header(self) -> None:
        """Refreshes status in top bar and bottom status bar."""
        sess = self.ctx.active_session
        if sess:
            self.top_session_lbl.configure(
                text=f"Session: {sess.site}",
                text_color=COLOR_CHARCOAL,
            )
            self.bottom_status_lbl.configure(
                text=f"Session: {sess.site}  |  Operator: {sess.operator}  |  Date: {sess.date}"
            )
        else:
            self.top_session_lbl.configure(
                text="Session: [None]",
                text_color=COLOR_TEXT_HINT,
            )
            self.bottom_status_lbl.configure(
                text="No active session  |  Create or select a session to begin capture"
            )

        cam_ready = self.ctx.camera_manager.is_ready()
        if cam_ready:
            self.top_cam_indicator.configure(
                text="● Connected",
                text_color=COLOR_SUCCESS,
            )
        else:
            self.top_cam_indicator.configure(
                text="● Disconnected",
                text_color=COLOR_ERROR,
            )

        free_gb = self.ctx.storage_manager.get_available_space_mb() / 1024.0
        self.top_storage_lbl.configure(
            text=f"Storage: {free_gb:.1f} GB",
            text_color=COLOR_TEXT_MUTED if free_gb > 1.0 else COLOR_ERROR,
        )

    def _startup_camera_init(self) -> None:
        """Initializes camera connection on app start."""
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
