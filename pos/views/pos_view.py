import tkinter as tk
from tkinter import ttk, messagebox

from .. import dao
from ..receipt import show_receipt_window


class PosView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Panel.TFrame", padding=16)
        self.app = app
        self.cart = []  # list of dicts: product_id, name, unit_price, qty, stock_qty
        self.selected_category = None

        self._build_ui()
        self.refresh_products()
        self.refresh_cart()

    # ---------- UI construction ----------

    def _build_ui(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        header = ttk.Label(self, text="Checkout", style="Heading.TLabel")
        header.grid(row=0, column=0, sticky="w", pady=(0, 12))

        # ----- Left: product search/list -----
        left = ttk.Frame(self, style="Card.TFrame", padding=14)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        search_row = ttk.Frame(left, style="Card.TFrame")
        search_row.grid(row=0, column=0, sticky="ew")
        search_row.columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.grid(row=0, column=0, sticky="ew", ipady=4)
        search_entry.insert(0, "")
        search_entry.focus_set()
        search_entry.bind("<Return>", self._on_search_enter)
        self.search_var.trace_add("write", lambda *a: self.refresh_products())
        self.search_entry = search_entry

        self.category_var = tk.StringVar(value="All Categories")
        self.category_combo = ttk.Combobox(
            search_row, textvariable=self.category_var, state="readonly", width=18
        )
        self.category_combo.grid(row=0, column=1, padx=(8, 0))
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_products())

        hint = ttk.Label(
            left,
            text="Scan a barcode, or type a name/SKU and press Enter to add.",
            style="CardMuted.TLabel",
        )
        hint.grid(row=1, column=0, sticky="w", pady=(6, 6))

        columns = ("name", "sku", "price", "stock")
        self.product_tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="browse")
        self.product_tree.heading("name", text="Product")
        self.product_tree.heading("sku", text="SKU")
        self.product_tree.heading("price", text="Price")
        self.product_tree.heading("stock", text="Stock")
        self.product_tree.column("name", width=220)
        self.product_tree.column("sku", width=100, anchor="center")
        self.product_tree.column("price", width=80, anchor="e")
        self.product_tree.column("stock", width=70, anchor="center")
        self.product_tree.grid(row=2, column=0, sticky="nsew")
        self.product_tree.bind("<Double-1>", self._on_product_double_click)

        add_btn = ttk.Button(left, text="Add to Cart", command=self._add_selected_product)
        add_btn.grid(row=3, column=0, sticky="e", pady=(10, 0))

        # ----- Right: cart & payment -----
        right = ttk.Frame(self, style="Card.TFrame", padding=14)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        ttk.Label(right, text="Cart", style="CardHeading.TLabel").grid(row=0, column=0, sticky="w")

        cart_cols = ("name", "qty", "price", "total")
        self.cart_tree = ttk.Treeview(right, columns=cart_cols, show="headings", selectmode="browse", height=8)
        self.cart_tree.heading("name", text="Item")
        self.cart_tree.heading("qty", text="Qty")
        self.cart_tree.heading("price", text="Price")
        self.cart_tree.heading("total", text="Total")
        self.cart_tree.column("name", width=140)
        self.cart_tree.column("qty", width=50, anchor="center")
        self.cart_tree.column("price", width=70, anchor="e")
        self.cart_tree.column("total", width=70, anchor="e")
        self.cart_tree.grid(row=1, column=0, sticky="nsew", pady=(8, 8))

        cart_btns = ttk.Frame(right, style="Card.TFrame")
        cart_btns.grid(row=2, column=0, sticky="ew")
        ttk.Button(cart_btns, text="+1", style="Secondary.TButton", command=lambda: self._change_qty(1)).pack(side="left")
        ttk.Button(cart_btns, text="-1", style="Secondary.TButton", command=lambda: self._change_qty(-1)).pack(side="left", padx=6)
        ttk.Button(cart_btns, text="Remove", style="Danger.TButton", command=self._remove_selected).pack(side="left")
        ttk.Button(cart_btns, text="Clear", style="Secondary.TButton", command=self._clear_cart).pack(side="right")

        totals = ttk.Frame(right, style="Card.TFrame")
        totals.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        totals.columnconfigure(1, weight=1)

        ttk.Label(totals, text="Discount:", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        self.discount_var = tk.StringVar(value="0")
        discount_entry = ttk.Entry(totals, textvariable=self.discount_var, width=10)
        discount_entry.grid(row=0, column=1, sticky="e")
        self.discount_var.trace_add("write", lambda *a: self.refresh_cart(recompute_only=True))

        self.subtotal_label = ttk.Label(totals, text="Subtotal: $0.00", style="Card.TLabel")
        self.subtotal_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.tax_label = ttk.Label(totals, text="Tax: $0.00", style="Card.TLabel")
        self.tax_label.grid(row=2, column=0, columnspan=2, sticky="w")
        self.total_label = ttk.Label(totals, text="Total: $0.00", style="Total.TLabel")
        self.total_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        payment = ttk.Frame(right, style="Card.TFrame")
        payment.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        payment.columnconfigure(1, weight=1)

        ttk.Label(payment, text="Payment:", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        self.payment_method_var = tk.StringVar(value="Cash")
        payment_combo = ttk.Combobox(
            payment, textvariable=self.payment_method_var, state="readonly",
            values=["Cash", "Card", "Mobile"], width=12,
        )
        payment_combo.grid(row=0, column=1, sticky="e")
        payment_combo.bind("<<ComboboxSelected>>", lambda e: self._update_tendered_state())

        ttk.Label(payment, text="Tendered:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.tendered_var = tk.StringVar(value="")
        self.tendered_entry = ttk.Entry(payment, textvariable=self.tendered_var, width=10)
        self.tendered_entry.grid(row=1, column=1, sticky="e", pady=(6, 0))

        self.change_label = ttk.Label(payment, text="", style="CardMuted.TLabel")
        self.change_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.tendered_var.trace_add("write", lambda *a: self._update_change())

        complete_btn = ttk.Button(
            right, text="Complete Sale", style="Success.TButton", command=self._complete_sale
        )
        complete_btn.grid(row=5, column=0, sticky="ew", pady=(16, 0))

    # ---------- Data refresh ----------

    def on_show(self):
        self.refresh_products()
        self._refresh_categories()

    def _refresh_categories(self):
        cats = dao.list_categories()
        names = ["All Categories"] + [c["name"] for c in cats]
        self.category_combo["values"] = names
        if self.category_var.get() not in names:
            self.category_var.set("All Categories")
        self._category_map = {c["name"]: c["id"] for c in cats}

    def refresh_products(self):
        if not hasattr(self, "_category_map"):
            self._refresh_categories()
        search = self.search_var.get().strip()
        cat_name = self.category_var.get()
        cat_id = self._category_map.get(cat_name) if cat_name != "All Categories" else None

        for row in self.product_tree.get_children():
            self.product_tree.delete(row)

        symbol = dao.get_setting("currency_symbol", "$")
        for p in dao.list_products(search=search or None, category_id=cat_id):
            self.product_tree.insert(
                "", "end", iid=str(p["id"]),
                values=(p["name"], p["sku"] or "", f"{symbol}{p['price']:.2f}", p["stock_qty"]),
            )

    # ---------- Search / scan ----------

    def _on_search_enter(self, event):
        code = self.search_var.get().strip()
        if not code:
            return
        product = dao.find_by_barcode_or_sku(code)
        if product:
            self._add_product_to_cart(product)
            self.search_var.set("")
        else:
            children = self.product_tree.get_children()
            if len(children) == 1:
                self.product_tree.selection_set(children[0])
                self._add_selected_product()

    def _on_product_double_click(self, event):
        self._add_selected_product()

    def _add_selected_product(self):
        selection = self.product_tree.selection()
        if not selection:
            return
        product_id = int(selection[0])
        product = dao.get_product(product_id)
        if product:
            self._add_product_to_cart(product)

    def _add_product_to_cart(self, product):
        if product["stock_qty"] <= 0:
            messagebox.showwarning("Out of stock", f"{product['name']} has no stock available.")
            return
        for item in self.cart:
            if item["product_id"] == product["id"]:
                if item["qty"] + 1 > product["stock_qty"]:
                    messagebox.showwarning("Insufficient stock", f"Only {product['stock_qty']} left.")
                    return
                item["qty"] += 1
                self.refresh_cart()
                return
        self.cart.append({
            "product_id": product["id"],
            "name": product["name"],
            "unit_price": product["price"],
            "qty": 1,
            "stock_qty": product["stock_qty"],
        })
        self.refresh_cart()

    # ---------- Cart manipulation ----------

    def _selected_cart_index(self):
        selection = self.cart_tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _change_qty(self, delta):
        idx = self._selected_cart_index()
        if idx is None or idx >= len(self.cart):
            return
        item = self.cart[idx]
        new_qty = item["qty"] + delta
        if new_qty <= 0:
            self.cart.pop(idx)
        elif new_qty > item["stock_qty"]:
            messagebox.showwarning("Insufficient stock", f"Only {item['stock_qty']} left.")
            return
        else:
            item["qty"] = new_qty
        self.refresh_cart()

    def _remove_selected(self):
        idx = self._selected_cart_index()
        if idx is None or idx >= len(self.cart):
            return
        self.cart.pop(idx)
        self.refresh_cart()

    def _clear_cart(self):
        self.cart = []
        self.discount_var.set("0")
        self.tendered_var.set("")
        self.refresh_cart()

    # ---------- Totals ----------

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
        symbol = dao.get_setting("currency_symbol", "$")
        if not recompute_only:
            for row in self.cart_tree.get_children():
                self.cart_tree.delete(row)
            for idx, item in enumerate(self.cart):
                line_total = item["unit_price"] * item["qty"]
                self.cart_tree.insert(
                    "", "end", iid=str(idx),
                    values=(item["name"], item["qty"], f"{symbol}{item['unit_price']:.2f}", f"{symbol}{line_total:.2f}"),
                )

        subtotal, discount, tax, total = self.compute_totals()
        self.subtotal_label.configure(text=f"Subtotal: {symbol}{subtotal:.2f}")
        self.tax_label.configure(text=f"Tax: {symbol}{tax:.2f}")
        self.total_label.configure(text=f"Total: {symbol}{total:.2f}")
        self._update_change()

    def _update_tendered_state(self):
        if self.payment_method_var.get() != "Cash":
            self.tendered_var.set("")

    def _update_change(self):
        subtotal, discount, tax, total = self.compute_totals()
        tendered = self._safe_float(self.tendered_var.get(), None) if self.tendered_var.get() else None
        if tendered is not None:
            change = round(tendered - total, 2)
            self.change_label.configure(text=f"Change due: {dao.get_setting('currency_symbol', '$')}{change:.2f}")
        else:
            self.change_label.configure(text="")

    # ---------- Complete sale ----------

    def _complete_sale(self):
        if not self.cart:
            messagebox.showinfo("Empty cart", "Add at least one item before completing the sale.")
            return

        subtotal, discount, tax, total = self.compute_totals()
        payment_method = self.payment_method_var.get()
        amount_tendered = None
        if payment_method == "Cash":
            amount_tendered = self._safe_float(self.tendered_var.get(), None) if self.tendered_var.get() else None
            if amount_tendered is None or amount_tendered < total:
                messagebox.showwarning("Insufficient payment", "Enter an amount tendered that covers the total.")
                return

        tax_rate = self._safe_float(dao.get_setting("tax_rate", "0"), 0.0)
        sale = dao.create_sale(self.cart, discount, tax_rate, payment_method, amount_tendered)

        from datetime import datetime
        sale_display = dict(sale)
        sale_display["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        _, items = dao.get_sale(sale["id"])

        show_receipt_window(self, sale_display, items)

        self.cart = []
        self.discount_var.set("0")
        self.tendered_var.set("")
        self.refresh_cart()
        self.refresh_products()
