from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        if session.get("role") != "admin":
            flash("Access denied. Admin only.", "danger")
            return redirect(url_for("voter.dashboard"))

        return f(*args, **kwargs)
    return decorated_function

def voter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        if session.get("role") != "voter":
            flash("Access denied. Voter only.", "danger")
            return redirect(url_for("admin.dashboard"))

        return f(*args, **kwargs)
    return decorated_function
