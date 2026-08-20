"""Central color/font palette for the CustomTkinter UI."""
import customtkinter as ctk

FONT_FAMILY = "Myanmar Text"

# ----- palette -----
BG_APP = "#eef1f6"
BG_SIDEBAR = "#161a24"
BG_HEADER = "#161a24"
BG_CARD = "#ffffff"
BG_TOTAL_BOX = "#0f2f1c"

ACCENT = "#2f6fed"
ACCENT_HOVER = "#1f4fbd"
ACCENT_SOFT = "#e4ecfd"

SUCCESS = "#2fa84f"
SUCCESS_HOVER = "#248a41"
DANGER = "#e5484d"
DANGER_HOVER = "#c53b3f"

TEXT_DARK = "#1c1f26"
TEXT_MUTED = "#6b7280"
TEXT_LIGHT = "#e7e9ee"
TEXT_ON_ACCENT = "#ffffff"

BORDER = "#e1e4ea"
ROW_ALT = "#f6f8fb"
ROW_SELECTED = "#dbe6fd"
ROW_WARN = "#fdecea"

CATEGORY_COLORS = [
    "#bfe8c9", "#c6d6f7", "#f6e79c", "#f3c6c6",
    "#c8ecec", "#e3d3f6", "#ffdcb0", "#d6e9b3",
]
CATEGORY_HOVER = "#9fd6ae"

RADIUS = 10
RADIUS_SMALL = 6


def setup_theme():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def font(size=13, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def mono_font(size=13, weight="normal"):
    return ctk.CTkFont(family="Consolas", size=size, weight=weight)
