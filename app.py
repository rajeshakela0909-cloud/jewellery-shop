from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "/tmp/jewellery.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["user"] = "admin"
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Login"
    return render_template("login.html")

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
        conn.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                     (name, price, stock))
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_product.html")

# ---------------- SALE ----------------
@app.route("/sale/<int:id>", methods=["GET", "POST"])
def sale(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        customer = request.form["customer"]
        quantity = int(request.form["quantity"])

        if quantity > product["stock"]:
            return "Not enough stock"

        total = product["price"] * quantity
        new_stock = product["stock"] - quantity

        conn.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, id))

        conn.execute("""
            INSERT INTO sales (product_id, customer_name, quantity, total_price, date)
            VALUES (?, ?, ?, ?, ?)
        """, (id, customer, quantity, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("sale.html", product=product)

# ---------------- SALES HISTORY ----------------
@app.route("/sales")
def sales():
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

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete_product(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
