from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from core.backtrader_runner import run_backtrader_backtest
from live_trading import LiveTrader, _order_value


@pytest.fixture
def sample():
    return pd.read_csv(Path(__file__).parents[1] / 'examples/sample_ohlcv.csv')


def test_api_and_cli_engine_return_identical_results(sample):
    frame = sample.copy()
    frame['timestamp'] = pd.to_datetime(frame.timestamp, utc=True)
    expected = run_backtrader_backtest(strategy_name='ma_cross', data=frame.set_index('timestamp'))
    with TestClient(create_app(initialize_database=False)) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/openapi.json').status_code == 200
        response = client.post('/api/backtests', json={'bars': sample.to_dict('records')})
        assert response.status_code == 200, response.text
        actual = response.json()['data']
        assert actual == expected
        assert len(client.get('/api/backtests/strategies').json()['data']) == 10


def test_invalid_api_data_and_unknown_strategy_return_422(sample):
    with TestClient(create_app(initialize_database=False)) as client:
        assert client.post('/api/backtests', json={'bars': []}).status_code == 422
        response = client.post('/api/backtests', json={
            'strategy_name': 'missing', 'bars': sample.iloc[:2].to_dict('records')})
        assert response.status_code == 422


def test_api_construction_does_not_start_scheduler_or_initialize_db(monkeypatch):
    from api.app import QuantTradeAPI
    initialize = Mock()
    start = Mock()
    monkeypatch.setattr(QuantTradeAPI, '_init_database_tables', initialize)
    monkeypatch.setattr(QuantTradeAPI, '_start_scheduler_service', start)
    app = create_app()
    initialize.assert_not_called()
    start.assert_not_called()
    with TestClient(app):
        initialize.assert_called_once()
        start.assert_not_called()


def test_live_summary_does_not_access_missing_paper_trader():
    trader = LiveTrader.__new__(LiveTrader)
    trader.test_mode = False
    trader.trader = None
    trader.symbol = 'BTC/USDT'
    trader.positions = {'BTC/USDT': {'entry_price': 90}}
    trader.account = Mock()
    trader.account.get_balance.side_effect = lambda asset: {'USDT': 100, 'BTC': 2}[asset]
    summary = trader._account_summary(100)
    assert summary['total_balance'] == 300
    assert summary['positions']['BTC/USDT'].avg_price == 90


def test_ccxt_order_metadata_is_preserved():
    order = {'id': 'mock-order', 'status': 'open', 'fee': {'cost': 0.1}}
    assert _order_value(order, 'id') == 'mock-order'
    assert _order_value(order, 'status') == 'open'
    assert _order_value(order, 'commission') == 0.1
