from flask import Blueprint, render_template
from app.extensions import mysql

public_result_bp = Blueprint("public_result", __name__, url_prefix="/results")

@public_result_bp.route("/")
def public_results():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM elections
        WHERE result_published=1
        ORDER BY election_id DESC
    """)
    elections = cur.fetchall()
    cur.close()

    return render_template("results/public_results.html", elections=elections)

@public_result_bp.route("/<int:election_id>")
def public_election_result(election_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT * FROM elections
        WHERE election_id=%s AND result_published=1
    """, (election_id,))
    election = cur.fetchone()

    if not election:
        cur.close()
        return render_template("results/result_not_published.html")

    cur.execute("""
        SELECT c.full_name, c.party_name, c.photo, c.symbol, COUNT(v.vote_id) AS total_votes
        FROM election_candidates ec
        JOIN candidates c ON ec.candidate_id = c.candidate_id
        LEFT JOIN votes v ON v.candidate_id = c.candidate_id AND v.election_id = ec.election_id
        WHERE ec.election_id=%s
        GROUP BY c.candidate_id, c.full_name, c.party_name, c.photo, c.symbol
        ORDER BY total_votes DESC
    """, (election_id,))
    results = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS total FROM votes WHERE election_id=%s", (election_id,))
    total_votes = cur.fetchone()["total"]

    cur.close()

    return render_template(
        "results/public_election_result.html",
        election=election,
        results=results,
        total_votes=total_votes
    )
