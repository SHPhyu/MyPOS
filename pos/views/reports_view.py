import tkinter as tk
from tkinter import ttk

from .. import dao

BAR_COLOR = "#2f6fed"


class ReportsView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Panel.TFrame", padding=16)
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Label(self, text="Reports", style="Heading.TLabel")
        header.grid(row=0, column=0, sticky="w", pady=(0, 12))

        toolbar = ttk.Frame(self, style="Panel.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        self.range_var = tk.StringVar(value="Today")
        for i, label in enumerate(["Today", "Last 7 Days", "Last 30 Days"]):
            ttk.Radiobutton(
                toolbar, text=label, value=label, variable=self.range_var,
                command=self.refresh,
            ).pack(side="left", padx=(0 if i == 0 else 10, 0))

        body = ttk.Frame(self, style="Panel.TFrame")
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ----- Summary cards -----
        summary = ttk.Frame(body, style="Card.TFrame", padding=18)
        summary.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(summary, text="Summary", style="CardHeading.TLabel").pack(anchor="w", pady=(0, 10))
        self.revenue_label = ttk.Label(summary, text="", style="Total.TLabel")
        self.revenue_label.pack(anchor="w")
        self.sub_labels = {}
        for key, text in [("num_sales", "Transactions"), ("profit", "Gross profit"), ("discounts", "Discounts given"), ("tax", "Tax collected")]:
            row = ttk.Frame(summary, style="Card.TFrame")
            row.pack(anchor="w", fill="x", pady=4)
            ttk.Label(row, text=f"{text}:", style="CardMuted.TLabel").pack(side="left")
            lbl = ttk.Label(row, text="", style="Card.TLabel")
            lbl.pack(side="left", padx=(6, 0))
            self.sub_labels[key] = lbl

        low_stock_frame = ttk.Frame(summary, style="Card.TFrame")
        low_stock_frame.pack(anchor="w", fill="x", pady=(16, 0))
        ttk.Label(low_stock_frame, text="Low Stock Alerts", style="CardHeading.TLabel").pack(anchor="w")
        self.low_stock_list = tk.Listbox(low_stock_frame, height=6, borderwidth=0, highlightthickness=0)
        self.low_stock_list.pack(fill="x", pady=(6, 0))

        # ----- Top products chart -----
        chart_frame = ttk.Frame(body, style="Card.TFrame", padding=18)
        chart_frame.grid(row=0, column=1, sticky="nsew")
        ttk.Label(chart_frame, text="Top Products", style="CardHeading.TLabel").pack(anchor="w", pady=(0, 10))
        self.canvas = tk.Canvas(chart_frame, bg="#ffffff", highlightthickness=0, height=360)
        self.canvas.pack(fill="both", expand=True)

    def on_show(self):
        self.refresh()

    def _date_range(self):
        label = self.range_var.get()
        if label == "Today":
            start = dao.today_str()
        elif label == "Last 7 Days":
            start = dao.days_ago_str(6)
        else:
            start = dao.days_ago_str(29)
        end = dao.today_str()
        return start, end

    def refresh(self):
        start, end = self._date_range()
        summary = dao.sales_summary(start, end)
        symbol = dao.get_setting("currency_symbol", "$")

        self.revenue_label.configure(text=f"{symbol}{summary['revenue']:.2f}")
        self.sub_labels["num_sales"].configure(text=str(summary["num_sales"]))
        self.sub_labels["profit"].configure(text=f"{symbol}{summary['profit']:.2f}")
        self.sub_labels["discounts"].configure(text=f"{symbol}{summary['discounts']:.2f}")
        self.sub_labels["tax"].configure(text=f"{symbol}{summary['tax']:.2f}")

        self.low_stock_list.delete(0, tk.END)
        low_items = dao.low_stock_products()
        if not low_items:
            self.low_stock_list.insert(tk.END, "All products well stocked")
        for p in low_items:
            self.low_stock_list.insert(tk.END, f"{p['name']} — {p['stock_qty']} left")

        self._draw_chart(dao.top_products(start, end))

    def _draw_chart(self, rows):
        self.canvas.delete("all")
        self.canvas.update_idletasks()
        width = max(self.canvas.winfo_width(), 300)
        height = max(self.canvas.winfo_height(), 300)

        if not rows:
            self.canvas.create_text(width / 2, height / 2, text="No sales in this period", fill="#6b7280")
            return

        max_qty = max(r["qty_sold"] for r in rows) or 1
        padding_left = 140
        padding_right = 20
        top = 10
        bottom = 20
        bar_area_width = width - padding_left - padding_right
        row_height = max((height - top - bottom) / len(rows), 24)

        for i, row in enumerate(rows):
            y0 = top + i * row_height
            y1 = y0 + row_height * 0.6
            bar_len = (row["qty_sold"] / max_qty) * bar_area_width
            self.canvas.create_text(
                padding_left - 10, (y0 + y1) / 2, text=row["product_name"], anchor="e", fill="#1c1f26",
                font=("Segoe UI", 9),
            )
            self.canvas.create_rectangle(
                padding_left, y0, padding_left + bar_len, y1, fill=BAR_COLOR, outline=""
            )
            self.canvas.create_text(
                padding_left + bar_len + 6, (y0 + y1) / 2, text=str(row["qty_sold"]), anchor="w",
                fill="#1c1f26", font=("Segoe UI", 9, "bold"),
            )
