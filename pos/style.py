from tkinter import ttk

BG = "#1f2430"
SIDEBAR_BG = "#161a24"
CARD_BG = "#ffffff"
PANEL_BG = "#f4f5f7"
ACCENT = "#2f6fed"
ACCENT_DARK = "#1f4fbd"
DANGER = "#e5484d"
SUCCESS = "#2fa84f"
TEXT_DARK = "#1c1f26"
TEXT_MUTED = "#6b7280"
TEXT_LIGHT = "#e7e9ee"
BORDER = "#dfe3e8"

FONT_FAMILY = "Segoe UI"


def apply_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=PANEL_BG)

    style.configure("TFrame", background=PANEL_BG)
    style.configure("Panel.TFrame", background=PANEL_BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("Sidebar.TFrame", background=SIDEBAR_BG)

    style.configure(
        "TLabel", background=PANEL_BG, foreground=TEXT_DARK, font=(FONT_FAMILY, 10)
    )
    style.configure(
        "Card.TLabel", background=CARD_BG, foreground=TEXT_DARK, font=(FONT_FAMILY, 10)
    )
    style.configure(
        "Muted.TLabel", background=PANEL_BG, foreground=TEXT_MUTED, font=(FONT_FAMILY, 9)
    )
    style.configure(
        "CardMuted.TLabel", background=CARD_BG, foreground=TEXT_MUTED, font=(FONT_FAMILY, 9)
    )
    style.configure(
        "Heading.TLabel",
        background=PANEL_BG,
        foreground=TEXT_DARK,
        font=(FONT_FAMILY, 16, "bold"),
    )
    style.configure(
        "CardHeading.TLabel",
        background=CARD_BG,
        foreground=TEXT_DARK,
        font=(FONT_FAMILY, 13, "bold"),
    )
    style.configure(
        "Total.TLabel",
        background=CARD_BG,
        foreground=TEXT_DARK,
        font=(FONT_FAMILY, 20, "bold"),
    )
    style.configure(
        "Sidebar.TLabel",
        background=SIDEBAR_BG,
        foreground=TEXT_LIGHT,
        font=(FONT_FAMILY, 10),
    )
    style.configure(
        "SidebarTitle.TLabel",
        background=SIDEBAR_BG,
        foreground="#ffffff",
        font=(FONT_FAMILY, 14, "bold"),
    )

    style.configure(
        "TButton",
        background=ACCENT,
        foreground="#ffffff",
        font=(FONT_FAMILY, 10, "bold"),
        padding=(12, 8),
        borderwidth=0,
    )
    style.map("TButton", background=[("active", ACCENT_DARK), ("disabled", "#a9b6d6")])

    style.configure(
        "Secondary.TButton",
        background="#e5e8ee",
        foreground=TEXT_DARK,
        font=(FONT_FAMILY, 10),
        padding=(10, 7),
        borderwidth=0,
    )
    style.map("Secondary.TButton", background=[("active", "#d4d9e2")])

    style.configure(
        "Danger.TButton",
        background=DANGER,
        foreground="#ffffff",
        font=(FONT_FAMILY, 10, "bold"),
        padding=(10, 7),
        borderwidth=0,
    )
    style.map("Danger.TButton", background=[("active", "#c53b3f")])

    style.configure(
        "Success.TButton",
        background=SUCCESS,
        foreground="#ffffff",
        font=(FONT_FAMILY, 12, "bold"),
        padding=(14, 10),
        borderwidth=0,
    )
    style.map("Success.TButton", background=[("active", "#248a41")])

    style.configure(
        "Nav.TButton",
        background=SIDEBAR_BG,
        foreground=TEXT_LIGHT,
        font=(FONT_FAMILY, 11),
        padding=(14, 10),
        borderwidth=0,
        anchor="w",
    )
    style.map(
        "Nav.TButton",
        background=[("active", "#262c3b")],
        foreground=[("active", "#ffffff")],
    )
    style.configure(
        "NavActive.TButton",
        background=ACCENT,
        foreground="#ffffff",
        font=(FONT_FAMILY, 11, "bold"),
        padding=(14, 10),
        borderwidth=0,
        anchor="w",
    )
    style.map("NavActive.TButton", background=[("active", ACCENT)])

    style.configure("TEntry", padding=6, fieldbackground="#ffffff")
    style.configure("TCombobox", padding=6)

    style.configure(
        "Treeview",
        background="#ffffff",
        fieldbackground="#ffffff",
        foreground=TEXT_DARK,
        rowheight=28,
        font=(FONT_FAMILY, 10),
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        background="#eef1f5",
        foreground=TEXT_DARK,
        font=(FONT_FAMILY, 10, "bold"),
        borderwidth=0,
    )
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#ffffff")])

    return style
