import customtkinter as ctk

from . import dao
from . import theme

MANAGER_ITEMS = [
    ("products", "ကုန်ပစ္စည်းများ"),
    ("customers", "ဖောက်သည်များ"),
    ("sales", "ရောင်းအားမှတ်တမ်း"),
    ("reports", "အစီရင်ခံစာများ"),
    ("settings", "ဆက်တင်များ"),
]


def _view_factories():
    # Imported lazily (inside a function) so importing pos.app doesn't
    # eagerly import every view module before it's needed.
    from .views.pos_view import PosView
    from .views.products_view import ProductsView
    from .views.customers_view import CustomersView
    from .views.sales_view import SalesView
    from .views.reports_view import ReportsView
    from .views.settings_view import SettingsView

    return {
        "pos": PosView,
        "products": ProductsView,
        "customers": CustomersView,
        "sales": SalesView,
        "reports": ReportsView,
        "settings": SettingsView,
    }


class PosApp(ctk.CTk):
    """Checkout is the only permanent screen — everything else (Products,
    Customers, Sales History, Reports, Settings) is reached through the
    "Manager" tool on the Checkout screen and always returns to Checkout.
    """

    def __init__(self):
        super().__init__()
        theme.setup_theme()

        settings = dao.get_settings()
        self.title(f"{settings.get('store_name', 'သြဇာ')} — ရောင်းချရေးစနစ်")
        self.geometry("1280x800")
        self.minsize(1000, 640)
        self.configure(fg_color=theme.BG_APP)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self, fg_color=theme.BG_APP, corner_radius=0)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self._view_factories = _view_factories()
        self.views = {}

        self.show_view("pos")

    def open_manager_menu(self, parent_widget):
        ManagerMenu(parent_widget, self)

    def show_view(self, key):
        if key not in self.views:
            # Built on first visit, not at startup — so launching the app
            # only ever pays for the screen you're actually looking at.
            self.views[key] = self._view_factories[key](self.container, self)
            self.views[key].grid(row=0, column=0, sticky="nsew")

        view = self.views[key]
        view.tkraise()
        if hasattr(view, "on_show"):
            view.on_show()

    def refresh_title(self):
        settings = dao.get_settings()
        self.title(f"{settings.get('store_name', 'သြဇာ')} — ရောင်းချရေးစနစ်")


class ManagerMenu(ctk.CTkToplevel):
    """Popup replacing the old sidebar — every screen except Checkout."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("မန်နေဂျာ")
        self.geometry("320x420")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_APP)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(frame, text="မန်နေဂျာ", font=theme.font(18, "bold"), text_color=theme.TEXT_DARK).pack(
            anchor="w", pady=(0, 14)
        )

        for key, label in MANAGER_ITEMS:
            ctk.CTkButton(
                frame, text=label, font=theme.font(14, "bold"), height=52,
                fg_color=theme.BG_CARD, text_color=theme.TEXT_DARK,
                hover_color=theme.ROW_ALT, border_width=1, border_color=theme.BORDER,
                corner_radius=theme.RADIUS, anchor="w",
                command=lambda k=key: self._open(k),
            ).pack(fill="x", pady=5, padx=2)

        ctk.CTkButton(
            frame, text="ပိတ်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
            hover_color=theme.BORDER, command=self.destroy,
        ).pack(fill="x", pady=(14, 0))

        self.transient(parent)
        self.grab_set()

    def _open(self, key):
        self.destroy()
        self.app.show_view(key)


def run():
    app = PosApp()
    app.mainloop()
