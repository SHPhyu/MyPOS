import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from .. import dao
from .. import theme
from ..widgets import DataTable, ScreenHeader


class CustomersView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG_APP, corner_radius=0)
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ScreenHeader(self, self.app, "ဖောက်သည်များ")
        header.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 12))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(toolbar, textvariable=self.search_var, width=260, height=36, placeholder_text="ရှာဖွေရန်...")
        search_entry.pack(side="left")
        self.search_var.trace_add("write", lambda *a: self.refresh())

        ctk.CTkButton(toolbar, text="ဖောက်သည်အသစ်ထည့်ရန်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      height=36, command=self._open_add_dialog).pack(side="right")

        columns = [
            {"key": "name", "heading": "အမည်", "width": 160, "anchor": "w"},
            {"key": "phone", "heading": "ဖုန်းနံပါတ်", "width": 110, "anchor": "center"},
            {"key": "email", "heading": "အီးမေးလ်", "width": 160, "anchor": "w"},
            {"key": "address", "heading": "လိပ်စာ", "width": 180, "anchor": "w"},
            {"key": "credit_balance", "heading": "ကျန်ငွေ", "width": 100, "anchor": "e", "format": dao.format_money},
        ]
        self.table = DataTable(self, columns=columns, on_double_click=lambda row: self._open_edit_dialog())
        self.table.grid(row=2, column=0, sticky="nsew", padx=20)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        ctk.CTkButton(actions, text="ပြင်ဆင်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self._open_edit_dialog).pack(side="left")
        ctk.CTkButton(actions, text="ငွေပေးချေမှု မှတ်တမ်းတင်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self._open_payment_dialog).pack(side="left", padx=6)
        ctk.CTkButton(actions, text="ဖျက်ရန်", fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                      command=self._delete_selected).pack(side="left")

    def on_show(self):
        self.refresh()

    def refresh(self):
        search = self.search_var.get().strip()
        customers = dao.list_customers(search=search or None)
        self.table.set_rows(customers, row_tag=lambda c: "warn" if c["credit_balance"] > 0 else None)

    def _selected_customer_id(self):
        row = self.table.get_selected()
        return row["id"] if row else None

    def _open_add_dialog(self):
        CustomerDialog(self, self.app, on_saved=self.refresh)

    def _open_edit_dialog(self):
        cid = self._selected_customer_id()
        if cid is None:
            messagebox.showinfo("ရွေးချယ်ထားခြင်းမရှိပါ", "ပြင်ဆင်ရန် ဖောက်သည်တစ်ဦးကို ရွေးပါ။")
            return
        CustomerDialog(self, self.app, customer_id=cid, on_saved=self.refresh)

    def _open_payment_dialog(self):
        cid = self._selected_customer_id()
        if cid is None:
            messagebox.showinfo("ရွေးချယ်ထားခြင်းမရှိပါ", "ငွေပေးချေမှု မှတ်တမ်းတင်ရန် ဖောက်သည်တစ်ဦးကို ရွေးပါ။")
            return
        PaymentDialog(self, cid, on_saved=self.refresh)

    def _delete_selected(self):
        cid = self._selected_customer_id()
        if cid is None:
            messagebox.showinfo("ရွေးချယ်ထားခြင်းမရှိပါ", "ဖျက်ရန် ဖောက်သည်တစ်ဦးကို ရွေးပါ။")
            return
        customer = dao.get_customer(cid)
        if customer["credit_balance"] > 0:
            messagebox.showwarning(
                "ကျန်ငွေရှိနေပါသည်",
                f"{customer['name']} တွင် ကျန်ငွေရှိနေပါသေးသည်။ ဖျက်ရန် ကျန်ငွေကို ဦးစွာရှင်းပါ။",
            )
            return
        if not messagebox.askyesno("ဖောက်သည်ဖျက်ရန်", f"'{customer['name']}' ကို ဖယ်ရှားမှာ သေချာပါသလား?"):
            return
        dao.set_customer_active(cid, False)
        self.refresh()


class CustomerDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, customer_id=None, on_saved=None):
        super().__init__(parent)
        self.app = app
        self.customer_id = customer_id
        self.on_saved = on_saved
        self.title("ဖောက်သည်ပြင်ဆင်ရန်" if customer_id else "ဖောက်သည်အသစ်ထည့်ရန်")
        self.geometry("380x360")
        self.configure(fg_color=theme.BG_APP)
        self.resizable(False, False)

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.address_var = tk.StringVar()

        self._build_form()

        if customer_id:
            self._load_customer()

        self.transient(parent)
        self.grab_set()

    def _build_form(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("အမည်*", self.name_var),
            ("ဖုန်းနံပါတ်", self.phone_var),
            ("အီးမေးလ်", self.email_var),
            ("လိပ်စာ", self.address_var),
        ]
        for row_idx, (label_text, var) in enumerate(fields):
            ctk.CTkLabel(frame, text=label_text, text_color=theme.TEXT_DARK).grid(row=row_idx, column=0, sticky="w", pady=8)
            ctk.CTkEntry(frame, textvariable=var, height=34).grid(row=row_idx, column=1, sticky="ew", pady=8, padx=(10, 0))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=18, pady=(0, 18))
        ctk.CTkButton(btn_frame, text="မလုပ်တော့ပါ", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                      hover_color=theme.BORDER, command=self.destroy).pack(side="right")
        ctk.CTkButton(btn_frame, text="သိမ်းမည်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._save).pack(side="right", padx=6)

    def _load_customer(self):
        c = dao.get_customer(self.customer_id)
        if not c:
            return
        self.name_var.set(c["name"])
        self.email_var.set(c["email"] or "")
        self.phone_var.set(c["phone"] or "")
        self.address_var.set(c["address"] or "")

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("အမည်မရှိပါ", "ဖောက်သည်အမည် ထည့်သွင်းရန် လိုအပ်ပါသည်။")
            return

        if self.customer_id:
            dao.update_customer(self.customer_id, name, self.email_var.get(), self.phone_var.get(), self.address_var.get())
        else:
            dao.add_customer(name, self.email_var.get(), self.phone_var.get(), self.address_var.get())

        if self.on_saved:
            self.on_saved()
        self.destroy()


class PaymentDialog(ctk.CTkToplevel):
    def __init__(self, parent, customer_id, on_saved=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.on_saved = on_saved
        customer = dao.get_customer(customer_id)

        self.title(f"ငွေပေးချေမှု မှတ်တမ်းတင်ရန် — {customer['name']}")
        self.geometry("340x260")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_APP)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(frame, text=f"ကျန်ငွေ - {dao.format_money(customer['credit_balance'])}", text_color=theme.TEXT_DARK).pack(
            anchor="w", pady=(0, 10)
        )

        ctk.CTkLabel(frame, text="ပေးချေငွေပမာဏ", text_color=theme.TEXT_DARK).pack(anchor="w")
        self.amount_var = tk.StringVar(value=f"{customer['credit_balance']:.0f}")
        ctk.CTkEntry(frame, textvariable=self.amount_var, height=34).pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="မှတ်ချက်", text_color=theme.TEXT_DARK).pack(anchor="w")
        self.note_var = tk.StringVar(value="အကောင့်ငွေပေးချေမှု")
        ctk.CTkEntry(frame, textvariable=self.note_var, height=34).pack(fill="x", pady=(4, 0))

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
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showwarning("မှားယွင်းနေပါသည်", "မှန်ကန်သော ငွေပမာဏကို ထည့်ပါ။")
            return
        if amount <= 0:
            messagebox.showwarning("မှားယွင်းနေပါသည်", "ငွေပမာဏသည် သုညထက်ကြီးရပါမည်။")
            return
        dao.record_customer_payment(self.customer_id, amount, self.note_var.get().strip())
        if self.on_saved:
            self.on_saved()
        self.destroy()
