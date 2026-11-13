"""Command-file entry point for the actual ECE-055 project."""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .engine import process
from .models import Item, Rate, Request, Source
from .reports import write_credit_notes, write_monthly_summary, write_schedule


class InputProblem(Exception):
    """An input problem that can be explained without a traceback."""


def read_rows(path):
    try:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise InputProblem(f"{path.name}: missing CSV header")
            return list(reader)
    except OSError as exc:
        raise InputProblem(f"Cannot read {path}: {exc}") from exc


def load_sources(path):
    result = {}
    for row_no, row in enumerate(read_rows(path), 2):
        source_id = row["source_id"].strip()
        if source_id in result:
            raise InputProblem(f"{path.name}, row {row_no}: duplicate source_id {source_id}")
        kind = row["source_type"].strip().upper()
        if kind not in {"BULK", "HOUSEHOLD"}:
            raise InputProblem(f"{path.name}, row {row_no}: source_type must be BULK or HOUSEHOLD")
        try:
            distance = Decimal(row["distance_km"])
        except InvalidOperation as exc:
            raise InputProblem(f"{path.name}, row {row_no}: invalid distance_km") from exc
        result[source_id] = Source(source_id, kind, distance,
                                   row["source_name"].strip(), row["area"].strip())
    return result


def load_rates(path):
    result = {}
    for row_no, row in enumerate(read_rows(path), 2):
        category = row["category"].strip().upper()
        if category in result:
            raise InputProblem(f"{path.name}, row {row_no}: duplicate category {category}")
        try:
            value = Decimal(row["credit_per_kg_rs"])
        except InvalidOperation as exc:
            raise InputProblem(f"{path.name}, row {row_no}: invalid credit_per_kg_rs") from exc
        hazard = row["hazardous"].strip().lower()
        if hazard not in {"true", "false"}:
            raise InputProblem(f"{path.name}, row {row_no}: hazardous must be true or false")
        result[category] = Rate(category, value, hazard == "true")
    return result


def load_requests(path, sources):
    result = []
    seen = set()
    for row_no, row in enumerate(read_rows(path), 2):
        request_id = row["request_id"].strip()
        source_id = row["source_id"].strip()
        if request_id in seen:
            raise InputProblem(f"{path.name}, row {row_no}: duplicate request_id {request_id}")
        if source_id not in sources:
            raise InputProblem(f"{path.name}, row {row_no}: unknown source_id {source_id}")
        try:
            request_date = date.fromisoformat(row["request_date"].strip())
        except ValueError as exc:
            raise InputProblem(f"{path.name}, row {row_no}: invalid request_date") from exc
        result.append(Request(request_id, request_date, source_id, ()))
        seen.add(request_id)
    return result


def attach_items(requests, path, rates):
    request_ids = {request.request_id for request in requests}
    grouped = {}
    for row_no, row in enumerate(read_rows(path), 2):
        request_id = row["request_id"].strip()
        category = row["category"].strip().upper()
        if request_id not in request_ids:
            raise InputProblem(f"{path.name}, row {row_no}: unknown request_id {request_id}")
        if category not in rates:
            raise InputProblem(f"{path.name}, row {row_no}: unknown category {category}")
        try:
            line_no = int(row["line_no"])
            count = int(row["item_count"])
            weight = Decimal(row["weight_kg"])
        except (ValueError, InvalidOperation) as exc:
            raise InputProblem(f"{path.name}, row {row_no}: invalid item number") from exc
        if line_no <= 0 or count <= 0 or weight <= 0:
            raise InputProblem(f"{path.name}, row {row_no}: line, count, and weight must be positive")
        grouped.setdefault(request_id, []).append((line_no, Item(category, weight)))

    completed = []
    for request in requests:
        lines = grouped.get(request.request_id, [])
        if not lines:
            raise InputProblem(f"{path.name}: no item lines for {request.request_id}")
        lines.sort(key=lambda pair: pair[0])
        completed.append(Request(request.request_id, request.request_date, request.source_id,
                                 tuple(item for _, item in lines)))
    return completed


def print_processing_summary(results, days):
    refused = sum(result.status == "REFUSED" for result in results)
    print("\nPROCESSING SUMMARY")
    print(f"Requests: {len(results)}    Scheduled: {len(results) - refused}    Refused: {refused}")
    if days:
        fullest = max(days.values(), key=lambda day: day.total_kg)
        print(f"Vehicle days used: {len(days)}")
        print(f"Highest-load day: {fullest.pickup_date} | {len(fullest.request_ids)} stops | "
              f"{fullest.total_kg:.1f}/1200.0 kg | {fullest.hazardous_kg:.1f}/300.0 kg hazardous")


def main():
    parser = argparse.ArgumentParser(description="ECE-055 input processing and scheduling")
    parser.add_argument("--commands", type=Path,
        default=Path("E030-ECE-055-sample-data/E030-ECE-055-sample-data/commands.txt"),
        help="Path to the support pack commands.txt")
    args = parser.parse_args()
    command_file = args.commands.resolve()
    pack_dir = command_file.parent
    sources = rates = requests = results = days = None
    report_commands_seen = False
    print("ECE-055 E-WASTE ENGINE | PHASE 3")
    output_dir = command_file.parent / "output"
    try:
        for line_no, raw in enumerate(command_file.read_text(encoding="utf-8-sig").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            command, *arg = [part.strip() for part in line.split("|")]
            if command == "LOAD_SOURCES" and len(arg) == 1:
                sources = load_sources(pack_dir / arg[0])
                print(f"Loaded sources: {len(sources)}")
            elif command == "LOAD_RATE_CARD" and len(arg) == 1:
                rates = load_rates(pack_dir / arg[0])
                print(f"Loaded categories: {len(rates)}")
            elif command == "LOAD_REQUESTS" and len(arg) == 1:
                if sources is None:
                    raise InputProblem("Load sources before requests")
                requests = load_requests(pack_dir / arg[0], sources)
                print(f"Loaded request headers: {len(requests)}")
            elif command == "LOAD_REQUEST_ITEMS" and len(arg) == 1:
                if requests is None or rates is None:
                    raise InputProblem("Load requests and rate card before request items")
                requests = attach_items(requests, pack_dir / arg[0], rates)
                line_count = sum(len(request.items) for request in requests)
                print(f"Linked item lines: {line_count}")
            elif command == "PROCESS_REQUESTS" and not arg:
                if requests is None or sources is None or rates is None:
                    raise InputProblem("Load all four input files before processing")
                results, days = process(requests, sources, rates)
                print_processing_summary(results, days)
            elif command == "PRINT_CREDIT_NOTES" and not arg:
                if results is None:
                    raise InputProblem("Run PROCESS_REQUESTS before printing reports")
                write_credit_notes(output_dir / "credit_notes.csv", results)
                print("Created report: output/credit_notes.csv")
            elif command == "PRINT_SCHEDULE" and not arg:
                if results is None:
                    raise InputProblem("Run PROCESS_REQUESTS before printing reports")
                write_schedule(output_dir / "pickup_schedule.csv", results, days)
                print("Created report: output/pickup_schedule.csv")
            elif command == "MONTHLY_SUMMARY" and len(arg) == 1:
                if results is None or sources is None:
                    raise InputProblem("Run PROCESS_REQUESTS before printing reports")
                try:
                    date.fromisoformat(arg[0] + "-01")
                except ValueError as exc:
                    raise InputProblem("MONTHLY_SUMMARY expects a month in YYYY-MM format") from exc
                write_monthly_summary(output_dir / "monthly_summary.csv", arg[0], results, sources)
                print("Created report: output/monthly_summary.csv")
            else:
                raise InputProblem(f"commands.txt, line {line_no}: unknown command or wrong arguments")
    except (OSError, InputProblem, KeyError, IndexError) as exc:
        print(f"\nINPUT ERROR\n{exc}")
        return 2
    print("Phase 3 complete. Reports are in the sample pack's output folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
