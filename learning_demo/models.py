"""Small data containers used by the learning demo."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Source:
    source_id: str
    source_name: str
    source_type: str
    area: str
    distance_km: Decimal


@dataclass(frozen=True)
class Rate:
    category: str
    credit_per_kg_rs: Decimal
    hazardous: bool


@dataclass(frozen=True)
class Item:
    category: str
    item_count: int
    weight_kg: Decimal


@dataclass(frozen=True)
class Request:
    request_id: str
    request_date: date
    source_id: str
    items: tuple[Item, ...]

    @property
    def total_kg(self) -> Decimal:
        return sum((item.weight_kg for item in self.items), Decimal("0"))


@dataclass
class VehicleDay:
    pickup_date: date
    request_ids: list[str] = field(default_factory=list)
    total_kg: Decimal = Decimal("0")
    hazardous_kg: Decimal = Decimal("0")


@dataclass(frozen=True)
class RequestResult:
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
    stop_no: int | None = None
    day_kg_after: Decimal | None = None
    day_hazardous_kg_after: Decimal | None = None
