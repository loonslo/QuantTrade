# QuantTrade tasks

## Repository consolidation — 2026-10-25

- [x] Preserve QuantTrade identity/history and import the reviewed Sys source snapshot.
- [x] Combine dependencies/configuration and exclude runtime/credential files.
- [x] Provide the shared offline API/CLI engine and canonical strategy class exports.
- [x] Verify ten strategies, fill accounting, input failures, zero-trade behavior and adapter test doubles.
- [x] Verify fresh SQLite initialization and repeated API startup without external jobs.
- [x] Preserve original tools and identify historical/approximate behavior explicitly.
- [x] Add publication/source guards, dependency lock and Windows/Linux CI configuration.
- [ ] Publish the reviewed change to QuantTrade main and verify remote checks.

## Follow-up acceptance

- [ ] Verify every market-data/scheduler provider in an authorized network environment.
- [ ] Review and validate advanced portfolio, optimization and optional LLM service paths.
- [ ] Replace/verify the inherited KAMA and KDJ indicator approximations.
- [ ] Consolidate the original Pandas/live compatibility path after behavioral comparison.
- [ ] Implement durable order/fill reconciliation, partial-fill restart recovery and idempotency.
- [ ] Apply consistent position/daily-loss risk controls to every live execution path.
- [ ] Perform exchange-sandbox acceptance before considering any live-money run.
- [ ] Modernize inherited Pydantic/SQLAlchemy deprecations and track Backtrader Python compatibility.

Original task lists are preserved with source attribution under `docs/consolidation/`; checked historical entries do not establish current acceptance.
