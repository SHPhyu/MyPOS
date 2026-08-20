import tkinter as tk
from tkinter import messagebox
from datetime import datetime

import customtkinter as ctk

from .. import dao
from .. import theme
from ..receipt import show_receipt_window
from ..widgets import DataTable

PAYMENT_METHODS = ["ငွေသား", "ကတ်", "မိုဘိုင်းငွေပေးချေမှု", "အကြွေးရောင်း"]


class PosView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG_APP, corner_radius=0)
        self.app = app
        self.cart = []  # list of dicts: product_id, name, unit_price, qty, stock_qty
        self.pending_multiplier = None  # armed by the × key: next Add uses this qty

        self.code_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0")
        self.payment_method_var = tk.StringVar(value=PAYMENT_METHODS[0])
        self.tendered_var = tk.StringVar()

        self._build_ui()
        self.refresh_cart()

    # ---------- UI construction ----------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=3)
        body.grid_columnconfigure(2, weight=4)
        body.grid_rowconfigure(0, weight=1)

        self._build_cart_panel(body)
        self._build_tools_panel(body)
        self._build_control_panel(body)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=theme.BG_HEADER, corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        settings = dao.get_settings()
        self.store_name_label = ctk.CTkLabel(
            header, text=settings.get("store_name", "သြဇာ"), font=theme.font(20, "bold"), text_color="#ffffff",
        )
        self.store_name_label.pack(side="left", padx=20)

        self.clock_label = ctk.CTkLabel(header, font=theme.font(13), text_color=theme.TEXT_LIGHT)
        self.clock_label.pack(side="right", padx=20)
        self._tick_clock()

    def _tick_clock(self):
        self.clock_label.configure(text=datetime.now().strftime("%Y-%m-%d   %H:%M:%S"))
        self.after(1000, self._tick_clock)

    # ----- left: cart -----

    def _build_cart_panel(self, parent):
        col = ctk.CTkFrame(parent, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        col.grid_columnconfigure(0, weight=1)
        col.grid_rowconfigure(2, weight=1)

        total_box = ctk.CTkFrame(col, fg_color=theme.BG_TOTAL_BOX, corner_radius=theme.RADIUS)
        total_box.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        ctk.CTkLabel(total_box, text="ကျသင့်ငွေ", font=theme.font(12), text_color="#9fe6b0").pack(
            anchor="w", padx=16, pady=(12, 0)
        )
        self.total_value_label = ctk.CTkLabel(
            total_box, text=dao.format_money(0), font=theme.font(30, "bold"), text_color="#4ee27a"
        )
        self.total_value_label.pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkLabel(col, text="ရောင်းချမည့် ပစ္စည်းများ", font=theme.font(14, "bold"), text_color=theme.TEXT_DARK).grid(
            row=1, column=0, sticky="w", padx=14, pady=(0, 6)
        )

        columns = [
            {"key": "name", "heading": "ပစ္စည်းအမည်", "width": 130, "anchor": "w"},
            {"key": "qty", "heading": "အရေအတွက်", "width": 60, "anchor": "center"},
            {"key": "price", "heading": "ဈေးနှုန်း", "width": 90, "anchor": "e", "format": dao.format_money},
            {"key": "total", "heading": "စုစုပေါင်း", "width": 100, "anchor": "e", "format": dao.format_money},
        ]
        self.cart_table = DataTable(col, columns=columns, empty_text="ပစ္စည်းစာရင်း ဗလာဖြစ်နေသည်")
        self.cart_table.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 10))

        self.cart_count_label = ctk.CTkLabel(col, text="", font=theme.font(11), text_color=theme.TEXT_MUTED)
        self.cart_count_label.grid(row=3, column=0, sticky="w", padx=14, pady=(0, 12))

    # ----- middle: tools -----

    def _build_tools_panel(self, parent):
        col = ctk.CTkFrame(parent, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        col.grid(row=0, column=1, sticky="nsew", padx=8)
        col.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(col, text="ကိရိယာများ", font=theme.font(14, "bold"), text_color=theme.TEXT_DARK).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(14, 8)
        )

        ctk.CTkButton(
            col, text="မန်နေဂျာ", font=theme.font(14, "bold"), height=60,
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, corner_radius=theme.RADIUS,
            command=lambda: self.app.open_manager_menu(self),
        ).grid(row=1, column=0, columnspan=2, sticky="nsew", padx=14, pady=6)

        ctk.CTkButton(
            col, text="ဈေးနှုန်းစစ်ဆေးရန်", font=theme.font(13, "bold"), height=54,
            fg_color=theme.ACCENT_SOFT, text_color=theme.ACCENT_HOVER, hover_color=theme.BORDER,
            corner_radius=theme.RADIUS,
            command=self._open_price_check,
        ).grid(row=2, column=0, columnspan=2, sticky="nsew", padx=14, pady=6)

        tool_defs = [
            ("ပစ္စည်းရှာဖွေရန်", self._open_item_lookup),
            ("လျှော့စျေးထည့်ရန်", self._open_discount_dialog),
            ("ငွေတိုက်ဖွင့်ရန်", self._no_sale),
            ("ရောင်းချမှုပယ်ဖျက်", self._clear_cart_confirm),
            ("ဘောက်ချာ ပြန်ထုတ်ရန်", self._reprint_last_receipt),
        ]
        for i, (label, cmd) in enumerate(tool_defs):
            r, c = divmod(i, 2)
            ctk.CTkButton(
                col, text=label, font=theme.font(12, "bold"), height=54,
                fg_color="#3a4256", hover_color="#4c5670", corner_radius=theme.RADIUS,
                command=cmd,
            ).grid(row=3 + r, column=c, sticky="nsew", padx=14, pady=6)

    # ----- right: keypad, payment -----

    def _build_control_panel(self, parent):
        col = ctk.CTkFrame(parent, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        col.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        col.grid_columnconfigure(0, weight=1)

        pad = {"padx": 14}

        ctk.CTkLabel(col, text="ဘားကုဒ် / ကုဒ်နံပါတ်", font=theme.font(13, "bold"), text_color=theme.TEXT_DARK).grid(
            row=0, column=0, sticky="w", **pad, pady=(14, 4)
        )
        code_entry = ctk.CTkEntry(
            col, textvariable=self.code_var, font=theme.font(18, "bold"), justify="right", height=42,
        )
        code_entry.grid(row=1, column=0, sticky="ew", **pad, pady=(0, 2))
        code_entry.bind("<Return>", lambda e: self._add_by_code())

        self.multiplier_label = ctk.CTkLabel(col, text="", font=theme.font(11, "bold"), text_color=theme.ACCENT)
        self.multiplier_label.grid(row=2, column=0, sticky="w", **pad, pady=(0, 6))

        keypad = ctk.CTkFrame(col, fg_color="transparent")
        keypad.grid(row=3, column=0, sticky="ew", **pad)
        for c in range(4):
            keypad.grid_columnconfigure(c, weight=1)

        digit_style = dict(font=theme.font(18, "bold"), height=44, fg_color=theme.ROW_ALT,
                            text_color=theme.TEXT_DARK, hover_color=theme.BORDER)
        op_style = dict(font=theme.font(16, "bold"), height=44, fg_color=theme.ACCENT_SOFT,
                         text_color=theme.ACCENT_HOVER, hover_color=theme.BORDER)

        ctk.CTkButton(keypad, text="7", command=lambda: self._keypad_press("7"), **digit_style).grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="8", command=lambda: self._keypad_press("8"), **digit_style).grid(row=0, column=1, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="9", command=lambda: self._keypad_press("9"), **digit_style).grid(row=0, column=2, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="+", command=lambda: self._change_qty(1), **op_style).grid(row=0, column=3, sticky="nsew", padx=3, pady=3)

        ctk.CTkButton(keypad, text="4", command=lambda: self._keypad_press("4"), **digit_style).grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="5", command=lambda: self._keypad_press("5"), **digit_style).grid(row=1, column=1, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="6", command=lambda: self._keypad_press("6"), **digit_style).grid(row=1, column=2, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="-", command=lambda: self._change_qty(-1), **op_style).grid(row=1, column=3, sticky="nsew", padx=3, pady=3)

        ctk.CTkButton(keypad, text="1", command=lambda: self._keypad_press("1"), **digit_style).grid(row=2, column=0, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="2", command=lambda: self._keypad_press("2"), **digit_style).grid(row=2, column=1, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="3", command=lambda: self._keypad_press("3"), **digit_style).grid(row=2, column=2, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="×", command=self._arm_multiplier, **op_style).grid(row=2, column=3, sticky="nsew", padx=3, pady=3)

        ctk.CTkButton(keypad, text="⌫", command=self._keypad_backspace, **digit_style).grid(row=3, column=0, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text="0", command=lambda: self._keypad_press("0"), **digit_style).grid(row=3, column=1, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(keypad, text=".", command=lambda: self._keypad_press("."), **digit_style).grid(row=3, column=2, sticky="nsew", padx=3, pady=3)
        ctk.CTkButton(
            keypad, text="ဖျက်", font=theme.font(14, "bold"), height=44,
            fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER, command=self._remove_selected,
        ).grid(row=3, column=3, sticky="nsew", padx=3, pady=3)

        ctk.CTkButton(
            col, text="ထည့်ရန်", font=theme.font(14, "bold"), height=42,
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, corner_radius=theme.RADIUS,
            command=self._add_by_code,
        ).grid(row=4, column=0, sticky="ew", **pad, pady=(8, 12))

        payment = ctk.CTkFrame(col, fg_color="transparent")
        payment.grid(row=5, column=0, sticky="ew", **pad)
        payment.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(payment, text="ငွေပေးချေမှုပုံစံ", font=theme.font(12), text_color=theme.TEXT_DARK).grid(
            row=0, column=0, sticky="w"
        )
        payment_combo = ctk.CTkComboBox(
            payment, values=PAYMENT_METHODS, variable=self.payment_method_var, state="readonly", width=150,
            command=lambda choice: self._update_tendered_state(),
        )
        payment_combo.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(payment, text="ပေးချေငွေ", font=theme.font(12), text_color=theme.TEXT_DARK).grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        self.tendered_entry = ctk.CTkEntry(payment, textvariable=self.tendered_var, width=140, justify="right")
        self.tendered_entry.grid(row=1, column=1, sticky="e", pady=(8, 0))
        self.tendered_var.trace_add("write", lambda *a: self._update_change())

        self.change_label = ctk.CTkLabel(payment, text="", font=theme.font(11), text_color=theme.TEXT_MUTED)
        self.change_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        discount_row = ctk.CTkFrame(col, fg_color="transparent")
        discount_row.grid(row=6, column=0, sticky="ew", **pad, pady=(6, 0))
        ctk.CTkLabel(discount_row, text="လျှော့စျေး -", font=theme.font(11), text_color=theme.TEXT_MUTED).pack(side="left")
        self.discount_display = ctk.CTkLabel(discount_row, text=dao.format_money(0), font=theme.font(11), text_color=theme.TEXT_MUTED)
        self.discount_display.pack(side="left", padx=(6, 0))

        ctk.CTkButton(
            col, text="ငွေရှင်းမည်", font=theme.font(18, "bold"), height=56,
            fg_color=theme.SUCCESS, hover_color=theme.SUCCESS_HOVER, corner_radius=theme.RADIUS,
            command=self._complete_sale,
        ).grid(row=7, column=0, sticky="ew", **pad, pady=(14, 16))

    # ---------- lifecycle ----------

    def on_show(self):
        settings = dao.get_settings()
        self.store_name_label.configure(text=settings.get("store_name", "သြဇာ"))

    # ---------- keypad ----------

    def _keypad_press(self, ch):
        self.code_var.set(self.code_var.get() + ch)

    def _keypad_backspace(self):
        self.code_var.set(self.code_var.get()[:-1])

    def _arm_multiplier(self):
        raw = self.code_var.get().strip()
        if not raw:
            if self.pending_multiplier is not None:
                self.pending_multiplier = None
                self.multiplier_label.configure(text="")
            return
        try:
            qty = int(float(raw))
        except ValueError:
            messagebox.showwarning("မှားယွင်းနေပါသည်", "ဂဏန်းအမှန်ကို ရိုက်ထည့်ပါ။")
            return
        if qty <= 0:
            messagebox.showwarning("မှားယွင်းနေပါသည်", "အရေအတွက်သည် သုညထက်ကြီးရပါမည်။")
            return
        self.pending_multiplier = qty
        self.code_var.set("")
        self.multiplier_label.configure(text=f"× {qty} ကြိမ် ထည့်ရန် ကုဒ်ရိုက်ပါ")

    def _consume_multiplier(self):
        qty = self.pending_multiplier or 1
        self.pending_multiplier = None
        self.multiplier_label.configure(text="")
        return qty

    def _add_by_code(self):
        code = self.code_var.get().strip()
        if not code:
            return
        product = dao.find_by_barcode_or_sku(code)
        if product:
            qty = self._consume_multiplier()
            self._add_product_to_cart(product, qty=qty)
            self.code_var.set("")
        else:
            messagebox.showinfo("မတွေ့ပါ", f"ကုဒ် '{code}' နှင့် ကိုက်ညီသော ပစ္စည်းကို မတွေ့ပါ။")

    # ---------- tools ----------

    def _open_item_lookup(self):
        ItemLookupDialog(self, on_pick=self._add_product_to_cart)

    def _open_price_check(self):
        PriceCheckDialog(self)

    # ---------- cart manipulation ----------

    def _add_product_to_cart(self, product, qty=1):
        if product["stock_qty"] <= 0:
            messagebox.showwarning("ပစ္စည်းကုန်နေပါသည်", f"{product['name']} လက်ကျန်မရှိတော့ပါ။")
            return
        for item in self.cart:
            if item["product_id"] == product["id"]:
                if item["qty"] + qty > product["stock_qty"]:
                    messagebox.showwarning("ကုန်ပစ္စည်း မလုံလောက်ပါ", f"လက်ကျန် {product['stock_qty']} ခုသာ ရှိပါသည်။")
                    return
                item["qty"] += qty
                self.refresh_cart()
                return
        if qty > product["stock_qty"]:
            messagebox.showwarning("ကုန်ပစ္စည်း မလုံလောက်ပါ", f"လက်ကျန် {product['stock_qty']} ခုသာ ရှိပါသည်။")
            return
        self.cart.append({
            "product_id": product["id"],
            "name": product["name"],
            "unit_price": product["price"],
            "qty": qty,
            "stock_qty": product["stock_qty"],
        })
        self.refresh_cart()

    def _change_qty(self, delta):
        idx = self.cart_table.selected_index
        if idx is None or idx >= len(self.cart):
            return
        item = self.cart[idx]
        new_qty = item["qty"] + delta
        if new_qty <= 0:
            self.cart.pop(idx)
        elif new_qty > item["stock_qty"]:
            messagebox.showwarning("ကုန်ပစ္စည်း မလုံလောက်ပါ", f"လက်ကျန် {item['stock_qty']} ခုသာ ရှိပါသည်။")
            return
        else:
            item["qty"] = new_qty
        self.refresh_cart()

    def _remove_selected(self):
        idx = self.cart_table.selected_index
        if idx is None or idx >= len(self.cart):
            return
        self.cart.pop(idx)
        self.refresh_cart()

    def _clear_cart_confirm(self):
        if not self.cart:
            return
        if messagebox.askyesno("ရောင်းချမှုပယ်ဖျက်ရန်", "လက်ရှိစာရင်းအားလုံးကို ဖျက်မှာ သေချာပါသလား?"):
            self._clear_cart()

    def _clear_cart(self):
        self.cart = []
        self.discount_var.set("0")
        self.tendered_var.set("")
        self.refresh_cart()

    def _no_sale(self):
        messagebox.showinfo("ငွေတိုက်", "ငွေတိုက်ကို ဖွင့်လိုက်ပါပြီ။")

    # ---------- totals ----------

    def _safe_float(self, value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def compute_totals(self):
        subtotal = sum(item["unit_price"] * item["qty"] for item in self.cart)
        discount = self._safe_float(self.discount_var.get(), 0.0)
        discount = max(0.0, min(discount, subtotal))
        tax_rate = self._safe_float(dao.get_setting("tax_rate", "0"), 0.0)
        taxable = max(subtotal - discount, 0.0)
        tax = round(taxable * tax_rate / 100, 2)
        total = round(taxable + tax, 2)
        return subtotal, discount, tax, total

    def refresh_cart(self, recompute_only=False):
        if not recompute_only:
            prev_selected = self.cart_table.selected_index
            rows = [
                {"name": item["name"], "qty": item["qty"], "price": item["unit_price"], "total": item["unit_price"] * item["qty"]}
                for item in self.cart
            ]
            self.cart_table.set_rows(rows)
            if prev_selected is not None and prev_selected < len(rows):
                self.cart_table.select_index(prev_selected)

        subtotal, discount, tax, total = self.compute_totals()
        self.total_value_label.configure(text=dao.format_money(total))
        self.discount_display.configure(text=dao.format_money(discount))
        total_qty = sum(item["qty"] for item in self.cart)
        self.cart_count_label.configure(text=f"စုစုပေါင်း ပစ္စည်းအရေအတွက်: {total_qty}")
        self._update_change()

    def _update_tendered_state(self):
        if self.payment_method_var.get() != PAYMENT_METHODS[0]:
            self.tendered_var.set("")

    def _update_change(self):
        subtotal, discount, tax, total = self.compute_totals()
        tendered = self._safe_float(self.tendered_var.get(), None) if self.tendered_var.get() else None
        if tendered is not None:
            change = round(tendered - total, 2)
            self.change_label.configure(text=f"ပြန်အမ်းငွေ - {dao.format_money(change)}")
        else:
            self.change_label.configure(text="")

    # ---------- discount ----------

    def _open_discount_dialog(self):
        DiscountDialog(self, current=self.discount_var.get(), on_apply=self._set_discount)

    def _set_discount(self, value):
        self.discount_var.set(value)
        self.refresh_cart(recompute_only=True)

    # ---------- receipts ----------

    def _reprint_last_receipt(self):
        sale, items = dao.get_last_sale()
        if not sale:
            messagebox.showinfo("ဘောက်ချာမရှိပါ", "ယခင်ရောင်းချမှု မရှိသေးပါ။")
            return
        show_receipt_window(self, sale, items)

    # ---------- complete sale ----------

    def _complete_sale(self):
        if not self.cart:
            messagebox.showinfo("ပစ္စည်းမရှိပါ", "ငွေရှင်းမည့်ပစ္စည်းအနည်းဆုံး တစ်ခုထည့်ပါ။")
            return

        subtotal, discount, tax, total = self.compute_totals()
        payment_method = self.payment_method_var.get()

        if payment_method == "အကြွေးရောင်း":
            CreditSaleDialog(
                self, total,
                on_complete=lambda customer_id: self._finalize_sale(payment_method, None, customer_id),
            )
            return

        amount_tendered = None
        if payment_method == "ငွေသား":
            amount_tendered = self._safe_float(self.tendered_var.get(), None) if self.tendered_var.get() else None
            if amount_tendered is None or amount_tendered < total:
                messagebox.showwarning("ငွေမလုံလောက်ပါ", "ကျသင့်ငွေအပြည့်ရှိအောင် ပေးချေငွေကို ထည့်ပါ။")
                return

        self._finalize_sale(payment_method, amount_tendered, None)

    def _finalize_sale(self, payment_method, amount_tendered, customer_id):
        subtotal, discount, tax, total = self.compute_totals()
        tax_rate = self._safe_float(dao.get_setting("tax_rate", "0"), 0.0)
        sale = dao.create_sale(self.cart, discount, tax_rate, payment_method, amount_tendered, customer_id)

        sale_display = dict(sale)
        sale_display["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        _, items = dao.get_sale(sale["id"])

        show_receipt_window(self, sale_display, items)

        self.cart = []
        self.discount_var.set("0")
        self.tendered_var.set("")
        self.refresh_cart()


class ItemLookupDialog(ctk.CTkToplevel):
    """Full product search — the main way to find an item now that the
    checkout screen no longer shows a product tile grid."""

    def __init__(self, parent, on_pick):
        super().__init__(parent)
        self.on_pick = on_pick
        self.title("ပစ္စည်းရှာဖွေရန်")
        self.geometry("460x540")
        self.configure(fg_color=theme.BG_APP)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(frame, textvariable=self.search_var, placeholder_text="ရှာဖွေရန်...", height=38)
        search_entry.pack(fill="x", pady=(0, 10))
        search_entry.focus_set()
        self.search_var.trace_add("write", lambda *a: self._refresh())

        columns = [
            {"key": "name", "heading": "ပစ္စည်းအမည်", "width": 180, "anchor": "w"},
            {"key": "sku", "heading": "ကုဒ်", "width": 80, "anchor": "center"},
            {"key": "price", "heading": "ဈေးနှုန်း", "width": 90, "anchor": "e", "format": dao.format_money},
            {"key": "stock_qty", "heading": "လက်ကျန်", "width": 70, "anchor": "center"},
        ]
        self.table = DataTable(frame, columns=columns, height=340, on_double_click=self._pick)
        self.table.pack(fill="both", expand=True)

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(btn_row, text="ပိတ်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self.destroy).pack(side="right")
        ctk.CTkButton(btn_row, text="ထည့်ရန်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._pick_selected).pack(side="right", padx=6)

        self._refresh()
        self.transient(parent)
        self.grab_set()

    def _refresh(self):
        search = self.search_var.get().strip()
        self.table.set_rows(dao.list_products(search=search or None))

    def _pick(self, row):
        self.on_pick(row)

    def _pick_selected(self):
        row = self.table.get_selected()
        if row:
            self.on_pick(row)


class PriceCheckDialog(ctk.CTkToplevel):
    """Read-only lookup — shows a product's price without touching the
    cart, for 'how much is this?' questions at the register."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("ဈေးနှုန်းစစ်ဆေးရန်")
        self.geometry("460x600")
        self.configure(fg_color=theme.BG_APP)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(frame, textvariable=self.search_var, placeholder_text="ကုဒ် သို့မဟုတ် အမည်ဖြင့် ရှာပါ...", height=38)
        search_entry.pack(fill="x", pady=(0, 10))
        search_entry.focus_set()
        search_entry.bind("<Return>", lambda e: self._lookup_exact())
        self.search_var.trace_add("write", lambda *a: self._refresh())

        self.price_box = ctk.CTkFrame(frame, fg_color=theme.BG_TOTAL_BOX, corner_radius=theme.RADIUS)
        self.price_box.pack(fill="x", pady=(0, 10))
        self.price_name_label = ctk.CTkLabel(self.price_box, text="ပစ္စည်းတစ်ခုကို ရွေးပါ", font=theme.font(13), text_color="#9fe6b0")
        self.price_name_label.pack(anchor="w", padx=16, pady=(12, 0))
        self.price_value_label = ctk.CTkLabel(self.price_box, text="—", font=theme.font(28, "bold"), text_color="#4ee27a")
        self.price_value_label.pack(anchor="w", padx=16, pady=(0, 14))

        columns = [
            {"key": "name", "heading": "ပစ္စည်းအမည်", "width": 190, "anchor": "w"},
            {"key": "sku", "heading": "ကုဒ်", "width": 90, "anchor": "center"},
            {"key": "price", "heading": "ဈေးနှုန်း", "width": 100, "anchor": "e", "format": dao.format_money},
        ]
        self.table = DataTable(frame, columns=columns, height=280, on_select=self._show_price, on_double_click=self._show_price)
        self.table.pack(fill="both", expand=True)

        ctk.CTkButton(frame, text="ပိတ်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self.destroy).pack(fill="x", pady=(10, 0))

        self._refresh()
        self.transient(parent)
        self.grab_set()

    def _refresh(self):
        search = self.search_var.get().strip()
        self.table.set_rows(dao.list_products(search=search or None))

    def _lookup_exact(self):
        code = self.search_var.get().strip()
        if not code:
            return
        product = dao.find_by_barcode_or_sku(code)
        if product:
            self._show_price(product)
        else:
            self.price_name_label.configure(text="မတွေ့ပါ")
            self.price_value_label.configure(text="—")

    def _show_price(self, row):
        stock_note = f"  (လက်ကျန် {row['stock_qty']})" if "stock_qty" in row.keys() else ""
        self.price_name_label.configure(text=f"{row['name']}{stock_note}")
        self.price_value_label.configure(text=dao.format_money(row["price"]))


class DiscountDialog(ctk.CTkToplevel):
    def __init__(self, parent, current, on_apply):
        super().__init__(parent)
        self.on_apply = on_apply
        self.title("လျှော့စျေးထည့်ရန်")
        self.geometry("300x180")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_APP)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text="လျှော့စျေးပမာဏ", text_color=theme.TEXT_DARK).pack(anchor="w")
        self.value_var = tk.StringVar(value=current)
        entry = ctk.CTkEntry(frame, textvariable=self.value_var, justify="right", height=38)
        entry.pack(fill="x", pady=(4, 14))
        entry.focus_set()
        entry.select_range(0, "end")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x")
        ctk.CTkButton(btn_row, text="မလုပ်တော့ပါ", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self.destroy).pack(side="right")
        ctk.CTkButton(btn_row, text="သိမ်းမည်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._apply).pack(side="right", padx=6)

        self.transient(parent)
        self.grab_set()

    def _apply(self):
        try:
            float(self.value_var.get())
        except ValueError:
            messagebox.showwarning("မှားယွင်းနေပါသည်", "ဂဏန်းအမှန်ကို ရိုက်ထည့်ပါ။")
            return
        self.on_apply(self.value_var.get())
        self.destroy()


class CreditSaleDialog(ctk.CTkToplevel):
    """Pick (or settle) the customer a credit sale should be billed to.

    Enforces the store's tab policy: a customer with any outstanding
    balance must be paid down to zero before a new credit sale is allowed.
    """

    def __init__(self, parent, total, on_complete):
        super().__init__(parent)
        self.on_complete = on_complete
        self.selected_customer_id = None

        self.title("အကြွေးရောင်း")
        self.geometry("440x540")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_APP)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            frame, text=f"ကျသင့်ငွေ - {dao.format_money(total)}", font=theme.font(14, "bold"), text_color=theme.TEXT_DARK
        ).pack(anchor="w", pady=(0, 10))

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(frame, textvariable=self.search_var, placeholder_text="ဖောက်သည်ရှာရန်...", height=38)
        search_entry.pack(fill="x", pady=(0, 10))
        search_entry.focus_set()
        self.search_var.trace_add("write", lambda *a: self._refresh_list())

        columns = [
            {"key": "name", "heading": "ဖောက်သည်", "width": 150, "anchor": "w"},
            {"key": "phone", "heading": "ဖုန်းနံပါတ်", "width": 100, "anchor": "center"},
            {"key": "credit_balance", "heading": "ကျန်ငွေ", "width": 90, "anchor": "e", "format": dao.format_money},
        ]
        self.table = DataTable(frame, columns=columns, height=220, on_select=lambda row: self._on_select(row))
        self.table.pack(fill="both", expand=True)

        self.balance_label = ctk.CTkLabel(
            frame, text="အထက်မှ ဖောက်သည်တစ်ဦးကို ရွေးပါ။", wraplength=380, justify="left", text_color=theme.TEXT_DARK
        )
        self.balance_label.pack(anchor="w", pady=(10, 4))

        settle_row = ctk.CTkFrame(frame, fg_color="transparent")
        settle_row.pack(fill="x")
        ctk.CTkLabel(settle_row, text="ပေးချေမည့်ငွေ", text_color=theme.TEXT_DARK).pack(side="left")
        self.settle_var = tk.StringVar()
        ctk.CTkEntry(settle_row, textvariable=self.settle_var, width=100).pack(side="left", padx=(6, 6))
        ctk.CTkButton(
            settle_row, text="ငွေပေးချေမည်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
            hover_color=theme.BORDER, command=self._apply_payment,
        ).pack(side="left")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(16, 0))
        ctk.CTkButton(btn_row, text="မလုပ်တော့ပါ", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self.destroy).pack(side="right")
        ctk.CTkButton(btn_row, text="အကြွေးရောင်းချမည်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._complete).pack(side="right", padx=6)

        self._refresh_list()
        self.transient(parent)
        self.grab_set()

    def _refresh_list(self):
        search = self.search_var.get().strip()
        self.table.set_rows(dao.list_customers(search=search or None), row_tag=lambda r: "warn" if r["credit_balance"] > 0 else None)

    def _on_select(self, row):
        self.selected_customer_id = row["id"]
        customer = dao.get_customer(self.selected_customer_id)
        if customer["credit_balance"] > 0:
            self.balance_label.configure(
                text=f"{customer['name']} သည် ယခင်ဝယ်ယူမှုမှ {dao.format_money(customer['credit_balance'])} ကျန်ရှိနေပါသည် — "
                     "အကြွေးအသစ်မရောင်းမီ ထိုငွေအား ဦးစွာရှင်းရပါမည်။"
            )
            self.settle_var.set(f"{customer['credit_balance']:.0f}")
        else:
            self.balance_label.configure(text=f"{customer['name']} တွင် ကျန်ငွေမရှိပါ။")
            self.settle_var.set("")

    def _apply_payment(self):
        if self.selected_customer_id is None:
            messagebox.showinfo("ဖောက်သည်မရွေးရသေးပါ", "ဖောက်သည်တစ်ဦးကို အရင်ရွေးပါ။")
            return
        try:
            amount = float(self.settle_var.get())
        except ValueError:
            messagebox.showwarning("မှားယွင်းနေပါသည်", "ငွေပမာဏအမှန်ကို ရိုက်ထည့်ပါ။")
            return
        if amount <= 0:
            messagebox.showwarning("မှားယွင်းနေပါသည်", "ငွေပမာဏသည် သုညထက်ကြီးရပါမည်။")
            return
        dao.record_customer_payment(self.selected_customer_id, amount, "အကြွေးရောင်းအသစ်မတိုင်မီ ငွေပေးချေမှု")
        customer_id = self.selected_customer_id
        self._refresh_list()
        self.selected_customer_id = customer_id
        self._on_select({"id": customer_id})

    def _complete(self):
        if self.selected_customer_id is None:
            messagebox.showinfo("ဖောက်သည်မရွေးရသေးပါ", "အကြွေးရောင်းအတွက် ဖောက်သည်တစ်ဦးကို ရွေးပါ။")
            return
        customer = dao.get_customer(self.selected_customer_id)
        if customer["credit_balance"] > 0:
            messagebox.showwarning(
                "ကျန်ငွေရှိနေပါသည်",
                f"{customer['name']} သည် အကြွေးအသစ်မဝယ်မီ ကျန်ငွေ {dao.format_money(customer['credit_balance'])} ကို ဦးစွာပေးချေရပါမည်။",
            )
            return
        customer_id = self.selected_customer_id
        self.destroy()
        self.on_complete(customer_id)
