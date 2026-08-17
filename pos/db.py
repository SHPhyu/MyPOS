import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "pos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE,
    barcode TEXT UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    price REAL NOT NULL DEFAULT 0,
    cost REAL NOT NULL DEFAULT 0,
    stock_qty INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER NOT NULL DEFAULT 5,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no TEXT UNIQUE NOT NULL,
    subtotal REAL NOT NULL,
    discount REAL NOT NULL DEFAULT 0,
    tax REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL,
    payment_method TEXT NOT NULL,
    amount_tendered REAL,
    change_due REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL,
    unit_price REAL NOT NULL,
    qty INTEGER NOT NULL,
    line_total REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS stock_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    delta INTEGER NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

DEFAULT_SETTINGS = {
    "store_name": "My Store",
    "currency_symbol": "$",
    "tax_rate": "0",
    "receipt_footer": "Thank you for your purchase!",
    "next_receipt_seq": "1",
}

_connection = None


def get_connection():
    global _connection
    if _connection is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(DB_PATH))
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA foreign_keys = ON")
    return _connection


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
    conn.commit()
    _seed_demo_data(conn)


def _seed_demo_data(conn):
    count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    if count > 0:
        return

    categories = ["Beverages", "Snacks", "Household", "Produce"]
    cat_ids = {}
    for name in categories:
        cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        cat_ids[name] = cur.lastrowid

    demo_products = [
        ("SKU-1001", "0001", "Bottled Water 500ml", "Beverages", 1.25, 0.50, 50),
        ("SKU-1002", "0002", "Cola Can 330ml", "Beverages", 1.75, 0.70, 40),
        ("SKU-1003", "0003", "Potato Chips", "Snacks", 2.50, 1.10, 30),
        ("SKU-1004", "0004", "Chocolate Bar", "Snacks", 1.99, 0.80, 45),
        ("SKU-1005", "0005", "Paper Towels", "Household", 4.99, 2.50, 20),
        ("SKU-1006", "0006", "Dish Soap", "Household", 3.49, 1.60, 15),
        ("SKU-1007", "0007", "Bananas (bunch)", "Produce", 1.50, 0.60, 25),
        ("SKU-1008", "0008", "Apples (bag)", "Produce", 3.99, 1.80, 18),
    ]
    for sku, barcode, name, cat, price, cost, stock in demo_products:
        conn.execute(
            """INSERT INTO products
               (sku, barcode, name, category_id, price, cost, stock_qty, low_stock_threshold)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (sku, barcode, name, cat_ids[cat], price, cost, stock, 5),
        )
    conn.commit()
