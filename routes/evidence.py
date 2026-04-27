from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from extensions import db
from models import AuditLog, Assessment, EvidenceRecord, EvidenceUpload
from services.parser_service import allowed_file, parse_evidence_file


evidence_bp = Blueprint("evidence", __name__)


@evidence_bp.post("/upload")
def upload_evidence():
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400
    assessment_id = request.form.get("assessment_id")
    if not assessment_id:
        return jsonify({"error": "assessment_id is required"}), 400

    assessment = Assessment.query.get_or_404(int(assessment_id))
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "filename is required"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only CSV and TXT files are allowed"}), 400

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid4().hex}_{original_filename}"
    upload_path = Path(current_app.config["UPLOAD_FOLDER"]) / stored_filename
    file.save(upload_path)

    try:
        parsed_records = parse_evidence_file(upload_path)
    except ValueError as exc:
        upload_path.unlink(missing_ok=True)
        return jsonify({"error": str(exc)}), 400

    upload = EvidenceUpload(
        filename=stored_filename,
        original_filename=original_filename,
        file_type=extension,
        assessment_id=assessment.id,
        uploaded_by_id=request.form.get("uploaded_by_id") or None,
    )
    db.session.add(upload)
    db.session.flush()

    for parsed in parsed_records:
        db.session.add(
            EvidenceRecord(
                upload_id=upload.id,
                assessment_id=assessment.id,
                setting_key=parsed["setting_key"],
                observed_value=parsed["observed_value"],
                source_reference=parsed.get("source_reference"),
            )
        )

    assessment.status = "Evidence Uploaded"
    db.session.add(
        AuditLog(
            action="evidence_uploaded",
            entity_type="EvidenceUpload",
            entity_id=upload.id,
            details=f"Uploaded {original_filename} with {len(parsed_records)} records",
        )
    )
    db.session.commit()
    data = upload.to_dict()
    data["records_created"] = len(parsed_records)
    return jsonify(data), 201


@evidence_bp.get("")
def list_evidence_uploads():
    uploads = EvidenceUpload.query.order_by(EvidenceUpload.uploaded_at.desc()).all()
    return jsonify([upload.to_dict() for upload in uploads])


@evidence_bp.get("/assessment/<int:assessment_id>")
def list_evidence_for_assessment(assessment_id):
    Assessment.query.get_or_404(assessment_id)
    records = EvidenceRecord.query.filter_by(assessment_id=assessment_id).order_by(
        EvidenceRecord.setting_key
    )
    return jsonify([record.to_dict() for record in records])
