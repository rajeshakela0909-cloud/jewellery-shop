from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "/tmp/database.db"


# ---------------- DATABASE CONNECTION ----------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT DATABASE ----------------
def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            customer_name TEXT,
            quantity INTEGER,
            total_price REAL,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()


if not os.path.exists(DATABASE):
    init_db()


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["user"] = "admin"
            return redirect(url_for("dashboard"))
        return "Invalid Login"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    return render_template("dashboard.html", products=products)


# ---------------- ADD PRODUCT ----------------
@app.route("/add", methods=["GET", "POST"])
def add_product():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            (name, price, stock)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_product.html")


# ---------------- EDIT PRODUCT ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        conn.execute(
            "UPDATE products SET name=?, price=?, stock=? WHERE id=?",
            (
                request.form["name"],
                float(request.form["price"]),
                int(request.form["stock"]),
                id
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("edit_product.html", product=product)


# ---------------- DELETE PRODUCT ----------------
@app.route("/delete/<int:id>")
def delete_product(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# ---------------- SALE ----------------
@app.route("/sale/<int:id>", methods=["GET", "POST"])
def sale(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        quantity = int(request.form["quantity"])
        customer = request.form["customer"]

        if quantity > product["stock"]:
            conn.close()
            return "Not enough stock"

        total = product["price"] * quantity
        new_stock = product["stock"] - quantity

        conn.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, id))

        conn.execute("""
            INSERT INTO sales (product_id, customer_name, quantity, total_price, date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            id,
            customer,
            quantity,
            total,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        sale_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        return redirect(url_for("bill", sale_id=sale_id))

    conn.close()
    return render_template("sale.html", product=product)


# ---------------- BILL ----------------
@app.route("/bill/<int:sale_id>")
def bill(sale_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    sale = conn.execute("""
        SELECT sales.*, products.name
        FROM sales
        JOIN products ON sales.product_id = products.id
        WHERE sales.id=?
    """, (sale_id,)).fetchone()
    conn.close()

    return render_template("bill.html", sale=sale)


# ---------------- SALES HISTORY ----------------
@app.route("/sales")
def sales_history():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    sales = conn.execute("""
        SELECT sales.*, products.name
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.id DESC
    """).fetchall()
    conn.close()

    return render_template("sales.html", sales=sales)


# ---------------- MONTHLY REPORT ----------------
@app.route("/monthly-report")
def monthly_report():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    current_month = datetime.now().strftime("%Y-%m")

    current_total = conn.execute("""
        SELECT SUM(total_price) as total
        FROM sales
        WHERE strftime('%Y-%m', date) = ?
    """, (current_month,)).fetchone()["total"]

    if current_total is None:
        current_total = 0

    monthly_data = conn.execute("""
        SELECT strftime('%Y-%m', date) as month,
               SUM(total_price) as total
        FROM sales
        GROUP BY month
        ORDER BY month DESC
    """).fetchall()

    conn.close()

    return render_template(
        "monthly_report.html",
        current_total=current_total,
        monthly_data=monthly_data
    )


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
