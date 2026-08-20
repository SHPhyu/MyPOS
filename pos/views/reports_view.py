import tkinter as tk

import customtkinter as ctk

from .. import dao
from .. import theme

RANGE_LABELS = ["ယနေ့", "လွန်ခဲ့သော ၇ ရက်", "လွန်ခဲ့သော ၃၀ ရက်"]


class ReportsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG_APP, corner_radius=0)
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkLabel(self, text="အစီရင်ခံစာများ", font=theme.font(20, "bold"), text_color=theme.TEXT_DARK)
        header.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 12))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 14))

        self.range_var = tk.StringVar(value=RANGE_LABELS[0])
        segmented = ctk.CTkSegmentedButton(
            toolbar, values=RANGE_LABELS, variable=self.range_var, command=lambda choice: self.refresh(),
        )
        segmented.pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ----- Summary cards -----
        summary = ctk.CTkFrame(body, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        summary.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(summary, text="အကျဉ်းချုပ်", font=theme.font(15, "bold"), text_color=theme.TEXT_DARK).pack(
            anchor="w", padx=18, pady=(18, 10)
        )
        self.revenue_label = ctk.CTkLabel(summary, text="", font=theme.font(26, "bold"), text_color=theme.TEXT_DARK)
        self.revenue_label.pack(anchor="w", padx=18)

        self.sub_labels = {}
        for key, text in [("num_sales", "ရောင်းချမှုအကြိမ်ရေ"), ("profit", "အသားတင်အမြတ်"), ("discounts", "လျှော့စျေးပေးထားသည့်ငွေ"), ("tax", "ကောက်ခံရရှိသည့် အခွန်")]:
            row = ctk.CTkFrame(summary, fg_color="transparent")
            row.pack(anchor="w", fill="x", padx=18, pady=4)
            ctk.CTkLabel(row, text=f"{text} -", font=theme.font(11), text_color=theme.TEXT_MUTED).pack(side="left")
            lbl = ctk.CTkLabel(row, text="", font=theme.font(12, "bold"), text_color=theme.TEXT_DARK)
            lbl.pack(side="left", padx=(6, 0))
            self.sub_labels[key] = lbl

        ctk.CTkLabel(summary, text="လက်ကျန်နည်းသော ပစ္စည်းများ", font=theme.font(14, "bold"), text_color=theme.TEXT_DARK).pack(
            anchor="w", padx=18, pady=(18, 6)
        )
        self.low_stock_frame = ctk.CTkFrame(summary, fg_color="transparent")
        self.low_stock_frame.pack(anchor="w", fill="both", expand=True, padx=18, pady=(0, 18))

        # ----- Top products chart -----
        chart_frame = ctk.CTkFrame(body, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        chart_frame.grid(row=0, column=1, sticky="nsew")
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(chart_frame, text="အရောင်းရဆုံးပစ္စည်းများ", font=theme.font(15, "bold"), text_color=theme.TEXT_DARK).grid(
            row=0, column=0, sticky="w", padx=18, pady=(18, 10)
        )
        self.canvas = tk.Canvas(chart_frame, bg=theme.BG_CARD, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))

    def on_show(self):
        self.refresh()

    def _date_range(self):
        label = self.range_var.get()
        if label == RANGE_LABELS[0]:
            start = dao.today_str()
        elif label == RANGE_LABELS[1]:
            start = dao.days_ago_str(6)
        else:
            start = dao.days_ago_str(29)
        end = dao.today_str()
        return start, end

    def refresh(self):
        start, end = self._date_range()
        summary = dao.sales_summary(start, end)

        self.revenue_label.configure(text=dao.format_money(summary["revenue"]))
        self.sub_labels["num_sales"].configure(text=str(summary["num_sales"]))
        self.sub_labels["profit"].configure(text=dao.format_money(summary["profit"]))
        self.sub_labels["discounts"].configure(text=dao.format_money(summary["discounts"]))
        self.sub_labels["tax"].configure(text=dao.format_money(summary["tax"]))

        for w in self.low_stock_frame.winfo_children():
            w.destroy()
        low_items = dao.low_stock_products()
        if not low_items:
            ctk.CTkLabel(self.low_stock_frame, text="ပစ္စည်းအားလုံး လက်ကျန်လုံလောက်ပါသည်", font=theme.font(12), text_color=theme.TEXT_MUTED).pack(anchor="w")
        for p in low_items:
            ctk.CTkLabel(
                self.low_stock_frame, text=f"{p['name']} — {p['stock_qty']} ကျန်", font=theme.font(12), text_color=theme.TEXT_DARK
            ).pack(anchor="w", pady=2)

        self._draw_chart(dao.top_products(start, end))

    def _draw_chart(self, rows):
        self.canvas.delete("all")
        self.canvas.update_idletasks()
        width = max(self.canvas.winfo_width(), 300)
        height = max(self.canvas.winfo_height(), 300)

        if not rows:
            self.canvas.create_text(width / 2, height / 2, text="ဤကာလအတွင်း ရောင်းချမှုမရှိပါ", fill=theme.TEXT_MUTED)
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
                padding_left - 10, (y0 + y1) / 2, text=row["product_name"], anchor="e", fill=theme.TEXT_DARK,
                font=(theme.FONT_FAMILY, 9),
            )
            self.canvas.create_rectangle(
                padding_left, y0, padding_left + bar_len, y1, fill=theme.ACCENT, outline=""
            )
            self.canvas.create_text(
                padding_left + bar_len + 6, (y0 + y1) / 2, text=str(row["qty_sold"]), anchor="w",
                fill=theme.TEXT_DARK, font=("Segoe UI", 9, "bold"),
            )
