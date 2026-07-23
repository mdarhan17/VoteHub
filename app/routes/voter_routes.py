from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from app.extensions import mysql
from app.utils.decorators import voter_required

voter_bp = Blueprint("voter", __name__, url_prefix="/voter")


@voter_bp.route("/dashboard")
@voter_required
def dashboard():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM voters
        WHERE user_id=%s
    """, (user_id,))
    voter = cur.fetchone()

    cur.execute("""
        SELECT
            e.*,
            COUNT(DISTINCT ec.candidate_id) AS candidate_count
        FROM elections e
        LEFT JOIN election_candidates ec
            ON e.election_id = ec.election_id
        WHERE e.status='active'
        GROUP BY e.election_id
        ORDER BY e.start_datetime DESC
    """)
    active_elections = cur.fetchall()

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM votes v
        INNER JOIN voters vt
            ON v.voter_id = vt.voter_id
        WHERE vt.user_id=%s
    """, (user_id,))
    result = cur.fetchone()
    total_votes = result["total"] if result else 0

    cur.close()

    return render_template(
        "voter/dashboard.html",
        voter=voter,
        active_elections=active_elections,
        total_votes=total_votes
    )


@voter_bp.route("/profile", methods=["GET", "POST"])
@voter_required
def profile():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM users
        WHERE user_id=%s
    """, (user_id,))
    user = cur.fetchone()

    cur.execute("""
        SELECT *
        FROM voters
        WHERE user_id=%s
    """, (user_id,))
    voter = cur.fetchone()

    if request.method == "POST":
        date_of_birth = request.form.get("date_of_birth")
        gender = request.form.get("gender")
        address = request.form.get("address")
        id_type = request.form.get("id_type")
        id_number = request.form.get("id_number")

        if not all([
            date_of_birth,
            gender,
            address,
            id_type,
            id_number
        ]):
            cur.close()
            flash("Please fill all voter profile details.", "danger")
            return redirect(url_for("voter.profile"))

        if voter:
            cur.execute("""
                UPDATE voters
                SET
                    date_of_birth=%s,
                    gender=%s,
                    address=%s,
                    id_type=%s,
                    id_number=%s,
                    verification_status='pending'
                WHERE user_id=%s
            """, (
                date_of_birth,
                gender,
                address,
                id_type,
                id_number,
                user_id
            ))
        else:
            voter_uid = "VH-VOTER-" + str(user_id).zfill(5)

            cur.execute("""
                INSERT INTO voters
                (
                    user_id,
                    voter_uid,
                    date_of_birth,
                    gender,
                    address,
                    id_type,
                    id_number,
                    verification_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
            """, (
                user_id,
                voter_uid,
                date_of_birth,
                gender,
                address,
                id_type,
                id_number
            ))

        mysql.connection.commit()
        cur.close()

        flash(
            "Profile submitted successfully. Waiting for admin approval.",
            "success"
        )
        return redirect(url_for("voter.dashboard"))

    cur.close()

    return render_template(
        "voter/profile.html",
        user=user,
        voter=voter
    )


@voter_bp.route("/history")
@voter_required
def history():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            v.vote_id,
            v.voted_at,
            v.vote_hash,
            vr.receipt_code,
            e.title AS election_title,
            c.full_name AS candidate_name,
            c.party_name,
            c.photo,
            c.symbol
        FROM votes v
        INNER JOIN vote_receipts vr
            ON v.vote_id = vr.vote_id
        INNER JOIN elections e
            ON v.election_id = e.election_id
        INNER JOIN candidates c
            ON v.candidate_id = c.candidate_id
        INNER JOIN voters vt
            ON v.voter_id = vt.voter_id
        WHERE vt.user_id=%s
        ORDER BY v.voted_at DESC
    """, (user_id,))

    history = cur.fetchall()
    cur.close()

    return render_template(
        "voter/history.html",
        history=history
    )
