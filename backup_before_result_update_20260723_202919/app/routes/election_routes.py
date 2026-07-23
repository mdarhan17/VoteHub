from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import mysql
from app.utils.decorators import admin_required

election_bp = Blueprint("election", __name__, url_prefix="/admin/elections")

@election_bp.route("/")
@admin_required
def elections():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM elections ORDER BY election_id DESC")
    elections = cur.fetchall()
    cur.close()
    return render_template("admin/elections.html", elections=elections)

@election_bp.route("/add", methods=["POST"])
@admin_required
def add_election():
    title = request.form.get("title")
    description = request.form.get("description")
    start_datetime = request.form.get("start_datetime")
    end_datetime = request.form.get("end_datetime")

    if not title or not start_datetime or not end_datetime:
        flash("Title, start date, and end date are required.", "danger")
        return redirect(url_for("election.elections"))

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO elections 
        (title, description, start_datetime, end_datetime, status)
        VALUES (%s, %s, %s, %s, 'draft')
    """, (title, description, start_datetime, end_datetime))
    mysql.connection.commit()
    cur.close()

    flash("Election created successfully.", "success")
    return redirect(url_for("election.elections"))

@election_bp.route("/assign/<int:election_id>", methods=["GET", "POST"])
@admin_required
def assign_candidates(election_id):
    cur = mysql.connection.cursor()

    if request.method == "POST":
        candidate_id = request.form.get("candidate_id")

        cur.execute("""
            SELECT * FROM election_candidates
            WHERE election_id=%s AND candidate_id=%s
        """, (election_id, candidate_id))
        existing = cur.fetchone()

        if existing:
            flash("Candidate already assigned to this election.", "warning")
        else:
            cur.execute("""
                INSERT INTO election_candidates (election_id, candidate_id)
                VALUES (%s, %s)
            """, (election_id, candidate_id))
            mysql.connection.commit()
            flash("Candidate assigned successfully.", "success")

        return redirect(url_for("election.assign_candidates", election_id=election_id))

    cur.execute("SELECT * FROM elections WHERE election_id=%s", (election_id,))
    election = cur.fetchone()

    cur.execute("SELECT * FROM candidates ORDER BY full_name ASC")
    candidates = cur.fetchall()

    cur.execute("""
        SELECT ec.id, c.candidate_id, c.full_name, c.party_name, c.symbol
        FROM election_candidates ec
        JOIN candidates c ON ec.candidate_id = c.candidate_id
        WHERE ec.election_id=%s
        ORDER BY c.full_name ASC
    """, (election_id,))
    assigned_candidates = cur.fetchall()

    cur.close()

    return render_template(
        "admin/assign_candidates.html",
        election=election,
        candidates=candidates,
        assigned_candidates=assigned_candidates
    )

@election_bp.route("/remove-candidate/<int:assign_id>/<int:election_id>")
@admin_required
def remove_candidate(assign_id, election_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM election_candidates WHERE id=%s", (assign_id,))
    mysql.connection.commit()
    cur.close()

    flash("Candidate removed from election.", "info")
    return redirect(url_for("election.assign_candidates", election_id=election_id))

@election_bp.route("/activate/<int:election_id>")
@admin_required
def activate_election(election_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE elections SET status='active' WHERE election_id=%s", (election_id,))
    mysql.connection.commit()
    cur.close()

    flash("Election activated successfully.", "success")
    return redirect(url_for("election.elections"))

@election_bp.route("/complete/<int:election_id>")
@admin_required
def complete_election(election_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE elections SET status='completed' WHERE election_id=%s", (election_id,))
    mysql.connection.commit()
    cur.close()

    flash("Election completed successfully.", "info")
    return redirect(url_for("election.elections"))

@election_bp.route("/delete/<int:election_id>")
@admin_required
def delete_election(election_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM elections WHERE election_id=%s", (election_id,))
    mysql.connection.commit()
    cur.close()

    flash("Election deleted successfully.", "warning")
    return redirect(url_for("election.elections"))
