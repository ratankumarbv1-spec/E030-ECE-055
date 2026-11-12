"""Read the four CSV input files from the supplied sample data pack."""

import csv
from dataclasses import replace
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Item, Rate, Request, Source


class DataError(ValueError):
    """Readable error for malformed or inconsistent sample data."""


def read_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise DataError(f"{path.name}: CSV header is missing")
            return list(reader)
    except OSError as exc:
        raise DataError(f"Cannot open {path}: {exc}") from exc


def load_sources(path: Path) -> dict[str, Source]:
    sources = {}
    for row_number, row in enumerate(read_rows(path), start=2):
        source_id = row["source_id"].strip()
        if source_id in sources:
            raise DataError(f"{path.name}, row {row_number}: repeated source_id {source_id}")
        try:
            distance = Decimal(row["distance_km"])
        except InvalidOperation as exc:
            raise DataError(f"{path.name}, row {row_number}: invalid distance_km") from exc
        sources[source_id] = Source(
            source_id=source_id,
            source_name=row["source_name"].strip(),
            source_type=row["source_type"].strip().upper(),
            area=row["area"].strip(),
            distance_km=distance,
        )
    return sources


def load_rates(path: Path) -> dict[str, Rate]:
    rates = {}
    for row_number, row in enumerate(read_rows(path), start=2):
        category = row["category"].strip().upper()
        if category in rates:
            raise DataError(f"{path.name}, row {row_number}: repeated category {category}")
        try:
            rate = Decimal(row["credit_per_kg_rs"])
        except InvalidOperation as exc:
            raise DataError(f"{path.name}, row {row_number}: invalid credit_per_kg_rs") from exc
        hazard_text = row["hazardous"].strip().lower()
        if hazard_text not in {"true", "false"}:
            raise DataError(f"{path.name}, row {row_number}: hazardous must be true or false")
        rates[category] = Rate(category, rate, hazard_text == "true")
    return rates


def load_request_headers(request_path: Path, sources: dict[str, Source]) -> list[Request]:
    request_rows = read_rows(request_path)
    requests = []
    seen_ids = set()
    for row_number, row in enumerate(request_rows, start=2):
        request_id = row["request_id"].strip()
        source_id = row["source_id"].strip()
        if request_id in seen_ids:
            raise DataError(f"{request_path.name}, row {row_number}: duplicate request_id {request_id}")
        if source_id not in sources:
            raise DataError(f"{request_path.name}, row {row_number}: unknown source_id {source_id}")
        try:
            request_date = date.fromisoformat(row["request_date"].strip())
        except ValueError as exc:
            raise DataError(f"{request_path.name}, row {row_number}: invalid request_date") from exc
        requests.append(Request(request_id, request_date, source_id, ()))
        seen_ids.add(request_id)
    return requests


def attach_request_items(requests: list[Request], items_path: Path, rates: dict[str, Rate]) -> list[Request]:
    item_rows = read_rows(items_path)
    item_rows_by_request: dict[str, list[tuple[int, Item]]] = {}
    known_request_ids = {request.request_id for request in requests}

    for row_number, row in enumerate(item_rows, start=2):
        request_id = row["request_id"].strip()
        if request_id not in known_request_ids:
            raise DataError(f"{items_path.name}, row {row_number}: unknown request_id {request_id}")
        category = row["category"].strip().upper()
        if category not in rates:
            raise DataError(f"{items_path.name}, row {row_number}: unknown category {category}")
        try:
            line_number = int(row["line_no"])
            count = int(row["item_count"])
            weight = Decimal(row["weight_kg"])
        except (ValueError, InvalidOperation) as exc:
            raise DataError(f"{items_path.name}, row {row_number}: invalid number") from exc
        if count <= 0 or weight <= 0:
            raise DataError(f"{items_path.name}, row {row_number}: count and weight must be positive")
        item_rows_by_request.setdefault(request_id, []).append(
            (line_number, Item(category, count, weight))
        )

    completed_requests = []
    for request in requests:
        item_rows_for_request = item_rows_by_request.get(request.request_id, [])
        if not item_rows_for_request:
            raise DataError(f"{items_path.name}: no item lines for {request.request_id}")
        item_rows_for_request.sort(key=lambda pair: pair[0])
        completed_requests.append(replace(
            request,
            items=tuple(item for _, item in item_rows_for_request),
        ))
    return completed_requests
