"""Session Management Screen (PRD Section 10).
Allows operator to create a New Session or Continue an existing Session with autosave recovery.
Designed with Light Mode aesthetics, clear placeholders, and supporting guidance.
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
        super().__init__(master, fg_color="#F8FAFC", **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------- Header -----------------
        header = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 10))

        title = ctk.CTkLabel(
            header,
            text="Langkah 1: Manajemen Sesi Foto (Session)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        )
        title.pack(anchor="w", padx=20, pady=(14, 2))

        subtitle = ctk.CTkLabel(
            header,
            text="Setiap foto dikelompokkan ke dalam satu sesi berdasarkan Site, Operator, dan Tanggal. Anda dapat membuat sesi baru atau melanjutkan sesi sebelumnya.",
            font=ctk.CTkFont(size=12),
            text_color="#64748B",
            wraplength=950,
            justify="left"
        )
        subtitle.pack(anchor="w", padx=20, pady=(0, 14))

        # ----------------- Left Column: Create New Session -----------------
        new_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        new_card.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 16))

        ctk.CTkLabel(
            new_card,
            text="➕ Buat Sesi Baru (New Session)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            new_card,
            text="Isi formulir di bawah ini untuk memulai sesi foto baru di lapangan.",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).pack(anchor="w", padx=20, pady=(0, 14))

        # 1. Site
        ctk.CTkLabel(new_card, text="Lokasi / Pit / Site *", font=ctk.CTkFont(size=13, weight="bold"), text_color="#334155").pack(anchor="w", padx=20, pady=(4, 2))
        self.entry_site = ctk.CTkEntry(
            new_card,
            placeholder_text="Contoh: PIT_NORTH_01 atau PROJECT_A",
            height=38,
            fg_color="#F8FAFC",
            border_color="#CBD5E1"
        )
        self.entry_site.pack(fill="x", padx=20, pady=(0, 2))

        ctk.CTkLabel(
            new_card,
            text="Gunakan huruf kapital atau angka tanpa spasi untuk konsistensi penamaan.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # 2. Operator
        ctk.CTkLabel(new_card, text="Nama Operator / Geologis *", font=ctk.CTkFont(size=13, weight="bold"), text_color="#334155").pack(anchor="w", padx=20, pady=(4, 2))
        self.entry_operator = ctk.CTkEntry(
            new_card,
            placeholder_text="Contoh: Dimas Prasetyo",
            height=38,
            fg_color="#F8FAFC",
            border_color="#CBD5E1"
        )
        self.entry_operator.pack(fill="x", padx=20, pady=(0, 2))

        ctk.CTkLabel(
            new_card,
            text="Nama teknisi atau geologis yang memimpin pengambilan foto tray.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # 3. Date
        ctk.CTkLabel(new_card, text="Tanggal Sesi (Format: YYYYMMDD) *", font=ctk.CTkFont(size=13, weight="bold"), text_color="#334155").pack(anchor="w", padx=20, pady=(4, 2))
        today_str = datetime.now().strftime("%Y%m%d")
        self.entry_date = ctk.CTkEntry(
            new_card,
            height=38,
            fg_color="#F8FAFC",
            border_color="#CBD5E1"
        )
        self.entry_date.insert(0, today_str)
        self.entry_date.pack(fill="x", padx=20, pady=(0, 2))

        ctk.CTkLabel(
            new_card,
            text="Otomatis diisi dengan tanggal hari ini. Ubah jika mendokumentasikan data kemarin.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=20, pady=(0, 16))

        # Button Create
        self.btn_create_session = ctk.CTkButton(
            new_card,
            text="Simpan & Mulai Sesi Baru →",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            corner_radius=8,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            command=self._on_create_session
        )
        self.btn_create_session.pack(fill="x", padx=20, pady=6)

        # Feedback box
        self.new_feedback_lbl = ctk.CTkLabel(new_card, text="", font=ctk.CTkFont(size=12, weight="bold"), wraplength=420)
        self.new_feedback_lbl.pack(anchor="w", padx=20, pady=4)

        # ----------------- Right Column: Continue Existing Session -----------------
        cont_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E2E8F0")
        cont_card.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 16))

        ctk.CTkLabel(
            cont_card,
            text="📂 Lanjutkan Sesi (Continue Session)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            cont_card,
            text="Pilih sesi yang belum selesai dari penyimpanan lokal:",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).pack(anchor="w", padx=20, pady=(0, 12))

        # Scrollable list for existing sessions
        self.sessions_scroll = ctk.CTkScrollableFrame(
            cont_card,
            height=260,
            fg_color="#F8FAFC",
            border_width=1,
            border_color="#E2E8F0",
            corner_radius=8
        )
        self.sessions_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        self.selected_session_var = ctk.StringVar(value="")

        self.btn_open_session = ctk.CTkButton(
            cont_card,
            text="Buka Sesi Terpilih →",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            corner_radius=8,
            fg_color="#059669",
            hover_color="#047857",
            command=self._on_open_session
        )
        self.btn_open_session.pack(fill="x", padx=20, pady=6)

        self.cont_feedback_lbl = ctk.CTkLabel(cont_card, text="", font=ctk.CTkFont(size=12, weight="bold"), wraplength=420)
        self.cont_feedback_lbl.pack(anchor="w", padx=20, pady=4)

    def refresh(self) -> None:
        """Reloads existing session list from storage."""
        for child in self.sessions_scroll.winfo_children():
            child.destroy()

        sessions = self.ctx.list_available_sessions()
        if not sessions:
            lbl = ctk.CTkLabel(
                self.sessions_scroll,
                text="Belum ada sesi tersimpan di penyimpanan lokal.\nSilakan buat sesi baru di kolom sebelah kiri.",
                text_color="#94A3B8",
                justify="center",
                font=ctk.CTkFont(size=12)
            )
            lbl.pack(pady=40)
            self.btn_open_session.configure(state="disabled", fg_color="#94A3B8")
            return

        self.btn_open_session.configure(state="normal", fg_color="#059669")
        sessions.sort(reverse=True)
        self.selected_session_var.set(sessions[0])

        for s_name in sessions:
            is_active = (self.ctx.active_session and self.ctx.active_session.id == s_name)
            item_frame = ctk.CTkFrame(self.sessions_scroll, fg_color="#FFFFFF" if not is_active else "#EFF6FF", corner_radius=6, border_width=1, border_color="#BFDBFE" if is_active else "#E2E8F0")
            item_frame.pack(fill="x", padx=4, pady=4)

            rb = ctk.CTkRadioButton(
                item_frame,
                text=f"{s_name}  (Aktif Sekarang)" if is_active else s_name,
                variable=self.selected_session_var,
                value=s_name,
                font=ctk.CTkFont(size=13, weight="bold" if is_active else "normal"),
                text_color="#1D4ED8" if is_active else "#334155"
            )
            rb.pack(anchor="w", padx=12, pady=10)

    def _on_create_session(self) -> None:
        site = self.entry_site.get().strip()
        operator = self.entry_operator.get().strip()
        date_str = self.entry_date.get().strip()

        if not site:
            self.new_feedback_lbl.configure(text="⚠️ Lokasi / Site wajib diisi sebelum melanjutkan.", text_color="#DC2626")
            return
        if not operator:
            self.new_feedback_lbl.configure(text="⚠️ Nama Operator wajib diisi.", text_color="#DC2626")
            return
        if not date_str:
            self.new_feedback_lbl.configure(text="⚠️ Tanggal wajib diisi.", text_color="#DC2626")
            return

        try:
            sess = self.ctx.create_new_session(site, operator, date_str)
            self.new_feedback_lbl.configure(
                text=f"✅ Sesi '{sess.id}' berhasil dibuat! Mengalihkan ke Capture...",
                text_color="#059669"
            )
            self.refresh()
            # Navigate smoothly to capture
            self.after(500, lambda: self.navigate_fn("capture"))
        except Exception as e:
            logger.error("Error creating session: %s", e)
            self.new_feedback_lbl.configure(text=f"❌ Gagal membuat sesi: {e}", text_color="#DC2626")

    def _on_open_session(self) -> None:
        chosen = self.selected_session_var.get()
        if not chosen:
            self.cont_feedback_lbl.configure(text="⚠️ Pilih salah satu sesi terlebih dahulu.", text_color="#DC2626")
            return

        try:
            sess = self.ctx.open_session(chosen)
            if sess:
                self.cont_feedback_lbl.configure(
                    text=f"✅ Sesi '{sess.id}' aktif! Mengalihkan ke Capture...",
                    text_color="#059669"
                )
                self.refresh()
                self.after(500, lambda: self.navigate_fn("capture"))
            else:
                self.cont_feedback_lbl.configure(text="❌ Gagal membuka sesi terpilih.", text_color="#DC2626")
        except Exception as e:
            logger.error("Error opening session %s: %s", chosen, e)
            self.cont_feedback_lbl.configure(text=f"❌ Error: {e}", text_color="#DC2626")
