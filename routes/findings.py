from flask import Blueprint, jsonify, request

from extensions import db
from models import AuditLog, Finding, RemediationTask


findings_bp = Blueprint("findings", __name__)


@findings_bp.get("")
def list_findings():
    status = request.args.get("status")
    query = Finding.query
    if status:
        query = query.filter_by(status=status)
    findings = query.order_by(Finding.created_at.desc()).all()
    return jsonify([finding.to_dict() for finding in findings])


@findings_bp.get("/<int:finding_id>")
def get_finding(finding_id):
    finding = Finding.query.get_or_404(finding_id)
    data = finding.to_dict()
    data["tasks"] = [task.to_dict() for task in finding.tasks]
    return jsonify(data)


@findings_bp.patch("/<int:finding_id>/status")
def update_finding_status(finding_id):
    finding = Finding.query.get_or_404(finding_id)
    data = request.get_json() or {}
    if not data.get("status"):
        return jsonify({"error": "status is required"}), 400
    finding.status = data["status"]
    db.session.add(
        AuditLog(
            action="finding_status_updated",
            entity_type="Finding",
            entity_id=finding.id,
            details=f"Finding status changed to {finding.status}",
        )
    )
    db.session.commit()
    return jsonify(finding.to_dict())


@findings_bp.patch("/tasks/<int:task_id>")
def update_task(task_id):
    task = RemediationTask.query.get_or_404(task_id)
    data = request.get_json() or {}
    for field in ["title", "description", "owner", "status", "due_date"]:
        if field in data:
            setattr(task, field, data[field])
    db.session.add(
        AuditLog(
            action="remediation_task_updated",
            entity_type="RemediationTask",
            entity_id=task.id,
            details=f"Task status is {task.status}",
        )
    )
    db.session.commit()
    return jsonify(task.to_dict())
