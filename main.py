"""QuantTrade public entry point. No services or exchange access run on import."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='QuantTrade research and market-data platform')
    commands = parser.add_subparsers(dest='command', required=True)
    api = commands.add_parser('api', help='Start the Sys-based API')
    api.add_argument('--host', default='127.0.0.1')
    api.add_argument('--port', type=int, default=8000)
    api.add_argument('--scheduler', action='store_true', help='Enable external market-data sync jobs')
    backtest = commands.add_parser('backtest', help='Run an offline CSV backtest')
    backtest.add_argument('--csv', type=Path, required=True)
    backtest.add_argument('--strategy', default='ma_cross')
    backtest.add_argument('--position', default='fixed_ratio')
    backtest.add_argument('--symbol', default='BTC/USDT')
    backtest.add_argument('--timeframe', default='1h')
    backtest.add_argument('--cash', type=float, default=10000)
    backtest.add_argument('--commission', type=float, default=0.001)
    backtest.add_argument('--slippage', type=float, default=0)
    backtest.add_argument('--params', default='{}', help='Strategy parameters as a JSON object')
    backtest.add_argument('--periods-per-year', type=float)
    backtest.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'api':
        import uvicorn
        from api.app import create_app

        uvicorn.run(create_app(enable_scheduler=args.scheduler), host=args.host, port=args.port)
        return 0

    import pandas as pd
    from core.backtrader_runner import run_backtrader_backtest

    try:
        frame = pd.read_csv(args.csv)
        frame['timestamp'] = pd.to_datetime(frame['timestamp'], utc=True)
        frame = frame.set_index('timestamp')
        params = json.loads(args.params)
        if not isinstance(params, dict):
            raise ValueError('--params must be a JSON object')
        with contextlib.redirect_stdout(sys.stderr):
            result = run_backtrader_backtest(
                strategy_name=args.strategy, position_type=args.position, symbol=args.symbol,
                timeframe=args.timeframe, start_cash=args.cash, commission=args.commission,
                slippage=args.slippage, strategy_params=params, data=frame,
                periods_per_year=args.periods_per_year,
            )
        rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + '\n', encoding='utf-8')
        else:
            print(rendered)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f'Backtest failed: {exc}\n')
    return 0


def __getattr__(name: str):
    if name == 'app':  # Compatibility with uvicorn main:app.
        from api.app import create_app
        return create_app()
    raise AttributeError(name)


if __name__ == '__main__':
    raise SystemExit(main())
