from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Line:
    description: str
    amount: Decimal
    currency: str  # ISO 4217 code, uppercase ("EUR")


@dataclass
class Invoice:
    number: str
    customer: str  # customer id, normalized for lookups
    currency: str  # ISO 4217 code, uppercase; what the customer is billed in
    lines: list = field(default_factory=list)
