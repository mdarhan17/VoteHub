from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import mysql
from app.utils.decorators import admin_required
from werkzeug.utils import secure_filename
import os
import uuid

candidate_bp = Blueprint("candidate", __name__, url_prefix="/admin/candidates")

PHOTO_FOLDER = "app/static/images/candidates"
MANIFESTO_FOLDER = "app/static/uploads/manifestos"

ALLOWED_IMAGE = {"png", "jpg", "jpeg", "webp"}
ALLOWED_PDF = {"pdf"}

def allowed_file(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

def save_file(file, folder, allowed):
    if file and file.filename:
        if allowed_file(file.filename, allowed):
            filename = secure_filename(file.filename)
            unique_name = str(uuid.uuid4())[:8] + "_" + filename
            path = os.path.join(folder, unique_name)
            file.save(path)
            return unique_name
    return None

@candidate_bp.route("/")
@admin_required
def candidates():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM candidates ORDER BY candidate_id DESC")
    candidates = cur.fetchall()
    cur.close()
    return render_template("admin/candidates.html", candidates=candidates)

@candidate_bp.route("/add", methods=["POST"])
@admin_required
def add_candidate():
    full_name = request.form.get("full_name")
    party_name = request.form.get("party_name")
    description = request.form.get("description")

    photo = save_file(request.files.get("photo"), PHOTO_FOLDER, ALLOWED_IMAGE)
    symbol = save_file(request.files.get("symbol"), PHOTO_FOLDER, ALLOWED_IMAGE)
    manifesto_file = save_file(request.files.get("manifesto_file"), MANIFESTO_FOLDER, ALLOWED_PDF)

    if not full_name:
        flash("Candidate name is required.", "danger")
        return redirect(url_for("candidate.candidates"))

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO candidates 
        (full_name, party_name, photo, symbol, manifesto_file, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (full_name, party_name, photo, symbol, manifesto_file, description))
    mysql.connection.commit()
    cur.close()

    flash("Candidate added successfully.", "success")
    return redirect(url_for("candidate.candidates"))

@candidate_bp.route("/edit/<int:candidate_id>", methods=["POST"])
@admin_required
def edit_candidate(candidate_id):
    full_name = request.form.get("full_name")
    party_name = request.form.get("party_name")
    description = request.form.get("description")

    photo = save_file(request.files.get("photo"), PHOTO_FOLDER, ALLOWED_IMAGE)
    symbol = save_file(request.files.get("symbol"), PHOTO_FOLDER, ALLOWED_IMAGE)
    manifesto_file = save_file(request.files.get("manifesto_file"), MANIFESTO_FOLDER, ALLOWED_PDF)

    cur = mysql.connection.cursor()

    if photo:
        cur.execute("UPDATE candidates SET photo=%s WHERE candidate_id=%s", (photo, candidate_id))

    if symbol:
        cur.execute("UPDATE candidates SET symbol=%s WHERE candidate_id=%s", (symbol, candidate_id))

    if manifesto_file:
        cur.execute("UPDATE candidates SET manifesto_file=%s WHERE candidate_id=%s", (manifesto_file, candidate_id))

    cur.execute("""
        UPDATE candidates
        SET full_name=%s, party_name=%s, description=%s
        WHERE candidate_id=%s
    """, (full_name, party_name, description, candidate_id))

    mysql.connection.commit()
    cur.close()

    flash("Candidate updated successfully.", "success")
    return redirect(url_for("candidate.candidates"))

@candidate_bp.route("/delete/<int:candidate_id>")
@admin_required
def delete_candidate(candidate_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM candidates WHERE candidate_id=%s", (candidate_id,))
    mysql.connection.commit()
    cur.close()

    flash("Candidate deleted successfully.", "info")
    return redirect(url_for("candidate.candidates"))
