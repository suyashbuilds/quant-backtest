import pytest

from execution import Order, OrderSide, OrderType, OrderStatus


def test_valid_buy_order():
    order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=10)

    assert order.symbol == "AAPL"
    assert order.side == OrderSide.BUY
    assert order.quantity == 10
    assert order.order_type == OrderType.MARKET
    assert order.status == OrderStatus.CREATED


def test_valid_sell_order():
    order = Order(symbol="MSFT", side=OrderSide.SELL, quantity=5)

    assert order.symbol == "MSFT"
    assert order.side == OrderSide.SELL
    assert order.quantity == 5
    assert order.status == OrderStatus.CREATED


def test_default_order_type_and_status():
    order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    assert order.order_type is OrderType.MARKET
    assert order.status is OrderStatus.CREATED
    assert order.reject_reason is None


def test_zero_quantity_rejected():
    with pytest.raises(ValueError):
        Order(symbol="AAPL", side=OrderSide.BUY, quantity=0)


def test_negative_quantity_rejected():
    with pytest.raises(ValueError):
        Order(symbol="AAPL", side=OrderSide.BUY, quantity=-5)


def test_empty_symbol_rejected():
    with pytest.raises(ValueError):
        Order(symbol="", side=OrderSide.BUY, quantity=10)


def test_whitespace_only_symbol_rejected():
    with pytest.raises(ValueError):
        Order(symbol="   ", side=OrderSide.BUY, quantity=10)


def test_symbol_is_normalized():
    order = Order(symbol=" aapl ", side=OrderSide.BUY, quantity=10)
    assert order.symbol == "AAPL"


def test_side_must_be_enum():
    with pytest.raises(TypeError):
        Order(symbol="AAPL", side="BUY", quantity=10)


def test_order_type_must_be_enum():
    with pytest.raises(TypeError):
        Order(symbol="AAPL", side=OrderSide.BUY, quantity=10, order_type="MARKET")


def test_orders_get_unique_ids():
    order_a = Order(symbol="AAPL", side=OrderSide.BUY, quantity=1)
    order_b = Order(symbol="AAPL", side=OrderSide.BUY, quantity=1)
    assert order_a.id != order_b.id


def test_lifecycle_helpers():
    order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=10)

    order.mark_pending()
    assert order.status == OrderStatus.PENDING

    order.mark_filled()
    assert order.status == OrderStatus.FILLED


def test_lifecycle_reject_helper_records_reason():
    order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=10)
    order.mark_pending()
    order.mark_rejected("insufficient cash")

    assert order.status == OrderStatus.REJECTED
    assert order.reject_reason == "insufficient cash"