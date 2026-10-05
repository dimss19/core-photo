"""Capture Screen (PRD Section 9, 11, 12 & 13).
Integrates live camera stream, framing tools, Tray Crop overlay,
real-time 10-point pre-flight validation, and single-click capture.
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

logger = get_logger(__name__)


class CaptureView(ctk.CTkFrame):
    """Core photography and framing screen."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        # Framing / Crop state
        self.grid_enabled = True
        self.crop_region: Optional[CropRegion] = None
        self._current_photo_image: Optional[ImageTk.PhotoImage] = None
        self._is_capturing = False

        self._build_ui()
        self._setup_bindings()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=3)  # Live view
        self.grid_columnconfigure(1, weight=2)  # Tray controls & preflight
        self.grid_rowconfigure(0, weight=1)

        # ----------------- LEFT: Live View & Framing -----------------
        left_panel = ctk.CTkFrame(self, corner_radius=12)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # Live View Toolbar
        toolbar = ctk.CTkFrame(left_panel, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        self.cam_title_lbl = ctk.CTkLabel(
            toolbar,
            text="Live View",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.cam_title_lbl.pack(side="left")

        self.btn_reconnect = ctk.CTkButton(
            toolbar,
            text="Hubungkan Kamera",
            width=130,
            height=28,
            command=self._on_reconnect_cam
        )
        self.btn_reconnect.pack(side="right", padx=4)

        self.btn_grid_toggle = ctk.CTkButton(
            toolbar,
            text="Grid: ON",
            width=80,
            height=28,
            fg_color="#333333",
            command=self._toggle_grid
        )
        self.btn_grid_toggle.pack(side="right", padx=4)

        # Canvas for Camera Stream & Overlays
        canvas_container = ctk.CTkFrame(left_panel, fg_color="#181818", corner_radius=8)
        canvas_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_container,
            bg="#181818",
            highlightthickness=0,
            cursor="cross"
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Live View Status footer
        self.live_status_lbl = ctk.CTkLabel(
            left_panel,
            text="Inisialisasi kamera...",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.live_status_lbl.grid(row=2, column=0, sticky="w", padx=16, pady=(4, 10))

        # ----------------- RIGHT: Data Tray & Pre-flight -----------------
        right_panel = ctk.CTkScrollableFrame(self, corner_radius=12)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        ctk.CTkLabel(
            right_panel,
            text="Data Tray Core",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=10, pady=(6, 12))

        # Hole ID
        ctk.CTkLabel(right_panel, text="Hole ID (Wajib):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10)
        self.entry_hole = ctk.CTkEntry(right_panel, placeholder_text="Contoh: Core01", height=34)
        self.entry_hole.pack(fill="x", padx=10, pady=(2, 8))

        # Tray ID
        ctk.CTkLabel(right_panel, text="Nomor Tray (Wajib):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10)
        self.entry_tray = ctk.CTkEntry(right_panel, placeholder_text="Contoh: 1", height=34)
        self.entry_tray.pack(fill="x", padx=10, pady=(2, 8))

        # Intervals
        interval_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        interval_frame.pack(fill="x", padx=10, pady=4)
        interval_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(interval_frame, text="Interval Dari (From):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(interval_frame, text="Interval Hingga (To):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.entry_from = ctk.CTkEntry(interval_frame, placeholder_text="0.00", height=34)
        self.entry_from.grid(row=1, column=0, sticky="ew", pady=(2, 4))
        self.entry_from.insert(0, "0.00")

        self.entry_to = ctk.CTkEntry(interval_frame, placeholder_text="2.60", height=34)
        self.entry_to.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(2, 4))
        self.entry_to.insert(0, "2.60")

        # Tray Physical Dimensions (optional)
        dim_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        dim_frame.pack(fill="x", padx=10, pady=4)
        dim_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(dim_frame, text="Baris:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(dim_frame, text="Panjang (cm):", font=ctk.CTkFont(size=11)).grid(row=0, column=1, sticky="w", padx=4)
        ctk.CTkLabel(dim_frame, text="Lebar (cm):", font=ctk.CTkFont(size=11)).grid(row=0, column=2, sticky="w")

        self.entry_rows = ctk.CTkEntry(dim_frame, height=30)
        self.entry_rows.grid(row=1, column=0, sticky="ew")
        self.entry_rows.insert(0, "3")

        self.entry_length = ctk.CTkEntry(dim_frame, height=30)
        self.entry_length.grid(row=1, column=1, sticky="ew", padx=4)
        self.entry_length.insert(0, "100.0")

        self.entry_width = ctk.CTkEntry(dim_frame, height=30)
        self.entry_width.grid(row=1, column=2, sticky="ew")
        self.entry_width.insert(0, "40.0")

        # Comments
        ctk.CTkLabel(right_panel, text="Catatan (Comments):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(6, 2))
        self.entry_comments = ctk.CTkEntry(right_panel, placeholder_text="Kondisi core / keterangan...", height=34)
        self.entry_comments.pack(fill="x", padx=10, pady=(0, 12))

        # Pre-flight Checklist Card
        self.preflight_card = ctk.CTkFrame(right_panel, fg_color="#202020", corner_radius=8)
        self.preflight_card.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            self.preflight_card,
            text="Pemeriksaan Pra-Ambil (Pre-flight)",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.preflight_msg_lbl = ctk.CTkLabel(
            self.preflight_card,
            text="Memeriksa kelayakan capture...",
            font=ctk.CTkFont(size=12),
            text_color="#E5A93C",
            wraplength=280,
            justify="left"
        )
        self.preflight_msg_lbl.pack(anchor="w", padx=12, pady=(0, 10))

        # Action: CAPTURE BUTTON
        self.btn_capture = ctk.CTkButton(
            right_panel,
            text="📸  CAPTURE FOTO",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#2CC985",
            hover_color="#229965",
            command=self._on_capture_click
        )
        self.btn_capture.pack(fill="x", padx=10, pady=(14, 10))

        self.capture_feedback_lbl = ctk.CTkLabel(
            right_panel,
            text="",
            font=ctk.CTkFont(size=12),
            wraplength=280
        )
        self.capture_feedback_lbl.pack(anchor="w", padx=10, pady=4)

    def _setup_bindings(self) -> None:
        """Trace changes in input entries to automatically re-evaluate preflight."""
        for entry in [self.entry_hole, self.entry_tray, self.entry_from, self.entry_to]:
            entry.bind("<KeyRelease>", lambda e: self._evaluate_preflight())

    def start_view(self) -> None:
        """Called when this view becomes active."""
        logger.info("Starting CaptureView live view...")
        self.ctx.subscribe_live_frames(self._handle_incoming_frame)
        self._evaluate_preflight()

    def stop_view(self) -> None:
        """Called when navigating away."""
        logger.info("Stopping CaptureView live view...")
        self.ctx.unsubscribe_live_frames(self._handle_incoming_frame)

    def _handle_incoming_frame(self, frame_rgb: np.ndarray) -> None:
        """Receives RGB frame from background camera thread."""
        try:
            # Safely schedule update on Tkinter main GUI thread
            self.after(0, self._render_frame, frame_rgb)
        except Exception as e:
            logger.debug("Failed to schedule frame render: %s", e)

    def _render_frame(self, frame_rgb: np.ndarray) -> None:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w < 50 or canvas_h < 50:
            return

        frame_h, frame_w = frame_rgb.shape[:2]
        # Calculate aspect ratio fit
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
            # Rule of thirds
            x1 = offset_x + disp_w // 3
            x2 = offset_x + (2 * disp_w) // 3
            y1 = offset_y + disp_h // 3
            y2 = offset_y + (2 * disp_h) // 3
            self.canvas.create_line(x1, offset_y, x1, offset_y + disp_h, fill="#00E5FF", dash=(4, 4))
            self.canvas.create_line(x2, offset_y, x2, offset_y + disp_h, fill="#00E5FF", dash=(4, 4))
            self.canvas.create_line(offset_x, y1, offset_x + disp_w, y1, fill="#00E5FF", dash=(4, 4))
            self.canvas.create_line(offset_x, y2, offset_x + disp_w, y2, fill="#00E5FF", dash=(4, 4))

        # Draw Standard Tray Crop Framing box (300 x 200 aspect ratio)
        crop_w_box = int(disp_w * 0.85)
        crop_h_box = int(crop_w_box / 1.5)  # 300:200 ratio
        if crop_h_box > disp_h * 0.85:
            crop_h_box = int(disp_h * 0.85)
            crop_w_box = int(crop_h_box * 1.5)

        cx1 = offset_x + (disp_w - crop_w_box) // 2
        cy1 = offset_y + (disp_h - crop_h_box) // 2
        cx2 = cx1 + crop_w_box
        cy2 = cy1 + crop_h_box

        # Overlay crop box
        self.canvas.create_rectangle(cx1, cy1, cx2, cy2, outline="#2CC985", width=2)
        self.canvas.create_text(cx1 + 8, cy1 + 14, text="Tray Crop Area (300x200)", fill="#2CC985", anchor="w", font=("Segoe UI", 9, "bold"))

        # Map display crop coordinates back to original frame coordinates for imaging processor
        orig_crop_x = int((cx1 - offset_x) / scale)
        orig_crop_y = int((cy1 - offset_y) / scale)
        orig_crop_w = int(crop_w_box / scale)
        orig_crop_h = int(crop_h_box / scale)
        self.crop_region = CropRegion(x=orig_crop_x, y=orig_crop_y, width=orig_crop_w, height=orig_crop_h)

        status_text = f"Live: {frame_w}x{frame_h} @ ~30 FPS | {self.ctx.camera_manager.get_status_summary()}"
        self.live_status_lbl.configure(text=status_text)

    def _toggle_grid(self) -> None:
        self.grid_enabled = not self.grid_enabled
        self.btn_grid_toggle.configure(text="Grid: ON" if self.grid_enabled else "Grid: OFF")

    def _on_reconnect_cam(self) -> None:
        self.live_status_lbl.configure(text="Menghubungkan ulang kamera...")
        self.ctx.camera_manager.connect_camera()
        self._evaluate_preflight()

    def _evaluate_preflight(self) -> None:
        """Evaluates the 10 pre-flight checks and updates UI."""
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
            crop_region=self.crop_region
        )

        if res.is_ready:
            self.preflight_msg_lbl.configure(
                text="Semua pemeriksaan berhasil. Kamera siap melakukan capture.",
                text_color="#2CC985"
            )
            self.btn_capture.configure(state="normal", fg_color="#2CC985")
        else:
            first_issue = res.summary_errors[0] if res.summary_errors else "Lengkapi data."
            self.preflight_msg_lbl.configure(
                text=f"{first_issue}",
                text_color="#E5A93C"
            )
            self.btn_capture.configure(state="disabled", fg_color="#555555")

    def _on_capture_click(self) -> None:
        if self._is_capturing:
            return

        self._is_capturing = True
        self.btn_capture.configure(text="Mengambil foto...", state="disabled")
        self.capture_feedback_lbl.configure(text="Sedang menyimpan RAW & memproses gambar...", text_color="#3B8ED0")

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
                    comments=comments
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
        self.btn_capture.configure(text="📸  CAPTURE FOTO", state="normal")
        self.capture_feedback_lbl.configure(
            text=f"Berhasil: {photo.filename_base}.jpg",
            text_color="#2CC985"
        )
        # Navigate to Review screen (PRD Section 14)
        self.navigate_fn("review")

    def _on_capture_error(self, err_msg: str) -> None:
        self._is_capturing = False
        self.btn_capture.configure(text="📸  CAPTURE FOTO", state="normal")
        self.capture_feedback_lbl.configure(
            text=f"Gagal capture: {err_msg}",
            text_color="#D9534F"
        )

    def advance_to_next_tray(self) -> None:
        """Auto-increments tray number and updates intervals (PRD Section 6 & 11)."""
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
