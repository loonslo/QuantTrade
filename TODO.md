# QuantTrade TODO

> Binance API-based BTC/ETH quantitative trading system.

## 🔴 High Priority

- [ ] Merge or clearly distinguish `live_trading.py` and `demo_trading.py`
- [ ] Implement API key IP whitelist check on startup
- [ ] Add comprehensive order fill tracking (partial fills)
- [ ] Implement trading halt detection and safe shutdown
- [ ] Add database backup/restore mechanism

## 🟡 Medium Priority

- [ ] Migrate from SQLite to PostgreSQL for production deployment
- [ ] Add more technical indicators (MACD, KDJ, ATR)
- [ ] Machine learning-based strategy (predict price direction)
- [ ] Advanced risk management (VaR, Kelly criterion)
- [ ] Multi-exchange support (add OKX, Bybit)
- [ ] Web UI dashboard for strategy management
- [ ] Real-time WebSocket data feed (Binance streams)
- [ ] Automated report generation (daily/weekly P&L email)

## 🟢 Low Priority / Nice to Have

- [ ] Strategy combination optimizer
- [ ] Paper trading mode with full exchange simulation
- [ ] Mobile push notifications for trade alerts
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests

## ✅ Completed

- [x] Basic backtesting system (main.py) (2024)
- [x] Real-time trading execution (live_trading.py) (2024)
- [x] Binance API integration (ccxt) (2024)
- [x] SQLite database (market_data, trading_signals, trade_records, backtest_results) (2024)
- [x] Risk management (max position 10%, daily loss limit 5%) (2024)
- [x] Visualization (K-line charts, equity curve, trade markers) (2024)
- [x] Encrypted config storage (key_manager.py) (2024)
- [x] API key environment variable support (ALPHA_VANTAGE_API_KEY) (2026-03-25)
- [x] .gitignore: exclude *.xlsx, *.db, .env, __pycache__/ (2026-03-25)
- [x] Unit tests: test_key_manager, test_secure_config, test_trading_config (653 lines) (2026-03-25)
- [x] Commission analysis tool (test_commission.py) (2026-03-25)
