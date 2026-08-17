import os
import tempfile
import tkinter as tk
from tkinter import ttk

from . import dao

LINE_WIDTH = 40


def _money(value, symbol):
    return f"{symbol}{value:,.2f}"


def build_receipt_text(sale, items):
    settings = dao.get_settings()
    symbol = settings.get("currency_symbol", "$")
    store_name = settings.get("store_name", "My Store")
    footer = settings.get("receipt_footer", "Thank you!")

    lines = []
    lines.append(store_name.center(LINE_WIDTH))
    lines.append("=" * LINE_WIDTH)
    lines.append(f"Receipt: {sale['receipt_no']}")
    lines.append(f"Date:    {sale['created_at'] if 'created_at' in sale.keys() else ''}")
    lines.append("-" * LINE_WIDTH)

    for item in items:
        name = item["product_name"]
        qty = item["qty"]
        unit = item["unit_price"]
        total = item["line_total"]
        header = f"{name}"
        lines.append(header[:LINE_WIDTH])
        detail = f"  {qty} x {_money(unit, symbol)}"
        lines.append(f"{detail:<28}{_money(total, symbol):>12}")

    lines.append("-" * LINE_WIDTH)
    lines.append(f"{'Subtotal':<28}{_money(sale['subtotal'], symbol):>12}")
    if sale["discount"]:
        lines.append(f"{'Discount':<28}{'-' + _money(sale['discount'], symbol):>12}")
    if sale["tax"]:
        lines.append(f"{'Tax':<28}{_money(sale['tax'], symbol):>12}")
    lines.append(f"{'TOTAL':<28}{_money(sale['total'], symbol):>12}")
    lines.append("")
    lines.append(f"Payment: {sale['payment_method']}")
    if sale["amount_tendered"] is not None:
        lines.append(f"{'Tendered':<28}{_money(sale['amount_tendered'], symbol):>12}")
        lines.append(f"{'Change':<28}{_money(sale['change_due'], symbol):>12}")

    lines.append("=" * LINE_WIDTH)
    lines.append(footer.center(LINE_WIDTH))

    return "\n".join(lines)


def show_receipt_window(parent, sale, items):
    text = build_receipt_text(sale, items)

    win = tk.Toplevel(parent)
    win.title(f"Receipt {sale['receipt_no']}")
    win.geometry("420x600")
    win.configure(bg="#ffffff")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    txt = tk.Text(frame, font=("Consolas", 10), wrap="none")
    txt.insert("1.0", text)
    txt.configure(state="disabled")
    txt.pack(fill="both", expand=True)

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", pady=(10, 0))

    def do_print():
        fd, path = tempfile.mkstemp(suffix=".txt", prefix="receipt_")
        with os.fdopen(fd, "w") as f:
            f.write(text)
        try:
            os.startfile(path, "print")
        except Exception:
            os.startfile(path)

    def do_close():
        win.destroy()

    ttk.Button(btn_frame, text="Print", command=do_print).pack(side="left")
    ttk.Button(btn_frame, text="Close", style="Secondary.TButton", command=do_close).pack(
        side="right"
    )

    win.transient(parent)
    win.grab_set()
    return win
