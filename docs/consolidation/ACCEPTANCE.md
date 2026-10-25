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

Windows/Linux CI is configured in `.github/workflows/ci.yml`. Both remote jobs passed: each parsed 336 Python files, passed the publication guard and completed 97 tests (62 deprecation warnings). Ubuntu completed its tests in 10.22 seconds; Windows in 18.20 seconds. These results are from the reviewed source revision, not inferred from local validation.

## Publication

Published to the existing public `loonslo/QuantTrade` main branch through [PR #1](https://github.com/loonslo/QuantTrade/pull/1), merged **2026-10-25 17:54:32 Asia/Shanghai**. Source revision: `ace017834e474b2189232aff42a502e74fee1948`; merge commit: `3f677fab4021069642a311b744b01bfd57e5a349`.

The [PR validation run](https://github.com/loonslo/QuantTrade/actions/runs/40182383594) and source-branch push run both passed on Windows and Linux before merge. The first source commit has the original QuantTrade head as its sole parent, preserving the public history without importing private Sys ancestry. Repository visibility and default branch were verified as PUBLIC/main; its existing 7 stars remained present.

This follow-up publication record updates documentation/status only; application code is unchanged from the validated revision. No production deployment or real trading acceptance is implied.
