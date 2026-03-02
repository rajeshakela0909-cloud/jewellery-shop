from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

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

# ---------------- CREATE DB + DEFAULT ADMIN ---------------- #

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
        print("Default admin created!")

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
    return "Login Successful! Dashboard Working"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
