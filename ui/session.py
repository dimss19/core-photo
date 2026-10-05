"""Session Management Screen (Professional Industrial Redesign).
Allows operator to initialize a New Session or Open an existing Session with automated recovery.
Zero emojis, strict professional standards.
"""

from datetime import datetime
from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
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


class SessionView(ctk.CTkFrame):
    """View for creating and opening photography sessions."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------- Top Header -----------------
        header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            title_box,
            text="SESSION CONFIGURATION",
            font=get_font(16, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Core logging sessions organize captured photos, raw arrays, metadata, and checksums by Site, Operator, and Date.",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # ----------------- Left: Create New Session -----------------
        new_card = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        new_card.grid(row=1, column=0, sticky="nsew", padx=(24, 8), pady=(0, 20))

        ctk.CTkLabel(
            new_card,
            text="CREATE NEW SESSION",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=18, pady=(18, 2))

        ctk.CTkLabel(
            new_card,
            text="Initialize a new borehole logging session.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(0, 12))

        # 1. Site
        ctk.CTkLabel(new_card, text="Site / Project Reference *", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(4, 1))
        self.entry_site = ctk.CTkEntry(
            new_card,
            placeholder_text="e.g. NORTH_PIT or PROJECT_X",
            height=34,
            font=get_font(12),
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.entry_site.pack(fill="x", padx=18, pady=(0, 2))
        ctk.CTkLabel(new_card, text="Standard alphanumeric identifier", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(anchor="w", padx=18, pady=(0, 8))

        # 2. Operator
        ctk.CTkLabel(new_card, text="Operator / Geologist *", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(4, 1))
        self.entry_operator = ctk.CTkEntry(
            new_card,
            placeholder_text="e.g. J. Doe",
            height=34,
            font=get_font(12),
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.entry_operator.pack(fill="x", padx=18, pady=(0, 2))
        ctk.CTkLabel(new_card, text="Responsible technician or logging geologist", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(anchor="w", padx=18, pady=(0, 8))

        # 3. Date
        ctk.CTkLabel(new_card, text="Date (YYYYMMDD) *", font=get_font(11, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(4, 1))
        today_str = datetime.now().strftime("%Y%m%d")
        self.entry_date = ctk.CTkEntry(
            new_card,
            height=34,
            font=get_font(12),
            fg_color=COLOR_PANEL_ALT,
            border_color=COLOR_BORDER_STRONG,
            border_width=1,
        )
        self.entry_date.insert(0, today_str)
        self.entry_date.pack(fill="x", padx=18, pady=(0, 2))
        ctk.CTkLabel(new_card, text="Defaults to current calendar date", font=get_font(10), text_color=COLOR_TEXT_HINT).pack(anchor="w", padx=18, pady=(0, 16))

        # Action: Create Button
        self.btn_create_session = ctk.CTkButton(
            new_card,
            text="INITIALIZE SESSION",
            font=get_font(12, "bold"),
            height=42,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_create_session,
        )
        self.btn_create_session.pack(fill="x", padx=18, pady=4)

        self.new_feedback_lbl = ctk.CTkLabel(new_card, text="", font=get_font(11, "bold"), wraplength=400)
        self.new_feedback_lbl.pack(anchor="w", padx=18, pady=4)

        # ----------------- Right: Continue Existing Session -----------------
        cont_card = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        cont_card.grid(row=1, column=1, sticky="nsew", padx=(8, 24), pady=(0, 20))

        ctk.CTkLabel(
            cont_card,
            text="SAVED SESSIONS",
            font=get_font(13, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=18, pady=(18, 2))

        ctk.CTkLabel(
            cont_card,
            text="Resume an existing logging session from storage.",
            font=get_font(10),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(0, 12))

        # Scrollable list for existing sessions
        self.sessions_scroll = ctk.CTkScrollableFrame(
            cont_card,
            height=250,
            fg_color=COLOR_PANEL_ALT,
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=4,
        )
        self.sessions_scroll.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        self.selected_session_var = ctk.StringVar(value="")

        self.btn_open_session = ctk.CTkButton(
            cont_card,
            text="OPEN SELECTED SESSION",
            font=get_font(12, "bold"),
            height=42,
            corner_radius=4,
            fg_color=COLOR_CHARCOAL,
            hover_color="#27272A",
            text_color="#FFFFFF",
            command=self._on_open_session,
        )
        self.btn_open_session.pack(fill="x", padx=18, pady=4)

        self.cont_feedback_lbl = ctk.CTkLabel(cont_card, text="", font=get_font(11, "bold"), wraplength=400)
        self.cont_feedback_lbl.pack(anchor="w", padx=18, pady=4)

    def refresh(self) -> None:
        """Reloads existing session list from storage."""
        for child in self.sessions_scroll.winfo_children():
            child.destroy()

        sessions = self.ctx.list_available_sessions()
        if not sessions:
            lbl = ctk.CTkLabel(
                self.sessions_scroll,
                text="No saved sessions found in local database.\nInitialize a new session on the left.",
                text_color=COLOR_TEXT_HINT,
                justify="center",
                font=get_font(11),
            )
            lbl.pack(pady=40)
            self.btn_open_session.configure(state="disabled", fg_color=COLOR_BORDER_STRONG)
            return

        self.btn_open_session.configure(state="normal", fg_color=COLOR_CHARCOAL)
        sessions.sort(reverse=True)
        self.selected_session_var.set(sessions[0])

        for s_name in sessions:
            is_active = bool(self.ctx.active_session and self.ctx.active_session.id == s_name)
            item_frame = ctk.CTkFrame(
                self.sessions_scroll,
                fg_color=COLOR_PANEL if not is_active else "#EFF6FF",
                corner_radius=4,
                border_width=1,
                border_color=COLOR_BORDER if not is_active else "#BFDBFE",
            )
            item_frame.pack(fill="x", padx=4, pady=3)

            label_text = f"{s_name}  [Active]" if is_active else s_name
            rb = ctk.CTkRadioButton(
                item_frame,
                text=label_text,
                variable=self.selected_session_var,
                value=s_name,
                font=get_font(11, "bold" if is_active else "normal"),
                text_color=COLOR_TEXT_PRIMARY,
            )
            rb.pack(anchor="w", padx=12, pady=8)

    def _on_create_session(self) -> None:
        site = self.entry_site.get().strip()
        operator = self.entry_operator.get().strip()
        date_str = self.entry_date.get().strip()

        if not site:
            self.new_feedback_lbl.configure(text="Site reference is required.", text_color=COLOR_ERROR)
            return
        if not operator:
            self.new_feedback_lbl.configure(text="Operator name is required.", text_color=COLOR_ERROR)
            return
        if not date_str:
            self.new_feedback_lbl.configure(text="Date is required.", text_color=COLOR_ERROR)
            return

        try:
            sess = self.ctx.create_new_session(site, operator, date_str)
            self.new_feedback_lbl.configure(
                text=f"Session '{sess.id}' initialized successfully. Redirecting...",
                text_color=COLOR_SUCCESS,
            )
            self.refresh()
            self.after(400, lambda: self.navigate_fn("capture"))
        except Exception as e:
            logger.error("Error creating session: %s", e)
            self.new_feedback_lbl.configure(text=f"Error initializing session: {e}", text_color=COLOR_ERROR)

    def _on_open_session(self) -> None:
        chosen = self.selected_session_var.get()
        if not chosen:
            self.cont_feedback_lbl.configure(text="Select a session from the list.", text_color=COLOR_WARNING)
            return

        try:
            sess = self.ctx.open_session(chosen)
            if sess:
                self.cont_feedback_lbl.configure(
                    text=f"Session '{sess.id}' loaded. Redirecting to capture...",
                    text_color=COLOR_SUCCESS,
                )
                self.refresh()
                self.after(400, lambda: self.navigate_fn("capture"))
            else:
                self.cont_feedback_lbl.configure(text="Failed to open selected session.", text_color=COLOR_ERROR)
        except Exception as e:
            logger.error("Error opening session %s: %s", chosen, e)
            self.cont_feedback_lbl.configure(text=f"Error: {e}", text_color=COLOR_ERROR)
