"""Session & Data Archives Hub (Professional Industrial Redesign).
Unified control center for borehole logging sessions, local disk storage archives,
and geological 15-column CSV report generation.
Zero emojis, strict industrial standards.
"""

from datetime import datetime
import os
from pathlib import Path
from tkinter import filedialog, messagebox
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
    COLOR_ERROR_BG,
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


class EditSessionModal(ctk.CTkToplevel):
    """Clean industrial modal dialog for updating session metadata."""

    def __init__(
        self,
        parent,
        folder_name: str,
        initial_site: str,
        initial_operator: str,
        initial_date: str,
        on_save_callback: Callable[[str, str, str, str], bool],
    ):
        super().__init__(parent)
        self.folder_name = folder_name
        self.on_save_callback = on_save_callback

        self.title("Edit Session")
        self.geometry("420x350")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        try:
            top_window = parent.winfo_toplevel()
            self.transient(top_window)
            x = top_window.winfo_x() + (top_window.winfo_width() // 2) - 210
            y = top_window.winfo_y() + (top_window.winfo_height() // 2) - 175
            self.geometry(f"420x350+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.grab_set()

        card = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            card,
            text="EDIT SESSION METADATA",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=16, pady=(16, 2))

        ctk.CTkLabel(
            card,
            text=f"Archive: {folder_name}",
            font=get_font(10),
            text_color=COLOR_TEXT_HINT,
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Site Code
        ctk.CTkLabel(card, text="Site Code *", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        self.entry_site = ctk.CTkEntry(card, height=30, font=get_font(11))
        self.entry_site.insert(0, initial_site)
        self.entry_site.pack(fill="x", padx=16, pady=(0, 6))

        # Operator
        ctk.CTkLabel(card, text="Operator Name", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        self.entry_operator = ctk.CTkEntry(card, height=30, font=get_font(11))
        self.entry_operator.insert(0, initial_operator)
        self.entry_operator.pack(fill="x", padx=16, pady=(0, 6))

        # Date
        ctk.CTkLabel(card, text="Date (YYYYMMDD) *", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        self.entry_date = ctk.CTkEntry(card, height=30, font=get_font(11))
        self.entry_date.insert(0, initial_date)
        self.entry_date.pack(fill="x", padx=16, pady=(0, 10))

        self.lbl_status = ctk.CTkLabel(card, text="", font=get_font(10), text_color=COLOR_ERROR)
        self.lbl_status.pack(padx=16, pady=(0, 6))

        # Actions
        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 14))

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Cancel",
            font=get_font(10, "bold"),
            height=30,
            width=80,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.destroy,
        )
        btn_cancel.pack(side="left")

        btn_save = ctk.CTkButton(
            btn_box,
            text="Save Changes",
            font=get_font(10, "bold"),
            height=30,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_save,
        )
        btn_save.pack(side="right")

    def _on_save(self) -> None:
        site = self.entry_site.get().strip().upper()
        op = self.entry_operator.get().strip()
        dt = self.entry_date.get().strip()
        if not site or not dt:
            self.lbl_status.configure(text="Site Code and Date cannot be blank.")
            return

        success = self.on_save_callback(self.folder_name, site, op, dt)
        if success:
            self.destroy()
        else:
            self.lbl_status.configure(text="Failed to update session database.")


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
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # MAIN CONTAINER
        # =========================================================================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=16)
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

        self.btn_edit_active = ctk.CTkButton(
            act_right,
            text="Edit Session",
            font=get_font(10, "bold"),
            height=30,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_edit_active_session,
        )
        self.btn_edit_active.pack(side="left", padx=4)

        btn_open_exp = ctk.CTkButton(
            act_right,
            text="Open Folder in Explorer",
            font=get_font(10, "bold"),
            height=30,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._on_open_active_folder,
        )
        btn_open_exp.pack(side="left", padx=4)

        btn_export_csv = ctk.CTkButton(
            act_right,
            text="Export CSV",
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

        ctk.CTkLabel(new_card, text="Operator Name", font=get_font(10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(2, 1))
        self.entry_operator = ctk.CTkEntry(new_card, placeholder_text="e.g. Geologist / Field Tech", height=32, font=get_font(11))
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

        # Right: Session Archives
        hist_card = ctk.CTkFrame(self.main_container, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        hist_card.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        hist_card.grid_rowconfigure(1, weight=1)
        hist_card.grid_columnconfigure(0, weight=1)

        hist_header = ctk.CTkFrame(hist_card, fg_color="transparent")
        hist_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        ctk.CTkLabel(hist_header, text="SESSION ARCHIVE", font=get_font(12, "bold"), text_color=COLOR_CHARCOAL).pack(side="left")

        btn_refresh_hist = ctk.CTkButton(
            hist_header,
            text="Refresh",
            font=get_font(10),
            height=24,
            width=65,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
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

    def _notify_app_state(self) -> None:
        """Notifies top window to refresh system status indicators."""
        try:
            app_win = self.winfo_toplevel()
            if hasattr(app_win, "_update_top_header"):
                app_win._update_top_header()
        except Exception:
            pass

    def _refresh_active_session_card(self) -> None:
        sess = self.ctx.active_session
        if not sess:
            self.lbl_active_title.configure(text="ACTIVE SESSION: [None]")
            self.lbl_active_meta.configure(text="No active borehole logging session loaded.")
            self.lbl_active_stats.configure(text="Trays: 0  ·  Storage: 0 MB  ·  Status: INACTIVE")
            if hasattr(self, "btn_edit_active"):
                self.btn_edit_active.configure(state="disabled")
            return

        if hasattr(self, "btn_edit_active"):
            self.btn_edit_active.configure(state="normal")

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

        op_str = f"  ·  Operator: {sess.operator}" if sess.operator and sess.operator.strip() else ""
        self.lbl_active_title.configure(text=f"ACTIVE SESSION: {display_name}")
        self.lbl_active_meta.configure(text=f"Site: {sess.site}{op_str}  ·  Date: {sess.date}")
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
            info_box.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            is_cur = False
            if self.ctx.session_paths and self.ctx.session_paths.session_dir.name == folder_name:
                is_cur = True
            elif self.ctx.active_session and self.ctx.active_session.id == folder_name:
                is_cur = True

            title_color = COLOR_ACCENT if is_cur else COLOR_TEXT_PRIMARY
            cur_tag = " (Active)" if is_cur else ""

            site_val = ""
            op_val = ""
            date_val = ""
            tray_count = 0
            photo_count = 0
            has_db = False

            try:
                paths = self.ctx.storage_manager.get_session_paths(folder_name)
                if paths.db_path.exists():
                    has_db = True
                    db = DatabaseManager(paths.db_path)
                    try:
                        s_repo = SessionRepository(db)
                        sess_info = s_repo.get_active() or (s_repo.list_all()[0] if s_repo.list_all() else None)
                        if sess_info:
                            site_val = sess_info.site
                            op_val = sess_info.operator or ""
                            date_val = sess_info.date

                        t_row = db.execute_one("SELECT COUNT(*) AS c FROM trays")
                        if t_row:
                            tray_count = t_row["c"]
                        p_row = db.execute_one("SELECT COUNT(*) AS c FROM photos")
                        if p_row:
                            photo_count = p_row["c"]
                    finally:
                        db.close()
            except Exception as e:
                logger.debug("Could not inspect session %s: %s", folder_name, e)

            if not site_val and "_" in folder_name:
                parts = folder_name.split("_")
                site_val = parts[0]
                if len(parts) > 1:
                    date_val = parts[1]

            op_info = f"  ·  Operator: {op_val}" if op_val else ""
            stat_info = f"  ·  Trays: {tray_count}  ·  Photos: {photo_count}" if has_db else ""
            sub_meta = f"Site: {site_val or '-'}  ·  Date: {date_val or '-'}{op_info}{stat_info}"

            ctk.CTkLabel(info_box, text=f"{folder_name}{cur_tag}", font=get_font(11, "bold"), text_color=title_color).pack(anchor="w")
            ctk.CTkLabel(info_box, text=sub_meta, font=get_font(10), text_color=COLOR_TEXT_MUTED).pack(anchor="w")

            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=10, pady=8)

            if not is_cur:
                btn_switch = ctk.CTkButton(
                    btn_box,
                    text="Open",
                    font=get_font(10, "bold"),
                    height=26,
                    width=50,
                    corner_radius=4,
                    fg_color=COLOR_PANEL_ALT,
                    hover_color=COLOR_BORDER,
                    text_color=COLOR_TEXT_PRIMARY,
                    border_width=1,
                    border_color=COLOR_BORDER,
                    command=lambda fname=folder_name: self._on_switch_session(fname),
                )
                btn_switch.pack(side="left", padx=2)

            btn_edit = ctk.CTkButton(
                btn_box,
                text="Edit",
                font=get_font(10),
                height=26,
                width=46,
                corner_radius=4,
                fg_color=COLOR_PANEL_ALT,
                hover_color=COLOR_BORDER,
                text_color=COLOR_TEXT_PRIMARY,
                border_width=1,
                border_color=COLOR_BORDER,
                command=lambda fname=folder_name, s=site_val, o=op_val, d=date_val: self._on_edit_session(fname, s, o, d),
            )
            btn_edit.pack(side="left", padx=2)

            btn_del = ctk.CTkButton(
                btn_box,
                text="Delete",
                font=get_font(10),
                height=26,
                width=50,
                corner_radius=4,
                fg_color=COLOR_PANEL_ALT,
                hover_color=COLOR_ERROR_BG,
                text_color=COLOR_ERROR,
                border_width=1,
                border_color=COLOR_BORDER,
                command=lambda fname=folder_name: self._on_delete_session(fname),
            )
            btn_del.pack(side="left", padx=2)

    # =========================================================================
    # EVENT HANDLERS (CRUD)
    # =========================================================================
    def _on_create_session(self) -> None:
        site = self.entry_site.get().strip().upper()
        operator = self.entry_operator.get().strip()
        date_str = self.entry_date.get().strip()

        if not site or not date_str:
            self.lbl_create_status.configure(text="Please fill in Site and Date.", text_color=COLOR_ERROR)
            return

        try:
            sess = self.ctx.create_session(site=site, date=date_str, operator=operator)
            self.lbl_create_status.configure(text=f"Session {sess.id} created successfully!", text_color=COLOR_SUCCESS)
            self.refresh()
            self._notify_app_state()
        except Exception as e:
            logger.error("Failed creating session: %s", e)
            self.lbl_create_status.configure(text=f"Error: {e}", text_color=COLOR_ERROR)

    def _on_switch_session(self, folder_name: str) -> None:
        try:
            self.ctx.open_session(folder_name)
            self.refresh()
            self._notify_app_state()
        except Exception as e:
            logger.error("Failed switching session to %s: %s", folder_name, e)

    def _on_edit_session(self, folder_name: str, site: str, operator: str, date_str: str) -> None:
        EditSessionModal(
            parent=self,
            folder_name=folder_name,
            initial_site=site,
            initial_operator=operator,
            initial_date=date_str,
            on_save_callback=self._handle_save_session_edit,
        )

    def _on_edit_active_session(self) -> None:
        sess = self.ctx.active_session
        if not sess:
            return
        folder_name = self.ctx.session_paths.session_dir.name if self.ctx.session_paths else sess.id
        self._on_edit_session(folder_name, sess.site, sess.operator, sess.date)

    def _handle_save_session_edit(self, folder_name: str, site: str, operator: str, date_str: str) -> bool:
        try:
            success = self.ctx.update_session(folder_name, site=site, operator=operator, date_str=date_str)
            if success:
                logger.info("Session %s updated successfully: site=%s, op=%s, date=%s", folder_name, site, operator, date_str)
                self.refresh()
                self._notify_app_state()
                return True
            return False
        except Exception as e:
            logger.error("Failed updating session %s: %s", folder_name, e)
            return False

    def _on_delete_session(self, folder_name: str) -> None:
        confirm = messagebox.askyesno(
            title="Confirm Delete Session",
            message=(
                f"Are you sure you want to permanently delete session archive:\n\n"
                f"'{folder_name}'\n\n"
                f"All captured core photos, raw files, thumbnails, and database records in this session will be permanently deleted.\n\n"
                f"This action cannot be undone."
            ),
            icon="warning",
            parent=self.winfo_toplevel(),
        )
        if not confirm:
            return

        try:
            self.ctx.delete_session(folder_name)
            logger.info("Session archive deleted: %s", folder_name)
            self.refresh()
            self._notify_app_state()
        except Exception as e:
            logger.error("Failed deleting session %s: %s", folder_name, e)
            messagebox.showerror(
                title="Delete Error",
                message=f"Failed to delete session {folder_name}:\n{e}",
                parent=self.winfo_toplevel(),
            )

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
