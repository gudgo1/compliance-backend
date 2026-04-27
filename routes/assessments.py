from flask import Blueprint, jsonify, request

from extensions import db
from models import Assessment, AuditLog
from services.rules_engine import run_assessment


assessments_bp = Blueprint("assessments", __name__)


@assessments_bp.get("")
def list_assessments():
    assessments = Assessment.query.order_by(Assessment.created_at.desc()).all()
    return jsonify([assessment.to_dict() for assessment in assessments])


@assessments_bp.post("")
def create_assessment():
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    assessment = Assessment(
        name=data["name"],
        description=data.get("description"),
        status=data.get("status", "Draft"),
        created_by_id=data.get("created_by_id"),
    )
    db.session.add(assessment)
    db.session.flush()
    db.session.add(
        AuditLog(
            action="assessment_created",
            entity_type="Assessment",
            entity_id=assessment.id,
            details=f"Created assessment {assessment.name}",
        )
    )
    db.session.commit()
    return jsonify(assessment.to_dict()), 201


@assessments_bp.get("/<int:assessment_id>")
def get_assessment(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    data = assessment.to_dict()
    data["evidence_uploads"] = [upload.to_dict() for upload in assessment.evidence_uploads]
    data["findings"] = [finding.to_dict() for finding in assessment.findings]
    return jsonify(data)


@assessments_bp.post("/<int:assessment_id>/run")
def run_assessment_endpoint(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    result = run_assessment(assessment)
    db.session.commit()
    return jsonify(result)
