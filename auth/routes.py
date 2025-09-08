from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db, bcrypt
from models import User

auth_bp = Blueprint("auth", __name__, template_folder="../templates")

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            flash("Login successful!", "success")
            return redirect(url_for("blog.home"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("auth.login"))
