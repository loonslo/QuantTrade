# QuantTrade consolidation record

Date: 2026-10-25. Target: the existing public `loonslo/QuantTrade` repository and its `main` branch. The owner authorized publication of the reviewed QuantTradeSys source in this repository. Keep existing stars, repository identity and public commit history.

## Source snapshots

- QuantTrade: `a3ef30daebd058930dd4a1ae68a0a405512d66d9` (main).
- QuantTradeSys: `d274294f6284ed8c77de16b0f9f2ab4a5da9d04c` (master).

Import a reviewed Sys working-tree snapshot without its private Git ancestry. The original QuantTrade checkout and Git bundle were backed up outside the repository before changes. No force push, repository replacement, database migration or history rewrite is required.

## Architecture and state boundaries

The Sys API/data/services/core/strategies/analytics structure is the baseline. Preserve original QuantTrade modules, secure configuration, key management, analysis and live scripts as compatibility tools. Save its original `main.py` as `cli_backtest.py`; expose the platform through `main.py api` and the shared offline engine through `main.py backtest`.

Backtest state belongs to a new Backtrader Cerebro instance per invocation. Record actual broker cash/equity on every bar. Signals generated at a close execute at the following open. End-of-data inventory remains open and is marked to market. Do not synthesize final fills or smooth the reported equity curve. API and CLI share validation, strategies, accounting and metrics.

Keep one canonical set of Sys strategy classes in the split individual modules; the former monolithic module now re-exports those classes. Preserve the old QuantTrade Pandas strategy functions as compatibility behavior; their old historical results are not declared equivalent to the new engine.

The API initializes the database during application lifespan, starts external jobs only when explicitly enabled, and shuts jobs down during lifespan cleanup. It does not automatically start live trading. Paper trading has isolated in-memory balances and explicit quote inputs; exchange sandbox and live modes are separate choices.

## Integration fixes

- Resolve two inherited syntax errors, missing extractor data type/imports and stale analytics exports.
- Repair split strategy logging compatibility, RSI zero division and Stochastic line names.
- Normalize trade extraction using Backtrader's actual `[size, price, data_id, symbol, value]` layout; remove BTC-specific price-range guessing.
- Make annualization configurable/inferable by bar interval; handle zero-volatility returns and JSON serialization of undefined profit factors.
- Complete the Binance TradingEngine interface, preserve order status and partial-fill quantities, reject invalid orders before mutation, and keep paper mode independent of exchange networking.
- Fix CCXT dictionary metadata reading and the missing-paper-trader access in the original live script. These fixes do not establish live-trading acceptance.
- Merge configuration exports and secret-variable aliases, remove embedded development credentials and configuration dumps, and repair ineffective test mocks/isolation.
- Use Python 3.14-compatible dependencies, a universal lock file, offline tests and Windows/Linux CI.

## Publication and data

Retain the Sys MIT license. Exclude IDE state, source caches, credentials and source runtime data from the imported snapshot. Stop tracking the original public database and Excel results; retain local recoverable files/backups. The old public history remains intact, so any genuinely exposed historical credential must be rotated at its provider; the snapshot guard is not a history audit.

`QUANTTRADE_TODO_HISTORY.md`, `SYS_TODO_HISTORY.md`, and the imported architectural/API reports are historical documents from the source snapshots. Their old completion claims and dates are not results of this merge. Current verification belongs only in `ACCEPTANCE.md`.

## Known boundaries

External market data, LLM/news providers, scheduled sync tasks, advanced optimization/portfolio service paths and genuine exchange account behavior have not been integration-tested here. KAMA and KDJ retain the Sys approximation semantics described in README. Full partial-fill recovery, durable reconciliation and trading risk controls remain follow-up work. No production deployment or real order is part of this merge.
