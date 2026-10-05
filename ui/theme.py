"""Core Photo — Industrial Desktop Design System (Tokens & Components).
Professional, clean, reliable palette for geological drill core photography.
Uses Segoe UI, industrial safety orange accent, dark charcoal, and off-white surfaces.
Strictly avoids emojis, gimmicks, or CRUD admin templates.
"""

import customtkinter as ctk

# ----------------- Industrial Color Palette -----------------
# Brand & Accent
COLOR_ACCENT = "#D9531E"         # Industrial Precision Safety Orange
COLOR_ACCENT_HOVER = "#C2410C"   # Deep Orange Hover
COLOR_ACCENT_LIGHT = "#FFF7ED"   # Warm Light Accent Background
COLOR_ACCENT_BORDER = "#FDBA74"  # Subtle Accent Border

# Neutral & Surfaces
COLOR_CHARCOAL = "#18181B"       # Dark Charcoal Brand Header / Dark elements
COLOR_CHARCOAL_HOVER = "#27272A" # Dark Charcoal Hover
COLOR_BG = "#F4F5F7"             # Industrial Off-white Application Canvas
COLOR_PANEL = "#FFFFFF"          # Surface Panel Background
COLOR_PANEL_ALT = "#F8FAFC"      # Subtle Input / Item Background
COLOR_BORDER = "#E2E8F0"         # Clean 1px Boundary Line
COLOR_BORDER_STRONG = "#CBD5E1"  # Input Focus / Active Border

# Typography Colors
COLOR_TEXT_PRIMARY = "#18181B"   # Near Black High Contrast Body
COLOR_TEXT_MUTED = "#52525B"     # Neutral Medium Gray
COLOR_TEXT_HINT = "#71717A"      # Muted Label & Hint Gray
COLOR_TEXT_ON_DARK = "#F8FAFC"   # Top bar / Dark button text

# Functional Status Indicators (Strictly applied only when necessary)
COLOR_SUCCESS = "#16A34A"        # Green (Connected / Valid)
COLOR_SUCCESS_BG = "#ECFDF5"
COLOR_SUCCESS_BORDER = "#A7F3D0"

COLOR_WARNING = "#D97706"        # Amber (Warning / Pending)
COLOR_WARNING_BG = "#FFFBEB"
COLOR_WARNING_BORDER = "#FDE68A"

COLOR_ERROR = "#DC2626"          # Red (Camera Disconnected / Invalid / Failed)
COLOR_ERROR_BG = "#FEF2F2"
COLOR_ERROR_BORDER = "#FCA5A5"

# ----------------- Typography Definitions (Segoe UI) -----------------
FONT_FAMILY = "Segoe UI"


def get_font(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    """Helper to produce consistent CTkFont instances."""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)
