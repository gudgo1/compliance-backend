from flask import Blueprint, jsonify, request

from extensions import db
from models import AuditLog, Control


controls_bp = Blueprint("controls", __name__)


@controls_bp.get("")
def list_controls():
    controls = Control.query.order_by(Control.control_code).all()
    return jsonify([control.to_dict() for control in controls])


@controls_bp.get("/<int:control_id>")
def get_control(control_id):
    control = Control.query.get_or_404(control_id)
    return jsonify(control.to_dict())


@controls_bp.post("")
def create_control():
    data = request.get_json() or {}
    required = ["control_code", "title", "setting_key", "operator", "expected_value"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": "Missing required fields", "fields": missing}), 400

    control = Control(
        control_code=data["control_code"],
        title=data["title"],
        description=data.get("description"),
        setting_key=data["setting_key"],
        operator=data["operator"],
        expected_value=str(data["expected_value"]),
        severity=data.get("severity", "medium"),
        active=data.get("active", True),
        category_id=data.get("category_id"),
    )
    db.session.add(control)
    db.session.flush()
    db.session.add(
        AuditLog(
            action="control_created",
            entity_type="Control",
            entity_id=control.id,
            details=f"Created control {control.control_code}",
        )
    )
    db.session.commit()
    return jsonify(control.to_dict()), 201


@controls_bp.put("/<int:control_id>")
def update_control(control_id):
    control = Control.query.get_or_404(control_id)
    data = request.get_json() or {}
    for field in [
        "control_code",
        "title",
        "description",
        "setting_key",
        "operator",
        "expected_value",
        "severity",
        "active",
        "category_id",
    ]:
        if field in data:
            setattr(control, field, str(data[field]) if field == "expected_value" else data[field])

    db.session.add(
        AuditLog(
            action="control_updated",
            entity_type="Control",
            entity_id=control.id,
            details=f"Updated control {control.control_code}",
        )
    )
    db.session.commit()
    return jsonify(control.to_dict())
