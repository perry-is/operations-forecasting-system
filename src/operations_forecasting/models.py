"""Immutable input records; quantities and costs use Decimal."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Item:
    item_id: str
    description: str
    category: str
    current_on_hand: Decimal
    allocated_quantity: Decimal
    minimum_stock: Decimal
    target_stock: Decimal
    supplier_lead_time_days: int | None
    unit_cost: Decimal | None
    criticality: str
    last_updated: date


@dataclass(frozen=True)
class Usage:
    item_id: str
    month: date
    quantity: Decimal


@dataclass(frozen=True)
class PurchaseOrder:
    po_reference: str
    item_id: str
    quantity: Decimal
    expected_receipt_date: date | None
    status: str


@dataclass(frozen=True)
class Scenario:
    name: str = "BASELINE"
    demand_multiplier: Decimal = Decimal("1")
    lead_time_extra_days: int = 0
    inbound_delay_days: int = 0

    def __post_init__(self):
        if not self.demand_multiplier.is_finite() or self.demand_multiplier < 0:
            raise ValueError("Scenario demand multiplier must be finite and nonnegative")
        if self.lead_time_extra_days < 0 or self.inbound_delay_days < 0:
            raise ValueError("Scenario delays must be nonnegative")


@dataclass(frozen=True)
class DataSet:
    items: tuple[Item, ...]
    usage: tuple[Usage, ...]
    purchase_orders: tuple[PurchaseOrder, ...]
