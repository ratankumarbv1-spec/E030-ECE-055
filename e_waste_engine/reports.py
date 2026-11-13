"""CSV report writers for Phase 3."""
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path


def _write_csv(path: Path, columns: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _money(value):
    return f"{value:.2f}"


def write_credit_notes(path, results):
    columns = ["request_id", "source_id", "status", "reason", "total_kg", "hazardous_kg",
               "credit_rs", "deduction_rs", "pickup_charge_rs", "net_rs", "net_type", "pickup_date"]
    rows = []
    for result in results:
        rows.append({
            "request_id": result.request.request_id,
            "source_id": result.request.source_id,
            "status": result.status,
            "reason": result.reason,
            "total_kg": f"{result.request.total_kg:.1f}",
            "hazardous_kg": f"{result.hazardous_kg:.1f}",
            "credit_rs": _money(result.credit_rs) if result.credit_rs is not None else "NONE",
            "deduction_rs": _money(result.deduction_rs) if result.deduction_rs is not None else "NONE",
            "pickup_charge_rs": _money(result.pickup_charge_rs) if result.pickup_charge_rs is not None else "NONE",
            "net_rs": result.net_rs if result.net_rs is not None else "NONE",
            "net_type": result.net_type,
            "pickup_date": result.pickup_date.isoformat() if result.pickup_date else "NONE",
        })
    _write_csv(path, columns, rows)


def write_schedule(path, results, days):
    columns = ["pickup_date", "stop_no", "request_id", "source_id", "kg", "hazardous_kg",
               "day_kg_after", "day_hazardous_kg_after"]
    result_by_id = {result.request.request_id: result for result in results}
    rows = []
    for day_date, day in sorted(days.items()):
        kg = Decimal("0")
        hazard = Decimal("0")
        for stop_no, request_id in enumerate(day.request_ids, 1):
            result = result_by_id[request_id]
            kg += result.request.total_kg
            hazard += result.hazardous_kg
            rows.append({"pickup_date": day_date.isoformat(), "stop_no": stop_no,
                         "request_id": request_id, "source_id": result.request.source_id,
                         "kg": f"{result.request.total_kg:.1f}", "hazardous_kg": f"{result.hazardous_kg:.1f}",
                         "day_kg_after": f"{kg:.1f}", "day_hazardous_kg_after": f"{hazard:.1f}"})
    _write_csv(path, columns, rows)


def write_monthly_summary(path, month: str, results, sources):
    columns = ["month", "source_id", "requests", "collected_kg", "net_credit_rs", "net_payable_rs", "certificate"]
    totals = defaultdict(lambda: {"requests": 0, "kg": Decimal("0"), "credit": 0, "payable": 0})
    for result in results:
        if result.status != "SCHEDULED" or result.pickup_date.strftime("%Y-%m") != month:
            continue
        item = totals[result.request.source_id]
        item["requests"] += 1
        item["kg"] += result.request.total_kg
        if result.net_type == "CREDIT":
            item["credit"] += result.net_rs
        else:
            item["payable"] += result.net_rs
    rows = []
    for source_id in sorted(totals):
        item = totals[source_id]
        rows.append({"month": month, "source_id": source_id, "requests": item["requests"],
                     "collected_kg": f"{item['kg']:.1f}", "net_credit_rs": item["credit"],
                     "net_payable_rs": item["payable"],
                     "certificate": "RECYCLING_CERTIFICATE" if item["kg"] >= Decimal("500") else "NONE"})
    _write_csv(path, columns, rows)
