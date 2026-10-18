"""Industrial Date Picker Modal Dialog for Core Photo.
Clean, lightweight popup calendar built with standard library calendar and CustomTkinter.
Zero external dependencies, fast, and fully themed to industrial standards.
"""

import calendar
from datetime import date, datetime
from typing import Callable, Optional
import customtkinter as ctk

from ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_ACCENT_LIGHT,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_BORDER_STRONG,
    COLOR_CHARCOAL,
    COLOR_PANEL,
    COLOR_PANEL_ALT,
    COLOR_TEXT_HINT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    get_font,
)


class DatePickerModal(ctk.CTkToplevel):
    """Clean popup calendar modal for selecting dates."""

    def __init__(
        self,
        parent,
        initial_date: Optional[str] = None,
        on_select: Optional[Callable[[str], None]] = None,
        date_format: str = "%Y%m%d",
    ):
        super().__init__(parent)
        self.on_select = on_select
        self.date_format = date_format

        # Parse initial date or default to current date
        self.selected_date = self._parse_date(initial_date) or date.today()
        self.current_year = self.selected_date.year
        self.current_month = self.selected_date.month

        self.title("Select Date")
        self.geometry("310x330")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        # Positioning: Center on parent or mouse
        try:
            top_window = parent.winfo_toplevel()
            self.transient(top_window)
            x = top_window.winfo_x() + (top_window.winfo_width() // 2) - 155
            y = top_window.winfo_y() + (top_window.winfo_height() // 2) - 165
            self.geometry(f"310x330+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.grab_set()
        self._build_ui()
        self._render_calendar()

    def _parse_date(self, val: Optional[str]) -> Optional[date]:
        """Parses YYYYMMDD or YYYY-MM-DD string into a date object."""
        if not val:
            return None
        val_clean = str(val).strip().replace("-", "").replace("/", "")
        if len(val_clean) == 8 and val_clean.isdigit():
            try:
                return datetime.strptime(val_clean, "%Y%m%d").date()
            except ValueError:
                return None
        return None

    def _build_ui(self) -> None:
        self.card = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.card.pack(fill="both", expand=True, padx=10, pady=10)

        # ----------------- Month / Year Navigation Header -----------------
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))
        header.grid_columnconfigure(2, weight=1)

        # Prev Year & Prev Month
        btn_prev_year = ctk.CTkButton(
            header,
            text="«",
            width=26,
            height=26,
            font=get_font(12, "bold"),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._prev_year,
        )
        btn_prev_year.grid(row=0, column=0, padx=(0, 2))

        btn_prev_month = ctk.CTkButton(
            header,
            text="‹",
            width=26,
            height=26,
            font=get_font(12, "bold"),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._prev_month,
        )
        btn_prev_month.grid(row=0, column=1, padx=(0, 4))

        # Month and Year label
        self.lbl_month_year = ctk.CTkLabel(
            header,
            text="",
            font=get_font(12, "bold"),
            text_color=COLOR_CHARCOAL,
        )
        self.lbl_month_year.grid(row=0, column=2, sticky="ew")

        # Next Month & Next Year
        btn_next_month = ctk.CTkButton(
            header,
            text="›",
            width=26,
            height=26,
            font=get_font(12, "bold"),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._next_month,
        )
        btn_next_month.grid(row=0, column=3, padx=(4, 2))

        btn_next_year = ctk.CTkButton(
            header,
            text="»",
            width=26,
            height=26,
            font=get_font(12, "bold"),
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._next_year,
        )
        btn_next_year.grid(row=0, column=4, padx=(0, 0))

        # ----------------- Days of Week Header -----------------
        dow_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        dow_frame.pack(fill="x", padx=10, pady=(2, 2))
        for col_idx in range(7):
            dow_frame.grid_columnconfigure(col_idx, weight=1)

        day_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col_idx, d_name in enumerate(day_names):
            lbl_d = ctk.CTkLabel(
                dow_frame,
                text=d_name,
                font=get_font(10, "bold"),
                text_color=COLOR_TEXT_HINT,
            )
            lbl_d.grid(row=0, column=col_idx, sticky="ew")

        # ----------------- Days Grid -----------------
        self.grid_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=2)
        for col_idx in range(7):
            self.grid_frame.grid_columnconfigure(col_idx, weight=1)

        # ----------------- Footer Buttons -----------------
        footer = ctk.CTkFrame(self.card, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=(4, 8))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)

        btn_today = ctk.CTkButton(
            footer,
            text="Today",
            font=get_font(10, "bold"),
            height=26,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_CHARCOAL,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._select_today,
        )
        btn_today.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        btn_cancel = ctk.CTkButton(
            footer,
            text="Cancel",
            font=get_font(10),
            height=26,
            fg_color=COLOR_PANEL_ALT,
            text_color=COLOR_TEXT_MUTED,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.destroy,
        )
        btn_cancel.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _prev_month(self) -> None:
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._render_calendar()

    def _next_month(self) -> None:
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._render_calendar()

    def _prev_year(self) -> None:
        self.current_year -= 1
        self._render_calendar()

    def _next_year(self) -> None:
        self.current_year += 1
        self._render_calendar()

    def _select_today(self) -> None:
        self._choose_date(date.today())

    def _choose_date(self, d: date) -> None:
        formatted = d.strftime(self.date_format)
        if self.on_select:
            self.on_select(formatted)
        self.destroy()

    def _render_calendar(self) -> None:
        # Update month/year title
        month_name = calendar.month_name[self.current_month]
        self.lbl_month_year.configure(text=f"{month_name} {self.current_year}")

        # Clear existing grid children
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdatescalendar(self.current_year, self.current_month)
        today = date.today()

        for r_idx, week in enumerate(month_days):
            for c_idx, d in enumerate(week):
                is_current_month = (d.month == self.current_month)
                is_selected = (d == self.selected_date)
                is_today = (d == today)

                if is_selected:
                    fg_col = COLOR_ACCENT
                    txt_col = "#FFFFFF"
                    border_col = COLOR_ACCENT_HOVER
                    hover_col = COLOR_ACCENT_HOVER
                    b_width = 1
                elif is_today:
                    fg_col = COLOR_ACCENT_LIGHT
                    txt_col = COLOR_ACCENT
                    border_col = COLOR_ACCENT
                    hover_col = COLOR_BORDER
                    b_width = 1
                elif is_current_month:
                    fg_col = "transparent"
                    txt_col = COLOR_TEXT_PRIMARY
                    border_col = COLOR_BORDER
                    hover_col = COLOR_PANEL_ALT
                    b_width = 0
                else:
                    fg_col = "transparent"
                    txt_col = COLOR_TEXT_HINT
                    border_col = COLOR_BORDER
                    hover_col = COLOR_PANEL_ALT
                    b_width = 0

                btn = ctk.CTkButton(
                    self.grid_frame,
                    text=str(d.day),
                    width=32,
                    height=26,
                    corner_radius=4,
                    font=get_font(10, "bold" if (is_selected or is_today) else "normal"),
                    fg_color=fg_col,
                    text_color=txt_col,
                    hover_color=hover_col,
                    border_width=b_width,
                    border_color=border_col,
                    command=lambda target_d=d: self._choose_date(target_d),
                )
                btn.grid(row=r_idx, column=c_idx, padx=1, pady=1, sticky="nsew")
