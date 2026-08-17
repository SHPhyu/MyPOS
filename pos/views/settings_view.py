import tkinter as tk
from tkinter import ttk, messagebox

from .. import dao


class SettingsView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Panel.TFrame", padding=16)
        self.app = app
        self._build_ui()
        self.load()

    def _build_ui(self):
        header = ttk.Label(self, text="Settings", style="Heading.TLabel")
        header.pack(anchor="w", pady=(0, 16))

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(anchor="w", fill="x")

        self.store_name_var = tk.StringVar()
        self.currency_var = tk.StringVar()
        self.tax_rate_var = tk.StringVar()
        self.footer_var = tk.StringVar()

        rows = [
            ("Store name", self.store_name_var),
            ("Currency symbol", self.currency_var),
            ("Tax rate (%)", self.tax_rate_var),
            ("Receipt footer text", self.footer_var),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(card, text=label, style="Card.TLabel").grid(row=i, column=0, sticky="w", pady=8)
            ttk.Entry(card, textvariable=var, width=36).grid(row=i, column=1, sticky="ew", pady=8, padx=(12, 0))
        card.columnconfigure(1, weight=1)

        ttk.Button(self, text="Save Settings", command=self._save).pack(anchor="w", pady=(16, 0))

    def on_show(self):
        self.load()

    def load(self):
        settings = dao.get_settings()
        self.store_name_var.set(settings.get("store_name", "My Store"))
        self.currency_var.set(settings.get("currency_symbol", "$"))
        self.tax_rate_var.set(settings.get("tax_rate", "0"))
        self.footer_var.set(settings.get("receipt_footer", "Thank you!"))

    def _save(self):
        try:
            float(self.tax_rate_var.get())
        except ValueError:
            messagebox.showwarning("Invalid tax rate", "Tax rate must be a number.")
            return

        dao.update_settings({
            "store_name": self.store_name_var.get().strip() or "My Store",
            "currency_symbol": self.currency_var.get().strip() or "$",
            "tax_rate": self.tax_rate_var.get().strip() or "0",
            "receipt_footer": self.footer_var.get().strip(),
        })
        self.app.refresh_title()
        messagebox.showinfo("Saved", "Settings updated.")
