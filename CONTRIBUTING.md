# Contributing to QuantTrade

Thank you for your interest in contributing to QuantTrade!

## Project Overview

QuantTrade is a quantitative trading system for BTC/ETH on Binance, supporting historical backtesting, real-time signals, live trading execution, and SQLite database management.

## How to Contribute

### Reporting Issues

Found a bug or have a feature request? Please open an issue with:
- Clear description of the problem or suggestion
- Steps to reproduce (for bugs)
- Your environment (OS, Python version)

### Pull Requests

1. **Fork the repository** and create a feature branch from `main`.
2. **Write tests** for any new functionality.
3. **Follow existing code style** — this project uses Python 3.
4. **Test your changes** before committing.
5. **Commit with a clear message** describing what you changed and why.
6. **Open a PR** against `main`.

### Code Style

- Use meaningful variable and function names
- Add docstrings for public functions and classes
- Handle errors explicitly — don't silently swallow exceptions
- Keep functions focused and small

### Adding New Strategies

To add a new strategy:
1. Create a new file in `modules/` (e.g., `modules/new_strategy.py`).
2. Implement the strategy interface compatible with `modules/strategy.py`.
3. Add tests in `tests/`.
4. Update `modules/__init__.py` if needed.

### Key Files

- `live_trading.py` — Real trading execution (use with caution, involves real funds)
- `demo_trading.py` — Trading function demonstration (no real orders)
- `backtest.py` — Historical backtesting framework
- `key_manager.py` — API key management (keys stored encrypted, never in plain text)

### Environment Variables

See `env_example.txt` for required environment variables. Never commit API keys.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
