# Contributing to QuantTrade

Use Python 3.14 and the dependencies in `requirements.lock`. Develop on a branch and open a pull request against `main`.

The Sys-based implementation is the platform baseline. New strategies belong in `strategies/bt_strategies/individual/` and must be registered through `strategies/registry.py`. Both CLI and API must call `core.backtrader_runner.run_backtrader_backtest`. Keep `modules/` as a compatibility layer; do not add another execution pipeline there.

Validate changes with `python scripts/check_source.py`, `python scripts/check_publication.py`, and `python -m pytest -q`. Default tests must not access exchanges or external services; use test doubles. Synthetic market data belongs in `examples/` and must be labeled as synthetic.

Never commit credentials, local environments, databases, logs, or private execution data. Import reviewed source snapshots with provenance. Preserve the original MIT license.

Update `TODO.md`, the acceptance record, and then `PROJECT_STATUS.md` for substantive progress, following `AGENTS.md`. A passing unit test does not establish production or live-trading acceptance.
