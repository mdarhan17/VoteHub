from flask import Blueprint, render_template, redirect, url_for, flash
from app.extensions import mysql
from app.utils.decorators import admin_required

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role='voter'
    """)
    total_voters = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM elections
    """)
    total_elections = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM candidates
    """)
    total_candidates = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM votes
    """)
    total_votes = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(DISTINCT v.voter_id) AS total
        FROM voters v
        INNER JOIN users u
            ON v.user_id = u.user_id
        WHERE v.verification_status='pending'
          AND u.role='voter'
          AND u.status='active'
          AND v.date_of_birth IS NOT NULL
          AND v.gender IS NOT NULL
          AND TRIM(COALESCE(v.address, '')) <> ''
          AND TRIM(COALESCE(v.id_type, '')) <> ''
          AND TRIM(COALESCE(v.id_number, '')) <> ''
    """)
    pending_voters = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM elections
        WHERE status='active'
          AND start_datetime <= NOW()
          AND end_datetime > NOW()
    """)
    live_elections = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM elections
        WHERE result_published=1
    """)
    published_results = cur.fetchone()["total"]

    cur.close()

    stats = {
        "total_voters": total_voters,
        "total_elections": total_elections,
        "total_candidates": total_candidates,
        "total_votes": total_votes,
        "pending_voters": pending_voters,
        "live_elections": live_elections,
        "published_results": published_results
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats
    )


@admin_bp.route("/voters")
@admin_required
def voters():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            u.user_id,
            u.full_name,
            u.email,
            u.phone,
            u.status,
            v.voter_id,
            v.voter_uid,
            v.date_of_birth,
            v.gender,
            v.address,
            v.id_type,
            v.id_number,
            v.verification_status
        FROM users u
        LEFT JOIN voters v
            ON u.user_id = v.user_id
        WHERE u.role='voter'
        ORDER BY u.user_id DESC
    """)

    voter_list = cur.fetchall()
    cur.close()

    return render_template(
        "admin/voters.html",
        voters=voter_list
    )


@admin_bp.route("/voters/approve/<int:voter_id>")
@admin_required
def approve_voter(voter_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE voters
        SET verification_status='approved'
        WHERE voter_id=%s
    """, (voter_id,))

    mysql.connection.commit()
    cur.close()

    flash("Voter approved successfully.", "success")
    return redirect(url_for("admin.voters"))


@admin_bp.route("/voters/reject/<int:voter_id>")
@admin_required
def reject_voter(voter_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE voters
        SET verification_status='rejected'
        WHERE voter_id=%s
    """, (voter_id,))

    mysql.connection.commit()
    cur.close()

    flash("Voter rejected successfully.", "warning")
    return redirect(url_for("admin.voters"))


@admin_bp.route("/voters/block/<int:user_id>")
@admin_required
def block_voter(user_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE users
        SET status='blocked'
        WHERE user_id=%s
          AND role='voter'
    """, (user_id,))

    mysql.connection.commit()
    cur.close()

    flash("Voter account blocked.", "danger")
    return redirect(url_for("admin.voters"))


@admin_bp.route("/voters/activate/<int:user_id>")
@admin_required
def activate_voter(user_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE users
        SET status='active'
        WHERE user_id=%s
          AND role='voter'
    """, (user_id,))

    mysql.connection.commit()
    cur.close()

    flash("Voter account activated.", "success")
    return redirect(url_for("admin.voters"))
