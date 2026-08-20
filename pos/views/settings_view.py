import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from .. import dao
from .. import theme
from ..widgets import ScreenHeader


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG_APP, corner_radius=0)
        self.app = app
        self._build_ui()
        self.load()

    def _build_ui(self):
        header = ScreenHeader(self, self.app, "ဆက်တင်များ")
        header.pack(anchor="w", padx=20, pady=(20, 16))

        card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        card.pack(anchor="w", fill="x", padx=20)
        card.grid_columnconfigure(1, weight=1)

        self.store_name_var = tk.StringVar()
        self.currency_var = tk.StringVar()
        self.tax_rate_var = tk.StringVar()
        self.footer_var = tk.StringVar()

        rows = [
            ("ဆိုင်အမည်", self.store_name_var),
            ("ငွေကြေးအမှတ်အသား", self.currency_var),
            ("အခွန်နှုန်း (%)", self.tax_rate_var),
            ("ဘောက်ချာအောက်ခြေစာသား", self.footer_var),
        ]
        for i, (label, var) in enumerate(rows):
            ctk.CTkLabel(card, text=label, text_color=theme.TEXT_DARK).grid(row=i, column=0, sticky="w", padx=(20, 12), pady=12)
            ctk.CTkEntry(card, textvariable=var, width=340, height=36).grid(row=i, column=1, sticky="ew", padx=(0, 20), pady=12)

        ctk.CTkButton(self, text="ဆက်တင်များ သိမ်းမည်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      height=40, command=self._save).pack(anchor="w", padx=20, pady=(16, 0))

    def on_show(self):
        self.load()

    def load(self):
        settings = dao.get_settings()
        self.store_name_var.set(settings.get("store_name", "သြဇာ"))
        self.currency_var.set(settings.get("currency_symbol", "Ks"))
        self.tax_rate_var.set(settings.get("tax_rate", "0"))
        self.footer_var.set(settings.get("receipt_footer", "ကျေးဇူးတင်ပါသည်။"))

    def _save(self):
        try:
            float(self.tax_rate_var.get())
        except ValueError:
            messagebox.showwarning("အခွန်နှုန်းမှားနေပါသည်", "အခွန်နှုန်းသည် ဂဏန်းဖြစ်ရပါမည်။")
            return

        dao.update_settings({
            "store_name": self.store_name_var.get().strip() or "သြဇာ",
            "currency_symbol": self.currency_var.get().strip() or "Ks",
            "tax_rate": self.tax_rate_var.get().strip() or "0",
            "receipt_footer": self.footer_var.get().strip(),
        })
        self.app.refresh_title()
        messagebox.showinfo("သိမ်းဆည်းပြီးပါပြီ", "ဆက်တင်များကို အပ်ဒိတ်လုပ်ပြီးပါပြီ။")
