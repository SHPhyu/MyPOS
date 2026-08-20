import customtkinter as ctk

from . import dao
from . import theme

NAV_ITEMS = [
    ("pos", "ရောင်းချမည်"),
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
    def __init__(self):
        super().__init__()
        theme.setup_theme()

        settings = dao.get_settings()
        self.title(f"{settings.get('store_name', 'သြဇာ')} — ရောင်းချရေးစနစ်")
        self.geometry("1280x800")
        self.minsize(1000, 640)
        self.configure(fg_color=theme.BG_APP)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, fg_color=theme.BG_SIDEBAR, width=210, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.container = ctk.CTkFrame(self, fg_color=theme.BG_APP, corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self._view_factories = _view_factories()
        self.views = {}
        self.nav_buttons = {}
        self._build_nav_buttons()

        self.show_view("pos")

    def _build_sidebar(self):
        settings = dao.get_settings()
        self.sidebar_title = ctk.CTkLabel(
            self.sidebar, text=settings.get("store_name", "သြဇာ"),
            font=theme.font(20, "bold"), text_color="#ffffff",
        )
        self.sidebar_title.pack(anchor="w", padx=20, pady=(24, 2))
        ctk.CTkLabel(
            self.sidebar, text="လက်လီရောင်းချရေးစနစ်",
            font=theme.font(11), text_color=theme.TEXT_LIGHT,
        ).pack(anchor="w", padx=20, pady=(0, 24))

        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=12)

    def _build_nav_buttons(self):
        for key, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                self.nav_frame, text=label, anchor="w",
                font=theme.font(13),
                fg_color="transparent", hover_color="#262c3b",
                text_color=theme.TEXT_LIGHT, corner_radius=theme.RADIUS_SMALL,
                height=42,
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(fill="x", pady=3)
            self.nav_buttons[key] = btn

    def show_view(self, key):
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=theme.ACCENT, text_color="#ffffff", font=theme.font(13, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color=theme.TEXT_LIGHT, font=theme.font(13))

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
        self.sidebar_title.configure(text=settings.get("store_name", "သြဇာ"))


def run():
    app = PosApp()
    app.mainloop()
