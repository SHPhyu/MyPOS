import tkinter as tk
from tkinter import ttk, messagebox

from .. import dao


class ProductsView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Panel.TFrame", padding=16)
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Label(self, text="Products", style="Heading.TLabel")
        header.grid(row=0, column=0, sticky="w", pady=(0, 12))

        toolbar = ttk.Frame(self, style="Panel.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", ipady=3)
        self.search_var.trace_add("write", lambda *a: self.refresh())

        self.category_var = tk.StringVar(value="All Categories")
        self.category_combo = ttk.Combobox(toolbar, textvariable=self.category_var, state="readonly", width=18)
        self.category_combo.pack(side="left", padx=(8, 0))
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(toolbar, text="Add Product", command=self._open_add_dialog).pack(side="right")
        ttk.Button(toolbar, text="Categories", style="Secondary.TButton", command=self._open_categories_dialog).pack(side="right", padx=6)

        columns = ("name", "sku", "barcode", "category", "price", "cost", "stock")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        headings = {
            "name": "Name", "sku": "SKU", "barcode": "Barcode", "category": "Category",
            "price": "Price", "cost": "Cost", "stock": "Stock",
        }
        widths = {"name": 220, "sku": 100, "barcode": 100, "category": 120, "price": 80, "cost": 80, "stock": 70}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w" if col == "name" else "center")
        self.tree.grid(row=2, column=0, sticky="nsew")
        self.tree.tag_configure("low_stock", background="#fff2ef")
        self.tree.bind("<Double-1>", lambda e: self._open_edit_dialog())

        actions = ttk.Frame(self, style="Panel.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(actions, text="Edit", style="Secondary.TButton", command=self._open_edit_dialog).pack(side="left")
        ttk.Button(actions, text="Adjust Stock", style="Secondary.TButton", command=self._open_stock_dialog).pack(side="left", padx=6)
        ttk.Button(actions, text="Delete", style="Danger.TButton", command=self._delete_selected).pack(side="left")

    def on_show(self):
        self.refresh()

    def _refresh_categories(self):
        cats = dao.list_categories()
        names = ["All Categories"] + [c["name"] for c in cats]
        self.category_combo["values"] = names
        if self.category_var.get() not in names:
            self.category_var.set("All Categories")
        self._category_map = {c["name"]: c["id"] for c in cats}
        self._category_list = cats

    def refresh(self):
        self._refresh_categories()
        search = self.search_var.get().strip()
        cat_name = self.category_var.get()
        cat_id = self._category_map.get(cat_name) if cat_name != "All Categories" else None

        for row in self.tree.get_children():
            self.tree.delete(row)

        symbol = dao.get_setting("currency_symbol", "$")
        for p in dao.list_products(search=search or None, category_id=cat_id):
            tags = ("low_stock",) if p["stock_qty"] <= p["low_stock_threshold"] else ()
            self.tree.insert(
                "", "end", iid=str(p["id"]), tags=tags,
                values=(
                    p["name"], p["sku"] or "", p["barcode"] or "", p["category_name"] or "",
                    f"{symbol}{p['price']:.2f}", f"{symbol}{p['cost']:.2f}", p["stock_qty"],
                ),
            )

    def _selected_product_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _open_add_dialog(self):
        ProductDialog(self, self.app, on_saved=self.refresh)

    def _open_edit_dialog(self):
        pid = self._selected_product_id()
        if pid is None:
            messagebox.showinfo("No selection", "Select a product to edit.")
            return
        ProductDialog(self, self.app, product_id=pid, on_saved=self.refresh)

    def _open_stock_dialog(self):
        pid = self._selected_product_id()
        if pid is None:
            messagebox.showinfo("No selection", "Select a product to adjust.")
            return
        StockDialog(self, pid, on_saved=self.refresh)

    def _delete_selected(self):
        pid = self._selected_product_id()
        if pid is None:
            messagebox.showinfo("No selection", "Select a product to delete.")
            return
        product = dao.get_product(pid)
        if not messagebox.askyesno("Delete product", f"Remove '{product['name']}' from the catalog?"):
            return
        dao.set_product_active(pid, False)
        self.refresh()

    def _open_categories_dialog(self):
        CategoriesDialog(self, on_saved=self.refresh)


class ProductDialog(tk.Toplevel):
    def __init__(self, parent, app, product_id=None, on_saved=None):
        super().__init__(parent)
        self.app = app
        self.product_id = product_id
        self.on_saved = on_saved
        self.title("Edit Product" if product_id else "Add Product")
        self.geometry("380x460")
        self.configure(bg="#ffffff")
        self.resizable(False, False)

        self.name_var = tk.StringVar()
        self.sku_var = tk.StringVar()
        self.barcode_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.cost_var = tk.StringVar()
        self.stock_var = tk.StringVar(value="0")
        self.threshold_var = tk.StringVar(value="5")

        self._build_form()

        if product_id:
            self._load_product()

        self.transient(parent)
        self.grab_set()

    def _build_form(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        cats = dao.list_categories()
        self._category_map = {c["name"]: c["id"] for c in cats}
        cat_names = list(self._category_map.keys())

        fields = [
            ("Name*", self.name_var, "entry"),
            ("SKU", self.sku_var, "entry"),
            ("Barcode", self.barcode_var, "entry"),
            ("Category", self.category_var, "combo", cat_names),
            ("Price*", self.price_var, "entry"),
            ("Cost", self.cost_var, "entry"),
            ("Low stock threshold", self.threshold_var, "entry"),
        ]

        for row_idx, field in enumerate(fields):
            label_text, var, kind = field[0], field[1], field[2]
            ttk.Label(frame, text=label_text).grid(row=row_idx, column=0, sticky="w", pady=6)
            if kind == "entry":
                ttk.Entry(frame, textvariable=var).grid(row=row_idx, column=1, sticky="ew", pady=6)
            else:
                values = field[3]
                ttk.Combobox(frame, textvariable=var, values=values, state="readonly").grid(
                    row=row_idx, column=1, sticky="ew", pady=6
                )

        if not self.product_id:
            ttk.Label(frame, text="Initial stock").grid(row=len(fields), column=0, sticky="w", pady=6)
            ttk.Entry(frame, textvariable=self.stock_var).grid(row=len(fields), column=1, sticky="ew", pady=6)

        frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self, padding=(16, 0, 16, 16))
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="right")
        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=6)

    def _load_product(self):
        p = dao.get_product(self.product_id)
        if not p:
            return
        self.name_var.set(p["name"])
        self.sku_var.set(p["sku"] or "")
        self.barcode_var.set(p["barcode"] or "")
        self.category_var.set(p["category_name"] or "")
        self.price_var.set(str(p["price"]))
        self.cost_var.set(str(p["cost"]))
        self.threshold_var.set(str(p["low_stock_threshold"]))

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Product name is required.")
            return
        try:
            price = float(self.price_var.get())
        except ValueError:
            messagebox.showwarning("Invalid price", "Enter a valid price.")
            return
        try:
            cost = float(self.cost_var.get()) if self.cost_var.get().strip() else 0.0
        except ValueError:
            messagebox.showwarning("Invalid cost", "Enter a valid cost.")
            return
        try:
            threshold = int(self.threshold_var.get()) if self.threshold_var.get().strip() else 5
        except ValueError:
            threshold = 5

        category_id = self._category_map.get(self.category_var.get())
        sku = self.sku_var.get().strip() or None
        barcode = self.barcode_var.get().strip() or None

        try:
            if self.product_id:
                dao.update_product(self.product_id, sku, barcode, name, category_id, price, cost, threshold)
            else:
                try:
                    stock = int(self.stock_var.get()) if self.stock_var.get().strip() else 0
                except ValueError:
                    stock = 0
                dao.add_product(sku, barcode, name, category_id, price, cost, stock, threshold)
        except Exception as exc:
            messagebox.showerror("Could not save", f"SKU or barcode may already be in use.\n\n{exc}")
            return

        if self.on_saved:
            self.on_saved()
        self.destroy()


class StockDialog(tk.Toplevel):
    def __init__(self, parent, product_id, on_saved=None):
        super().__init__(parent)
        self.product_id = product_id
        self.on_saved = on_saved
        product = dao.get_product(product_id)

        self.title(f"Adjust Stock — {product['name']}")
        self.geometry("320x220")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Current stock: {product['stock_qty']}").pack(anchor="w", pady=(0, 10))

        ttk.Label(frame, text="Adjustment (+/-)").pack(anchor="w")
        self.delta_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.delta_var).pack(fill="x", pady=(0, 10))

        ttk.Label(frame, text="Reason").pack(anchor="w")
        self.reason_var = tk.StringVar(value="Manual adjustment")
        ttk.Entry(frame, textvariable=self.reason_var).pack(fill="x")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(16, 0))
        ttk.Button(btn_frame, text="Apply", command=self._apply).pack(side="right")
        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=6)

        self.transient(parent)
        self.grab_set()

    def _apply(self):
        try:
            delta = int(self.delta_var.get())
        except ValueError:
            messagebox.showwarning("Invalid value", "Enter a whole number for the adjustment.")
            return
        if delta == 0:
            self.destroy()
            return
        dao.adjust_stock(self.product_id, delta, self.reason_var.get().strip())
        if self.on_saved:
            self.on_saved()
        self.destroy()


class CategoriesDialog(tk.Toplevel):
    def __init__(self, parent, on_saved=None):
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("Categories")
        self.geometry("320x400")

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(frame)
        self.listbox.pack(fill="both", expand=True)
        self._reload()

        add_row = ttk.Frame(frame)
        add_row.pack(fill="x", pady=(10, 0))
        self.new_var = tk.StringVar()
        ttk.Entry(add_row, textvariable=self.new_var).pack(side="left", fill="x", expand=True)
        ttk.Button(add_row, text="Add", command=self._add).pack(side="left", padx=(6, 0))

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_row, text="Rename", style="Secondary.TButton", command=self._rename).pack(side="left")
        ttk.Button(btn_row, text="Delete", style="Danger.TButton", command=self._delete).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Close", style="Secondary.TButton", command=self._close).pack(side="right")

        self.transient(parent)
        self.grab_set()

    def _reload(self):
        self.listbox.delete(0, tk.END)
        self.categories = dao.list_categories()
        for c in self.categories:
            self.listbox.insert(tk.END, c["name"])

    def _add(self):
        name = self.new_var.get().strip()
        if not name:
            return
        try:
            dao.add_category(name)
        except Exception:
            messagebox.showwarning("Duplicate", "That category already exists.")
            return
        self.new_var.set("")
        self._reload()

    def _selected_category(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self.categories[sel[0]]

    def _rename(self):
        cat = self._selected_category()
        if not cat:
            return
        new_name = self.new_var.get().strip()
        if not new_name:
            messagebox.showinfo("Enter a name", "Type the new name in the field, then click Rename.")
            return
        dao.rename_category(cat["id"], new_name)
        self.new_var.set("")
        self._reload()

    def _delete(self):
        cat = self._selected_category()
        if not cat:
            return
        if not messagebox.askyesno("Delete category", f"Delete '{cat['name']}'? Products keep their data but lose this category."):
            return
        dao.delete_category(cat["id"])
        self._reload()

    def _close(self):
        if self.on_saved:
            self.on_saved()
        self.destroy()
