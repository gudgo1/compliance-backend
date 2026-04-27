from routes.assessments import assessments_bp
from routes.audit import audit_bp
from routes.controls import controls_bp
from routes.evidence import evidence_bp
from routes.findings import findings_bp
from routes.reports import reports_bp


def register_routes(app):
    app.register_blueprint(controls_bp, url_prefix="/api/controls")
    app.register_blueprint(assessments_bp, url_prefix="/api/assessments")
    app.register_blueprint(evidence_bp, url_prefix="/api/evidence")
    app.register_blueprint(findings_bp, url_prefix="/api/findings")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(audit_bp, url_prefix="/api/audit")
