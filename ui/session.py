"""Session Management Screen (PRD Section 10).
Allows operator to create a New Session or Continue an existing Session with autosave recovery.
"""

from datetime import datetime
from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger

logger = get_logger(__name__)


class SessionView(ctk.CTkFrame):
    """View for creating and opening photography sessions."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="Manajemen Sesi Foto (Session)",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Pilih sesi yang sedang berjalan atau buat sesi baru untuk site hari ini.",
            font=ctk.CTkFont(size=13),
            text_color="gray70"
        )
        subtitle.pack(anchor="w")

        # Left Column: New Session Card
        new_card = ctk.CTkFrame(self, corner_radius=12)
        new_card.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=12)

        ctk.CTkLabel(
            new_card,
            text="Buat Sesi Baru (New Session)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(18, 14))

        ctk.CTkLabel(new_card, text="Lokasi / Site:", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=20, pady=(6, 2))
        self.entry_site = ctk.CTkEntry(new_card, placeholder_text="Contoh: PIT_NORTH", height=36)
        self.entry_site.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(new_card, text="Nama Operator:", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=20, pady=(6, 2))
        self.entry_operator = ctk.CTkEntry(new_card, placeholder_text="Contoh: Dimas", height=36)
        self.entry_operator.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(new_card, text="Tanggal (YYYYMMDD):", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=20, pady=(6, 2))
        today_str = datetime.now().strftime("%Y%m%d")
        self.entry_date = ctk.CTkEntry(new_card, height=36)
        self.entry_date.insert(0, today_str)
        self.entry_date.pack(fill="x", padx=20, pady=(0, 16))

        self.btn_create_session = ctk.CTkButton(
            new_card,
            text="Simpan & Mulai Sesi Baru",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._on_create_session
        )
        self.btn_create_session.pack(fill="x", padx=20, pady=10)

        self.new_feedback_lbl = ctk.CTkLabel(new_card, text="", font=ctk.CTkFont(size=12))
        self.new_feedback_lbl.pack(anchor="w", padx=20, pady=4)

        # Right Column: Continue Existing Session Card
        cont_card = ctk.CTkFrame(self, corner_radius=12)
        cont_card.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=12)

        ctk.CTkLabel(
            cont_card,
            text="Lanjutkan Sesi (Continue Session)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(18, 14))

        ctk.CTkLabel(
            cont_card,
            text="Pilih dari daftar sesi yang tersimpan di disk lokal:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=20, pady=(0, 8))

        # Scrollable list for existing sessions
        self.sessions_scroll = ctk.CTkScrollableFrame(cont_card, height=220)
        self.sessions_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        self.selected_session_var = ctk.StringVar(value="")

        self.btn_open_session = ctk.CTkButton(
            cont_card,
            text="Buka Sesi Terpilih",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#2B2B2B",
            hover_color="#3A3A3A",
            command=self._on_open_session
        )
        self.btn_open_session.pack(fill="x", padx=20, pady=10)

        self.cont_feedback_lbl = ctk.CTkLabel(cont_card, text="", font=ctk.CTkFont(size=12))
        self.cont_feedback_lbl.pack(anchor="w", padx=20, pady=4)

    def refresh(self) -> None:
        """Reloads existing session list from storage."""
        # Clear existing radio buttons
        for child in self.sessions_scroll.winfo_children():
            child.destroy()

        sessions = self.ctx.list_available_sessions()
        if not sessions:
            lbl = ctk.CTkLabel(self.sessions_scroll, text="Belum ada sesi tersimpan.", text_color="gray60")
            lbl.pack(anchor="w", pady=10)
            self.btn_open_session.configure(state="disabled")
            return

        self.btn_open_session.configure(state="normal")
        sessions.sort(reverse=True)
        self.selected_session_var.set(sessions[0])

        for s_name in sessions:
            is_active = (self.ctx.active_session and self.ctx.active_session.id == s_name)
            display_text = f"{s_name}  (Aktif)" if is_active else s_name
            rb = ctk.CTkRadioButton(
                self.sessions_scroll,
                text=display_text,
                variable=self.selected_session_var,
                value=s_name,
                font=ctk.CTkFont(size=13)
            )
            rb.pack(anchor="w", padx=10, pady=6)

    def _on_create_session(self) -> None:
        site = self.entry_site.get().strip()
        operator = self.entry_operator.get().strip()
        date_str = self.entry_date.get().strip()

        if not site:
            self.new_feedback_lbl.configure(text="Lokasi / Site wajib diisi.", text_color="#D9534F")
            return
        if not operator:
            self.new_feedback_lbl.configure(text="Nama Operator wajib diisi.", text_color="#D9534F")
            return
        if not date_str:
            self.new_feedback_lbl.configure(text="Tanggal wajib diisi.", text_color="#D9534F")
            return

        try:
            sess = self.ctx.create_new_session(site, operator, date_str)
            self.new_feedback_lbl.configure(
                text=f"Sesi '{sess.id}' berhasil dibuat!",
                text_color="#2CC985"
            )
            self.refresh()
            # Navigate smoothly to capture
            self.after(500, lambda: self.navigate_fn("capture"))
        except Exception as e:
            logger.error("Error creating session: %s", e)
            self.new_feedback_lbl.configure(text=f"Gagal membuat sesi: {e}", text_color="#D9534F")

    def _on_open_session(self) -> None:
        chosen = self.selected_session_var.get()
        if not chosen:
            self.cont_feedback_lbl.configure(text="Pilih sesi terlebih dahulu.", text_color="#D9534F")
            return

        try:
            sess = self.ctx.open_session(chosen)
            if sess:
                self.cont_feedback_lbl.configure(
                    text=f"Sesi '{sess.id}' aktif!",
                    text_color="#2CC985"
                )
                self.refresh()
                self.after(500, lambda: self.navigate_fn("capture"))
            else:
                self.cont_feedback_lbl.configure(text="Gagal membuka sesi terpilih.", text_color="#D9534F")
        except Exception as e:
            logger.error("Error opening session %s: %s", chosen, e)
            self.cont_feedback_lbl.configure(text=f"Error: {e}", text_color="#D9534F")
