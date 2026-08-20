import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from .. import dao
from .. import theme
from ..widgets import DataTable, ScreenHeader


class ProductsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG_APP, corner_radius=0)
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ScreenHeader(self, self.app, "ကုန်ပစ္စည်းများ")
        header.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 12))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(toolbar, textvariable=self.search_var, width=240, height=36, placeholder_text="ရှာဖွေရန်...")
        search_entry.pack(side="left")
        self.search_var.trace_add("write", lambda *a: self.refresh())

        self.category_var = tk.StringVar(value="အမျိုးအစားအားလုံး")
        self.category_combo = ctk.CTkComboBox(
            toolbar, variable=self.category_var, state="readonly", width=180, height=36,
            command=lambda choice: self.refresh(),
        )
        self.category_combo.pack(side="left", padx=(8, 0))

        ctk.CTkButton(toolbar, text="ပစ္စည်းအသစ်ထည့်ရန်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      height=36, command=self._open_add_dialog).pack(side="right")
        ctk.CTkButton(toolbar, text="အမျိုးအစားများ", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, height=36, command=self._open_categories_dialog).pack(side="right", padx=6)

        columns = [
            {"key": "name", "heading": "အမည်", "width": 200, "anchor": "w"},
            {"key": "sku", "heading": "ကုဒ်", "width": 90, "anchor": "center"},
            {"key": "barcode", "heading": "ဘားကုဒ်", "width": 90, "anchor": "center"},
            {"key": "category_name", "heading": "အမျိုးအစား", "width": 110, "anchor": "center"},
            {"key": "price", "heading": "ဈေးနှုန်း", "width": 90, "anchor": "e", "format": dao.format_money},
            {"key": "cost", "heading": "ကုန်ကျစရိတ်", "width": 90, "anchor": "e", "format": dao.format_money},
            {"key": "stock_qty", "heading": "လက်ကျန်", "width": 70, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=columns, on_double_click=lambda row: self._open_edit_dialog())
        self.table.grid(row=2, column=0, sticky="nsew", padx=20)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        ctk.CTkButton(actions, text="ပြင်ဆင်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self._open_edit_dialog).pack(side="left")
        ctk.CTkButton(actions, text="လက်ကျန်ချိန်ညှိရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self._open_stock_dialog).pack(side="left", padx=6)
        ctk.CTkButton(actions, text="ဖျက်ရန်", fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                      command=self._delete_selected).pack(side="left")

    def on_show(self):
        self.refresh()

    def _refresh_categories(self):
        cats = dao.list_categories()
        names = ["အမျိုးအစားအားလုံး"] + [c["name"] for c in cats]
        self.category_combo.configure(values=names)
        if self.category_var.get() not in names:
            self.category_var.set("အမျိုးအစားအားလုံး")
        self._category_map = {c["name"]: c["id"] for c in cats}

    def refresh(self):
        self._refresh_categories()
        search = self.search_var.get().strip()
        cat_name = self.category_var.get()
        cat_id = self._category_map.get(cat_name) if cat_name != "အမျိုးအစားအားလုံး" else None

        products = dao.list_products(search=search or None, category_id=cat_id)
        self.table.set_rows(products, row_tag=lambda p: "warn" if p["stock_qty"] <= p["low_stock_threshold"] else None)

    def _selected_product_id(self):
        row = self.table.get_selected()
        return row["id"] if row else None

    def _open_add_dialog(self):
        ProductDialog(self, self.app, on_saved=self.refresh)

    def _open_edit_dialog(self):
        pid = self._selected_product_id()
        if pid is None:
            messagebox.showinfo("ရွေးချယ်ထားခြင်းမရှိပါ", "ပြင်ဆင်ရန် ပစ္စည်းတစ်ခုကို ရွေးပါ။")
            return
        ProductDialog(self, self.app, product_id=pid, on_saved=self.refresh)

    def _open_stock_dialog(self):
        pid = self._selected_product_id()
        if pid is None:
            messagebox.showinfo("ရွေးချယ်ထားခြင်းမရှိပါ", "ချိန်ညှိရန် ပစ္စည်းတစ်ခုကို ရွေးပါ။")
            return
        StockDialog(self, pid, on_saved=self.refresh)

    def _delete_selected(self):
        pid = self._selected_product_id()
        if pid is None:
            messagebox.showinfo("ရွေးချယ်ထားခြင်းမရှိပါ", "ဖျက်ရန် ပစ္စည်းတစ်ခုကို ရွေးပါ။")
            return
        product = dao.get_product(pid)
        if not messagebox.askyesno("ပစ္စည်းဖျက်ရန်", f"'{product['name']}' ကို ပစ္စည်းစာရင်းမှ ဖယ်ရှားမှာ သေချာပါသလား?"):
            return
        dao.set_product_active(pid, False)
        self.refresh()

    def _open_categories_dialog(self):
        CategoriesDialog(self, on_saved=self.refresh)


class ProductDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, product_id=None, on_saved=None):
        super().__init__(parent)
        self.app = app
        self.product_id = product_id
        self.on_saved = on_saved
        self.title("ပစ္စည်းပြင်ဆင်ရန်" if product_id else "ပစ္စည်းအသစ်ထည့်ရန်")
        self.geometry("400x520")
        self.configure(fg_color=theme.BG_APP)
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
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        frame.grid_columnconfigure(1, weight=1)

        cats = dao.list_categories()
        self._category_map = {c["name"]: c["id"] for c in cats}
        cat_names = list(self._category_map.keys())

        fields = [
            ("အမည်*", self.name_var, "entry"),
            ("ကုဒ် (SKU)", self.sku_var, "entry"),
            ("ဘားကုဒ်", self.barcode_var, "entry"),
            ("အမျိုးအစား", self.category_var, "combo", cat_names),
            ("ဈေးနှုန်း*", self.price_var, "entry"),
            ("ကုန်ကျစရိတ်", self.cost_var, "entry"),
            ("လက်ကျန်နည်းသတိပေးချက်", self.threshold_var, "entry"),
        ]

        for row_idx, field in enumerate(fields):
            label_text, var, kind = field[0], field[1], field[2]
            ctk.CTkLabel(frame, text=label_text, text_color=theme.TEXT_DARK).grid(row=row_idx, column=0, sticky="w", pady=8)
            if kind == "entry":
                ctk.CTkEntry(frame, textvariable=var, height=34).grid(row=row_idx, column=1, sticky="ew", pady=8, padx=(10, 0))
            else:
                values = field[3]
                ctk.CTkComboBox(frame, variable=var, values=values, state="readonly", height=34).grid(
                    row=row_idx, column=1, sticky="ew", pady=8, padx=(10, 0)
                )

        if not self.product_id:
            ctk.CTkLabel(frame, text="အစပိုင်းလက်ကျန်", text_color=theme.TEXT_DARK).grid(row=len(fields), column=0, sticky="w", pady=8)
            ctk.CTkEntry(frame, textvariable=self.stock_var, height=34).grid(row=len(fields), column=1, sticky="ew", pady=8, padx=(10, 0))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=18, pady=(0, 18))
        ctk.CTkButton(btn_frame, text="မလုပ်တော့ပါ", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self.destroy).pack(side="right")
        ctk.CTkButton(btn_frame, text="သိမ်းမည်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._save).pack(side="right", padx=6)

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
            messagebox.showwarning("အမည်မရှိပါ", "ပစ္စည်းအမည် ထည့်သွင်းရန် လိုအပ်ပါသည်။")
            return
        try:
            price = float(self.price_var.get())
        except ValueError:
            messagebox.showwarning("ဈေးနှုန်းမှားနေပါသည်", "မှန်ကန်သော ဈေးနှုန်းကို ထည့်ပါ။")
            return
        try:
            cost = float(self.cost_var.get()) if self.cost_var.get().strip() else 0.0
        except ValueError:
            messagebox.showwarning("ကုန်ကျစရိတ်မှားနေပါသည်", "မှန်ကန်သော ကုန်ကျစရိတ်ကို ထည့်ပါ။")
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
            messagebox.showerror("သိမ်းဆည်း၍မရပါ", f"ကုဒ် (SKU) သို့မဟုတ် ဘားကုဒ်ကို အခြားပစ္စည်းတွင် အသုံးပြုနေပြီး ဖြစ်နိုင်ပါသည်။\n\n{exc}")
            return

        if self.on_saved:
            self.on_saved()
        self.destroy()


class StockDialog(ctk.CTkToplevel):
    def __init__(self, parent, product_id, on_saved=None):
        super().__init__(parent)
        self.product_id = product_id
        self.on_saved = on_saved
        product = dao.get_product(product_id)

        self.title(f"လက်ကျန်ချိန်ညှိရန် — {product['name']}")
        self.geometry("340x260")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_APP)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(frame, text=f"လက်ရှိလက်ကျန်: {product['stock_qty']}", text_color=theme.TEXT_DARK).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(frame, text="ချိန်ညှိမည့်ပမာဏ (+/-)", text_color=theme.TEXT_DARK).pack(anchor="w")
        self.delta_var = tk.StringVar(value="0")
        ctk.CTkEntry(frame, textvariable=self.delta_var, height=34).pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="အကြောင်းရင်း", text_color=theme.TEXT_DARK).pack(anchor="w")
        self.reason_var = tk.StringVar(value="လက်ဖြင့်ချိန်ညှိခြင်း")
        ctk.CTkEntry(frame, textvariable=self.reason_var, height=34).pack(fill="x", pady=(4, 0))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(18, 0))
        ctk.CTkButton(btn_frame, text="မလုပ်တော့ပါ", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self.destroy).pack(side="right")
        ctk.CTkButton(btn_frame, text="သက်ရောက်စေမည်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._apply).pack(side="right", padx=6)

        self.transient(parent)
        self.grab_set()

    def _apply(self):
        try:
            delta = int(self.delta_var.get())
        except ValueError:
            messagebox.showwarning("မှားယွင်းနေပါသည်", "ချိန်ညှိရန် ကိန်းပြည့်ဂဏန်းကို ထည့်ပါ။")
            return
        if delta == 0:
            self.destroy()
            return
        dao.adjust_stock(self.product_id, delta, self.reason_var.get().strip())
        if self.on_saved:
            self.on_saved()
        self.destroy()


class CategoriesDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_saved=None):
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("အမျိုးအစားများ")
        self.geometry("340x460")
        self.configure(fg_color=theme.BG_APP)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        columns = [{"key": "name", "heading": "အမျိုးအစားအမည်", "width": 260, "anchor": "w"}]
        self.table = DataTable(frame, columns=columns, height=260)
        self.table.pack(fill="both", expand=True)
        self._reload()

        add_row = ctk.CTkFrame(frame, fg_color="transparent")
        add_row.pack(fill="x", pady=(10, 0))
        self.new_var = tk.StringVar()
        ctk.CTkEntry(add_row, textvariable=self.new_var, height=34).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(add_row, text="ထည့်ရန်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, width=70,
                      command=self._add).pack(side="left", padx=(6, 0))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(btn_row, text="အမည်ပြောင်းရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self._rename).pack(side="left")
        ctk.CTkButton(btn_row, text="ဖျက်ရန်", fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                      command=self._delete).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="ပိတ်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self._close).pack(side="right")

        self.transient(parent)
        self.grab_set()

    def _reload(self):
        self.categories = dao.list_categories()
        self.table.set_rows(self.categories)

    def _add(self):
        name = self.new_var.get().strip()
        if not name:
            return
        try:
            dao.add_category(name)
        except Exception:
            messagebox.showwarning("ထပ်နေပါသည်", "ဤအမျိုးအစားသည် ရှိပြီးသားဖြစ်ပါသည်။")
            return
        self.new_var.set("")
        self._reload()

    def _selected_category(self):
        return self.table.get_selected()

    def _rename(self):
        cat = self._selected_category()
        if not cat:
            messagebox.showinfo("ရွေးချယ်ထားခြင်းမရှိပါ", "အမျိုးအစားတစ်ခုကို ရွေးပါ။")
            return
        new_name = self.new_var.get().strip()
        if not new_name:
            messagebox.showinfo("အမည်ရိုက်ထည့်ပါ", "အမည်အသစ်ကို အကွက်ထဲရိုက်ထည့်ပြီး 'အမည်ပြောင်းရန်' ကို နှိပ်ပါ။")
            return
        dao.rename_category(cat["id"], new_name)
        self.new_var.set("")
        self._reload()

    def _delete(self):
        cat = self._selected_category()
        if not cat:
            messagebox.showinfo("ရွေးချယ်ထားခြင်းမရှိပါ", "အမျိုးအစားတစ်ခုကို ရွေးပါ။")
            return
        if not messagebox.askyesno("အမျိုးအစားဖျက်ရန်", f"'{cat['name']}' ကို ဖျက်မှာ သေချာပါသလား? ပစ္စည်းများ၏ အချက်အလက်များ ဆက်ရှိနေပါမည်၊ ဤအမျိုးအစားကိုသာ ပြန်ဖြုတ်ပါမည်။"):
            return
        dao.delete_category(cat["id"])
        self._reload()

    def _close(self):
        if self.on_saved:
            self.on_saved()
        self.destroy()
