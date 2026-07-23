from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from app.extensions import mysql
from app.utils.decorators import voter_required
from datetime import datetime
import hashlib
import uuid

vote_bp = Blueprint("vote", __name__, url_prefix="/vote")


@vote_bp.route("/election/<int:election_id>")
@voter_required
def election_details(election_id):
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM voters
        WHERE user_id=%s
    """, (user_id,))
    voter = cur.fetchone()

    if not voter:
        cur.close()
        flash("Please complete your voter profile first.", "warning")
        return redirect(url_for("voter.profile"))

    if voter["verification_status"] != "approved":
        cur.close()
        flash(
            "Your voter profile must be approved before voting.",
            "danger"
        )
        return redirect(url_for("voter.dashboard"))

    cur.execute("""
        SELECT *
        FROM elections
        WHERE election_id=%s
        AND status='active'
    """, (election_id,))
    election = cur.fetchone()

    if not election:
        cur.close()
        flash("Election is not active or does not exist.", "warning")
        return redirect(url_for("voter.dashboard"))

    now = datetime.now()

    if election.get("start_datetime") and now < election["start_datetime"]:
        cur.close()
        flash("Voting for this election has not started yet.", "warning")
        return redirect(url_for("voter.dashboard"))

    if election.get("end_datetime") and now > election["end_datetime"]:
        cur.close()
        flash("Voting for this election has ended.", "warning")
        return redirect(url_for("voter.dashboard"))

    cur.execute("""
        SELECT
            c.candidate_id,
            c.full_name,
            c.party_name,
            c.photo,
            c.symbol,
            c.manifesto_file,
            c.description
        FROM election_candidates ec
        INNER JOIN candidates c
            ON ec.candidate_id = c.candidate_id
        WHERE ec.election_id=%s
        ORDER BY c.full_name ASC
    """, (election_id,))
    candidates = cur.fetchall()

    cur.execute("""
        SELECT *
        FROM votes
        WHERE election_id=%s
        AND voter_id=%s
    """, (
        election_id,
        voter["voter_id"]
    ))
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
    election_id = request.form.get("election_id", type=int)
    candidate_id = request.form.get("candidate_id", type=int)

    if not election_id or not candidate_id:
        flash("Invalid vote request.", "danger")
        return redirect(url_for("voter.dashboard"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM voters
        WHERE user_id=%s
    """, (user_id,))
    voter = cur.fetchone()

    if not voter:
        cur.close()
        flash("Please complete your voter profile first.", "warning")
        return redirect(url_for("voter.profile"))

    if voter["verification_status"] != "approved":
        cur.close()
        flash("Only approved voters can cast a vote.", "danger")
        return redirect(url_for("voter.dashboard"))

    cur.execute("""
        SELECT *
        FROM elections
        WHERE election_id=%s
        AND status='active'
    """, (election_id,))
    election = cur.fetchone()

    if not election:
        cur.close()
        flash("Election is not active.", "danger")
        return redirect(url_for("voter.dashboard"))

    now = datetime.now()

    if election.get("start_datetime") and now < election["start_datetime"]:
        cur.close()
        flash("Voting has not started yet.", "warning")
        return redirect(url_for("voter.dashboard"))

    if election.get("end_datetime") and now > election["end_datetime"]:
        cur.close()
        flash("Voting for this election has ended.", "warning")
        return redirect(url_for("voter.dashboard"))

    cur.execute("""
        SELECT ec.id
        FROM election_candidates ec
        WHERE ec.election_id=%s
        AND ec.candidate_id=%s
    """, (
        election_id,
        candidate_id
    ))
    assigned_candidate = cur.fetchone()

    if not assigned_candidate:
        cur.close()
        flash(
            "The selected candidate does not belong to this election.",
            "danger"
        )
        return redirect(
            url_for(
                "vote.election_details",
                election_id=election_id
            )
        )

    cur.execute("""
        SELECT vote_id
        FROM votes
        WHERE election_id=%s
        AND voter_id=%s
    """, (
        election_id,
        voter["voter_id"]
    ))
    existing_vote = cur.fetchone()

    if existing_vote:
        cur.close()
        flash(
            "You have already voted in this election.",
            "warning"
        )
        return redirect(
            url_for(
                "vote.election_details",
                election_id=election_id
            )
        )

    raw_hash = (
        f"{election_id}-"
        f"{voter['voter_id']}-"
        f"{candidate_id}-"
        f"{uuid.uuid4()}"
    )

    vote_hash = hashlib.sha256(
        raw_hash.encode("utf-8")
    ).hexdigest()

    try:
        cur.execute("""
            INSERT INTO votes
            (
                election_id,
                voter_id,
                candidate_id,
                vote_hash
            )
            VALUES (%s, %s, %s, %s)
        """, (
            election_id,
            voter["voter_id"],
            candidate_id,
            vote_hash
        ))

        vote_id = cur.lastrowid
        receipt_code = "VH-RCPT-" + uuid.uuid4().hex[:10].upper()

        cur.execute("""
            INSERT INTO vote_receipts
            (
                vote_id,
                receipt_code
            )
            VALUES (%s, %s)
        """, (
            vote_id,
            receipt_code
        ))

        mysql.connection.commit()

    except Exception:
        mysql.connection.rollback()
        cur.close()

        flash(
            "Unable to record your vote. Please try again.",
            "danger"
        )
        return redirect(
            url_for(
                "vote.election_details",
                election_id=election_id
            )
        )

    cur.close()

    flash("Your vote was cast successfully.", "success")

    return redirect(
        url_for(
            "vote.vote_receipt",
            vote_id=vote_id
        )
    )


@vote_bp.route("/receipt/<int:vote_id>")
@voter_required
def vote_receipt(vote_id):
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
        WHERE v.vote_id=%s
        AND vt.user_id=%s
    """, (
        vote_id,
        user_id
    ))

    receipt = cur.fetchone()
    cur.close()

    if not receipt:
        flash("Vote receipt not found.", "danger")
        return redirect(url_for("voter.dashboard"))

    return render_template(
        "voter/receipt.html",
        receipt=receipt
    )
