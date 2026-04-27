# University Compliance Checker Backend

Flask + SQLAlchemy + PostgreSQL backend for a university Compliance Checker prototype.

## Features

- Baseline controls API
- Assessment creation and rule execution
- CSV and TXT evidence uploads
- Findings and remediation task generation
- Audit logs
- CSV and PDF reports

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Update `.env` if needed:

```env
DATABASE_URL=postgresql://postgres:roby@localhost:5432/compliance_checker
```

Create the PostgreSQL database:

```sql
CREATE DATABASE compliance_checker;
```

Seed and run:

```powershell
python seed.py
flask --app app run --debug
```

## Useful Endpoints

```text
GET  /api/health
GET  /api/controls
GET  /api/assessments
POST /api/evidence/upload
POST /api/assessments/<id>/run
GET  /api/findings
GET  /api/reports/findings.csv
GET  /api/reports/remediation.csv
GET  /api/reports/compliance.pdf
```
