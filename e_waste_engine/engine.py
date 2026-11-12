"""Phase 2 business rules and one-vehicle scheduling."""
from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from .models import Rate, Request, Result, Source, VehicleDay

MAX_KG = Decimal("1200.0")
MAX_STOPS = 8
MAX_HAZARD_KG = Decimal("300.0")
MIN_HOUSEHOLD_KG = Decimal("5.0")
CENT = Decimal("0.01")


def hazardous_weight(request: Request, rates: dict[str, Rate]) -> Decimal:
    return sum((item.weight_kg for item in request.items if rates[item.category].hazardous), Decimal("0"))


def calculate_money(request: Request, source: Source, rates: dict[str, Rate]):
    credit = Decimal("0")
    deduction = Decimal("0")
    for item in request.items:
        rate = rates[item.category]
        if source.source_type == "HOUSEHOLD" and rate.hazardous:
            deduction += item.weight_kg * Decimal("15.00")
        else:
            credit += (item.weight_kg * rate.credit_per_kg_rs).quantize(CENT, rounding=ROUND_HALF_UP)
    chargeable_km = max(Decimal("0"), source.distance_km.to_integral_value(rounding=ROUND_CEILING) - Decimal("10"))
    charge = Decimal("0") if request.total_kg >= Decimal("200.0") else chargeable_km * Decimal("12.00")
    deduction = deduction.quantize(CENT, rounding=ROUND_HALF_UP)
    signed = int((credit - deduction - charge).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return credit, deduction, charge, abs(signed), "AMOUNT_PAYABLE" if signed < 0 else "CREDIT"


def next_vehicle_day(day: date) -> date:
    while day.weekday() == 6:  # Sunday
        day += timedelta(days=1)
    return day


def schedule_one(request: Request, source: Source, rates: dict[str, Rate], days: dict[date, VehicleDay]) -> Result:
    hazard = hazardous_weight(request, rates)
    if source.source_type == "HOUSEHOLD" and request.total_kg < MIN_HOUSEHOLD_KG:
        return Result(request, "REFUSED", "BELOW_MINIMUM", hazard)
    if hazard > MAX_HAZARD_KG:
        return Result(request, "REFUSED", "HAZARD_OVER_LIMIT", hazard)
    if request.total_kg > MAX_KG:
        return Result(request, "REFUSED", "OVER_CAPACITY", hazard)

    candidate = next_vehicle_day(request.request_date + timedelta(days=1))
    while True:
        day = days.setdefault(candidate, VehicleDay(candidate))
        fits = (len(day.request_ids) < MAX_STOPS
                and day.total_kg + request.total_kg <= MAX_KG
                and day.hazardous_kg + hazard <= MAX_HAZARD_KG)
        if fits:
            day.request_ids.append(request.request_id)
            day.total_kg += request.total_kg
            day.hazardous_kg += hazard
            credit, deduction, charge, net, net_type = calculate_money(request, source, rates)
            return Result(request, "SCHEDULED", "NONE", hazard, credit, deduction, charge,
                          net, net_type, candidate)
        candidate = next_vehicle_day(candidate + timedelta(days=1))


def process(requests: list[Request], sources: dict[str, Source], rates: dict[str, Rate]):
    days: dict[date, VehicleDay] = {}
    results = [schedule_one(r, sources[r.source_id], rates, days) for r in requests]
    return results, days
