from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import mysql
from app.utils.security import hash_password, check_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def home():
    return render_template("index.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not full_name or not email or not password or not confirm_password:
            flash("All required fields must be filled.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = hash_password(password)

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.login"))

        cur.execute("""
            INSERT INTO users 
            (full_name, email, phone, password_hash, role, status, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, phone, hashed_password, "voter", "active", 1))

        mysql.connection.commit()
        cur.close()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not check_password(password, user["password_hash"]):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if user["status"] == "blocked":
            flash("Your account is blocked. Contact admin.", "danger")
            return redirect(url_for("auth.login"))

        session["user_id"] = user["user_id"]
        session["full_name"] = user["full_name"]
        session["email"] = user["email"]
        session["role"] = user["role"]

        flash("Login successful.", "success")

        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        else:
            return redirect(url_for("voter.dashboard"))

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))
