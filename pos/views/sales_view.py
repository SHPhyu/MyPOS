import tkinter as tk

import customtkinter as ctk

from .. import dao
from .. import theme
from ..receipt import show_receipt_window
from ..widgets import DataTable, ScreenHeader


class SalesView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG_APP, corner_radius=0)
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ScreenHeader(self, self.app, "ရောင်းအားမှတ်တမ်း")
        header.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 12))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkLabel(toolbar, text="ရက်စွဲမှ", text_color=theme.TEXT_DARK).pack(side="left")
        self.start_var = tk.StringVar(value=dao.days_ago_str(30))
        ctk.CTkEntry(toolbar, textvariable=self.start_var, width=110, height=34).pack(side="left", padx=(6, 14))

        ctk.CTkLabel(toolbar, text="ရက်စွဲအထိ", text_color=theme.TEXT_DARK).pack(side="left")
        self.end_var = tk.StringVar(value=dao.today_str())
        ctk.CTkEntry(toolbar, textvariable=self.end_var, width=110, height=34).pack(side="left", padx=(6, 14))

        ctk.CTkButton(toolbar, text="စစ်ထုတ်ရန်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      height=34, command=self.refresh).pack(side="left")
        ctk.CTkLabel(toolbar, text="(ရက်စွဲပုံစံ YYYY-MM-DD)", font=theme.font(11), text_color=theme.TEXT_MUTED).pack(
            side="left", padx=(10, 0)
        )

        columns = [
            {"key": "receipt_no", "heading": "ဘောက်ချာအမှတ်", "width": 120, "anchor": "center"},
            {"key": "created_at", "heading": "ရက်စွဲ", "width": 150, "anchor": "center"},
            {"key": "item_count", "heading": "ပစ္စည်းအရေအတွက်", "width": 110, "anchor": "center"},
            {"key": "total", "heading": "စုစုပေါင်း", "width": 100, "anchor": "e", "format": dao.format_money},
            {"key": "payment_method", "heading": "ငွေပေးချေမှုပုံစံ", "width": 140, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=columns, on_double_click=lambda row: self._view_receipt())
        self.table.grid(row=2, column=0, sticky="nsew", padx=20)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        ctk.CTkButton(actions, text="ဘောက်ချာကြည့်ရန် / ပြန်ထုတ်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self._view_receipt).pack(side="left")

    def on_show(self):
        self.refresh()

    def refresh(self):
        start = self.start_var.get().strip() or None
        end = self.end_var.get().strip() or None
        self.table.set_rows(dao.list_sales_with_item_counts(start, end))

    def _view_receipt(self):
        row = self.table.get_selected()
        if not row:
            return
        sale, items = dao.get_sale(row["id"])
        if sale:
            show_receipt_window(self, sale, items)
