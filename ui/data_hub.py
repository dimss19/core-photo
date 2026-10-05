"""Data & Transfer Hub (Professional Industrial Redesign).
Unified control center for borehole logging sessions, local storage archives,
CSV report generation, and central server synchronization.
Zero emojis, strict professional standards.
"""

from datetime import datetime
import os
from pathlib import Path
import threading
from typing import Callable, List, Optional
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from database.models import PhotoModel, SessionModel
from transfer.uploader import TransferUploader
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_ACCENT_LIGHT,
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


class DataHubView(ctk.CTkFrame):
    """Unified management view for sessions, local data archives, and server transfer."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()
        self.uploader = TransferUploader(
            photo_repo=self.ctx.photo_repo,
            transfer_repo=self.ctx.transfer_repo,
        )
        self._is_transferring = False
        self._active_tab = "session"  # "session" or "transfer"

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # =========================================================================
        # 1. TOP HEADER & SEGMENTED TAB SELECTOR
        # =========================================================================
        top_header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        top_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))

        header_inner = ctk.CTkFrame(top_header, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=12)

        title_box = ctk.CTkFrame(header_inner, fg_color="transparent")
        title_box.pack(side="left", anchor="w")

        ctk.CTkLabel(
            title_box,
            text="DATA MANAGEMENT & TRANSFER HUB",
            font=get_font(14, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Manage borehole logging sessions, archive directories, CSV reports, and central server synchronization.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Segmented Tab Buttons
        tab_btn_box = ctk.CTkFrame(header_inner, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        tab_btn_box.pack(side="right", anchor="e")

        self.btn_tab_session = ctk.CTkButton(
            tab_btn_box,
            text="SESSIONS & ARCHIVES",
            font=get_font(10, "bold"),
            height=30,
            width=150,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=lambda: self.select_tab("session"),
        )
        self.btn_tab_session.pack(side="left", padx=2, pady=2)

        self.btn_tab_transfer = ctk.CTkButton(
            tab_btn_box,
            text="SERVER SYNC & TRANSFER",
            font=get_font(10, "bold"),
            height=30,
            width=160,
            corner_radius=4,
            fg_color="transparent",
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            command=lambda: self.select_tab("transfer"),
        )
        self.btn_tab_transfer.pack(side="left", padx=2, pady=2)

        # =========================================================================
        # 2. MAIN CONTAINER FOR TAB PAGES
        # =========================================================================
        self.tab_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.tab_container.grid_columnconfigure(0, weight=1)
        self.tab_container.grid_rowconfigure(0, weight=1)

        self._build_session_tab()
        self._build_transfer_tab()

    def select_tab(self, tab_name: str) -> None:
        """Switches between 'session' and 'transfer' tab pages."""
        norm_tab = "transfer" if tab_name.lower() in ("transfer", "sync") else "session"
        self._active_tab = norm_tab

        if norm_tab == "session":
            self.btn_tab_session.configure(fg_color=COLOR_ACCENT, text_color="#FFFFFF")
            self.btn_tab_transfer.configure(fg_color="transparent", text_color=COLOR_TEXT_PRIMARY)
            self.frame_transfer.grid_forget()
            self.frame_session.grid(row=0, column=0, sticky="nsew")
        else:
            self.btn_tab_session.configure(fg_color="transparent", text_color=COLOR_TEXT_PRIMARY)
            self.btn_tab_transfer.configure(fg_color=COLOR_ACCENT, text_color="#FFFFFF")
            self.frame_session.grid_forget()
            self.frame_transfer.grid(row=0, column=0, sticky="nsew")

        self.refresh()

    # =========================================================================
    # TAB 1: SESSIONS & ARCHIVES
    # =========================================================================
    def _build_session_tab(self) -> None:
        self.frame_session = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.frame_session.grid(row=0, column=0, sticky="nsew")
        self.frame_session.grid_columnconfigure((0, 1), weight=1)
        self.frame_session.grid_rowconfigure(1, weight=1)

        # Active Session Overview Card
        self.active_session_card = ctk.CTkFrame(
            self.frame_session,
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
        new_card = ctk.CTkFrame(self.frame_session, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
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
        hist_card = ctk.CTkFrame(self.frame_session, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
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

    # =========================================================================
    # TAB 2: SERVER SYNC & TRANSFER
    # =========================================================================
    def _build_transfer_tab(self) -> None:
        self.frame_transfer = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        # grid managed in select_tab
        self.frame_transfer.grid_columnconfigure(0, weight=2)
        self.frame_transfer.grid_columnconfigure(1, weight=3)
        self.frame_transfer.grid_rowconfigure(0, weight=1)

        # Left Column: Configuration & Upload Controls
        cfg_panel = ctk.CTkScrollableFrame(self.frame_transfer, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        cfg_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(cfg_panel, text="CENTRAL SERVER ENDPOINT", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(cfg_panel, text="Target geological database API destination.", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 10))

        ctk.CTkLabel(cfg_panel, text="Server API URL *", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        server_url = self.ctx.config_manager.get("transfer", "server_url", "http://127.0.0.1:8000/api/v1")
        self.entry_url = ctk.CTkEntry(cfg_panel, height=32, font=get_font(11))
        self.entry_url.insert(0, server_url)
        self.entry_url.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(cfg_panel, text="API Key / Token (Optional)", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        api_key = self.ctx.config_manager.get("transfer", "api_key", "")
        self.entry_key = ctk.CTkEntry(cfg_panel, height=32, font=get_font(11), show="*")
        self.entry_key.insert(0, api_key)
        self.entry_key.pack(fill="x", padx=16, pady=(0, 10))

        # Test Connection & Save Row
        btn_box = ctk.CTkFrame(cfg_panel, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 14))
        btn_box.grid_columnconfigure((0, 1), weight=1)

        self.btn_save_cfg = ctk.CTkButton(
            btn_box,
            text="Save Settings",
            font=get_font(10, "bold"),
            height=30,
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            text_color="#FFFFFF",
            command=self._on_save_config,
        )
        self.btn_save_cfg.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_test_conn = ctk.CTkButton(
            btn_box,
            text="Test Connection",
            font=get_font(10, "bold"),
            height=30,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_test_connection,
        )
        self.btn_test_conn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.lbl_conn_status = ctk.CTkLabel(cfg_panel, text="", font=get_font(10), text_color=COLOR_TEXT_MUTED)
        self.lbl_conn_status.pack(anchor="w", padx=16, pady=(0, 10))

        # Batch Transfer Controls Card
        ctk.CTkLabel(cfg_panel, text="SYNCHRONIZATION CONTROLS", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(anchor="w", padx=16, pady=(10, 2))
        
        stat_frame = ctk.CTkFrame(cfg_panel, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        stat_frame.pack(fill="x", padx=16, pady=(2, 10))

        self.lbl_transfer_summary = ctk.CTkLabel(
            stat_frame,
            text="Pending: 0  ·  Uploaded: 0  ·  Failed: 0",
            font=get_font(11, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.lbl_transfer_summary.pack(padx=12, pady=10)

        self.btn_start_sync = ctk.CTkButton(
            cfg_panel,
            text="START BATCH TRANSFER",
            font=get_font(12, "bold"),
            height=40,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_start_batch_transfer,
        )
        self.btn_start_sync.pack(fill="x", padx=16, pady=(0, 6))

        self.btn_retry_failed = ctk.CTkButton(
            cfg_panel,
            text="Retry Failed Uploads",
            font=get_font(10, "bold"),
            height=32,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_retry_failed,
        )
        self.btn_retry_failed.pack(fill="x", padx=16, pady=(0, 14))

        # Right Column: Transfer Queue & Live Progress
        queue_panel = ctk.CTkFrame(self.frame_transfer, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        queue_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        queue_panel.grid_rowconfigure(1, weight=1)
        queue_panel.grid_columnconfigure(0, weight=1)

        queue_head = ctk.CTkFrame(queue_panel, fg_color="transparent")
        queue_head.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(queue_head, text="TRANSFER QUEUE & STATUS LOG", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(side="left")
        
        btn_refresh_q = ctk.CTkButton(
            queue_head,
            text="Refresh",
            font=get_font(10),
            height=24,
            width=65,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._refresh_transfer_queue,
        )
        btn_refresh_q.pack(side="right")

        self.queue_scroll = ctk.CTkScrollableFrame(queue_panel, fg_color=COLOR_PANEL_ALT, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
        self.queue_scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.queue_scroll.grid_columnconfigure(0, weight=1)

    # =========================================================================
    # REFRESH & DATA LOGIC
    # =========================================================================
    def refresh(self) -> None:
        """Refreshes active session header and the currently visible tab."""
        self._refresh_active_session_card()
        if self._active_tab == "session":
            self._refresh_session_history()
        else:
            self._refresh_transfer_queue()

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

        sp = self.ctx.storage_manager.get_session_paths(f"{sess.site}_{sess.date}")
        dir_size_mb = 0.0
        if sp.session_dir.exists():
            try:
                dir_size_bytes = sum(f.stat().st_size for f in sp.session_dir.rglob('*') if f.is_file())
                dir_size_mb = dir_size_bytes / (1024 * 1024)
            except Exception:
                pass

        self.lbl_active_title.configure(text=f"ACTIVE SESSION: {sess.site}_{sess.date}")
        self.lbl_active_meta.configure(text=f"Site: {sess.site}  ·  Operator: {sess.operator}  ·  Date: {sess.date}")
        self.lbl_active_stats.configure(
            text=f"Trays: {total_photos}  ·  Storage: {dir_size_mb:.1f} MB  ·  Audit: {valid_photos}/{total_photos} Valid ({pct:.0f}%)"
        )

    def _refresh_session_history(self) -> None:
        for widget in self.hist_scroll.winfo_children():
            widget.destroy()

        sessions = self.ctx.session_repo.list_all() if self.ctx.session_repo else []
        if not sessions:
            ctk.CTkLabel(self.hist_scroll, text="No previous sessions recorded.", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(pady=30)
            return

        for s in reversed(sessions[-15:]):
            row = ctk.CTkFrame(self.hist_scroll, fg_color=COLOR_PANEL, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
            row.pack(fill="x", padx=4, pady=3)

            info_box = ctk.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", padx=10, pady=8)

            is_cur = self.ctx.active_session and self.ctx.active_session.id == s.id
            title_color = COLOR_ACCENT if is_cur else COLOR_TEXT_PRIMARY
            cur_tag = " (Active)" if is_cur else ""

            ctk.CTkLabel(info_box, text=f"{s.site}_{s.date}{cur_tag}", font=get_font(11, "bold"), text_color=title_color).pack(anchor="w")
            ctk.CTkLabel(info_box, text=f"Operator: {s.operator}  ·  Created: {s.created_at[:10]}", font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w")

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
                    command=lambda sid=s.id: self._on_switch_session(sid),
                )
                btn_switch.pack(side="right", padx=10, pady=8)

    def _refresh_transfer_queue(self) -> None:
        for widget in self.queue_scroll.winfo_children():
            widget.destroy()

        sess = self.ctx.active_session
        if not sess or not self.ctx.photo_repo:
            ctk.CTkLabel(self.queue_scroll, text="No active session photos.", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(pady=30)
            self.lbl_transfer_summary.configure(text="Pending: 0  ·  Uploaded: 0  ·  Failed: 0")
            return

        photos = self.ctx.photo_repo.list_by_session(sess.id, active_only=True)
        pending = sum(1 for p in photos if p.status != "TRANSFERRED")
        uploaded = sum(1 for p in photos if p.status == "TRANSFERRED")
        failed = sum(1 for p in photos if p.status == "FAILED")

        self.lbl_transfer_summary.configure(text=f"Pending: {pending}  ·  Uploaded: {uploaded}  ·  Failed: {failed}")

        if not photos:
            ctk.CTkLabel(self.queue_scroll, text="No photos captured in this session yet.", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(pady=30)
            return

        for p in photos:
            card = ctk.CTkFrame(self.queue_scroll, fg_color=COLOR_PANEL, corner_radius=4, border_width=1, border_color=COLOR_BORDER)
            card.pack(fill="x", padx=4, pady=2)

            left_b = ctk.CTkFrame(card, fg_color="transparent")
            left_b.pack(side="left", padx=10, pady=6)

            ctk.CTkLabel(left_b, text=f"{p.filename_base}.jpg", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(left_b, text=f"Hole: {p.hole_id}  ·  Tray {p.tray_number} ({p.interval_from:.2f}-{p.interval_to:.2f}m)", font=get_font(9), text_color=COLOR_TEXT_MUTED).pack(anchor="w")

            status_color = COLOR_SUCCESS if p.status == "TRANSFERRED" else (COLOR_ERROR if p.status == "FAILED" else COLOR_TEXT_MUTED)
            badge = ctk.CTkLabel(card, text=p.status, font=get_font(9, "bold"), text_color=status_color)
            badge.pack(side="right", padx=10, pady=6)

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

    def _on_switch_session(self, session_id: str) -> None:
        try:
            self.ctx.open_session(session_id)
            self.refresh()
        except Exception as e:
            logger.error("Failed switching session to %s: %s", session_id, e)

    def _on_open_active_folder(self) -> None:
        sess = self.ctx.active_session
        if sess:
            sp = self.ctx.storage_manager.get_session_paths(f"{sess.site}_{sess.date}")
            try:
                os.startfile(str(sp.session_dir))
            except Exception as e:
                logger.error("Failed opening folder %s: %s", sp.session_dir, e)

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

    def _on_save_config(self) -> None:
        url = self.entry_url.get().strip()
        key = self.entry_key.get().strip()
        self.ctx.config_manager.set("transfer", "server_url", url)
        self.ctx.config_manager.set("transfer", "api_key", key)
        self.ctx.config_manager.save()
        self.lbl_conn_status.configure(text="Endpoint configuration saved.", text_color=COLOR_SUCCESS)

    def _on_test_connection(self) -> None:
        url = self.entry_url.get().strip()
        self.lbl_conn_status.configure(text="Testing connection...", text_color=COLOR_TEXT_MUTED)

        def run_test():
            ok, msg = self.uploader.test_connection(server_url=url)
            color = COLOR_SUCCESS if ok else COLOR_ERROR
            txt = f"✓ {msg}" if ok else f"✗ {msg}"
            self.after(0, lambda: self.lbl_conn_status.configure(text=txt, text_color=color))

        threading.Thread(target=run_test, daemon=True).start()

    def _on_start_batch_transfer(self) -> None:
        if self._is_transferring:
            return

        sess = self.ctx.active_session
        if not sess:
            return

        self._is_transferring = True
        self.btn_start_sync.configure(state="disabled", text="TRANSFERRING...")

        def run_sync():
            try:
                photos = self.ctx.photo_repo.list_by_session(sess.id, active_only=True)
                for p in photos:
                    if p.status != "TRANSFERRED":
                        self.uploader.upload_photo(p)
            finally:
                self._is_transferring = False
                self.after(0, self._on_sync_finished)

        threading.Thread(target=run_sync, daemon=True).start()

    def _on_sync_finished(self) -> None:
        self.btn_start_sync.configure(state="normal", text="START BATCH TRANSFER")
        self._refresh_transfer_queue()

    def _on_retry_failed(self) -> None:
        if self._is_transferring:
            return
        sess = self.ctx.active_session
        if not sess or not self.ctx.photo_repo:
            return

        self._is_transferring = True
        self.btn_retry_failed.configure(state="disabled", text="RETRYING...")

        def run_retry():
            try:
                photos = self.ctx.photo_repo.list_by_session(sess.id, active_only=True)
                for p in photos:
                    if p.status == "FAILED":
                        self.uploader.upload_photo(p)
            finally:
                self._is_transferring = False
                self.after(0, lambda: (
                    self.btn_retry_failed.configure(state="normal", text="Retry Failed Uploads"),
                    self._refresh_transfer_queue()
                ))

        threading.Thread(target=run_retry, daemon=True).start()

