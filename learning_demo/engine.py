"""Apply the brief's calculations, refusals, and one-vehicle scheduling rules."""

from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from .models import Rate, Request, RequestResult, Source, VehicleDay


MAX_TOTAL_KG = Decimal("1200.0")
MAX_STOPS = 8
MAX_HAZARDOUS_KG = Decimal("300.0")
MIN_HOUSEHOLD_KG = Decimal("5.0")
PICKUP_CHARGE_PER_KM = Decimal("12.00")
HANDLING_DEDUCTION_PER_KG = Decimal("15.00")
CENT = Decimal("0.01")


def hazardous_weight(request: Request, rates: dict[str, Rate]) -> Decimal:
    """Add the weights of all categories marked hazardous on the rate card."""
    return sum(
        (item.weight_kg for item in request.items if rates[item.category].hazardous),
        Decimal("0"),
    )


def calculate_money(request: Request, source: Source, rates: dict[str, Rate]):
    """Return credit, household deduction, pickup charge, rounded net, and type."""
    credit = Decimal("0")
    deduction = Decimal("0")
    for item in request.items:
        rate = rates[item.category]
        if source.source_type == "HOUSEHOLD" and rate.hazardous:
            deduction += item.weight_kg * HANDLING_DEDUCTION_PER_KG
        else:
            # Each item-line credit is rounded to two decimal places as specified.
            line_credit = (item.weight_kg * rate.credit_per_kg_rs).quantize(CENT, rounding=ROUND_HALF_UP)
            credit += line_credit

    rounded_distance = source.distance_km.to_integral_value(rounding=ROUND_CEILING)
    extra_km = max(Decimal("0"), rounded_distance - Decimal("10"))
    pickup_charge = Decimal("0")
    if request.total_kg < Decimal("200.0"):
        pickup_charge = extra_km * PICKUP_CHARGE_PER_KM

    deduction = deduction.quantize(CENT, rounding=ROUND_HALF_UP)
    net_decimal = credit - deduction - pickup_charge
    net_signed = int(net_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    net_type = "AMOUNT_PAYABLE" if net_signed < 0 else "CREDIT"
    return credit, deduction, pickup_charge, abs(net_signed), net_type, net_signed


def next_vehicle_day(start: date) -> date:
    """Vehicle days are Monday-Saturday; Sunday is skipped."""
    day = start
    while day.weekday() == 6:
        day += timedelta(days=1)
    return day


def schedule_request(request: Request, source: Source, rates: dict[str, Rate], days: dict[date, VehicleDay]):
    """Place one whole request on the earliest allowed day with room for all limits."""
    hazard_kg = hazardous_weight(request, rates)

    # Refusals do not have money lines in the required credit-note file.
    if source.source_type == "HOUSEHOLD" and request.total_kg < MIN_HOUSEHOLD_KG:
        return RequestResult(request, "REFUSED", "BELOW_MINIMUM", hazard_kg)
    if hazard_kg > MAX_HAZARDOUS_KG:
        return RequestResult(request, "REFUSED", "HAZARD_OVER_LIMIT", hazard_kg)
    if request.total_kg > MAX_TOTAL_KG:
        return RequestResult(request, "REFUSED", "OVER_CAPACITY", hazard_kg)

    first_day = next_vehicle_day(request.request_date + timedelta(days=1))
    candidate = first_day
    while True:
        vehicle_day = days.get(candidate)
        if vehicle_day is None:
            vehicle_day = VehicleDay(candidate)
            days[candidate] = vehicle_day

        fits = (
            len(vehicle_day.request_ids) < MAX_STOPS
            and vehicle_day.total_kg + request.total_kg <= MAX_TOTAL_KG
            and vehicle_day.hazardous_kg + hazard_kg <= MAX_HAZARDOUS_KG
        )
        if fits:
            vehicle_day.request_ids.append(request.request_id)
            vehicle_day.total_kg += request.total_kg
            vehicle_day.hazardous_kg += hazard_kg
            credit, deduction, charge, net_rs, net_type, signed_net = calculate_money(request, source, rates)
            result = RequestResult(
                request=request,
                status="SCHEDULED",
                reason="NONE",
                hazardous_kg=hazard_kg,
                credit_rs=credit,
                deduction_rs=deduction,
                pickup_charge_rs=charge,
                net_rs=net_rs,
                net_type=net_type,
                pickup_date=candidate,
                stop_no=len(vehicle_day.request_ids),
                day_kg_after=vehicle_day.total_kg,
                day_hazardous_kg_after=vehicle_day.hazardous_kg,
            )
            return result

        candidate = next_vehicle_day(candidate + timedelta(days=1))


def process_requests(requests: list[Request], sources: dict[str, Source], rates: dict[str, Rate]):
    """Process requests in file order and return request results plus day totals."""
    days: dict[date, VehicleDay] = {}
    results = []
    for request in requests:
        results.append(schedule_request(request, sources[request.source_id], rates, days))
    return results, days
