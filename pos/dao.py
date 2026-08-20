from datetime import datetime, timedelta

from .db import get_connection


# ---------- Settings ----------

def get_settings():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def update_settings(values: dict):
    conn = get_connection()
    for key, value in values.items():
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
    conn.commit()


def format_money(value):
    """Format an amount using the store's currency symbol, e.g. '1,500 Ks'."""
    symbol = get_setting("currency_symbol", "Ks")
    return f"{value:,.0f} {symbol}"


# ---------- Categories ----------

def list_categories():
    conn = get_connection()
    return conn.execute("SELECT * FROM categories ORDER BY name").fetchall()


def add_category(name):
    conn = get_connection()
    cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))
    conn.commit()
    return cur.lastrowid


def rename_category(category_id, name):
    conn = get_connection()
    conn.execute("UPDATE categories SET name = ? WHERE id = ?", (name.strip(), category_id))
    conn.commit()


def delete_category(category_id):
    conn = get_connection()
    conn.execute("UPDATE products SET category_id = NULL WHERE category_id = ?", (category_id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()


# ---------- Products ----------

def list_products(search=None, category_id=None, active_only=True):
    conn = get_connection()
    query = """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE 1=1
    """
    params = []
    if active_only:
        query += " AND p.active = 1"
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.barcode LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])
    query += " ORDER BY p.name"
    return conn.execute(query, params).fetchall()


def get_product(product_id):
    conn = get_connection()
    return conn.execute(
        """SELECT p.*, c.name AS category_name FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           WHERE p.id = ?""",
        (product_id,),
    ).fetchone()


def find_by_barcode_or_sku(code):
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM products WHERE (barcode = ? OR sku = ?) AND active = 1",
        (code, code),
    ).fetchone()


def add_product(sku, barcode, name, category_id, price, cost, stock_qty, low_stock_threshold):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO products
           (sku, barcode, name, category_id, price, cost, stock_qty, low_stock_threshold)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            sku or None,
            barcode or None,
            name.strip(),
            category_id,
            price,
            cost,
            stock_qty,
            low_stock_threshold,
        ),
    )
    conn.commit()
    return cur.lastrowid


def update_product(product_id, sku, barcode, name, category_id, price, cost, low_stock_threshold):
    conn = get_connection()
    conn.execute(
        """UPDATE products SET sku = ?, barcode = ?, name = ?, category_id = ?,
           price = ?, cost = ?, low_stock_threshold = ? WHERE id = ?""",
        (sku or None, barcode or None, name.strip(), category_id, price, cost, low_stock_threshold, product_id),
    )
    conn.commit()


def set_product_active(product_id, active):
    conn = get_connection()
    conn.execute("UPDATE products SET active = ? WHERE id = ?", (1 if active else 0, product_id))
    conn.commit()


def adjust_stock(product_id, delta, reason=""):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?", (delta, product_id)
    )
    conn.execute(
        "INSERT INTO stock_adjustments (product_id, delta, reason) VALUES (?, ?, ?)",
        (product_id, delta, reason),
    )
    conn.commit()


def low_stock_products():
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM products WHERE active = 1 AND stock_qty <= low_stock_threshold ORDER BY stock_qty"
    ).fetchall()


# ---------- Customers ----------

def list_customers(search=None, active_only=True):
    conn = get_connection()
    query = "SELECT * FROM customers WHERE 1=1"
    params = []
    if active_only:
        query += " AND active = 1"
    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])
    query += " ORDER BY name"
    return conn.execute(query, params).fetchall()


def get_customer(customer_id):
    conn = get_connection()
    return conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()


def add_customer(name, email, phone, address):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)",
        (name.strip(), (email or "").strip(), (phone or "").strip(), (address or "").strip()),
    )
    conn.commit()
    return cur.lastrowid


def update_customer(customer_id, name, email, phone, address):
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET name = ?, email = ?, phone = ?, address = ? WHERE id = ?",
        (name.strip(), (email or "").strip(), (phone or "").strip(), (address or "").strip(), customer_id),
    )
    conn.commit()


def set_customer_active(customer_id, active):
    conn = get_connection()
    conn.execute("UPDATE customers SET active = ? WHERE id = ?", (1 if active else 0, customer_id))
    conn.commit()


def record_customer_payment(customer_id, amount, note=""):
    """Apply a payment against a customer's outstanding credit balance."""
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET credit_balance = ROUND(credit_balance - ?, 2) WHERE id = ?",
        (amount, customer_id),
    )
    conn.execute(
        "INSERT INTO customer_payments (customer_id, amount, note) VALUES (?, ?, ?)",
        (customer_id, amount, note),
    )
    conn.commit()


# ---------- Sales ----------

def _next_receipt_no():
    seq = int(get_setting("next_receipt_seq", "1"))
    update_settings({"next_receipt_seq": seq + 1})
    return f"INV-{seq:06d}"


def create_sale(cart_items, discount, tax_rate, payment_method, amount_tendered, customer_id=None):
    """cart_items: list of dicts {product_id, name, unit_price, qty}"""
    conn = get_connection()
    subtotal = sum(item["unit_price"] * item["qty"] for item in cart_items)
    taxable = max(subtotal - discount, 0)
    tax = round(taxable * tax_rate / 100, 2)
    total = round(taxable + tax, 2)
    change_due = None
    if amount_tendered is not None:
        change_due = round(amount_tendered - total, 2)

    receipt_no = _next_receipt_no()
    cur = conn.execute(
        """INSERT INTO sales
           (receipt_no, subtotal, discount, tax, total, payment_method, amount_tendered, change_due, customer_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (receipt_no, subtotal, discount, tax, total, payment_method, amount_tendered, change_due, customer_id),
    )
    sale_id = cur.lastrowid

    if customer_id is not None and payment_method == "အကြွေးရောင်း":
        conn.execute(
            "UPDATE customers SET credit_balance = ROUND(credit_balance + ?, 2) WHERE id = ?",
            (total, customer_id),
        )

    for item in cart_items:
        line_total = round(item["unit_price"] * item["qty"], 2)
        conn.execute(
            """INSERT INTO sale_items (sale_id, product_id, product_name, unit_price, qty, line_total)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sale_id, item["product_id"], item["name"], item["unit_price"], item["qty"], line_total),
        )
        if item["product_id"] is not None:
            conn.execute(
                "UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?",
                (item["qty"], item["product_id"]),
            )

    conn.commit()
    return {
        "id": sale_id,
        "receipt_no": receipt_no,
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "total": total,
        "payment_method": payment_method,
        "amount_tendered": amount_tendered,
        "change_due": change_due,
        "customer_id": customer_id,
    }


def list_sales(start_date=None, end_date=None):
    conn = get_connection()
    query = "SELECT * FROM sales WHERE 1=1"
    params = []
    if start_date:
        query += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(created_at) <= date(?)"
        params.append(end_date)
    query += " ORDER BY created_at DESC"
    return conn.execute(query, params).fetchall()


def list_sales_with_item_counts(start_date=None, end_date=None):
    """Same as list_sales, but with an item_count column computed in one
    query instead of a separate get_sale() round-trip per row."""
    conn = get_connection()
    query = """
        SELECT s.*, COALESCE(SUM(si.qty), 0) AS item_count
        FROM sales s
        LEFT JOIN sale_items si ON si.sale_id = s.id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(s.created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(s.created_at) <= date(?)"
        params.append(end_date)
    query += " GROUP BY s.id ORDER BY s.created_at DESC"
    return conn.execute(query, params).fetchall()


def get_sale(sale_id):
    conn = get_connection()
    sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
    items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
    return sale, items


def get_last_sale():
    conn = get_connection()
    sale = conn.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 1").fetchone()
    if not sale:
        return None, []
    items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale["id"],)).fetchall()
    return sale, items


# ---------- Reports ----------

def sales_summary(start_date, end_date):
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS num_sales, COALESCE(SUM(total), 0) AS revenue,
                  COALESCE(SUM(discount), 0) AS discounts, COALESCE(SUM(tax), 0) AS tax
           FROM sales WHERE date(created_at) BETWEEN date(?) AND date(?)""",
        (start_date, end_date),
    ).fetchone()

    profit_row = conn.execute(
        """SELECT COALESCE(SUM(si.line_total - (p.cost * si.qty)), SUM(si.line_total)) AS profit
           FROM sale_items si
           JOIN sales s ON s.id = si.sale_id
           LEFT JOIN products p ON p.id = si.product_id
           WHERE date(s.created_at) BETWEEN date(?) AND date(?)""",
        (start_date, end_date),
    ).fetchone()

    return {
        "num_sales": row["num_sales"],
        "revenue": row["revenue"],
        "discounts": row["discounts"],
        "tax": row["tax"],
        "profit": profit_row["profit"] or 0,
    }


def top_products(start_date, end_date, limit=8):
    conn = get_connection()
    return conn.execute(
        """SELECT si.product_name, SUM(si.qty) AS qty_sold, SUM(si.line_total) AS revenue
           FROM sale_items si
           JOIN sales s ON s.id = si.sale_id
           WHERE date(s.created_at) BETWEEN date(?) AND date(?)
           GROUP BY si.product_name
           ORDER BY qty_sold DESC
           LIMIT ?""",
        (start_date, end_date, limit),
    ).fetchall()


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def days_ago_str(days):
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
