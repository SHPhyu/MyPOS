import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "pos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    credit_balance REAL NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS customer_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
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
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
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
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
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
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

DEFAULT_SETTINGS = {
    "store_name": "သြဇာ",
    "currency_symbol": "Ks",
    "tax_rate": "0",
    "receipt_footer": "ဝယ်ယူအားပေးမှုအတွက် ကျေးဇူးတင်ပါသည်။",
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
    _migrate_schema(conn)
    _seed_demo_data(conn)


def _migrate_schema(conn):
    """Add columns to tables that already existed before this field was introduced."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(sales)")}
    if "customer_id" not in columns:
        conn.execute(
            "ALTER TABLE sales ADD COLUMN customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL"
        )
        conn.commit()


def _seed_demo_data(conn):
    count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    if count > 0:
        return

    categories = ["အချိုရည်", "မုန့်ခြောက်", "အိမ်သုံးပစ္စည်း", "စျေးသီးနှံ"]
    cat_ids = {}
    for name in categories:
        cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        cat_ids[name] = cur.lastrowid

    demo_products = [
        ("SKU-1001", "0001", "ရေသန့်ဗူး 500ml", "အချိုရည်", 500, 300, 50),
        ("SKU-1002", "0002", "ကိုကာကိုလာ 330ml", "အချိုရည်", 900, 650, 40),
        ("SKU-1003", "0003", "အာလူးချစ်", "မုန့်ခြောက်", 1500, 1000, 30),
        ("SKU-1004", "0004", "ချောကလက်ဘား", "မုန့်ခြောက်", 1200, 800, 45),
        ("SKU-1005", "0005", "တစ်ရှူးစက္ကူလိပ်", "အိမ်သုံးပစ္စည်း", 2800, 2000, 20),
        ("SKU-1006", "0006", "ပန်းကန်ဆေးရည်", "အိမ်သုံးပစ္စည်း", 2200, 1500, 15),
        ("SKU-1007", "0007", "ငှက်ပျောသီး (တစ်ခိုင်)", "စျေးသီးနှံ", 1500, 900, 25),
        ("SKU-1008", "0008", "ပန်းသီး (တစ်ထုပ်)", "စျေးသီးနှံ", 3500, 2200, 18),
    ]
    for sku, barcode, name, cat, price, cost, stock in demo_products:
        conn.execute(
            """INSERT INTO products
               (sku, barcode, name, category_id, price, cost, stock_qty, low_stock_threshold)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (sku, barcode, name, cat_ids[cat], price, cost, stock, 5),
        )
    conn.commit()
