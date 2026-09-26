from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from execution.order import Order, OrderSide


@dataclass(frozen=True)
class Fill:
    """
    An immutable record of an order's actual execution.

    A Fill is created only when a Broker successfully executes an Order.
    It records what actually happened - not what was intended (that's
    Order's job) and not what it means for the portfolio (that's
    Portfolio/TradeLedger's job, in a later milestone).
    """

    order: Order
    quantity: int
    fill_price: float
    commission: float
    slippage: float
    timestamp: datetime

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"Fill quantity must be > 0, got {self.quantity}")
        if self.fill_price <= 0:
            raise ValueError(f"Fill price must be > 0, got {self.fill_price}")
        if self.commission < 0:
            raise ValueError(f"Commission cannot be negative, got {self.commission}")
        if self.slippage < 0:
            raise ValueError(f"Slippage cannot be negative, got {self.slippage}")

    @property
    def symbol(self) -> str:
        return self.order.symbol

    @property
    def side(self) -> OrderSide:
        return self.order.side

    @property
    def notional(self) -> float:
        """Gross value of the fill before commission (qty * price)."""
        return self.quantity * self.fill_price