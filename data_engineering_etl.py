from __future__ import annotations

import argparse
import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REQUIRED_COLUMNS = ("event_id", "user_id", "event_ts")
OUTPUT_COLUMNS = (
    "event_id",
    "user_id",
    "event_ts",
    "event_date",
    "event_type",
    "amount",
)


@dataclass
class ProcessResult:
    records: List[Dict[str, str]]
    summary: Dict[str, object]
    errors: List[str]


def normalize_header(name: str) -> str:
    if name is None:
        return ""
    return name.replace("\ufeff", "").strip().lower()


def validate_headers(fieldnames: Iterable[str]) -> List[str]:
    if not fieldnames:
        raise ValueError("CSV is missing a header row.")
    normalized = [normalize_header(name) for name in fieldnames]
    missing = [col for col in REQUIRED_COLUMNS if col not in normalized]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return normalized


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_event_ts(dt: datetime) -> str:
    dt = ensure_utc(dt)
    text = dt.isoformat()
    if text.endswith("+00:00"):
        text = f"{text[:-6]}Z"
    return text


def decimal_to_str(value: Decimal) -> str:
    return format(value, "f")


def parse_event_ts(value: str) -> datetime:
    text = (value or "").strip()
    if not text:
        raise ValueError("event_ts is blank.")
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"event_ts is not ISO-8601: {value}") from exc
    return ensure_utc(dt)


def parse_amount(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount is not numeric.") from exc


def normalize_record(raw: Dict[str, str], null_counts: Dict[str, int]) -> Dict[str, object]:
    event_id = (raw.get("event_id") or "").strip()
    if not event_id:
        raise ValueError("event_id is blank.")

    user_id = (raw.get("user_id") or "").strip()
    if not user_id:
        raise ValueError("user_id is blank.")

    event_ts = parse_event_ts(raw.get("event_ts") or "")

    event_type_raw = raw.get("event_type")
    if event_type_raw is None or str(event_type_raw).strip() == "":
        null_counts["event_type"] += 1
        event_type = "unknown"
    else:
        event_type = str(event_type_raw).strip().lower()

    amount_raw = raw.get("amount")
    if amount_raw is None or str(amount_raw).strip() == "":
        null_counts["amount"] += 1
        amount = Decimal("0")
    else:
        amount = parse_amount(str(amount_raw).strip())

    return {
        "event_id": event_id,
        "user_id": user_id,
        "event_ts": event_ts,
        "event_date": event_ts.date().isoformat(),
        "event_type": event_type,
        "amount": amount,
    }


def dedupe_records(
    records: Iterable[Dict[str, object]]
) -> Tuple[List[Dict[str, object]], int]:
    by_id: Dict[str, Dict[str, object]] = {}
    duplicates = 0
    for record in records:
        event_id = record["event_id"]
        existing = by_id.get(event_id)
        if existing is None:
            by_id[event_id] = record
            continue
        duplicates += 1
        if record["event_ts"] >= existing["event_ts"]:
            by_id[event_id] = record

    deduped = list(by_id.values())
    deduped.sort(key=lambda item: (item["event_ts"], item["event_id"]))
    return deduped, duplicates


def serialize_records(records: Iterable[Dict[str, object]]) -> List[Dict[str, str]]:
    serialized = []
    for record in records:
        serialized.append(
            {
                "event_id": record["event_id"],
                "user_id": record["user_id"],
                "event_ts": format_event_ts(record["event_ts"]),
                "event_date": record["event_date"],
                "event_type": record["event_type"],
                "amount": decimal_to_str(record["amount"]),
            }
        )
    return serialized


def build_summary(
    *,
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    deduped_rows: int,
    duplicates_dropped: int,
    records: Iterable[Dict[str, object]],
    null_counts: Dict[str, int],
) -> Dict[str, object]:
    total_amount = Decimal("0")
    amount_by_date: Dict[str, Decimal] = {}
    amount_by_user: Dict[str, Decimal] = {}
    event_type_counts: Dict[str, int] = {}

    for record in records:
        amount = record["amount"]
        total_amount += amount

        event_date = record["event_date"]
        amount_by_date[event_date] = amount_by_date.get(event_date, Decimal("0")) + amount

        user_id = record["user_id"]
        amount_by_user[user_id] = amount_by_user.get(user_id, Decimal("0")) + amount

        event_type = record["event_type"]
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

    return {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "deduped_rows": deduped_rows,
        "duplicates_dropped": duplicates_dropped,
        "total_amount": decimal_to_str(total_amount),
        "amount_by_date": {
            key: decimal_to_str(value) for key, value in sorted(amount_by_date.items())
        },
        "amount_by_user": {
            key: decimal_to_str(value) for key, value in sorted(amount_by_user.items())
        },
        "event_type_counts": dict(sorted(event_type_counts.items())),
        "null_or_blank_counts": {
            "event_type": null_counts.get("event_type", 0),
            "amount": null_counts.get("amount", 0),
        },
    }


def process_csv_text(csv_text: str, *, on_error: str = "skip") -> ProcessResult:
    if on_error not in {"skip", "raise"}:
        raise ValueError("on_error must be 'skip' or 'raise'.")

    reader = csv.DictReader(io.StringIO(csv_text))
    validate_headers(reader.fieldnames)

    errors: List[str] = []
    null_counts = {"event_type": 0, "amount": 0}
    cleaned: List[Dict[str, object]] = []
    total_rows = 0

    for row_index, row in enumerate(reader, start=2):
        total_rows += 1
        raw = {
            normalize_header(key): value
            for key, value in row.items()
            if key is not None
        }
        try:
            cleaned.append(normalize_record(raw, null_counts))
        except ValueError as exc:
            if on_error == "raise":
                raise
            errors.append(f"Line {row_index}: {exc}")

    valid_rows = len(cleaned)
    deduped, duplicates = dedupe_records(cleaned)
    summary = build_summary(
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=len(errors),
        deduped_rows=len(deduped),
        duplicates_dropped=duplicates,
        records=deduped,
        null_counts=null_counts,
    )

    return ProcessResult(
        records=serialize_records(deduped),
        summary=summary,
        errors=errors,
    )


def render_clean_csv(records: Iterable[Dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=OUTPUT_COLUMNS)
    writer.writeheader()
    for record in records:
        writer.writerow({key: record.get(key, "") for key in OUTPUT_COLUMNS})
    return buffer.getvalue()


def process_csv_file(
    input_path: str,
    *,
    cleaned_path: str | None = None,
    summary_path: str | None = None,
    on_error: str = "skip",
) -> ProcessResult:
    csv_text = Path(input_path).read_text(encoding="utf-8")
    result = process_csv_text(csv_text, on_error=on_error)

    if cleaned_path:
        Path(cleaned_path).write_text(
            render_clean_csv(result.records), encoding="utf-8"
        )
    if summary_path:
        Path(summary_path).write_text(
            json.dumps(result.summary, indent=2), encoding="utf-8"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Clean, deduplicate, and summarize event CSV data for data engineering tasks."
        )
    )
    parser.add_argument("input_csv", help="Path to the input CSV file.")
    parser.add_argument("--cleaned", help="Path to write the cleaned CSV output.")
    parser.add_argument("--summary", help="Path to write the summary JSON output.")
    parser.add_argument(
        "--on-error",
        default="skip",
        choices=["skip", "raise"],
        help="Whether to skip invalid rows or raise an error.",
    )

    args = parser.parse_args()
    result = process_csv_file(
        args.input_csv,
        cleaned_path=args.cleaned,
        summary_path=args.summary,
        on_error=args.on_error,
    )

    if result.errors:
        print(f"Completed with {len(result.errors)} invalid rows.")
    else:
        print("Completed with no invalid rows.")


if __name__ == "__main__":
    main()
