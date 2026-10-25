from unittest.mock import Mock, patch

import pytest

from core.trading import BinanceTrader, LiveTradingManager, OrderManager


def test_paper_trades_update_balances_without_client():
    trader = BinanceTrader({'paper_prices': {'BTC/USDT': 100}, 'initial_cash': 1000})
    assert trader._client is None
    buy = trader.buy('BTC/USDT', 2)
    assert buy['status'] == 'closed'
    assert trader.get_balance('USDT')['free'] == pytest.approx(799.8)
    assert trader.get_positions()[0]['quantity'] == 2
    trader.sell('BTC/USDT', 1)
    assert trader.get_balance('BTC')['total'] == 1
    trader.reset()
    assert trader.get_balance('USDT')['total'] == 1000
    assert trader.get_positions() == []


def test_limit_order_is_pending_until_explicitly_cancelled():
    trader = BinanceTrader({})
    order = trader.buy('BTC/USDT', 1, 100)
    assert trader.get_balance('USDT')['free'] == 10000
    assert trader.get_open_orders() == [order]
    assert trader.cancel_order('BTC/USDT', order['id'])
    assert trader.get_order('BTC/USDT', order['id'])['status'] == 'canceled'
    assert trader.get_open_orders() == []


@pytest.mark.parametrize('quantity', [0, -1, float('nan')])
def test_invalid_order_cannot_change_account(quantity):
    trader = BinanceTrader({'paper_prices': {'BTC/USDT': 100}})
    with pytest.raises(ValueError):
        trader.buy('BTC/USDT', quantity)
    assert trader.get_balance('USDT')['free'] == 10000


def test_rejected_paper_order_is_not_recorded_as_filled():
    trader = BinanceTrader({'paper_prices': {'BTC/USDT': 100}, 'initial_cash': 10})
    with pytest.raises(ValueError):
        trader.buy('BTC/USDT', 2)
    assert trader.get_positions() == []
    assert trader._paper_orders == {}


def test_order_manager_preserves_partial_exchange_fill():
    exchange = Mock()
    exchange.buy.return_value = {'id': 'mock-order', 'status': 'open', 'filled': 0.5, 'average': 100}
    order = OrderManager(exchange).create_order('BTC/USDT', 'buy', 1, order_type='market')
    assert order.order_id == 'mock-order'
    assert order.status == 'open'
    assert order.filled_quantity == 0.5


def test_live_adapter_uses_explicit_sandbox_and_forwards_order():
    with patch('ccxt.binance') as factory:
        trader = BinanceTrader({'test_mode': False, 'api_key': 'test_key',
                                'api_secret': 'test_secret', 'sandbox': True})
        trader.buy('BTC/USDT', 1)
        factory.return_value.set_sandbox_mode.assert_called_once_with(True)
        factory.return_value.create_order.assert_called_once_with('BTC/USDT', 'market', 'buy', 1, None)


def test_live_manager_satisfies_engine_contract_in_paper_mode():
    manager = LiveTradingManager({'paper_prices': {'BTC/USDT': 100}, 'symbols': ['BTC/USDT']})
    result = manager.buy('BTC/USDT', 1)
    assert result['success']
    manager.start()
    assert manager.get_positions()[0]['quantity'] == 1
    manager.reset()
    assert manager.get_positions() == []
