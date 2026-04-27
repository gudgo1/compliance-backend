from app import create_app
from extensions import db
from models import Assessment, Control, ControlCategory, User


DEMO_CONTROLS = [
    (
        "Identity",
        "ID-001",
        "Minimum password length must be at least 12",
        "password_min_length",
        "gte",
        "12",
    ),
    (
        "Identity",
        "ID-002",
        "Guest account must be disabled",
        "guest_account",
        "equals",
        "disabled",
    ),
    (
        "Network",
        "NW-001",
        "Firewall default inbound action must block traffic",
        "firewall_inbound_default",
        "equals",
        "block",
    ),
    (
        "System",
        "SY-001",
        "SMBv1 must be disabled",
        "smbv1",
        "equals",
        "disabled",
    ),
    (
        "System",
        "SY-002",
        "Telnet service must not be running",
        "telnet_service",
        "equals",
        "disabled",
    ),
]


def seed():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email="analyst@example.edu").first()
        if not user:
            user = User(name="Demo Analyst", email="analyst@example.edu", role="analyst")
            db.session.add(user)

        categories = {}
        for name in {"Identity", "Network", "System"}:
            category = ControlCategory.query.filter_by(name=name).first()
            if not category:
                category = ControlCategory(
                    name=name, description=f"{name} baseline compliance controls"
                )
                db.session.add(category)
            categories[name] = category
        db.session.flush()

        for category_name, code, title, setting_key, operator, expected in DEMO_CONTROLS:
            control = Control.query.filter_by(control_code=code).first()
            if not control:
                control = Control(control_code=code)
                db.session.add(control)
            control.title = title
            control.description = title
            control.setting_key = setting_key
            control.operator = operator
            control.expected_value = expected
            control.severity = "high" if code in {"SY-001", "SY-002"} else "medium"
            control.active = True
            control.category = categories[category_name]

        assessment = Assessment.query.filter_by(name="Demo Baseline Assessment").first()
        if not assessment:
            db.session.add(
                Assessment(
                    name="Demo Baseline Assessment",
                    description="Initial seeded assessment for demonstration evidence uploads.",
                    created_by_id=user.id,
                )
            )

        db.session.commit()
        print("Seed data loaded.")


if __name__ == "__main__":
    seed()
