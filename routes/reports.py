import csv
from io import BytesIO, StringIO

from flask import Blueprint, Response, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from models import Assessment, Finding, RemediationTask


reports_bp = Blueprint("reports", __name__)


@reports_bp.get("/findings.csv")
def findings_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["id", "assessment", "control_code", "title", "severity", "result", "status", "details"]
    )
    for finding in Finding.query.order_by(Finding.created_at.desc()).all():
        writer.writerow(
            [
                finding.id,
                finding.assessment.name,
                finding.control.control_code,
                finding.title,
                finding.severity,
                finding.result,
                finding.status,
                finding.details,
            ]
        )
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=findings.csv"},
    )


@reports_bp.get("/remediation.csv")
def remediation_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "finding_id", "title", "owner", "status", "due_date", "description"])
    for task in RemediationTask.query.order_by(RemediationTask.created_at.desc()).all():
        writer.writerow(
            [
                task.id,
                task.finding_id,
                task.title,
                task.owner,
                task.status,
                task.due_date,
                task.description,
            ]
        )
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=remediation.csv"},
    )


@reports_bp.get("/compliance.pdf")
def compliance_pdf():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Compliance Checker Report")
    y -= 30
    pdf.setFont("Helvetica", 10)

    assessments = Assessment.query.order_by(Assessment.created_at.desc()).all()
    findings = Finding.query.order_by(Finding.created_at.desc()).limit(30).all()
    pdf.drawString(50, y, f"Assessments: {len(assessments)}")
    y -= 15
    pdf.drawString(50, y, f"Open findings: {Finding.query.filter_by(status='Open').count()}")
    y -= 25

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Recent Findings")
    y -= 18
    pdf.setFont("Helvetica", 9)
    for finding in findings:
        line = (
            f"{finding.id}. {finding.control.control_code} | {finding.result} | "
            f"{finding.severity} | {finding.status}"
        )
        pdf.drawString(50, y, line[:110])
        y -= 14
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 9)

    pdf.save()
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="compliance-report.pdf",
    )
