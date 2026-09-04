"""

Domain model for a trading order.

An Order represents a *request* to buy or sell a quantity of a symbol —
never an executed trade. Execution (turning an Order into a Fill, at a
specific price and cost) is the responsibility of the future Broker
component and is deliberately NOT implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from itertools import count
from typing import Optional


class OrderSide(Enum):
    """Direction of an order: buy to open/increase, sell to reduce/close."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """
    Order type. Only MARKET is supported in the current MVP.

    LIMIT / STOP / STOP_LIMIT and other conditional order types are
    deliberately out of scope until the "Advanced Order Types" phase
    of the roadmap.
    """
    MARKET = "MARKET"


class OrderStatus(Enum):
    """
    Lifecycle status of an order.

    CREATED   -> just constructed, not yet queued by the engine
    PENDING   -> queued by the engine, waiting for the next bar's open
    FILLED    -> executed by the Broker (future milestone)
    REJECTED  -> the Broker declined to execute it (future milestone)
    CANCELLED -> reserved for future order types (limit/stop); unused by
                 MVP market orders, which are always attempted on the very
                 next bar and never sit around waiting to be cancelled.
    """
    CREATED = "CREATED"
    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


_id_counter = count(1)


def _next_order_id() -> int:
    """Simple auto-incrementing id generator, private to this module."""
    return next(_id_counter)


@dataclass
class Order:
    """
    A request to buy or sell a quantity of a symbol.

    An Order is an *intention*, not an executed trade. It carries no
    execution price, no commission, and no P&L — those only exist once
    a (future) Broker turns this Order into a Fill. Keeping that boundary
    strict is what lets Strategy, Broker, and Portfolio stay independently
    testable.

    Fields:
        symbol: the ticker this order applies to. Must be non-empty.
        side: BUY or SELL.
        quantity: number of shares/units requested. Must be > 0.
        order_type: MARKET only for the MVP.
        status: lifecycle status, defaults to CREATED.
        created_at: timestamp the order was constructed (or, once wired
            into the engine, the timestamp of the bar the strategy acted on).
        reject_reason: set by the Broker if the order is REJECTED. Left as
            None until then — this is metadata about the order's lifecycle,
            not an execution result, so it lives here rather than on a
            future Fill object.
        id: a simple auto-incrementing identifier, unique per process.
    """

    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType = OrderType.MARKET
    status: OrderStatus = OrderStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    reject_reason: Optional[str] = None
    id: int = field(default_factory=_next_order_id)

    def __post_init__(self) -> None:
        # --- symbol ---
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError(
                f"Order symbol must be a non-empty string, got {self.symbol!r}"
            )
        self.symbol = self.symbol.strip().upper()

        # --- quantity ---
        if not isinstance(self.quantity, int) or isinstance(self.quantity, bool):
            raise TypeError(
                f"Order quantity must be an int, got {type(self.quantity).__name__}"
            )
        if self.quantity <= 0:
            raise ValueError(f"Order quantity must be > 0, got {self.quantity}")

        # --- enum fields: must be the real enum, not a raw string ---
        if not isinstance(self.side, OrderSide):
            raise TypeError(
                f"Order side must be an OrderSide, got {type(self.side).__name__}"
            )
        if not isinstance(self.order_type, OrderType):
            raise TypeError(
                f"Order order_type must be an OrderType, got {type(self.order_type).__name__}"
            )
        if not isinstance(self.status, OrderStatus):
            raise TypeError(
                f"Order status must be an OrderStatus, got {type(self.status).__name__}"
            )

    # -- Small, deliberately trivial lifecycle helpers -----------------
    #
    # These do NOT contain broker logic (no fill price, no cash checks).
    # They exist only so calling code has a clear, named way to move an
    # order between states instead of setting `order.status = ...`
    # directly everywhere. The actual *decision* of when/whether to
    # transition (e.g. "insufficient cash -> reject") belongs to the
    # Broker, built in the next milestone.

    def mark_pending(self) -> None:
        """Mark a CREATED order as PENDING (queued by the engine)."""
        self.status = OrderStatus.PENDING

    def mark_filled(self) -> None:
        """Mark a PENDING order as FILLED. Fill details live on a Fill object."""
        self.status = OrderStatus.FILLED

    def mark_rejected(self, reason: str) -> None:
        """Mark a PENDING order as REJECTED, recording why."""
        self.status = OrderStatus.REJECTED
        self.reject_reason = reason

    def mark_cancelled(self) -> None:
        """Mark an order as CANCELLED. Unused by MVP market orders; reserved for later."""
        self.status = OrderStatus.CANCELLED

    def __repr__(self) -> str:
        return (
            f"Order(id={self.id}, symbol={self.symbol!r}, side={self.side.name}, "
            f"quantity={self.quantity}, order_type={self.order_type.name}, "
            f"status={self.status.name})"
        )