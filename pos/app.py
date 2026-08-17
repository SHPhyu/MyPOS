import tkinter as tk
from tkinter import ttk

from . import dao
from .style import apply_style, SIDEBAR_BG, PANEL_BG
from .views.pos_view import PosView
from .views.products_view import ProductsView
from .views.sales_view import SalesView
from .views.reports_view import ReportsView
from .views.settings_view import SettingsView

NAV_ITEMS = [
    ("pos", "Checkout"),
    ("products", "Products"),
    ("sales", "Sales History"),
    ("reports", "Reports"),
    ("settings", "Settings"),
]


class PosApp(tk.Tk):
    def __init__(self):
        super().__init__()
        settings = dao.get_settings()
        self.title(f"{settings.get('store_name', 'My Store')} — POS")
        self.geometry("1200x760")
        self.minsize(1000, 640)

        apply_style(self)

        self.container = ttk.Frame(self, style="Panel.TFrame")
        self.container.pack(side="right", fill="both", expand=True)

        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        self.views = {}
        self.nav_buttons = {}
        self._register_views()

        self.show_view("pos")

    def _build_sidebar(self):
        title = ttk.Label(self.sidebar, text="MyPOS", style="SidebarTitle.TLabel")
        title.pack(anchor="w", padx=18, pady=(20, 4))
        subtitle = ttk.Label(self.sidebar, text="Retail Point of Sale", style="Sidebar.TLabel")
        subtitle.pack(anchor="w", padx=18, pady=(0, 20))

        self.nav_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.nav_frame.pack(fill="x")

    def _register_views(self):
        for key, label in NAV_ITEMS:
            btn = ttk.Button(
                self.nav_frame,
                text=label,
                style="Nav.TButton",
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        self.views["pos"] = PosView(self.container, self)
        self.views["products"] = ProductsView(self.container, self)
        self.views["sales"] = SalesView(self.container, self)
        self.views["reports"] = ReportsView(self.container, self)
        self.views["settings"] = SettingsView(self.container, self)

    def show_view(self, key):
        for k, view in self.views.items():
            view.pack_forget()
        for k, btn in self.nav_buttons.items():
            btn.configure(style="NavActive.TButton" if k == key else "Nav.TButton")

        view = self.views[key]
        view.pack(fill="both", expand=True)
        if hasattr(view, "on_show"):
            view.on_show()

    def refresh_title(self):
        settings = dao.get_settings()
        self.title(f"{settings.get('store_name', 'My Store')} — POS")


def run():
    app = PosApp()
    app.mainloop()
