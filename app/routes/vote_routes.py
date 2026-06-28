from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from app.extensions import mysql
from app.utils.decorators import voter_required
import hashlib
import uuid

vote_bp = Blueprint("vote", __name__, url_prefix="/vote")

@vote_bp.route("/election/<int:election_id>")
@voter_required
def election_details(election_id):
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM voters WHERE user_id=%s", (user_id,))
    voter = cur.fetchone()

    if not voter:
        cur.close()
        flash("Please complete your voter profile first.", "warning")
        return redirect(url_for("voter.profile"))

    if voter["verification_status"] != "approved":
        cur.close()
        flash("Your voter profile must be approved before voting.", "danger")
        return redirect(url_for("voter.dashboard"))

    cur.execute("SELECT * FROM elections WHERE election_id=%s AND status='active'", (election_id,))
    election = cur.fetchone()

    if not election:
        cur.close()
        flash("Election is not active.", "warning")
        return redirect(url_for("voter.dashboard"))

    cur.execute("""
        SELECT c.*
        FROM election_candidates ec
        JOIN candidates c ON ec.candidate_id = c.candidate_id
        WHERE ec.election_id=%s
    """, (election_id,))
    candidates = cur.fetchall()

    cur.execute("""
        SELECT * FROM votes 
        WHERE election_id=%s AND voter_id=%s
    """, (election_id, voter["voter_id"]))
    existing_vote = cur.fetchone()

    cur.close()

    return render_template(
        "voter/vote.html",
        election=election,
        candidates=candidates,
        existing_vote=existing_vote
    )

@vote_bp.route("/cast", methods=["POST"])
@voter_required
def cast_vote():
    user_id = session.get("user_id")
    election_id = request.form.get("election_id")
    candidate_id = request.form.get("candidate_id")

    if not election_id or not candidate_id:
        flash("Invalid vote request.", "danger")
        return redirect(url_for("voter.dashboard"))

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM voters WHERE user_id=%s", (user_id,))
    voter = cur.fetchone()

    if not voter:
        cur.close()
        flash("Please complete your voter profile first.", "warning")
        return redirect(url_for("voter.profile"))

    if voter["verification_status"] != "approved":
        cur.close()
        flash("Only approved voters can cast vote.", "danger")
        return redirect(url_for("voter.dashboard"))

    cur.execute("SELECT * FROM elections WHERE election_id=%s AND status='active'", (election_id,))
    election = cur.fetchone()

    if not election:
        cur.close()
        flash("Election is not active.", "danger")
        return redirect(url_for("voter.dashboard"))

    cur.execute("""
        SELECT * FROM votes 
        WHERE election_id=%s AND voter_id=%s
    """, (election_id, voter["voter_id"]))
    existing_vote = cur.fetchone()

    if existing_vote:
        cur.close()
        flash("You have already voted in this election.", "warning")
        return redirect(url_for("vote.election_details", election_id=election_id))

    raw_hash = f"{election_id}-{voter['voter_id']}-{candidate_id}-{uuid.uuid4()}"
    vote_hash = hashlib.sha256(raw_hash.encode()).hexdigest()

    cur.execute("""
        INSERT INTO votes
        (election_id, voter_id, candidate_id, vote_hash)
        VALUES (%s, %s, %s, %s)
    """, (election_id, voter["voter_id"], candidate_id, vote_hash))

    vote_id = cur.lastrowid
    receipt_code = "VH-RCPT-" + str(uuid.uuid4())[:8].upper()

    cur.execute("""
        INSERT INTO vote_receipts
        (vote_id, receipt_code)
        VALUES (%s, %s)
    """, (vote_id, receipt_code))

    mysql.connection.commit()
    cur.close()

    flash("Vote cast successfully.", "success")
    return redirect(url_for("vote.vote_receipt", vote_id=vote_id))

@vote_bp.route("/receipt/<int:vote_id>")
@voter_required
def vote_receipt(vote_id):
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            v.vote_id, v.voted_at, v.vote_hash,
            vr.receipt_code,
            e.title AS election_title,
            c.full_name AS candidate_name,
            c.party_name
        FROM votes v
        JOIN vote_receipts vr ON v.vote_id = vr.vote_id
        JOIN elections e ON v.election_id = e.election_id
        JOIN candidates c ON v.candidate_id = c.candidate_id
        JOIN voters vt ON v.voter_id = vt.voter_id
        WHERE v.vote_id=%s AND vt.user_id=%s
    """, (vote_id, user_id))

    receipt = cur.fetchone()
    cur.close()

    if not receipt:
        flash("Receipt not found.", "danger")
        return redirect(url_for("voter.dashboard"))

    return render_template("voter/receipt.html", receipt=receipt)
