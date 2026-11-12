"""Typed records for the actual project processing stage."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Source:
    source_id: str
    source_type: str
    distance_km: Decimal
    source_name: str = ""
    area: str = ""


@dataclass(frozen=True)
class Rate:
    category: str
    credit_per_kg_rs: Decimal
    hazardous: bool


@dataclass(frozen=True)
class Item:
    category: str
    weight_kg: Decimal


@dataclass(frozen=True)
class Request:
    request_id: str
    request_date: date
    source_id: str
    items: tuple[Item, ...]

    @property
    def total_kg(self):
        return sum((item.weight_kg for item in self.items), Decimal("0"))


@dataclass
class VehicleDay:
    pickup_date: date
    request_ids: list[str] = field(default_factory=list)
    total_kg: Decimal = Decimal("0")
    hazardous_kg: Decimal = Decimal("0")


@dataclass(frozen=True)
class Result:
    request: Request
    status: str
    reason: str
    hazardous_kg: Decimal
    credit_rs: Decimal | None = None
    deduction_rs: Decimal | None = None
    pickup_charge_rs: Decimal | None = None
    net_rs: int | None = None
    net_type: str = "NONE"
    pickup_date: date | None = None

