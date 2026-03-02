from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)

# ================= LOGIN =================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid Login"

    return render_template("login.html")

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    products = Product.query.all()
    customers = Customer.query.all()
    return render_template("dashboard.html", products=products, customers=customers)

# ================= ADD PRODUCT =================

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        code = request.form["code"]
        name = request.form["name"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])

        product = Product(code=code, name=name, price=price, stock=stock)
        db.session.add(product)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("add_product.html")

# ================= SEARCH PRODUCT BY CODE =================

@app.route("/search", methods=["POST"])
def search():
    code = request.form["code"]
    product = Product.query.filter_by(code=code).first()
    products = [product] if product else []
    customers = Customer.query.all()
    return render_template("dashboard.html", products=products, customers=customers)

# ================= SELL PRODUCT =================

@app.route("/sell/<int:id>", methods=["POST"])
def sell(id):
    product = Product.query.get(id)
    qty = int(request.form["qty"])

    if product and product.stock >= qty:
        product.stock -= qty
        db.session.commit()

    return redirect("/dashboard")

# ================= DELETE PRODUCT =================

@app.route("/delete/<int:id>")
def delete(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return redirect("/dashboard")

# ================= ADD CUSTOMER =================

@app.route("/add_customer", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        mobile = request.form["mobile"]

        customer = Customer(name=name, mobile=mobile)
        db.session.add(customer)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("add_customer.html")

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
