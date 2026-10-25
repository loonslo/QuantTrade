"""Exercise the shared Sys execution path without exchange access."""

import json
from pathlib import Path

import pandas as pd
import pytest

from core.backtrader_runner import run_backtrader_backtest, validate_market_data
from strategies.registry import STRATEGY_CLASSES


@pytest.fixture
def bars():
    path = Path(__file__).parents[1] / 'examples/sample_ohlcv.csv'
    frame = pd.read_csv(path)
    frame['timestamp'] = pd.to_datetime(frame.timestamp, utc=True)
    return frame.set_index('timestamp')


@pytest.mark.parametrize('name', sorted(STRATEGY_CLASSES))
def test_all_registered_strategies_execute_offline(name, bars):
    result = run_backtrader_backtest(strategy_name=name, data=bars)
    assert len(result['equity_curve']) == len(bars)
    assert result['final_equity'] > 0
    assert result['periods_per_year'] == pytest.approx(365.25 * 24)
    json.dumps(result, allow_nan=False)


def test_ma_execution_and_transaction_accounting(bars):
    result = run_backtrader_backtest(strategy_name='ma_cross', data=bars)
    assert result['performance']['total_trades'] > 0
    assert result['trades']
    assert result['trades'][-1]['cash_after'] == pytest.approx(result['equity_curve'][-1]['cash'])
    assert result['final_equity'] == pytest.approx(result['equity_curve'][-1]['total_value'])
    from modules.strategy import Strategy
    signals = Strategy.ma_cross(bars.copy())
    buy_signal_times = signals.index[signals == 1]
    first_buy = pd.Timestamp(result['trades'][0]['datetime']).tz_localize('UTC')
    assert first_buy == buy_signal_times[0] + pd.Timedelta(hours=1)


@pytest.mark.parametrize('bad', ['duplicates', 'reversed', 'nan', 'range'])
def test_invalid_bars_are_rejected(bars, bad):
    if bad == 'duplicates':
        bars = pd.concat([bars.iloc[:2], bars.iloc[1:]])
    elif bad == 'reversed':
        bars = bars.iloc[::-1]
    elif bad == 'nan':
        bars.iloc[0, 0] = float('nan')
    else:
        bars.iloc[0, bars.columns.get_loc('high')] = 1
    with pytest.raises(ValueError):
        validate_market_data(bars)


def test_no_trade_short_dataset_has_finite_metrics(bars):
    result = run_backtrader_backtest(strategy_name='ma_cross', data=bars.iloc[:3])
    assert result['trades'] == []
    assert result['performance']['sharpe_ratio'] == 0
    assert result['final_equity'] == 10000


def test_backtest_rejects_unknown_strategy_before_data_access():
    with pytest.raises(ValueError, match='Unknown strategy'):
        run_backtrader_backtest(strategy_name='missing')
