from extensions import db
from models import AuditLog, Control, EvidenceRecord, Finding, RemediationTask, RuleRun


SUPPORTED_OPERATORS = {
    "equals",
    "not_equals",
    "contains",
    "not_contains",
    "gte",
    "lte",
    "gt",
    "lt",
}


def evaluate_rule(operator, observed_value, expected_value):
    operator = operator.lower()
    if operator not in SUPPORTED_OPERATORS:
        raise ValueError(f"Unsupported operator: {operator}")

    observed = str(observed_value).strip()
    expected = str(expected_value).strip()
    observed_normalized = observed.lower()
    expected_normalized = expected.lower()

    if operator == "equals":
        return observed_normalized == expected_normalized
    if operator == "not_equals":
        return observed_normalized != expected_normalized
    if operator == "contains":
        return expected_normalized in observed_normalized
    if operator == "not_contains":
        return expected_normalized not in observed_normalized

    observed_number = _to_number(observed)
    expected_number = _to_number(expected)
    if operator == "gte":
        return observed_number >= expected_number
    if operator == "lte":
        return observed_number <= expected_number
    if operator == "gt":
        return observed_number > expected_number
    if operator == "lt":
        return observed_number < expected_number
    return False


def run_assessment(assessment):
    controls = Control.query.filter_by(active=True).order_by(Control.control_code).all()
    evidence = EvidenceRecord.query.filter_by(assessment_id=assessment.id).all()
    evidence_by_key = {record.setting_key: record for record in evidence}

    # Prototype behavior: each run replaces existing generated results for the assessment.
    prior_finding_ids = db.session.query(Finding.id).filter_by(assessment_id=assessment.id)
    RemediationTask.query.filter(RemediationTask.finding_id.in_(prior_finding_ids)).delete(
        synchronize_session=False
    )
    Finding.query.filter_by(assessment_id=assessment.id).delete(synchronize_session=False)
    RuleRun.query.filter_by(assessment_id=assessment.id).delete(synchronize_session=False)

    results = []
    for control in controls:
        record = evidence_by_key.get(control.setting_key)
        if not record:
            result = "Unknown"
            message = "No matching evidence was found."
            observed_value = None
        else:
            observed_value = record.observed_value
            try:
                passed = evaluate_rule(
                    control.operator, record.observed_value, control.expected_value
                )
                result = "Compliant" if passed else "Non-compliant"
                message = _result_message(control, record.observed_value, result)
            except ValueError as exc:
                result = "Unknown"
                message = str(exc)

        rule_run = RuleRun(
            assessment_id=assessment.id,
            control_id=control.id,
            evidence_record_id=record.id if record else None,
            result=result,
            observed_value=observed_value,
            expected_value=control.expected_value,
            operator=control.operator,
            message=message,
        )
        db.session.add(rule_run)
        db.session.flush()

        finding = None
        task = None
        if result in {"Non-compliant", "Unknown"}:
            finding = Finding(
                assessment_id=assessment.id,
                control_id=control.id,
                rule_run_id=rule_run.id,
                title=f"{control.control_code}: {control.title}",
                severity=control.severity,
                result=result,
                details=message,
            )
            db.session.add(finding)
            db.session.flush()
            task = RemediationTask(
                finding_id=finding.id,
                title=f"Remediate {control.control_code}",
                description=_task_description(control, result),
            )
            db.session.add(task)

        db.session.add(
            AuditLog(
                action="rule_evaluated",
                entity_type="Assessment",
                entity_id=assessment.id,
                details=f"{control.control_code} evaluated as {result}",
            )
        )
        results.append(
            {
                "control_id": control.id,
                "control_code": control.control_code,
                "setting_key": control.setting_key,
                "result": result,
                "observed_value": observed_value,
                "expected_value": control.expected_value,
                "rule_run_id": rule_run.id,
                "finding_id": finding.id if finding else None,
                "remediation_task_id": task.id if task else None,
                "message": message,
            }
        )

    assessment.status = "Completed"
    db.session.add(
        AuditLog(
            action="assessment_run_completed",
            entity_type="Assessment",
            entity_id=assessment.id,
            details=f"Completed assessment run with {len(results)} control checks",
        )
    )
    return {"assessment_id": assessment.id, "status": assessment.status, "results": results}


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Value is not numeric: {value}") from exc


def _result_message(control, observed_value, result):
    return (
        f"Observed '{observed_value}' for {control.setting_key}; expected "
        f"{control.operator} '{control.expected_value}'. Result: {result}."
    )


def _task_description(control, result):
    if result == "Unknown":
        return f"Provide evidence for {control.setting_key} and re-run the assessment."
    return (
        f"Update {control.setting_key} so it satisfies {control.operator} "
        f"{control.expected_value}, then upload new evidence and re-run."
    )
