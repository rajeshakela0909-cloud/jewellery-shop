from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------- INIT DB + DEFAULT ADMIN ---------------- #

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        new_admin = User(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(new_admin)
        db.session.commit()

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user"] = user.username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Login"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    products = Product.query.all()
    return render_template("dashboard.html", products=products)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])

        new_product = Product(name=name, price=price, stock=stock)
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add_product.html")

@app.route("/delete/<int:id>")
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/make_sale/<int:id>", methods=["POST"])
def make_sale(id):
    product = Product.query.get_or_404(id)
    quantity = int(request.form["quantity"])

    if quantity <= product.stock:
        total = quantity * product.price
        product.stock -= quantity

        new_sale = Sale(
            product_name=product.name,
            quantity=quantity,
            total_price=total
        )

        db.session.add(new_sale)
        db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/sales")
def sales():
    if "user" not in session:
        return redirect(url_for("login"))

    sales = Sale.query.all()
    return render_template("sales.html", sales=sales)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
