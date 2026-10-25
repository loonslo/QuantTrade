# QuantTradeSys TODO

> Quantitative Trading System with multi-exchange support.

## 🔴 High Priority

- [ ] Fix any remaining config.json / futures_config.json sensitivity issues (ensure no API keys hardcoded)
- [ ] Complete resolve of core/extractors.py vs core/extractors/ module conflict
- [ ] Add API key rotation and failover support
- [ ] Implement comprehensive error recovery for exchange API disconnections
- [ ] Add backtest validation suite for all strategies

## 🟡 Medium Priority

- [ ] Add WebSocket real-time price feed support for all exchanges
- [ ] Implement position sync across multiple exchanges
- [ ] Add performance monitoring (latency, slippage estimation)
- [ ] Strategy parameter optimization framework
- [ ] Risk dashboard (real-time P&L, drawdown alerts)
- [ ] Migrate from SQLite to PostgreSQL for production

## 🟢 Low Priority / Nice to Have

- [ ] Mobile notification integration (push alerts)
- [ ] Strategy combination / portfolio mode
- [ ] GUI dashboard for strategy management
- [ ] Historical data backfill automation
- [ ] Docker compose setup for full stack deployment
- [ ] Kubernetes deployment manifests

## ✅ Completed

- [x] FastAPI server with exchange API integration (Binance, OKX, Bybit) (2025)
- [x] Multi-exchange futures data sync (docs/futures_data_sync_optimization.md)
- [x] K-line data synchronization (docs/kline_data_sync_manual_guide.md)
- [x] Technical indicator implementations (docs/indicators_implementation_guide.md)
- [x] .env.example with all required environment variables (2026-01-13)
- [x] .gitignore: exclude .env, *.db, __pycache__/ (2026-01-13)
- [x] requirements.txt (2026-01-13)
- [x] core/extractors.py → core/extractor_legacy.py rename to resolve name conflict (2026-03-25)
- [x] Remove .bak/.bak2/.new residual files (2026-03-25)
- [x] Add SILICONFLOW_API_KEY env var support, remove hardcoded keys (2026-03-25)
