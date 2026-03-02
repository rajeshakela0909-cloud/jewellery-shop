from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "secretkey"


# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                  ("admin", "1234", "owner"))

    # Products
    c.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT UNIQUE,
        name TEXT,
        category TEXT,
        purchase_price REAL,
        selling_price REAL,
        stock INTEGER
    )
    """)

    # Sales
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT,
        quantity INTEGER,
        total_amount REAL,
        date TEXT
    )
    """)

    # Expenses
    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        amount REAL,
        date TEXT
    )
    """)

    # Closing
    c.execute("""
    CREATE TABLE IF NOT EXISTS closing(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        total_sale REAL,
        total_profit REAL,
        total_expense REAL,
        net_profit REAL
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["username"] = user[1]
            session["role"] = user[3]
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM products")
    products = c.fetchall()

    today = datetime.now().strftime("%d-%m-%Y")

    c.execute("SELECT SUM(total_amount) FROM sales WHERE date=?", (today,))
    total_sale = c.fetchone()[0] or 0

    c.execute("""
        SELECT SUM((p.selling_price - p.purchase_price) * s.quantity)
        FROM sales s
        JOIN products p ON s.product_code = p.product_code
        WHERE s.date=?
    """, (today,))
    total_profit = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM expenses WHERE date=?", (today,))
    total_expense = c.fetchone()[0] or 0

    net_profit = total_profit - total_expense

    conn.close()

    return render_template("index.html",
                           products=products,
                           total_sale=total_sale,
                           total_profit=total_profit,
                           total_expense=total_expense,
                           net_profit=net_profit,
                           role=session.get("role"),
                           username=session.get("username"))


# ================= PRODUCT SEARCH API =================
@app.route("/get_product/<code>")
def get_product(code):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT name, selling_price, stock FROM products WHERE product_code=?", (code,))
    product = c.fetchone()
    conn.close()

    if product:
        return jsonify({
            "name": product[0],
            "price": product[1],
            "stock": product[2]
        })
    else:
        return jsonify({"error": "Not Found"})


# ================= ADD PRODUCT =================
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            c.execute("""
            INSERT INTO products
            (product_code,name,category,purchase_price,selling_price,stock)
            VALUES (?,?,?,?,?,?)
            """, (
                request.form["code"],
                request.form["name"],
                request.form["category"],
                request.form["purchase"],
                request.form["selling"],
                request.form["stock"]
            ))
            conn.commit()
        except:
            pass

        conn.close()
        return redirect("/dashboard")

    return render_template("add_product.html")


# ================= MAKE SALE =================
@app.route("/make_sale", methods=["GET", "POST"])
def make_sale():
    if request.method == "POST":
        code = request.form["code"]
        qty = int(request.form["qty"])
        today = datetime.now().strftime("%d-%m-%Y")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT selling_price, stock FROM products WHERE product_code=?",
                  (code,))
        product = c.fetchone()

        if product and product[1] >= qty:
            total = product[0] * qty

            c.execute("""
            INSERT INTO sales(product_code,quantity,total_amount,date)
            VALUES (?,?,?,?)
            """, (code, qty, total, today))

            c.execute("UPDATE products SET stock=stock-? WHERE product_code=?",
                      (qty, code))

            conn.commit()

        conn.close()
        return redirect("/dashboard")

    return render_template("make_sale.html")


# ================= ADD EXPENSE =================
@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        today = datetime.now().strftime("%d-%m-%Y")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO expenses(title,amount,date) VALUES (?,?,?)",
                  (request.form["title"], request.form["amount"], today))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("add_expense.html")


# ================= CLOSE TODAY =================
@app.route("/close_today")
def close_today():
    today = datetime.now().strftime("%d-%m-%Y")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT SUM(total_amount) FROM sales WHERE date=?", (today,))
    total_sale = c.fetchone()[0] or 0

    c.execute("""
        SELECT SUM((p.selling_price - p.purchase_price) * s.quantity)
        FROM sales s
        JOIN products p ON s.product_code = p.product_code
        WHERE s.date=?
    """, (today,))
    total_profit = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM expenses WHERE date=?", (today,))
    total_expense = c.fetchone()[0] or 0

    net_profit = total_profit - total_expense

    try:
        c.execute("""
        INSERT INTO closing(date,total_sale,total_profit,total_expense,net_profit)
        VALUES (?,?,?,?,?)
        """, (today, total_sale, total_profit, total_expense, net_profit))
    except:
        c.execute("""
        UPDATE closing
        SET total_sale=?,total_profit=?,total_expense=?,net_profit=?
        WHERE date=?
        """, (total_sale, total_profit, total_expense, net_profit, today))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= MONTHLY REPORT =================
@app.route("/monthly_report")
def monthly_report():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM closing ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return render_template("monthly_report.html", data=data)


# ================= RUN (RENDER READY) =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)