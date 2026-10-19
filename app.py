"""Main Desktop Application Entry Point for Core Photo.
Professional Industrial Desktop Application for geological drill core photography.
Window layout: TopBar (branding & subtle status) + Left compact Sidebar with Collapsible Accordion Dropdowns + Main Content Canvas + Bottom Status Bar.
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
from ui.capture import CaptureView
from ui.data_hub import DataHubView
from ui.review import ReviewView
from ui.settings import SettingsView
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

        # Primary navigation buttons state
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        self._build_layout()
        self._init_views()
        self.navigate_to("capture")

        # Automatically connect camera in background on startup
        self.after(300, self._startup_camera_init)

        # Handle clean window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
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
        self.top_bar.grid(row=0, column=0, sticky="ew")
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

        # Back to Camera Capture button (only shown when in Session view)
        self.top_back_btn = ctk.CTkButton(
            status_frame,
            text="← Camera Capture",
            font=get_font(11, "bold"),
            height=28,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=lambda: self.navigate_to("capture"),
        )

        # Session status (Interactive button linking to Session Manager & Archive)
        self.top_session_btn = ctk.CTkButton(
            status_frame,
            text="Session: [None]",
            font=get_font(11, "bold"),
            height=28,
            corner_radius=4,
            fg_color="transparent",
            hover_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_MUTED,
            border_width=1,
            border_color=COLOR_BORDER,
            command=lambda: self.navigate_to("data"),
        )
        self.top_session_btn.pack(side="left", padx=(0, 14))
        self.top_session_lbl = self.top_session_btn

        # Divider
        ctk.CTkLabel(status_frame, text="|", font=get_font(11), text_color=COLOR_BORDER_STRONG).pack(side="left", padx=(0, 14))

        # Camera status
        self.top_cam_indicator = ctk.CTkLabel(
            status_frame,
            text="● Disconnected",
            font=get_font(11, "bold"),
            text_color=COLOR_ERROR,
        )
        self.top_cam_indicator.pack(side="left", padx=(0, 14))

        # Divider
        ctk.CTkLabel(status_frame, text="|", font=get_font(11), text_color=COLOR_BORDER_STRONG).pack(side="left", padx=(0, 14))

        # Storage status
        self.top_storage_lbl = ctk.CTkLabel(
            status_frame,
            text="Storage: Checking...",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.top_storage_lbl.pack(side="left", padx=(0, 14))

        # Divider
        ctk.CTkLabel(status_frame, text="|", font=get_font(11), text_color=COLOR_BORDER_STRONG).pack(side="left", padx=(0, 14))

        # Camera Settings shortcut button
        self.top_settings_btn = ctk.CTkButton(
            status_frame,
            text="⚙ Camera Settings",
            font=get_font(11, "bold"),
            height=28,
            corner_radius=4,
            fg_color="transparent",
            hover_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=lambda: self.navigate_to("capture", tab="Camera Settings"),
        )
        self.top_settings_btn.pack(side="left")

        # =========================================================================
        # 2. MAIN CONTENT CONTAINER (Full Width, Off-white industrial canvas)
        # =========================================================================
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        self.content_area.grid(row=1, column=0, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # =========================================================================
        # 3. BOTTOM STATUS BAR (Industrial status & operational metadata)
        # =========================================================================
        self.bottom_bar = ctk.CTkFrame(
            self,
            height=26,
            corner_radius=0,
            fg_color=COLOR_PANEL,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.bottom_bar.grid(row=2, column=0, sticky="ew")
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
            text="System Ready  |  SQLite Database OK",
            font=get_font(10),
            text_color=COLOR_TEXT_HINT,
        )
        self.bottom_info_lbl.grid(row=0, column=1, padx=16, pady=2, sticky="e")

    def toggle_group(self, group_title: str, expand_only: bool = False) -> None:
        """Compatibility no-op for accordion groups."""
        pass

    def _init_views(self) -> None:
        """Instantiates all application screen frames."""
        capture_view = CaptureView(self.content_area, navigate_fn=self.navigate_to)
        self.views["capture"] = capture_view
        self.views["dashboard"] = capture_view

        data_hub_view = DataHubView(self.content_area, navigate_fn=self.navigate_to)
        self.views["data"] = data_hub_view
        self.views["session"] = data_hub_view
        self.views["transfer"] = data_hub_view

        review_view = ReviewView(
            self.content_area,
            navigate_fn=self.navigate_to,
            advance_tray_fn=capture_view.advance_to_next_tray,
        )
        self.views["review"] = review_view
        self.views["browser"] = review_view
        self.views["validation"] = review_view

        self.views["settings"] = SettingsView(self.content_area, navigate_fn=self.navigate_to)

    def navigate_to(self, route: str, tab: Optional[str] = None) -> None:
        """Navigates smoothly between screens."""
        logger.info("Navigating to view: %s (tab: %s)", route, tab)

        # Handle aliases and consolidated views
        target_tab = tab
        if route == "diagnostics":
            effective_route = "settings"
            target_tab = target_tab or "DIAGNOSTICS"
        elif route == "dashboard":
            effective_route = "capture"
        elif route == "validation":
            effective_route = "review"
            target_tab = "inspect"
        elif route == "browser":
            effective_route = "review"
            target_tab = "catalog"
        elif route in ("session", "transfer", "archive", "archives"):
            effective_route = "data"
            target_tab = "session"
        else:
            effective_route = route

        # Handle view lifecycle transitions
        if self.current_view_name == "capture" and effective_route != "capture":
            self.views["capture"].stop_view()

        # Update button highlights for Industrial Orange active indicator
        for r, btn in self.nav_buttons.items():
            if r == effective_route:
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
            if target_tab and hasattr(target_view, "select_tab"):
                target_view.select_tab(target_tab)
            if hasattr(target_view, "refresh"):
                target_view.refresh()
            if effective_route == "capture":
                target_view.start_view()

        self.current_view_name = effective_route
        self._update_top_header()

    def _update_top_header(self) -> None:
        """Refreshes status in top bar and bottom status bar."""
        sess = self.ctx.active_session
        is_on_session = (self.current_view_name == "data")

        if hasattr(self, "top_back_btn"):
            if is_on_session:
                self.top_back_btn.pack(side="left", padx=(0, 14), before=self.top_session_btn)
            else:
                self.top_back_btn.pack_forget()

        if hasattr(self, "top_settings_btn"):
            is_on_settings = (
                self.current_view_name == "capture"
                and hasattr(self.views.get("capture"), "left_tabs")
                and self.views["capture"].left_tabs.get() == "Camera Settings"
            )
            self.top_settings_btn.configure(
                text_color=COLOR_ACCENT if is_on_settings else COLOR_CHARCOAL,
                fg_color=COLOR_ACCENT_LIGHT if is_on_settings else "transparent",
                border_color=COLOR_ACCENT if is_on_settings else COLOR_BORDER,
            )

        if sess:
            self.top_session_btn.configure(
                text=f"Session: {sess.site}",
                text_color=COLOR_ACCENT if is_on_session else COLOR_CHARCOAL,
                fg_color=COLOR_ACCENT_LIGHT if is_on_session else "transparent",
                hover_color=COLOR_ACCENT_LIGHT if is_on_session else COLOR_PANEL_ALT,
                border_color=COLOR_ACCENT if is_on_session else COLOR_BORDER,
            )
            op_text = f"  |  Operator: {sess.operator}" if sess.operator and sess.operator.strip() else ""
            self.bottom_status_lbl.configure(
                text=f"Session: {sess.site}{op_text}  |  Date: {sess.date}"
            )
        else:
            self.top_session_btn.configure(
                text="Session: [None]",
                text_color=COLOR_ACCENT if is_on_session else COLOR_TEXT_HINT,
                fg_color=COLOR_ACCENT_LIGHT if is_on_session else "transparent",
                hover_color=COLOR_ACCENT_LIGHT if is_on_session else COLOR_PANEL_ALT,
                border_color=COLOR_ACCENT if is_on_session else COLOR_BORDER,
            )
            self.bottom_status_lbl.configure(
                text="No active session  |  Click 'Session' in header to create or select a session"
            )

        cam_ready = self.ctx.camera_manager.is_ready()
        info = self.ctx.camera_manager.get_info()
        if cam_ready and info and info.model:
            # Show concise model name if not too long
            short_model = info.model if len(info.model) <= 24 else info.model[:22] + "..."
            self.top_cam_indicator.configure(
                text=f"● {short_model}",
                text_color=COLOR_SUCCESS,
            )
        elif cam_ready:
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
        backend = self.ctx.config.get("camera", "default_adapter", "webcam")
        pref_idx = self.ctx.config.get("camera", "preferred_index", 0)
        device_id = str(self.ctx.config.get("camera", "device_id", pref_idx))
        if backend in ("wifi_dslr", "dslr_wifi", "tether", "hot_folder", "hotfolder"):
            backend = "webcam"
        if backend == "webcam":
            # Biarkan manager auto-fallback ke index fisik yang tersedia
            # bila preferred_index basi (mis. external dicabut).
            if not device_id or device_id.lower() in ("none", "auto", "default"):
                device_id = str(pref_idx)

        success = self.ctx.camera_manager.connect_camera(backend, device_id)
        # FIX: bila webcam menghasilkan standby (fisik gagal dibuka),
        # manager sudah mencoba fallback internal; bila tetap standby,
        # lanjutkan rantai fallback bawaan (direct -> webcam 0 -> sim).
        try:
            _active = getattr(self.ctx.camera_manager, "_active_adapter", None)
            if success and backend == "webcam" and getattr(_active, "_is_simulated", False) and str(device_id).lower() != "sim":
                success = False  # paksa coba backend lain di bawah
        except Exception:
            pass
        if not success:
            if backend != "direct_usb":
                success = self.ctx.camera_manager.connect_camera("direct_usb", "0")
            if not success and device_id != "0":
                success = self.ctx.camera_manager.connect_camera("webcam", "0")
            if not success:
                self.ctx.camera_manager.connect_camera("webcam", "sim")
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
