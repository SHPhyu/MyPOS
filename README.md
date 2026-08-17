# MyPOS

A simple offline desktop point-of-sale app for a retail store, built with Python (Tkinter + SQLite). No internet connection or extra installs required.

## Running

Double-click `run.bat`, or from a terminal:

```bash
python main.py
```

The database is stored locally in `data/pos.db` and is created automatically on first run, pre-loaded with a small demo catalog you can edit or delete.

## Features

- **Checkout** — search or scan (barcode/SKU) products, build a cart, apply a discount, auto-calculate tax, take cash/card/mobile payment, print or save the receipt.
- **Products** — add/edit/deactivate products, manage categories, track stock, adjust stock with a reason, low-stock highlighting.
- **Sales History** — browse past sales by date range, reprint any receipt.
- **Reports** — revenue, profit, discounts, tax collected, top-selling products, low-stock alerts for Today / 7 days / 30 days.
- **Settings** — store name, currency symbol, tax rate, receipt footer.

## Project layout

```
main.py              entry point
pos/db.py             SQLite schema + connection + demo seed data
pos/dao.py             all database queries (products, sales, reports, settings)
pos/app.py              main window, sidebar navigation
pos/style.py             ttk theme
pos/receipt.py            receipt text + print/save
pos/views/                one file per screen
data/pos.db                the database (created on first run)
```
