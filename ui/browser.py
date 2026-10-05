"""Photo Browser Screen (PRD Section 21).
Enables browsing, searching (Hole ID, Tray, Interval), inspecting thumbnails,
and viewing metadata without 3D complexity.
Designed with Light Mode aesthetics, clean filters, and gallery cards.
"""

from pathlib import Path
from typing import Callable, List, Optional
import customtkinter as ctk
from PIL import Image

from core.app_context import get_app_context
from core.logger import get_logger
from database.models import PhotoModel

logger = get_logger(__name__)


class BrowserView(ctk.CTkFrame):
    """Photo gallery and inspection browser."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color="#F8FAFC", **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self._thumb_cache = []
        self._selected_photo: Optional[PhotoModel] = None
        self._preview_ctk_img: Optional[ctk.CTkImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=3)  # Thumbnail gallery
        self.grid_columnconfigure(1, weight=2)  # Inspector details
        self.grid_rowconfigure(1, weight=1)

        # ----------------- Top Filter Bar -----------------
        filter_bar = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        filter_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 10))

        title_box = ctk.CTkFrame(filter_bar, fg_color="transparent")
        title_box.pack(side="left", padx=(16, 20), pady=12)

        ctk.CTkLabel(
            title_box,
            text="🔍 Photo Browser",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Jelajahi dan cari foto drill core dari sesi aktif.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        ).pack(anchor="w")

        # Search & Filter inputs
        controls_box = ctk.CTkFrame(filter_bar, fg_color="transparent")
        controls_box.pack(side="right", padx=16, pady=12)

        self.search_entry = ctk.CTkEntry(
            controls_box,
            placeholder_text="Cari Hole ID atau Tray...",
            width=220,
            height=36,
            fg_color="#F8FAFC",
            border_color="#CBD5E1"
        )
        self.search_entry.pack(side="left", padx=6)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        self.status_filter = ctk.CTkOptionMenu(
            controls_box,
            values=["Semua Status", "VALID", "PROCESSED", "INVALID", "TRANSFERRED"],
            command=lambda v: self.refresh(),
            height=36,
            width=140,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            button_color="#E2E8F0",
            button_hover_color="#CBD5E1"
        )
        self.status_filter.pack(side="left", padx=6)

        btn_refresh = ctk.CTkButton(
            controls_box,
            text="Segarkan",
            width=84,
            height=36,
            corner_radius=6,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            command=self.refresh
        )
        btn_refresh.pack(side="left", padx=6)

        # ----------------- Left: Scrollable Thumbnail Grid -----------------
        self.grid_container = ctk.CTkScrollableFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E2E8F0"
        )
        self.grid_container.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 16))
        self.grid_container.grid_columnconfigure((0, 1, 2), weight=1)

        # ----------------- Right: Inspector Details -----------------
        self.detail_panel = ctk.CTkScrollableFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E2E8F0"
        )
        self.detail_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 16))

        ctk.CTkLabel(
            self.detail_panel,
            text="Detail Foto Terpilih",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            self.detail_panel,
            text="Klik salah satu kartu foto di galeri untuk melihat detail lengkap.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        preview_card = ctk.CTkFrame(self.detail_panel, fg_color="#F1F5F9", corner_radius=8, border_width=1, border_color="#E2E8F0")
        preview_card.pack(fill="x", padx=16, pady=4)

        self.detail_img_lbl = ctk.CTkLabel(
            preview_card,
            text="Pilih foto dari galeri",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        )
        self.detail_img_lbl.pack(padx=12, pady=16)

        self.detail_info_lbl = ctk.CTkLabel(
            self.detail_panel,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#334155",
            justify="left",
            wraplength=300
        )
        self.detail_info_lbl.pack(anchor="w", padx=16, pady=10)

    def refresh(self) -> None:
        """Reloads photos from database matching active search filters."""
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self._thumb_cache.clear()

        if not self.ctx.photo_repo or not self.ctx.active_session:
            empty_lbl = ctk.CTkLabel(
                self.grid_container,
                text="Belum ada sesi aktif atau belum ada foto yang diambil.\nBuat sesi dan ambil foto untuk melihat galeri.",
                font=ctk.CTkFont(size=13),
                text_color="#94A3B8",
                justify="center"
            )
            empty_lbl.grid(row=0, column=0, columnspan=3, pady=60)
            return

        query = self.search_entry.get().strip()
        status_sel = self.status_filter.get()
        status_param = None if status_sel == "Semua Status" else status_sel

        photos = self.ctx.photo_repo.search(
            hole_id=query if query else None,
            tray_number=query if query else None,
            status=status_param
        )

        if not photos:
            empty_lbl = ctk.CTkLabel(
                self.grid_container,
                text="Tidak ada foto yang cocok dengan kata kunci pencarian.",
                font=ctk.CTkFont(size=13),
                text_color="#94A3B8"
            )
            empty_lbl.grid(row=0, column=0, columnspan=3, pady=60)
            return

        col_count = 3
        for idx, photo in enumerate(photos):
            row = idx // col_count
            col = idx % col_count

            card = ctk.CTkFrame(
                self.grid_container,
                fg_color="#F8FAFC",
                corner_radius=8,
                border_width=1,
                border_color="#E2E8F0",
                cursor="hand2"
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            # Load thumbnail
            thumb_path = Path(photo.thumbnail_path) if photo.thumbnail_path else None
            if thumb_path and thumb_path.exists():
                try:
                    pil_thumb = Image.open(thumb_path)
                    ctk_thumb = ctk.CTkImage(light_image=pil_thumb, dark_image=pil_thumb, size=(120, 80))
                    self._thumb_cache.append(ctk_thumb)
                    thumb_lbl = ctk.CTkLabel(card, image=ctk_thumb, text="")
                    thumb_lbl.pack(padx=8, pady=(8, 4))
                except Exception:
                    ctk.CTkLabel(card, text="[No Thumb]", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(pady=20)
            else:
                ctk.CTkLabel(card, text="[No Thumb]", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(pady=20)

            title_lbl = ctk.CTkLabel(
                card,
                text=f"{photo.hole_id} (Tray {photo.tray_number})",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#1E293B"
            )
            title_lbl.pack(padx=6, pady=2)

            sub_lbl = ctk.CTkLabel(
                card,
                text=f"{photo.interval_from:.2f} - {photo.interval_to:.2f} m",
                font=ctk.CTkFont(size=11),
                text_color="#64748B"
            )
            sub_lbl.pack(padx=6, pady=1)

            # Status pill
            is_valid = photo.status in ("VALID", "TRANSFERRED")
            status_color = "#059669" if is_valid else "#D97706"
            status_bg = "#ECFDF5" if is_valid else "#FFFBEB"

            pill = ctk.CTkLabel(
                card,
                text=f" {photo.status} ",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=status_color,
                fg_color=status_bg,
                corner_radius=4
            )
            pill.pack(padx=6, pady=(2, 8))

            # Click binding to inspect
            for widget in [card, title_lbl, sub_lbl, pill]:
                widget.bind("<Button-1>", lambda e, p=photo: self._inspect_photo(p))

        # Select first photo by default if none selected
        if not self._selected_photo and photos:
            self._inspect_photo(photos[0])

    def _inspect_photo(self, photo: PhotoModel) -> None:
        self._selected_photo = photo
        jpg_path = Path(photo.jpg_path) if photo.jpg_path else None

        if jpg_path and jpg_path.exists():
            try:
                pil_img = Image.open(jpg_path)
                self._preview_ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(300, 200))
                self.detail_img_lbl.configure(image=self._preview_ctk_img, text="")
            except Exception as e:
                logger.error("Error opening image %s: %s", jpg_path, e)
                self.detail_img_lbl.configure(image="", text="Gagal memuat gambar.")
        else:
            self.detail_img_lbl.configure(image="", text="File gambar tidak tersedia.")

        details_text = (
            f"• Nama File: {photo.filename_base}.jpg\n"
            f"• Hole ID: {photo.hole_id}\n"
            f"• Nomor Tray: {photo.tray_number}\n"
            f"• Interval: {photo.interval_from:.2f} m - {photo.interval_to:.2f} m\n"
            f"• Status Data: {photo.status}\n"
            f"• Waktu Capture: {photo.captured_at or '-'}\n"
            f"• MD5 RAW: {photo.md5_raw}\n"
            f"• MD5 JPG: {photo.md5_jpg}\n"
            f"• Model Kamera: {photo.camera_model}\n"
            f"• Lokasi File RAW:\n  {photo.raw_path}\n"
            f"• Lokasi File JPG:\n  {photo.jpg_path}"
        )
        self.detail_info_lbl.configure(text=details_text)
