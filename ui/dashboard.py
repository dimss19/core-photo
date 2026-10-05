"""Dashboard Screen (Industrial Redesign).
Focal points: Active Session, Camera Connection, Tray Progress, and Primary Capture Action.
Avoids CRUD admin sprawl and useless card clutter. Zero emojis.
"""

from typing import Callable
import customtkinter as ctk

from core.app_context import get_app_context
from core.logger import get_logger
from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_BG,
    COLOR_BORDER,
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


class DashboardView(ctk.CTkFrame):
    """Clean industrial dashboard focused strictly on operational readiness."""

    def __init__(self, master, navigate_fn: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        self.navigate_fn = navigate_fn
        self.ctx = get_app_context()

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ----------------- Top Header Section -----------------
        header_frame = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 16))
        header_frame.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=16)

        lbl_title = ctk.CTkLabel(
            title_box,
            text="OPERATIONAL OVERVIEW",
            font=get_font(16, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        lbl_title.pack(anchor="w")

        lbl_subtitle = ctk.CTkLabel(
            title_box,
            text="Real-time hardware status, active logging session, and direct capture workflow.",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        lbl_subtitle.pack(anchor="w", pady=(2, 0))

        # ----------------- Three Focus Cards Row -----------------
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.grid(row=1, column=0, sticky="ew", padx=24, pady=0)
        cards_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="dash_cards")

        # 1. Active Session Card
        self.session_card = ctk.CTkFrame(cards_row, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        self.session_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        ctk.CTkLabel(
            self.session_card,
            text="ACTIVE SESSION",
            font=get_font(10, "bold"),
            text_color=COLOR_TEXT_HINT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self.lbl_session_name = ctk.CTkLabel(
            self.session_card,
            text="[No Active Session]",
            font=get_font(15, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.lbl_session_name.pack(anchor="w", padx=16)

        self.lbl_session_details = ctk.CTkLabel(
            self.session_card,
            text="Select or create a session to start logging.",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_session_details.pack(anchor="w", padx=16, pady=(2, 16))

        # 2. Camera Status Card
        self.cam_card = ctk.CTkFrame(cards_row, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        self.cam_card.grid(row=0, column=1, sticky="nsew", padx=4, pady=0)

        ctk.CTkLabel(
            self.cam_card,
            text="CAMERA HARDWARE",
            font=get_font(10, "bold"),
            text_color=COLOR_TEXT_HINT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self.lbl_cam_status = ctk.CTkLabel(
            self.cam_card,
            text="● Disconnected",
            font=get_font(15, "bold"),
            text_color=COLOR_ERROR,
        )
        self.lbl_cam_status.pack(anchor="w", padx=16)

        self.lbl_cam_details = ctk.CTkLabel(
            self.cam_card,
            text="USB Video Device (OpenCV / WebcamAdapter)",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_cam_details.pack(anchor="w", padx=16, pady=(2, 16))

        # 3. Work Progress Card
        self.progress_card = ctk.CTkFrame(cards_row, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        self.progress_card.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=0)

        ctk.CTkLabel(
            self.progress_card,
            text="PROGRESS SUMMARY",
            font=get_font(10, "bold"),
            text_color=COLOR_TEXT_HINT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self.lbl_progress_main = ctk.CTkLabel(
            self.progress_card,
            text="0 Trays Completed",
            font=get_font(15, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.lbl_progress_main.pack(anchor="w", padx=16)

        self.lbl_progress_details = ctk.CTkLabel(
            self.progress_card,
            text="0 Trays pending review / transfer",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_progress_details.pack(anchor="w", padx=16, pady=(2, 16))

        # ----------------- Primary Action Section -----------------
        action_frame = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        action_frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=16)
        action_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            action_frame,
            text="OPERATOR ACTION",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        ).pack(anchor="w", padx=20, pady=(20, 4))

        self.lbl_action_hint = ctk.CTkLabel(
            action_frame,
            text="Continue capturing drill core photos with active camera calibration.",
            font=get_font(11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.lbl_action_hint.pack(anchor="w", padx=20, pady=(0, 16))

        # Primary Orange CTA
        self.btn_primary_cta = ctk.CTkButton(
            action_frame,
            text="CONTINUE CAPTURE",
            font=get_font(13, "bold"),
            height=46,
            corner_radius=4,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._on_primary_cta_click,
        )
        self.btn_primary_cta.pack(fill="x", padx=20, pady=(0, 10))

        # Secondary Actions Row
        sec_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        sec_row.pack(fill="x", padx=20, pady=(0, 20))
        sec_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_manage_session = ctk.CTkButton(
            sec_row,
            text="MANAGE SESSION",
            font=get_font(12, "bold"),
            height=38,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=lambda: self.navigate_fn("session"),
        )
        self.btn_manage_session.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_photo_browser = ctk.CTkButton(
            sec_row,
            text="PHOTO BROWSER",
            font=get_font(12, "bold"),
            height=38,
            corner_radius=4,
            fg_color=COLOR_PANEL_ALT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_CHARCOAL,
            border_width=1,
            border_color=COLOR_BORDER,
            command=lambda: self.navigate_fn("browser"),
        )
        self.btn_photo_browser.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _on_primary_cta_click(self) -> None:
        if self.ctx.active_session:
            self.navigate_fn("capture")
        else:
            self.navigate_fn("session")

    def refresh(self) -> None:
        """Updates dashboard state from AppContext."""
        # 1. Camera Status
        cam_ready = self.ctx.camera_manager.is_ready()
        cam_summary = self.ctx.camera_manager.get_status_summary()
        if cam_ready:
            self.lbl_cam_status.configure(text="● Connected", text_color=COLOR_SUCCESS)
            self.lbl_cam_details.configure(text=cam_summary)
        else:
            self.lbl_cam_status.configure(text="● Disconnected", text_color=COLOR_ERROR)
            self.lbl_cam_details.configure(text="No live camera feed detected")

        # 2. Active Session & CTA
        sess = self.ctx.active_session
        if sess:
            self.lbl_session_name.configure(text=sess.site, text_color=COLOR_CHARCOAL)
            self.lbl_session_details.configure(
                text=f"Operator: {sess.operator}  ·  Date: {sess.date}"
            )
            self.btn_primary_cta.configure(
                text="CONTINUE CAPTURE",
                fg_color=COLOR_ACCENT,
                hover_color=COLOR_ACCENT_HOVER,
            )
            self.lbl_action_hint.configure(
                text=f"Session '{sess.site}' is active. Advance directly to live view framing and capture."
            )
        else:
            self.lbl_session_name.configure(text="[No Active Session]", text_color=COLOR_TEXT_HINT)
            self.lbl_session_details.configure(text="Create or open a session to start logging core photos.")
            self.btn_primary_cta.configure(
                text="CREATE / SELECT SESSION",
                fg_color=COLOR_CHARCOAL,
                hover_color=COLOR_CHARCOAL_HOVER,
            )
            self.lbl_action_hint.configure(
                text="No active session found. A session must be initialized before photo acquisition."
            )

        # 3. Progress Summary
        if sess and self.ctx.photo_repo:
            photos = self.ctx.photo_repo.list_by_session(sess.id, active_only=True)
            total = len(photos)
            valid = sum(1 for p in photos if p.status in ("VALID", "PROCESSED", "TRANSFERRED"))
            pending = total - valid
            self.lbl_progress_main.configure(text=f"{total} Trays Logged")
            self.lbl_progress_details.configure(text=f"{valid} validated  ·  {pending} pending review")
        else:
            self.lbl_progress_main.configure(text="0 Trays Logged")
            self.lbl_progress_details.configure(text="0 Trays pending review / transfer")
