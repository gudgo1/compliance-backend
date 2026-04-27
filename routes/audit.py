from flask import Blueprint, jsonify

from models import AuditLog


audit_bp = Blueprint("audit", __name__)


@audit_bp.get("")
def list_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(250).all()
    return jsonify([log.to_dict() for log in logs])
