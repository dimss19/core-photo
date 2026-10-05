"""Capture Screen (Professional Industrial Redesign).
Priority: Large dominant Live View with framing overlays, structured Tray Information on Left,
Camera Controls on top/right toolbar, Pre-flight validation checklist, and a prominent
Industrial Orange [ CAPTURE ] button as the visual focal point.
Zero emojis, strict professional standards.
"""

import threading
import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk

from core.app_context import get_app_context
from core.logger import get_logger
from imaging.crop import CropRegion
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


class CaptureView(ctk.CTkFrame):
    """Core photography and framing screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        # Framing / Crop state
        self.grid_enabled = True
        self.crop_enabled = True
        self.crop_region: Optional[CropRegion] = None
        self._current_photo_image: Optional[ImageTk.PhotoImage] = None
        self._is_capturing = False

        self._build_ui()
        self._setup_bindings()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=0, minsize=320)  # Left: Tray Data Form
        self.grid_columnconfigure(1, weight=1)               # Center: Dominant Live View & Action
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # 1. LEFT PANEL: Tray Information
        # =========================================================================
        left_panel = ctk.CTkScrollableFrame(
            self,
            width=320,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)

        ctk.CTkLabel(
            left_panel,
            text="TRAY IDENTIFICATION",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            left_panel,
            text="Core tray parameters and borehole depth interval.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Session Guard Notice
        self.session_guard_frame = ctk.CTkFrame(
            left_panel,
            fg_color=COLOR_WARNING_BG,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_WARNING_BORDER,
        )
        self.session_guard_lbl = ctk.CTkLabel(
            self.session_guard_frame,
            text="No active session. Please open or create a session first.",
            font=get_font(11, "bold"),
            text_color=COLOR_WARNING,
            wraplength=270,
            justify="left",
        )
        self.session_guard_lbl.pack(anchor="w", padx=10, pady=(8, 4))

        self.btn_go_session = ctk.CTkButton(
            self.session_guard_frame,
            text="Manage Session →",
            font=get_font(11, "bold"),
            height=28,
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER_STRONG,
            text_color="#FFFFFF",
            command=lambda: self.navigate_fn("session"),
        )
        self.btn_go_session.pack(anchor="w", padx=10, pady=(0, 8))

        # 1. Hole ID
        ctk.CTkLabel(left_panel, text="Hole ID *", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=14, pady=(6, 2))
        self.entry_hole = ctk.CTkEntry(
            left_panel,
            placeholder_text="e.g. DDH-001 or CORE-12",
            height=34,
            font=get_font(12),
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.entry_hole.pack(fill="x", padx=14, pady=(0, 2))
        ctk.CTkLabel(left_panel, text="Borehole reference number", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(anchor="w", padx=14, pady=(0, 8))

        # 2. Tray ID
        ctk.CTkLabel(left_panel, text="Tray Number *", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=14, pady=(4, 2))
        self.entry_tray = ctk.CTkEntry(
            left_panel,
            placeholder_text="1",
            height=34,
            font=get_font(12),
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.entry_tray.pack(fill="x", padx=14, pady=(0, 2))
        ctk.CTkLabel(left_panel, text="Sequential tray index (auto-increments)", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(anchor="w", padx=14, pady=(0, 8))

        # 3. Intervals
        interval_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        interval_frame.pack(fill="x", padx=14, pady=2)
        interval_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(interval_frame, text="Interval From (m) *", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(interval_frame, text="Interval To (m) *", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.entry_from = ctk.CTkEntry(interval_frame, height=34, font=get_font(12), fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_from.grid(row=1, column=0, sticky="ew", pady=(2, 2))
        self.entry_from.insert(0, "0.00")

        self.entry_to = ctk.CTkEntry(interval_frame, height=34, font=get_font(12), fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_to.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(2, 2))
        self.entry_to.insert(0, "2.60")

        ctk.CTkLabel(left_panel, text="Depth boundary interval in meters", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(anchor="w", padx=14, pady=(0, 8))

        # 4. Tray Physical Dimensions
        dim_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        dim_frame.pack(fill="x", padx=14, pady=2)
        dim_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(dim_frame, text="Rows:", font=get_font(10, "bold"), text_color=COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(dim_frame, text="Len (cm):", font=get_font(10, "bold"), text_color=COLOR_TEXT_MUTED).grid(row=0, column=1, sticky="w", padx=4)
        ctk.CTkLabel(dim_frame, text="Wid (cm):", font=get_font(10, "bold"), text_color=COLOR_TEXT_MUTED).grid(row=0, column=2, sticky="w")

        self.entry_rows = ctk.CTkEntry(dim_frame, height=30, font=get_font(11), fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_rows.grid(row=1, column=0, sticky="ew")
        self.entry_rows.insert(0, "3")

        self.entry_length = ctk.CTkEntry(dim_frame, height=30, font=get_font(11), fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_length.grid(row=1, column=1, sticky="ew", padx=4)
        self.entry_length.insert(0, "100.0")

        self.entry_width = ctk.CTkEntry(dim_frame, height=30, font=get_font(11), fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER_STRONG, border_width=1)
        self.entry_width.grid(row=1, column=2, sticky="ew")
        self.entry_width.insert(0, "40.0")

        # 5. Comments
        ctk.CTkLabel(left_panel, text="Geological Comments", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=14, pady=(8, 2))
        self.entry_comments = ctk.CTkEntry(
            left_panel,
            placeholder_text="Core condition, fractures, recovery notes...",
            height=34,
            font=get_font(11),
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.entry_comments.pack(fill="x", padx=14, pady=(0, 14))

        # =========================================================================
        # 2. CENTER PANEL: Live View, Controls Toolbar, and Capture Action
        # =========================================================================
        center_panel = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        center_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        center_panel.grid_rowconfigure(1, weight=1)  # Dominant live view canvas
        center_panel.grid_columnconfigure(0, weight=1)

        # --- Top Toolbar: Stream status & Camera Controls ---
        toolbar = ctk.CTkFrame(center_panel, height=38, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 6))

        # Left status in toolbar
        self.stream_info_lbl = ctk.CTkLabel(
            toolbar,
            text="LIVE CAMERA STREAM",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        self.stream_info_lbl.pack(side="left")

        # Right camera controls in toolbar
        self.btn_reconnect = ctk.CTkButton(
            toolbar,
            text="Reconnect",
            font=get_font(11),
            width=90,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_reconnect_cam,
        )
        self.btn_reconnect.pack(side="right", padx=(4, 0))

        self.btn_crop_toggle = ctk.CTkButton(
            toolbar,
            text="Crop Box: ON",
            font=get_font(11, "bold"),
            width=100,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._toggle_crop,
        )
        self.btn_crop_toggle.pack(side="right", padx=(4, 0))

        self.btn_grid_toggle = ctk.CTkButton(
            toolbar,
            text="Grid: ON",
            font=get_font(11, "bold"),
            width=76,
            height=28,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._toggle_grid,
        )
        self.btn_grid_toggle.pack(side="right", padx=(4, 0))

        # --- Center Canvas: Large Live View ---
        canvas_container = ctk.CTkFrame(center_panel, fg_color="#09090B", corner_radius=4)
        canvas_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_container,
            bg="#09090B",
            highlightthickness=0,
            cursor="cross",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # --- Bottom Operational Section: Pre-flight & Bold Orange CAPTURE CTA ---
        bottom_box = ctk.CTkFrame(center_panel, fg_color="transparent")
        bottom_box.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 14))
        bottom_box.grid_columnconfigure(0, weight=1)

        # Pre-flight Checklist Banner
        self.preflight_banner = ctk.CTkFrame(
            bottom_box,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=4,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.preflight_banner.pack(fill="x", pady=(0, 10))

        # Checklist bullets row
        self.lbl_checklist_items = ctk.CTkLabel(
            self.preflight_banner,
            text="Camera ?  ·  Session ?  ·  Hole ID ?  ·  Tray ID ?  ·  Interval ?  ·  Storage ?  ·  Crop ?",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_checklist_items.pack(anchor="w", padx=12, pady=(6, 2))

        # Actionable verdict label
        self.lbl_preflight_verdict = ctk.CTkLabel(
            self.preflight_banner,
            text="Evaluating pre-flight parameters...",
            font=get_font(11, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.lbl_preflight_verdict.pack(anchor="w", padx=12, pady=(0, 6))

        # Focal Primary Action: Large Orange [ CAPTURE ] Button
        self.btn_capture = ctk.CTkButton(
            bottom_box,
            text="CAPTURE TRAY PHOTO",
            font=get_font(14, "bold"),
            height=48,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_capture_click,
        )
        self.btn_capture.pack(fill="x", pady=(0, 2))

        self.lbl_capture_feedback = ctk.CTkLabel(
            bottom_box,
            text="",
            font=get_font(10, "bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_capture_feedback.pack(anchor="center", pady=(2, 0))

    def _setup_bindings(self) -> None:
        """Trace changes in input entries to automatically re-evaluate preflight."""
        for entry in [self.entry_hole, self.entry_tray, self.entry_from, self.entry_to]:
            entry.bind("<KeyRelease>", lambda e: self._evaluate_preflight())

    def start_view(self) -> None:
        """Called when this view becomes active."""
        logger.info("Starting CaptureView live view...")
        self.ctx.subscribe_live_frames(self._handle_incoming_frame)
        self._check_session_guard()
        self._evaluate_preflight()

    def stop_view(self) -> None:
        """Called when navigating away."""
        logger.info("Stopping CaptureView live view...")
        self.ctx.unsubscribe_live_frames(self._handle_incoming_frame)

    def _check_session_guard(self) -> None:
        """Verifies an active session exists."""
        sess = self.ctx.active_session
        if sess:
            self.session_guard_frame.pack_forget()
        else:
            self.session_guard_frame.pack(fill="x", padx=14, pady=(0, 10), before=self.entry_hole)

    def _handle_incoming_frame(self, frame_rgb: np.ndarray) -> None:
        """Receives RGB frame from background camera thread."""
        try:
            self.after(0, self._render_frame, frame_rgb)
        except Exception as e:
            logger.debug("Failed to schedule frame render: %s", e)

    def _render_frame(self, frame_rgb: np.ndarray) -> None:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w < 50 or canvas_h < 50:
            return

        frame_h, frame_w = frame_rgb.shape[:2]
        # Aspect ratio fitting
        scale = min(canvas_w / frame_w, canvas_h / frame_h)
        disp_w = max(1, int(frame_w * scale))
        disp_h = max(1, int(frame_h * scale))

        offset_x = (canvas_w - disp_w) // 2
        offset_y = (canvas_h - disp_h) // 2

        pil_img = Image.fromarray(frame_rgb).resize((disp_w, disp_h), Image.Resampling.BILINEAR)
        self._current_photo_image = ImageTk.PhotoImage(pil_img)

        self.canvas.delete("all")
        self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self._current_photo_image)

        # Draw Grid if enabled
        if self.grid_enabled:
            x1 = offset_x + disp_w // 3
            x2 = offset_x + (2 * disp_w) // 3
            y1 = offset_y + disp_h // 3
            y2 = offset_y + (2 * disp_h) // 3
            self.canvas.create_line(x1, offset_y, x1, offset_y + disp_h, fill="#0284C7", dash=(3, 3))
            self.canvas.create_line(x2, offset_y, x2, offset_y + disp_h, fill="#0284C7", dash=(3, 3))
            self.canvas.create_line(offset_x, y1, offset_x + disp_w, y1, fill="#0284C7", dash=(3, 3))
            self.canvas.create_line(offset_x, y2, offset_x + disp_w, y2, fill="#0284C7", dash=(3, 3))

        # Standard Tray Crop Framing box (300 x 200 ratio)
        crop_w_box = int(disp_w * 0.88)
        crop_h_box = int(crop_w_box / 1.5)  # 300:200 ratio
        if crop_h_box > disp_h * 0.88:
            crop_h_box = int(disp_h * 0.88)
            crop_w_box = int(crop_h_box * 1.5)

        cx1 = offset_x + (disp_w - crop_w_box) // 2
        cy1 = offset_y + (disp_h - crop_h_box) // 2
        cx2 = cx1 + crop_w_box
        cy2 = cy1 + crop_h_box

        if self.crop_enabled:
            self.canvas.create_rectangle(cx1, cy1, cx2, cy2, outline=COLOR_SUCCESS, width=2)
            self.canvas.create_text(
                cx1 + 8,
                cy1 + 14,
                text="Tray Framing Area (300:200)",
                fill=COLOR_SUCCESS,
                anchor="w",
                font=("Segoe UI", 9, "bold"),
            )

        orig_crop_x = int((cx1 - offset_x) / scale)
        orig_crop_y = int((cy1 - offset_y) / scale)
        orig_crop_w = int(crop_w_box / scale)
        orig_crop_h = int(crop_h_box / scale)
        self.crop_region = CropRegion(x=orig_crop_x, y=orig_crop_y, width=orig_crop_w, height=orig_crop_h)

        cam_text = self.ctx.camera_manager.get_status_summary()
        self.stream_info_lbl.configure(text=f"LIVE VIEW — {frame_w}x{frame_h} @ ~30 FPS  |  {cam_text}")

    def _toggle_grid(self) -> None:
        self.grid_enabled = not self.grid_enabled
        self.btn_grid_toggle.configure(
            text="Grid: ON" if self.grid_enabled else "Grid: OFF",
            fg_color=COLOR_ACCENT_LIGHT if self.grid_enabled else COLOR_PANEL_ALT,
            text_color=COLOR_ACCENT if self.grid_enabled else COLOR_TEXT_MUTED,
        )

    def _toggle_crop(self) -> None:
        self.crop_enabled = not self.crop_enabled
        self.btn_crop_toggle.configure(
            text="Crop Box: ON" if self.crop_enabled else "Crop Box: OFF",
            fg_color=COLOR_ACCENT_LIGHT if self.crop_enabled else COLOR_PANEL_ALT,
            text_color=COLOR_ACCENT if self.crop_enabled else COLOR_TEXT_MUTED,
        )

    def _on_reconnect_cam(self) -> None:
        self.stream_info_lbl.configure(text="Reconnecting camera adapter...")
        self.ctx.camera_manager.connect_camera()
        self._evaluate_preflight()

    def _evaluate_preflight(self) -> None:
        """Evaluates pre-flight checks and updates UI."""
        self._check_session_guard()
        hole_id = self.entry_hole.get().strip()
        tray_id = self.entry_tray.get().strip()

        try:
            f_val = float(self.entry_from.get())
        except ValueError:
            f_val = -1.0
        try:
            t_val = float(self.entry_to.get())
        except ValueError:
            t_val = -1.0

        res = self.ctx.run_preflight(
            hole_id=hole_id,
            tray_id=tray_id,
            interval_from=f_val,
            interval_to=t_val,
            crop_region=self.crop_region,
        )

        # Build checklist summary status string
        cam_chk = "✓" if self.ctx.camera_manager.is_ready() else "✕"
        sess_chk = "✓" if self.ctx.active_session else "✕"
        hole_chk = "✓" if bool(hole_id) else "✕"
        tray_chk = "✓" if bool(tray_id) else "✕"
        int_chk = "✓" if (f_val >= 0 and t_val >= f_val) else "✕"
        stor_chk = "✓" if self.ctx.storage_manager.get_available_space_mb() > 500 else "✕"
        crop_chk = "✓" if self.crop_region else "✕"

        self.lbl_checklist_items.configure(
            text=f"Camera {cam_chk}  ·  Session {sess_chk}  ·  Hole ID {hole_chk}  ·  Tray ID {tray_chk}  ·  Interval {int_chk}  ·  Storage {stor_chk}  ·  Crop {crop_chk}"
        )

        if not self.ctx.active_session:
            self.preflight_banner.configure(fg_color=COLOR_ERROR_BG, border_color=COLOR_ERROR_BORDER)
            self.lbl_preflight_verdict.configure(
                text="Active session required. Select or create a session before capture.",
                text_color=COLOR_ERROR,
            )
            self.btn_capture.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)
        elif res.is_ready:
            self.preflight_banner.configure(fg_color=COLOR_SUCCESS_BG, border_color=COLOR_SUCCESS_BORDER)
            self.lbl_preflight_verdict.configure(
                text="READY TO CAPTURE",
                text_color=COLOR_SUCCESS,
            )
            self.btn_capture.configure(state="normal", fg_color=COLOR_ACCENT)
        else:
            issue = res.summary_errors[0] if res.summary_errors else "Complete all required tray parameters."
            self.preflight_banner.configure(fg_color=COLOR_WARNING_BG, border_color=COLOR_WARNING_BORDER)
            self.lbl_preflight_verdict.configure(
                text=f"CANNOT CAPTURE: {issue}",
                text_color=COLOR_WARNING,
            )
            self.btn_capture.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)

    def _on_capture_click(self) -> None:
        if self._is_capturing or not self.ctx.active_session:
            return

        self._is_capturing = True
        self.btn_capture.configure(text="ACQUIRING IMAGE...", state="disabled", fg_color=COLOR_BORDER_STRONG)
        self.lbl_capture_feedback.configure(text="Saving RAW buffer & generating 300x200 cropped archive...", text_color=COLOR_ACCENT)

        def capture_task():
            try:
                hole_id = self.entry_hole.get().strip()
                tray_id = self.entry_tray.get().strip()
                f_val = float(self.entry_from.get())
                t_val = float(self.entry_to.get())
                comments = self.entry_comments.get().strip()

                photo = self.ctx.execute_capture(
                    hole_id=hole_id,
                    tray_id=tray_id,
                    interval_from=f_val,
                    interval_to=t_val,
                    crop_region=self.crop_region,
                    comments=comments,
                )

                # Validate immediately
                self.ctx.validate_photo(photo.id)

                self.after(0, self._on_capture_success, photo)
            except Exception as e:
                logger.error("Capture failed: %s", e)
                self.after(0, self._on_capture_error, str(e))

        threading.Thread(target=capture_task, daemon=True).start()

    def _on_capture_success(self, photo) -> None:
        self._is_capturing = False
        self.btn_capture.configure(text="CAPTURE TRAY PHOTO", state="normal", fg_color=COLOR_ACCENT)
        self.lbl_capture_feedback.configure(
            text=f"Captured: {photo.filename_base}.jpg (Validated)",
            text_color=COLOR_SUCCESS,
        )
        # Advance directly to Review screen
        self.navigate_fn("review")

    def _on_capture_error(self, err_msg: str) -> None:
        self._is_capturing = False
        self.btn_capture.configure(text="CAPTURE TRAY PHOTO", state="normal", fg_color=COLOR_ACCENT)
        self.lbl_capture_feedback.configure(
            text=f"Capture Error: {err_msg}",
            text_color=COLOR_ERROR,
        )

    def advance_to_next_tray(self) -> None:
        """Auto-increments tray number and updates intervals."""
        try:
            curr_tray = int(self.entry_tray.get().strip())
            self.entry_tray.delete(0, "end")
            self.entry_tray.insert(0, str(curr_tray + 1))
        except ValueError:
            pass

        try:
            prev_to = float(self.entry_to.get().strip())
            interval_diff = prev_to - float(self.entry_from.get().strip())
            new_from = prev_to
            new_to = new_from + (interval_diff if interval_diff > 0 else 2.6)

            self.entry_from.delete(0, "end")
            self.entry_from.insert(0, f"{new_from:.2f}")

            self.entry_to.delete(0, "end")
            self.entry_to.insert(0, f"{new_to:.2f}")
        except ValueError:
            pass

        self._evaluate_preflight()
