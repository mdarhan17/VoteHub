from flask import Blueprint, render_template, redirect, url_for, flash, send_file
from app.extensions import mysql
from app.utils.decorators import admin_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from openpyxl import Workbook
import os

result_bp = Blueprint("result", __name__, url_prefix="/admin/results")

REPORT_FOLDER = "app/static/uploads/reports"

def get_result_data(election_id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM elections WHERE election_id=%s", (election_id,))
    election = cur.fetchone()

    cur.execute("""
        SELECT c.candidate_id, c.full_name, c.party_name, COUNT(v.vote_id) AS total_votes
        FROM election_candidates ec
        JOIN candidates c ON ec.candidate_id = c.candidate_id
        LEFT JOIN votes v ON v.candidate_id = c.candidate_id AND v.election_id = ec.election_id
        WHERE ec.election_id=%s
        GROUP BY c.candidate_id, c.full_name, c.party_name
        ORDER BY total_votes DESC
    """, (election_id,))
    results = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS total FROM votes WHERE election_id=%s", (election_id,))
    total_votes = cur.fetchone()["total"]

    cur.close()
    return election, results, total_votes

@result_bp.route("/")
@admin_required
def results():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM elections ORDER BY election_id DESC")
    elections = cur.fetchall()
    cur.close()
    return render_template("admin/result_dashboard.html", elections=elections)

@result_bp.route("/election/<int:election_id>")
@admin_required
def election_result(election_id):
    election, results, total_votes = get_result_data(election_id)

    return render_template(
        "admin/election_result.html",
        election=election,
        results=results,
        total_votes=total_votes
    )

@result_bp.route("/publish/<int:election_id>")
@admin_required
def publish_result(election_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE elections SET result_published=1 WHERE election_id=%s", (election_id,))
    mysql.connection.commit()
    cur.close()

    flash("Result published successfully.", "success")
    return redirect(url_for("result.results"))

@result_bp.route("/unpublish/<int:election_id>")
@admin_required
def unpublish_result(election_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE elections SET result_published=0 WHERE election_id=%s", (election_id,))
    mysql.connection.commit()
    cur.close()

    flash("Result unpublished successfully.", "warning")
    return redirect(url_for("result.results"))

@result_bp.route("/export/pdf/<int:election_id>")
@admin_required
def export_pdf(election_id):
    election, results, total_votes = get_result_data(election_id)

    if not election:
        flash("Election not found.", "danger")
        return redirect(url_for("result.results"))

    os.makedirs(REPORT_FOLDER, exist_ok=True)
    file_path = os.path.join(REPORT_FOLDER, f"election_result_{election_id}.pdf")

    pdf = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 60

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "VoteHub - Election Result Report")

    y -= 35
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, f"Election: {election['title']}")

    y -= 25
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Status: {election['status']}")

    y -= 20
    pdf.drawString(50, y, f"Total Votes Cast: {total_votes}")

    y -= 35
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Rank")
    pdf.drawString(110, y, "Candidate")
    pdf.drawString(300, y, "Party")
    pdf.drawString(470, y, "Votes")

    y -= 15
    pdf.line(50, y, 540, y)

    y -= 25
    pdf.setFont("Helvetica", 10)

    for index, item in enumerate(results, start=1):
        if y < 80:
            pdf.showPage()
            y = height - 60

        pdf.drawString(50, y, str(index))
        pdf.drawString(110, y, str(item["full_name"]))
        pdf.drawString(300, y, str(item["party_name"] or "N/A"))
        pdf.drawString(470, y, str(item["total_votes"]))
        y -= 22

    if results and total_votes > 0:
        y -= 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, f"Winner: {results[0]['full_name']} with {results[0]['total_votes']} votes")

    pdf.save()

    return send_file(file_path, as_attachment=True)

@result_bp.route("/export/excel/<int:election_id>")
@admin_required
def export_excel(election_id):
    election, results, total_votes = get_result_data(election_id)

    if not election:
        flash("Election not found.", "danger")
        return redirect(url_for("result.results"))

    os.makedirs(REPORT_FOLDER, exist_ok=True)
    file_path = os.path.join(REPORT_FOLDER, f"election_result_{election_id}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Election Result"

    ws.append(["VoteHub - Election Result Report"])
    ws.append([])
    ws.append(["Election", election["title"]])
    ws.append(["Status", election["status"]])
    ws.append(["Total Votes", total_votes])
    ws.append([])
    ws.append(["Rank", "Candidate", "Party", "Total Votes"])

    for index, item in enumerate(results, start=1):
        ws.append([
            index,
            item["full_name"],
            item["party_name"],
            item["total_votes"]
        ])

    if results and total_votes > 0:
        ws.append([])
        ws.append(["Winner", results[0]["full_name"], "Votes", results[0]["total_votes"]])

    wb.save(file_path)

    return send_file(file_path, as_attachment=True)
