from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import mysql
from app.utils.decorators import admin_required

election_bp = Blueprint(
    "election",
    __name__,
    url_prefix="/admin/elections"
)


def synchronize_election_statuses():
    """
    Automatically:
    - keeps future elections in draft
    - activates elections during their scheduled period
    - completes elections after their end time
    """
    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE elections
        SET status='completed'
        WHERE status='active'
          AND end_datetime IS NOT NULL
          AND end_datetime <= NOW()
    """)

    cur.execute("""
        UPDATE elections
        SET status='active'
        WHERE status IN ('draft', 'active')
          AND start_datetime IS NOT NULL
          AND end_datetime IS NOT NULL
          AND start_datetime <= NOW()
          AND end_datetime > NOW()
    """)

    mysql.connection.commit()
    cur.close()


@election_bp.route("/")
@admin_required
def elections():
    synchronize_election_statuses()

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            e.*,
            COUNT(DISTINCT ec.candidate_id) AS candidate_count,
            CASE
                WHEN e.end_datetime <= NOW() THEN 'closed'
                WHEN e.start_datetime > NOW() THEN 'upcoming'
                WHEN e.status='active'
                     AND NOW() BETWEEN e.start_datetime AND e.end_datetime
                    THEN 'live'
                ELSE e.status
            END AS timing_status
        FROM elections e
        LEFT JOIN election_candidates ec
            ON e.election_id = ec.election_id
        GROUP BY e.election_id
        ORDER BY e.election_id DESC
    """)
    election_list = cur.fetchall()
    cur.close()

    return render_template(
        "admin/elections.html",
        elections=election_list,
        current_time=datetime.now()
    )


@election_bp.route("/add", methods=["POST"])
@admin_required
def add_election():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    start_datetime = request.form.get("start_datetime")
    end_datetime = request.form.get("end_datetime")

    if not title or not start_datetime or not end_datetime:
        flash(
            "Title, start date and end date are required.",
            "danger"
        )
        return redirect(url_for("election.elections"))

    try:
        start_value = datetime.fromisoformat(start_datetime)
        end_value = datetime.fromisoformat(end_datetime)
    except ValueError:
        flash("Please provide valid election timings.", "danger")
        return redirect(url_for("election.elections"))

    if end_value <= start_value:
        flash(
            "Election end time must be later than the start time.",
            "danger"
        )
        return redirect(url_for("election.elections"))

    initial_status = (
        "active"
        if start_value <= datetime.now() < end_value
        else "draft"
    )

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO elections
        (
            title,
            description,
            start_datetime,
            end_datetime,
            status
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        title,
        description,
        start_value,
        end_value,
        initial_status
    ))

    mysql.connection.commit()
    cur.close()

    flash("Election created successfully.", "success")
    return redirect(url_for("election.elections"))


@election_bp.route(
    "/assign/<int:election_id>",
    methods=["GET", "POST"]
)
@admin_required
def assign_candidates(election_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM elections
        WHERE election_id=%s
    """, (election_id,))
    election = cur.fetchone()

    if not election:
        cur.close()
        flash("Election not found.", "danger")
        return redirect(url_for("election.elections"))

    if request.method == "POST":
        candidate_id = request.form.get(
            "candidate_id",
            type=int
        )

        if not candidate_id:
            cur.close()
            flash("Please select a candidate.", "warning")
            return redirect(
                url_for(
                    "election.assign_candidates",
                    election_id=election_id
                )
            )

        cur.execute("""
            SELECT id
            FROM election_candidates
            WHERE election_id=%s
              AND candidate_id=%s
        """, (
            election_id,
            candidate_id
        ))
        existing = cur.fetchone()

        if existing:
            flash(
                "Candidate is already assigned to this election.",
                "warning"
            )
        else:
            cur.execute("""
                INSERT INTO election_candidates
                (
                    election_id,
                    candidate_id
                )
                VALUES (%s, %s)
            """, (
                election_id,
                candidate_id
            ))

            mysql.connection.commit()
            flash(
                "Candidate assigned successfully.",
                "success"
            )

        cur.close()

        return redirect(
            url_for(
                "election.assign_candidates",
                election_id=election_id
            )
        )

    cur.execute("""
        SELECT *
        FROM candidates
        ORDER BY full_name ASC
    """)
    candidates = cur.fetchall()

    cur.execute("""
        SELECT
            ec.id,
            c.candidate_id,
            c.full_name,
            c.party_name,
            c.photo,
            c.symbol
        FROM election_candidates ec
        INNER JOIN candidates c
            ON ec.candidate_id = c.candidate_id
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


@election_bp.route(
    "/remove-candidate/<int:assign_id>/<int:election_id>"
)
@admin_required
def remove_candidate(assign_id, election_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM votes
        WHERE election_id=%s
    """, (election_id,))
    vote_count = cur.fetchone()["total"]

    if vote_count > 0:
        cur.close()
        flash(
            "Candidate cannot be removed after voting has started.",
            "danger"
        )
        return redirect(
            url_for(
                "election.assign_candidates",
                election_id=election_id
            )
        )

    cur.execute("""
        DELETE FROM election_candidates
        WHERE id=%s
          AND election_id=%s
    """, (
        assign_id,
        election_id
    ))

    mysql.connection.commit()
    cur.close()

    flash("Candidate removed from election.", "info")

    return redirect(
        url_for(
            "election.assign_candidates",
            election_id=election_id
        )
    )


@election_bp.route("/activate/<int:election_id>")
@admin_required
def activate_election(election_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM elections
        WHERE election_id=%s
    """, (election_id,))
    election = cur.fetchone()

    if not election:
        cur.close()
        flash("Election not found.", "danger")
        return redirect(url_for("election.elections"))

    now = datetime.now()

    if election["end_datetime"] <= now:
        cur.execute("""
            UPDATE elections
            SET status='completed'
            WHERE election_id=%s
        """, (election_id,))
        mysql.connection.commit()
        cur.close()

        flash(
            "This election has already ended and cannot be activated.",
            "danger"
        )
        return redirect(url_for("election.elections"))

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM election_candidates
        WHERE election_id=%s
    """, (election_id,))
    candidate_count = cur.fetchone()["total"]

    if candidate_count < 1:
        cur.close()
        flash(
            "Assign at least one candidate before activating.",
            "warning"
        )
        return redirect(url_for("election.elections"))

    cur.execute("""
        UPDATE elections
        SET status='active'
        WHERE election_id=%s
    """, (election_id,))

    mysql.connection.commit()
    cur.close()

    if election["start_datetime"] > now:
        flash(
            "Election activated. Voting will open automatically at the scheduled start time.",
            "success"
        )
    else:
        flash(
            "Election activated successfully. Voting is now open.",
            "success"
        )

    return redirect(url_for("election.elections"))


@election_bp.route("/complete/<int:election_id>")
@admin_required
def complete_election(election_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE elections
        SET status='completed'
        WHERE election_id=%s
    """, (election_id,))

    mysql.connection.commit()
    cur.close()

    flash(
        "Election completed. Voters can no longer cast votes.",
        "info"
    )

    return redirect(url_for("election.elections"))


@election_bp.route("/delete/<int:election_id>")
@admin_required
def delete_election(election_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM votes
        WHERE election_id=%s
    """, (election_id,))
    total_votes = cur.fetchone()["total"]

    if total_votes > 0:
        cur.close()
        flash(
            "Election cannot be deleted because votes have already been recorded.",
            "danger"
        )
        return redirect(url_for("election.elections"))

    cur.execute("""
        DELETE FROM election_candidates
        WHERE election_id=%s
    """, (election_id,))

    cur.execute("""
        DELETE FROM elections
        WHERE election_id=%s
    """, (election_id,))

    mysql.connection.commit()
    cur.close()

    flash("Election deleted successfully.", "warning")
    return redirect(url_for("election.elections"))
