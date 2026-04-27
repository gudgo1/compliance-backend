from datetime import datetime, timezone

from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class SerializerMixin:
    def to_dict(self):
        return {
            column.name: getattr(self, column.name).isoformat()
            if hasattr(getattr(self, column.name), "isoformat")
            else getattr(self, column.name)
            for column in self.__table__.columns
        }


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.String(80), nullable=False, default="analyst")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class ControlCategory(db.Model, SerializerMixin):
    __tablename__ = "control_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    controls = db.relationship("Control", back_populates="category")


class Control(db.Model, SerializerMixin):
    __tablename__ = "controls"

    id = db.Column(db.Integer, primary_key=True)
    control_code = db.Column(db.String(30), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    setting_key = db.Column(db.String(120), nullable=False, index=True)
    operator = db.Column(db.String(30), nullable=False)
    expected_value = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(30), nullable=False, default="medium")
    active = db.Column(db.Boolean, nullable=False, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey("control_categories.id"))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    category = db.relationship("ControlCategory", back_populates="controls")

    def to_dict(self):
        data = super().to_dict()
        data["category"] = self.category.name if self.category else None
        return data


class Assessment(db.Model, SerializerMixin):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(40), nullable=False, default="Draft")
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    evidence_uploads = db.relationship("EvidenceUpload", back_populates="assessment")
    rule_runs = db.relationship("RuleRun", back_populates="assessment")
    findings = db.relationship("Finding", back_populates="assessment")


class EvidenceUpload(db.Model, SerializerMixin):
    __tablename__ = "evidence_uploads"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    assessment = db.relationship("Assessment", back_populates="evidence_uploads")
    records = db.relationship(
        "EvidenceRecord", back_populates="upload", cascade="all, delete-orphan"
    )


class EvidenceRecord(db.Model, SerializerMixin):
    __tablename__ = "evidence_records"

    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey("evidence_uploads.id"), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    setting_key = db.Column(db.String(120), nullable=False, index=True)
    observed_value = db.Column(db.String(255), nullable=False)
    source_reference = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    upload = db.relationship("EvidenceUpload", back_populates="records")


class RuleRun(db.Model, SerializerMixin):
    __tablename__ = "rule_runs"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    control_id = db.Column(db.Integer, db.ForeignKey("controls.id"), nullable=False)
    evidence_record_id = db.Column(db.Integer, db.ForeignKey("evidence_records.id"))
    result = db.Column(db.String(40), nullable=False)
    observed_value = db.Column(db.String(255))
    expected_value = db.Column(db.String(255), nullable=False)
    operator = db.Column(db.String(30), nullable=False)
    message = db.Column(db.Text)
    run_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    assessment = db.relationship("Assessment", back_populates="rule_runs")
    control = db.relationship("Control")
    evidence_record = db.relationship("EvidenceRecord")


class Finding(db.Model, SerializerMixin):
    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    control_id = db.Column(db.Integer, db.ForeignKey("controls.id"), nullable=False)
    rule_run_id = db.Column(db.Integer, db.ForeignKey("rule_runs.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="Open")
    result = db.Column(db.String(40), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    assessment = db.relationship("Assessment", back_populates="findings")
    control = db.relationship("Control")
    rule_run = db.relationship("RuleRun")
    tasks = db.relationship(
        "RemediationTask", back_populates="finding", cascade="all, delete-orphan"
    )

    def to_dict(self):
        data = super().to_dict()
        data["control_code"] = self.control.control_code if self.control else None
        data["assessment_name"] = self.assessment.name if self.assessment else None
        return data


class RemediationTask(db.Model, SerializerMixin):
    __tablename__ = "remediation_tasks"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    owner = db.Column(db.String(120))
    status = db.Column(db.String(40), nullable=False, default="Open")
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    finding = db.relationship("Finding", back_populates="tasks")

    def to_dict(self):
        data = super().to_dict()
        data["finding_title"] = self.finding.title if self.finding else None
        return data


class AuditLog(db.Model, SerializerMixin):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(120), nullable=False)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User")
