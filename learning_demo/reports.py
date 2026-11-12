"""Write the exact report filenames and column order described in the pack."""

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import RequestResult, Source, VehicleDay


def decimal_text(value: Decimal, places: str) -> str:
    return str(value.quantize(Decimal(places)))


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_credit_notes(output_dir: Path, results: list[RequestResult]) -> Path:
    headers = [
        "request_id", "source_id", "status", "reason", "total_kg", "hazardous_kg",
        "credit_rs", "deduction_rs", "pickup_charge_rs", "net_rs", "net_type", "pickup_date",
    ]
    rows = []
    for result in results:
        request = result.request
        if result.status == "REFUSED":
            money = {key: "NONE" for key in ("credit_rs", "deduction_rs", "pickup_charge_rs", "net_rs", "net_type")}
            pickup_date = "NONE"
        else:
            money = {
                "credit_rs": decimal_text(result.credit_rs, "0.01"),
                "deduction_rs": decimal_text(result.deduction_rs, "0.01"),
                "pickup_charge_rs": decimal_text(result.pickup_charge_rs, "0.01"),
                "net_rs": str(result.net_rs),
                "net_type": result.net_type,
            }
            pickup_date = result.pickup_date.isoformat()
        rows.append({
            "request_id": request.request_id,
            "source_id": request.source_id,
            "status": result.status,
            "reason": result.reason,
            "total_kg": decimal_text(request.total_kg, "0.1"),
            "hazardous_kg": decimal_text(result.hazardous_kg, "0.1"),
            **money,
            "pickup_date": pickup_date,
        })
    path = output_dir / "credit_notes.csv"
    write_csv(path, headers, rows)
    return path


def write_schedule(output_dir: Path, results: list[RequestResult]) -> Path:
    headers = [
        "pickup_date", "stop_no", "request_id", "source_id", "kg", "hazardous_kg",
        "day_kg_after", "day_hazardous_kg_after",
    ]
    scheduled = [result for result in results if result.status == "SCHEDULED"]
    # Python's sort is stable, so equal dates stay in the original request-file order.
    scheduled.sort(key=lambda result: result.pickup_date)
    rows = [{
        "pickup_date": result.pickup_date.isoformat(),
        "stop_no": str(result.stop_no),
        "request_id": result.request.request_id,
        "source_id": result.request.source_id,
        "kg": decimal_text(result.request.total_kg, "0.1"),
        "hazardous_kg": decimal_text(result.hazardous_kg, "0.1"),
        "day_kg_after": decimal_text(result.day_kg_after, "0.1"),
        "day_hazardous_kg_after": decimal_text(result.day_hazardous_kg_after, "0.1"),
    } for result in scheduled]
    path = output_dir / "pickup_schedule.csv"
    write_csv(path, headers, rows)
    return path


def write_monthly_summary(output_dir: Path, month: str, results: list[RequestResult], sources: dict[str, Source]) -> Path:
    headers = [
        "month", "source_id", "requests", "collected_kg", "net_credit_rs", "net_payable_rs", "certificate",
    ]
    month_prefix = f"{month}-"
    per_source = {}
    for result in results:
        if result.status != "SCHEDULED" or not result.pickup_date.isoformat().startswith(month_prefix):
            continue
        source_id = result.request.source_id
        summary = per_source.setdefault(source_id, {
            "requests": 0,
            "collected_kg": Decimal("0"),
            "net_credit_rs": 0,
            "net_payable_rs": 0,
        })
        summary["requests"] += 1
        summary["collected_kg"] += result.request.total_kg
        if result.net_type == "CREDIT":
            summary["net_credit_rs"] += result.net_rs
        elif result.net_type == "AMOUNT_PAYABLE":
            summary["net_payable_rs"] += result.net_rs

    rows = []
    for source_id in sorted(per_source):
        summary = per_source[source_id]
        certified = summary["collected_kg"] >= Decimal("500.0")
        rows.append({
            "month": month,
            "source_id": source_id,
            "requests": str(summary["requests"]),
            "collected_kg": decimal_text(summary["collected_kg"], "0.1"),
            "net_credit_rs": str(summary["net_credit_rs"]),
            "net_payable_rs": str(summary["net_payable_rs"]),
            "certificate": "RECYCLING_CERTIFICATE" if certified else "NONE",
        })

    path = output_dir / "monthly_summary.csv"
    write_csv(path, headers, rows)
    return path


def day_totals(days: dict[date, VehicleDay]) -> list[str]:
    """Friendly console lines so learners can see the vehicle capacity checks."""
    lines = []
    for day, state in sorted(days.items()):
        stop_word = "stop" if len(state.request_ids) == 1 else "stops"
        lines.append(
            f"{day.isoformat()}: {len(state.request_ids)} {stop_word}, "
            f"{state.total_kg:.1f} / 1200.0 kg total, {state.hazardous_kg:.1f} / 300.0 kg hazardous"
        )
    return lines
