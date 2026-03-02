from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

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
    conn.commit()
    conn.close()

init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["user"] = "admin"
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Login"
    return render_template("login.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    return render_template("dashboard.html", products=products)

# ================= ADD =================
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
            (name, price, stock),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_product.html")

# ================= EDIT =================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])

        conn.execute(
            "UPDATE products SET name=?, price=?, stock=? WHERE id=?",
            (name, price, stock, id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    product = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("edit_product.html", product=product)

# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete_product(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
