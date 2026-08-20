import os
import tempfile

import customtkinter as ctk

from . import dao
from . import theme

LINE_WIDTH = 40


def _money(value):
    return dao.format_money(value)


def build_receipt_text(sale, items):
    settings = dao.get_settings()
    store_name = settings.get("store_name", "သြဇာ")
    footer = settings.get("receipt_footer", "ကျေးဇူးတင်ပါသည်။")

    lines = []
    lines.append(store_name.center(LINE_WIDTH))
    lines.append("=" * LINE_WIDTH)
    lines.append(f"ဘောက်ချာအမှတ်: {sale['receipt_no']}")
    lines.append(f"ရက်စွဲ:       {sale['created_at'] if 'created_at' in sale.keys() else ''}")
    lines.append("-" * LINE_WIDTH)

    for item in items:
        name = item["product_name"]
        qty = item["qty"]
        unit = item["unit_price"]
        total = item["line_total"]
        header = f"{name}"
        lines.append(header[:LINE_WIDTH])
        detail = f"  {qty} x {_money(unit)}"
        lines.append(f"{detail:<24}{_money(total):>16}")

    lines.append("-" * LINE_WIDTH)
    lines.append(f"{'ခွဲစုစုပေါင်း':<24}{_money(sale['subtotal']):>16}")
    if sale["discount"]:
        lines.append(f"{'လျှော့စျေး':<24}{'-' + _money(sale['discount']):>16}")
    if sale["tax"]:
        lines.append(f"{'အခွန်':<24}{_money(sale['tax']):>16}")
    lines.append(f"{'စုစုပေါင်းကျသင့်ငွေ':<24}{_money(sale['total']):>16}")
    lines.append("")
    lines.append(f"ငွေပေးချေမှုပုံစံ: {sale['payment_method']}")
    if sale["amount_tendered"] is not None:
        lines.append(f"{'ပေးချေငွေ':<24}{_money(sale['amount_tendered']):>16}")
        lines.append(f"{'ပြန်အမ်းငွေ':<24}{_money(sale['change_due']):>16}")

    lines.append("=" * LINE_WIDTH)
    lines.append(footer.center(LINE_WIDTH))

    return "\n".join(lines)


def show_receipt_window(parent, sale, items):
    text = build_receipt_text(sale, items)

    win = ctk.CTkToplevel(parent)
    win.title(f"ဘောက်ချာ {sale['receipt_no']}")
    win.geometry("420x600")
    win.configure(fg_color=theme.BG_APP)

    frame = ctk.CTkFrame(win, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=14, pady=14)

    txt = ctk.CTkTextbox(frame, font=theme.mono_font(11), fg_color=theme.BG_CARD, text_color=theme.TEXT_DARK, wrap="none")
    txt.insert("1.0", text)
    txt.configure(state="disabled")
    txt.pack(fill="both", expand=True)

    btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
    btn_frame.pack(fill="x", pady=(10, 0))

    def do_print():
        fd, path = tempfile.mkstemp(suffix=".txt", prefix="receipt_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            os.startfile(path, "print")
        except Exception:
            os.startfile(path)

    def do_close():
        win.destroy()

    ctk.CTkButton(btn_frame, text="ပရင့်ထုတ်ရန်", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                  command=do_print).pack(side="left")
    ctk.CTkButton(btn_frame, text="ပိတ်ရန်", fg_color=theme.ROW_ALT, text_color=theme.TEXT_DARK,
                  hover_color=theme.BORDER, command=do_close).pack(side="right")

    win.transient(parent)
    win.grab_set()
    return win
