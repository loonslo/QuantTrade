# Consolidation acceptance record

Actual local verification date: **2026-10-25**, Asia/Shanghai.

## Environment and scope

- Windows x64, CPython **3.14.0**, project-local virtual environment.
- Dependencies installed and synchronized from `requirements.lock`: 72 packages; dependency consistency check passed.
- Input: 600 deterministic synthetic hourly OHLCV bars in `examples/sample_ohlcv.csv`.
- Exchange requests in tests are replaced by test doubles or explicitly rejected. No real account order was submitted. The initial inherited test run exposed ineffective mocks; these were repaired before final validation.

## Verified results

| Check | Actual result |
| --- | --- |
| `python -m pytest -q --disable-warnings` | **97 passed**, 62 inherited/dependency deprecation warnings; no failed/skipped tests |
| `python scripts/check_source.py` | **336 tracked Python files parsed successfully** |
| `python scripts/check_publication.py` | Current Git snapshot passed runtime-file and embedded-credential pattern checks |
| `python -m pip check` | Installed dependency versions are consistent |
| Targeted Ruff `F821,F811,F401` | Shared entry points, execution, adapter, publication scripts and integration tests passed |
| Ten registered strategy cases | Each runs offline and returns finite JSON on the synthetic fixture |
| CLI/API parity | Identical result for the same bars, symbol, timeframe and defaults |
| Execution/accounting | MA entry occurs one bar after its signal; recorded trade cash matches broker cash; final equity matches recorded equity |
| Input failures and no trades | Invalid bars/unknown strategy are rejected; short warm-up-only data returns finite zero-trade results |
| API lifecycle | Health, OpenAPI and research endpoints work; database/jobs do not initialize at app construction |
| Fresh SQLite | Tables created in a disposable database; repeated application startup succeeds |
| Paper adapter | Buy/sell/reset, pending/cancelled limit orders and rejected quantities validated without an exchange client |
| Exchange adapter doubles | Explicit sandbox choice, submitted market order and partial-fill metadata validated using mocks |
| Legacy compatibility | CCXT dictionary metadata and real-account summary path validated without the missing paper trader |

The existing public repository and the reviewed Sys source were backed up before consolidation. Databases, Excel outputs, caches and IDE state are excluded from the final source snapshot. Embedded development credential literals and configuration dumps were removed. This is a current-snapshot check, not a claim that the historical public Git history contains no credentials.

## Not verified / not accepted

- Real Binance data access, exchange sandbox or live order execution, order precision/minimums, reconnect behavior, partial-fill restart recovery, or production account reconciliation.
- Scheduled external synchronization, optional LLM/news integrations, and the full advanced portfolio/optimization service paths.
- Standard KAMA/KDJ numerical correctness: inherited Sys approximations remain explicitly documented.
- Profitability, real historical performance, or suitability for real-money trading. The fixture is synthetic.
- Production deployment, authentication boundaries for an externally exposed API, and migration of personal runtime databases.

Windows/Linux CI is configured in `.github/workflows/ci.yml`. Its remote results and publication outcome are recorded below after the GitHub run; local validation alone does not establish Linux acceptance.

## Publication

Prepared for the existing public `loonslo/QuantTrade` repository using a reviewed source-snapshot commit on top of its existing history. Publication and remote CI verification are pending at this record's initial creation.
