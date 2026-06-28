from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import mysql
from app.utils.security import hash_password, check_password
from app.services.otp_service import save_otp, verify_otp_code
from app.services.email_service import send_otp_email

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

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        hashed_password = hash_password(password)

        cur.execute("""
            INSERT INTO users 
            (full_name, email, phone, password_hash, role, status, email_verified)
            VALUES (%s, %s, %s, %s, 'voter', 'pending', 0)
        """, (full_name, email, phone, hashed_password))

        mysql.connection.commit()
        cur.close()

        otp = save_otp(email, "register")
        sent, msg = send_otp_email(email, otp)

        session["pending_email"] = email

        if sent:
            flash("Registration successful. OTP sent to your email.", "success")
        else:
            flash(f"Email sending failed. Demo OTP: {otp}. Error: {msg}", "warning")

        return redirect(url_for("auth.verify_otp"))

    return render_template("auth/register.html")

@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    email = session.get("pending_email")

    if not email:
        flash("No email found for OTP verification.", "warning")
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        otp_code = request.form.get("otp_code")

        is_valid, message = verify_otp_code(email, otp_code, "register")

        if not is_valid:
            flash(message, "danger")
            return redirect(url_for("auth.verify_otp"))

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE users
            SET email_verified=1, status='active'
            WHERE email=%s
        """, (email,))
        mysql.connection.commit()
        cur.close()

        session.pop("pending_email", None)

        flash("Email verified successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/verify_otp.html", email=email)

@auth_bp.route("/resend-otp")
def resend_otp():
    email = session.get("pending_email")

    if not email:
        flash("No email found for OTP resend.", "warning")
        return redirect(url_for("auth.register"))

    otp = save_otp(email, "register")
    sent, msg = send_otp_email(email, otp)

    if sent:
        flash("New OTP sent to your email.", "info")
    else:
        flash(f"Email sending failed. Demo OTP: {otp}. Error: {msg}", "warning")

    return redirect(url_for("auth.verify_otp"))

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

        if user["email_verified"] == 0:
            session["pending_email"] = user["email"]
            otp = save_otp(user["email"], "register")
            sent, msg = send_otp_email(user["email"], otp)

            if sent:
                flash("Please verify your email first. OTP sent to your email.", "warning")
            else:
                flash(f"Please verify your email first. Demo OTP: {otp}. Error: {msg}", "warning")

            return redirect(url_for("auth.verify_otp"))

        if user["status"] == "blocked":
            flash("Your account is blocked. Contact admin.", "danger")
            return redirect(url_for("auth.login"))

        if user["status"] == "pending":
            flash("Your account is pending verification.", "warning")
            return redirect(url_for("auth.login"))

        session["user_id"] = user["user_id"]
        session["full_name"] = user["full_name"]
        session["email"] = user["email"]
        session["role"] = user["role"]

        flash("Login successful.", "success")

        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("voter.dashboard"))

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))
