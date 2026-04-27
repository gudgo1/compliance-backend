import csv
from pathlib import Path


ALLOWED_EXTENSIONS = {"csv", "txt"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_evidence_file(path):
    extension = Path(path).suffix.lower()
    if extension == ".csv":
        return parse_csv(path)
    if extension == ".txt":
        return parse_txt(path)
    raise ValueError("Unsupported evidence file type")


def parse_csv(path):
    records = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"setting_key", "observed_value", "source_reference"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")

        for row in reader:
            if not row.get("setting_key"):
                continue
            records.append(
                {
                    "setting_key": row["setting_key"].strip(),
                    "observed_value": (row.get("observed_value") or "").strip(),
                    "source_reference": (row.get("source_reference") or "").strip(),
                }
            )
    return records


def parse_txt(path):
    records = []
    current = {}
    with open(path, encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                _append_txt_record(records, current)
                current = {}
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            current[key.strip().lower()] = value.strip()

    _append_txt_record(records, current)
    return records


def _append_txt_record(records, current):
    setting_key = current.get("setting") or current.get("setting_key")
    observed_value = current.get("value") or current.get("observed_value")
    if setting_key and observed_value is not None:
        records.append(
            {
                "setting_key": setting_key,
                "observed_value": observed_value,
                "source_reference": current.get("source_reference", "txt_upload"),
            }
        )
