"""Rule-focused tests for the ECE-055 processing engine.

Run from the repository root with: python -m unittest discover -s tests -v
"""
import unittest
from datetime import date
from decimal import Decimal

from e_waste_engine.engine import process, schedule_one
from e_waste_engine.models import Item, Rate, Request, Source, VehicleDay


RATES = {
    "IT": Rate("IT", Decimal("18.00"), False),
    "BATTERY": Rate("BATTERY", Decimal("25.00"), True),
    "CRT": Rate("CRT", Decimal("4.00"), True),
}


def make_request(request_id, weight, category="IT", day=date(2026, 10, 1)):
    return Request(request_id, day, "SRC-01", (Item(category, Decimal(str(weight))),))


def source(kind="BULK", distance="10.0"):
    return Source("SRC-01", kind, Decimal(distance))


class CreditEngineRuleTests(unittest.TestCase):
    def test_exactly_ten_km_has_no_pickup_charge(self):
        result = schedule_one(make_request("R1", 10), source(distance="10.0"), RATES, {})
        self.assertEqual(result.pickup_charge_rs, Decimal("0.00"))

    def test_distance_above_ten_rounds_up_to_whole_km(self):
        result = schedule_one(make_request("R1", 10), source(distance="10.1"), RATES, {})
        self.assertEqual(result.pickup_charge_rs, Decimal("12.00"))

    def test_exactly_two_hundred_kg_waives_pickup_charge(self):
        result = schedule_one(make_request("R1", 200), source(distance="25.0"), RATES, {})
        self.assertEqual(result.pickup_charge_rs, Decimal("0.00"))

    def test_household_minimum_boundary(self):
        refused = schedule_one(make_request("R1", "4.9"), source("HOUSEHOLD"), RATES, {})
        accepted = schedule_one(make_request("R2", "5.0"), source("HOUSEHOLD"), RATES, {})
        self.assertEqual((refused.status, refused.reason), ("REFUSED", "BELOW_MINIMUM"))
        self.assertEqual(accepted.status, "SCHEDULED")

    def test_household_hazardous_item_gets_deduction_not_credit(self):
        result = schedule_one(make_request("R1", 5, "BATTERY"), source("HOUSEHOLD"), RATES, {})
        self.assertEqual(result.credit_rs, Decimal("0"))
        self.assertEqual(result.deduction_rs, Decimal("75.00"))
        self.assertEqual(result.net_type, "AMOUNT_PAYABLE")

    def test_bulk_hazardous_item_gets_rate_card_credit(self):
        result = schedule_one(make_request("R1", 2, "BATTERY"), source("BULK"), RATES, {})
        self.assertEqual(result.credit_rs, Decimal("50.00"))
        self.assertEqual(result.deduction_rs, Decimal("0.00"))

    def test_request_over_daily_hazard_limit_is_refused(self):
        result = schedule_one(make_request("R1", 350, "BATTERY"), source(), RATES, {})
        self.assertEqual((result.status, result.reason), ("REFUSED", "HAZARD_OVER_LIMIT"))

    def test_combined_hazard_room_moves_request_to_next_day(self):
        first = make_request("R1", 90, "BATTERY")
        second = make_request("R2", 250, "BATTERY")
        results, days = process([first, second], {"SRC-01": source()}, RATES)
        self.assertEqual(results[0].pickup_date, date(2026, 10, 2))
        self.assertEqual(results[1].pickup_date, date(2026, 10, 3))
        self.assertEqual(days[date(2026, 10, 2)].hazardous_kg, Decimal("90"))

    def test_stop_limit_moves_ninth_request_to_next_day(self):
        requests = [make_request(f"R{i}", 5) for i in range(1, 10)]
        results, days = process(requests, {"SRC-01": source()}, RATES)
        self.assertEqual(len(days[date(2026, 10, 2)].request_ids), 8)
        self.assertEqual(results[8].pickup_date, date(2026, 10, 3))

    def test_sunday_is_skipped(self):
        saturday = make_request("R1", 5, day=date(2026, 10, 3))
        result = schedule_one(saturday, source(), RATES, {})
        self.assertEqual(result.pickup_date, date(2026, 10, 5))


if __name__ == "__main__":
    unittest.main()
