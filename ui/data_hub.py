"""Session & Data Archives Hub (Professional Industrial Redesign).
Unified control center for borehole logging sessions, local disk storage archives,
and geological 15-column CSV report generation.
100% Offline Standalone Mode.
Zero emojis, strict industrial standards.
"""

from datetime import datetime
import os
from pathlib import Path
from typing import Callable, List, Optional
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from database.db import DatabaseManager
from database.models import PhotoModel, SessionModel
from database.repositories import SessionRepository
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
    get_font,
)

logger = get_logger(__name__)


class DataHubView(ctk.CTkFrame):
    """Unified offline management view for borehole sessions and local data archives."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self._active_tab = "session"

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # =========================================================================
        # 1. TOP HEADER
        # =========================================================================
        top_header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        top_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))

        header_inner = ctk.CTkFrame(top_header, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=12)

        title_box = ctk.CTkFrame(header_inner, fg_color="transparent")
        title_box.pack(side="left", anchor="w")

        ctk.CTkLabel(
            title_box,
            text="SESSION & DATA ARCHIVES",
            font=get_font(14, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Manage borehole logging sessions, local disk storage archives, and geological CSV report generation.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))


        # =========================================================================
        # 2. MAIN CONTAINER
        # =========================================================================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.main_container.grid_columnconfigure((0, 1), weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Active Session Overview Card
        self.active_session_card = ctk.CTkFrame(
            self.main_container,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.active_session_card.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        active_inner = ctk.CTkFrame(self.active_session_card, fg_color="transparent")
        active_inner.pack(fill="x", padx=16, pady=12)

        # Left info
        info_left = ctk.CTkFrame(active_inner, fg_color="transparent")
        info_left.pack(side="left", anchor="w")

        self.lbl_active_title = ctk.CTkLabel(
            info_left,
            text="ACTIVE SESSION: [None]",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        self.lbl_active_title.pack(anchor="w")

        self.lbl_active_meta = ctk.CTkLabel(
            info_left,
            text="Site: -  ·  Operator: -  ·  Date: -",
            font=get_font(11),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.lbl_active_meta.pack(anchor="w", pady=(2, 2))

        self.lbl_active_stats = ctk.CTkLabel(
            info_left,
            text="Trays: 0  ·  Storage: 0 MB  ·  Status: INACTIVE",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_active_stats.pack(anchor="w")

        # Right actions
        act_right = ctk.CTkFrame(active_inner, fg_color="transparent")
        act_right.pack(side="right", anchor="e")

        btn_open_exp = ctk.CTkButton(
            act_right,
            text="Open Folder in Explorer",
            font=get_font(10, "bold"),
            height=30,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_open_active_folder,
        )
        btn_open_exp.pack(side="left", padx=4)

        btn_export_csv = ctk.CTkButton(
            act_right,
            text="Export CSV Report",
            font=get_font(10, "bold"),
            height=30,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_export_session_csv,
        )
        btn_export_csv.pack(side="left", padx=4)

        # Bottom Split: Create Session (Left) vs Session Archives (Right)
        # Left: Create New Session
        new_card = ctk.CTkFrame(self.main_container, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        new_card.grid(row=1, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(new_card, text="CREATE NEW BOREHOLE SESSION", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(new_card, text="Organize new drill core trays under a unique site and date directory.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 10))

        ctk.CTkLabel(new_card, text="Site / Project Reference *", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        self.entry_site = ctk.CTkEntry(new_card, placeholder_text="e.g. GOSOWONG or PIT_A", height=32, font=get_font(11))
        self.entry_site.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(new_card, text="Operator / Geologist *", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        self.entry_operator = ctk.CTkEntry(new_card, placeholder_text="e.g. J. Smith", height=32, font=get_font(11))
        self.entry_operator.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(new_card, text="Date (YYYYMMDD) *", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        self.entry_date = ctk.CTkEntry(new_card, height=32, font=get_font(11))
        self.entry_date.insert(0, datetime.now().strftime("%Y%m%d"))
        self.entry_date.pack(fill="x", padx=16, pady=(0, 12))

        self.btn_create_session = ctk.CTkButton(
            new_card,
            text="CREATE & ACTIVATE SESSION",
            font=get_font(11, "bold"),
            height=38,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_create_session,
        )
        self.btn_create_session.pack(fill="x", padx=16, pady=(0, 10))

        self.lbl_create_status = ctk.CTkLabel(new_card, text="", font=get_font(10), text_color=COLOR_SUCCESS)
        self.lbl_create_status.pack(padx=16, pady=(0, 10))

        # Right: Session Archives & History
        hist_card = ctk.CTkFrame(self.main_container, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        hist_card.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        hist_card.grid_rowconfigure(1, weight=1)
        hist_card.grid_columnconfigure(0, weight=1)

        hist_header = ctk.CTkFrame(hist_card, fg_color="transparent")
        hist_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(hist_header, text="SESSION ARCHIVE & HISTORY", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(side="left")

        btn_refresh_hist = ctk.CTkButton(
            hist_header,
            text="Refresh",
            font=get_font(10),
            height=24,
            width=65,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._refresh_session_history,
        )
        btn_refresh_hist.pack(side="right")

        self.hist_scroll = ctk.CTkScrollableFrame(hist_card, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        self.hist_scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.hist_scroll.grid_columnconfigure(0, weight=1)

    def select_tab(self, tab_name: str) -> None:
        """Compatibility tab selector (offline data archives view)."""
        self._active_tab = "session"
        self.refresh()

    def refresh(self) -> None:
        """Refreshes active session header and session history."""
        self._refresh_active_session_card()
        self._refresh_session_history()

    def _refresh_active_session_card(self) -> None:
        sess = self.ctx.active_session
        if not sess:
            self.lbl_active_title.configure(text="ACTIVE SESSION: [None]")
            self.lbl_active_meta.configure(text="No active borehole logging session loaded.")
            self.lbl_active_stats.configure(text="Trays: 0  ·  Storage: 0 MB  ·  Status: INACTIVE")
            return

        photos = self.ctx.photo_repo.list_by_session(sess.id, active_only=True) if self.ctx.photo_repo else []
        total_photos = len(photos)
        valid_photos = sum(1 for p in photos if p.status == "VALID")
        pct = (valid_photos / total_photos * 100) if total_photos > 0 else 0.0

        dir_size_mb = 0.0
        display_name = f"{sess.site}_{sess.date}"
        if self.ctx.session_paths and self.ctx.session_paths.session_dir.exists():
            display_name = self.ctx.session_paths.session_dir.name
            try:
                dir_size_bytes = sum(f.stat().st_size for f in self.ctx.session_paths.session_dir.rglob('*') if f.is_file())
                dir_size_mb = dir_size_bytes / (1024 * 1024)
            except Exception:
                pass

        self.lbl_active_title.configure(text=f"ACTIVE SESSION: {display_name}")
        self.lbl_active_meta.configure(text=f"Site: {sess.site}  ·  Operator: {sess.operator}  ·  Date: {sess.date}")
        self.lbl_active_stats.configure(
            text=f"Trays: {total_photos}  ·  Storage: {dir_size_mb:.1f} MB  ·  Audit: {valid_photos}/{total_photos} Valid ({pct:.0f}%)"
        )

    def _refresh_session_history(self) -> None:
        for widget in self.hist_scroll.winfo_children():
            widget.destroy()

        folders = self.ctx.storage_manager.list_sessions()
        if not folders:
            ctk.CTkLabel(self.hist_scroll, text="No previous sessions recorded.", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(pady=30)
            return

        folders.sort(reverse=True)
        for folder_name in folders[:25]:
            row = ctk.CTkFrame(self.hist_scroll, fg_color=COLOR_PANEL, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
            row.pack(fill="x", padx=4, pady=3)

            info_box = ctk.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", padx=10, pady=8)

            is_cur = False
            if self.ctx.session_paths and self.ctx.session_paths.session_dir.name == folder_name:
                is_cur = True
            elif self.ctx.active_session and self.ctx.active_session.id == folder_name:
                is_cur = True

            title_color = COLOR_ACCENT if is_cur else COLOR_TEXT_PRIMARY
            cur_tag = " (Active)" if is_cur else ""

            sub_meta = "Session Directory"
            try:
                paths = self.ctx.storage_manager.get_session_paths(folder_name)
                if paths.db_path.exists():
                    db = DatabaseManager(paths.db_path)
                    s_repo = SessionRepository(db)
                    sess_info = s_repo.get_active() or (s_repo.list_all()[0] if s_repo.list_all() else None)
                    if sess_info:
                        sub_meta = f"Site: {sess_info.site}  ·  Operator: {sess_info.operator}  ·  Date: {sess_info.date}"
            except Exception:
                pass

            ctk.CTkLabel(info_box, text=f"{folder_name}{cur_tag}", font=get_font(11, "bold"), text_color=title_color).pack(anchor="w")
            ctk.CTkLabel(info_box, text=sub_meta, font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w")

            if not is_cur:
                btn_switch = ctk.CTkButton(
                    row,
                    text="Open",
                    font=get_font(10, "bold"),
                    height=26,
                    width=60,
                    corner_radius=4,
                    fg_color=COLOR_PANEL_ALT,
                    text_color=COLOR_TEXT_PRIMARY,
                    border_width=1,
                    border_color=COLOR_BORDER,
                    command=lambda fname=folder_name: self._on_switch_session(fname),
                )
                btn_switch.pack(side="right", padx=10, pady=8)

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    def _on_create_session(self) -> None:
        site = self.entry_site.get().strip().upper()
        operator = self.entry_operator.get().strip()
        date_str = self.entry_date.get().strip()

        if not site or not operator or not date_str:
            self.lbl_create_status.configure(text="Please fill in Site, Operator, and Date.", text_color=COLOR_ERROR)
            return

        try:
            sess = self.ctx.create_session(site=site, date=date_str, operator=operator)
            self.lbl_create_status.configure(text=f"Session {sess.id} created successfully!", text_color=COLOR_SUCCESS)
            self.refresh()
        except Exception as e:
            logger.error("Failed creating session: %s", e)
            self.lbl_create_status.configure(text=f"Error: {e}", text_color=COLOR_ERROR)

    def _on_switch_session(self, folder_name: str) -> None:
        try:
            self.ctx.open_session(folder_name)
            self.refresh()
        except Exception as e:
            logger.error("Failed switching session to %s: %s", folder_name, e)

    def _on_open_active_folder(self) -> None:
        target_dir = None
        if self.ctx.session_paths and self.ctx.session_paths.session_dir.exists():
            target_dir = self.ctx.session_paths.session_dir
        elif self.ctx.active_session:
            sess = self.ctx.active_session
            for cand in self.ctx.storage_manager.list_sessions():
                if cand == f"{sess.site}_{sess.date}" or cand.startswith(f"{sess.site}_{sess.date}") or cand == sess.id:
                    cand_path = self.ctx.storage_manager.get_session_paths(cand).session_dir
                    if cand_path.exists():
                        target_dir = cand_path
                        break

        if not target_dir or not target_dir.exists():
            target_dir = self.ctx.storage_manager.sessions_dir

        if target_dir and target_dir.exists():
            try:
                os.startfile(str(target_dir))
                logger.info("Opened folder in Explorer: %s", target_dir)
            except Exception as e:
                logger.error("os.startfile failed for %s: %s", target_dir, e)
                try:
                    import subprocess
                    subprocess.Popen(f'explorer "{target_dir}"', shell=True)
                except Exception as ex:
                    logger.error("subprocess explorer failed: %s", ex)

    def _on_export_session_csv(self) -> None:
        from tkinter import filedialog
        sess = self.ctx.active_session
        if not sess:
            return

        photos = self.ctx.photo_repo.list_by_session(sess.id) if self.ctx.photo_repo else []
        hole_id = photos[0].hole_id if photos and photos[0].hole_id else "TSD168"

        dest = filedialog.asksaveasfilename(
            title="Export Geological Report CSV",
            initialfile=f"{hole_id}.csv",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
        )
        if dest:
            from imaging.processor import ImageProcessor
            out_path = ImageProcessor.export_csv_report(sess, photos, Path(dest))
            try:
                os.startfile(str(out_path))
            except Exception:
                pass
