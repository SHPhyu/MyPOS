import tkinter as tk
from tkinter import ttk

from .. import dao
from ..receipt import show_receipt_window


class SalesView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Panel.TFrame", padding=16)
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Label(self, text="Sales History", style="Heading.TLabel")
        header.grid(row=0, column=0, sticky="w", pady=(0, 12))

        toolbar = ttk.Frame(self, style="Panel.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(toolbar, text="From").pack(side="left")
        self.start_var = tk.StringVar(value=dao.days_ago_str(30))
        ttk.Entry(toolbar, textvariable=self.start_var, width=12).pack(side="left", padx=(4, 12))

        ttk.Label(toolbar, text="To").pack(side="left")
        self.end_var = tk.StringVar(value=dao.today_str())
        ttk.Entry(toolbar, textvariable=self.end_var, width=12).pack(side="left", padx=(4, 12))

        ttk.Button(toolbar, text="Filter", command=self.refresh).pack(side="left")
        ttk.Label(toolbar, text="(dates as YYYY-MM-DD)", style="Muted.TLabel").pack(side="left", padx=(10, 0))

        columns = ("receipt", "date", "items", "total", "payment")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        headings = {"receipt": "Receipt #", "date": "Date", "items": "Items", "total": "Total", "payment": "Payment"}
        widths = {"receipt": 120, "date": 160, "items": 70, "total": 90, "payment": 100}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.grid(row=2, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda e: self._view_receipt())

        actions = ttk.Frame(self, style="Panel.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(actions, text="View / Reprint Receipt", style="Secondary.TButton", command=self._view_receipt).pack(side="left")

    def on_show(self):
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        symbol = dao.get_setting("currency_symbol", "$")
        start = self.start_var.get().strip() or None
        end = self.end_var.get().strip() or None
        for s in dao.list_sales(start, end):
            _, items = dao.get_sale(s["id"])
            item_count = sum(i["qty"] for i in items)
            self.tree.insert(
                "", "end", iid=str(s["id"]),
                values=(s["receipt_no"], s["created_at"], item_count, f"{symbol}{s['total']:.2f}", s["payment_method"]),
            )

    def _view_receipt(self):
        selection = self.tree.selection()
        if not selection:
            return
        sale_id = int(selection[0])
        sale, items = dao.get_sale(sale_id)
        if sale:
            show_receipt_window(self, sale, items)
