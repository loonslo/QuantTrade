# QuantTrade

以 QuantTradeSys 分层架构为基础的量化研究与行情服务项目，统一维护在 **loonslo/QuantTrade**。原 QuantTrade 的仓库地址、stars、issues 和公开提交历史保持连续。

当前已验证：Python 3.14 安装、十种内置策略离线执行、命令行与 API 回测结果一致、SQLite 新库及重复启动、模拟交易和交易所接口替身测试。真实行情同步、第三方 LLM 与真实资金交易尚未验收。

## 快速开始

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.lock
python main.py backtest --csv examples/sample_ohlcv.csv --output tmp/backtest.json
python main.py api
```

浏览器打开 http://127.0.0.1:8000/docs；健康检查为 `/health`。也可使用：

```bash
python run_server.py --port 8000
python -m uvicorn api.app:create_app --factory --host 127.0.0.1 --port 8000
```

`examples/sample_ohlcv.csv` 是确定性合成数据，仅用于复现软件行为，不是历史行情或收益证明。离线回测不需要 API Key，也不会连接交易所。

## 回测

```bash
python main.py backtest --csv examples/sample_ohlcv.csv --strategy ma_cross --params '{"short_window":5,"long_window":20}'
```

PowerShell 对 JSON 参数的引号处理可能随版本变化；默认参数无需 `--params`。
CSV 列为 `timestamp,open,high,low,close,volume`，时间必须递增且不重复，建议显式标注 UTC。无时区时间按 UTC 解释。

- 策略唯一类实现位于 `strategies/bt_strategies/individual/`，注册入口为 `strategies/registry.py`。
- 市价指令在下一根 K 线开盘成交；包含手续费及可选滑点。期末未平仓头寸按最后收盘价计入权益。
- 默认 `fixed_ratio` 仓位，保留现金应对下一根价格变化。`all_in` 在向上跳空时可能因资金不足被 Backtrader 拒单。
- 收益率、回撤与胜率使用小数；`profit_factor=null` 表示无亏损样本，不能给出有限比值。
- 默认按连续交易的实际时间间隔计算年化因子；非连续交易市场请显式传入 `--periods-per-year`。
- 兼容旧结果字段 `final_cash`，其含义是期末总权益；新代码优先读取 `final_equity`。

`GET /api/backtests/strategies` 列出策略；`POST /api/backtests` 接收 OHLCV bars 和策略参数，调用同一个离线引擎。请求样例和字段约束见交互式 API 文档。

## 模块

| 目录/入口 | 职责 |
| --- | --- |
| `api/` | FastAPI、行情查询、数据同步及离线回测接口 |
| `data/` | 数据提供器、SQLAlchemy 模型、存储与仓储 |
| `services/` | 数据同步、策略服务、风控及可选 LLM 集成 |
| `core/` | 回测执行、交易适配与组合接口 |
| `strategies/`、`analytics/` | 策略定义、仓位管理与分析 |
| `modules/`、`cli_backtest.py`、`live_trading.py` | 原 QuantTrade 兼容工具 |
| `config/secure.py`、`key_manager.py` | 原密钥管理工具与测试 |
| `tests/` | 默认运行的离线测试；外部交易所网络调用被禁止 |

`cli_backtest.py` 保留原 `main.py` 的用法；其 Pandas 策略和旧回测器作为历史兼容实现保留，新研究优先使用统一入口。未将旧数据库中的历史回测改写成新引擎结果。

## 配置与运行边界

从 `.env.example` 创建本机 `.env`，密钥仅放在本机环境变量或加密存储中。`BINANCE_SECRET` 为统一变量名，兼容 `BINANCE_SECRET_KEY`。

API 默认不启动外部行情调度。需要时显式执行 `python main.py api --scheduler`，或为应用工厂设置 `QUANTTRADE_ENABLE_SCHEDULER=1`。启动 API 不会启动交易策略或自动下单。

`core.trading.BinanceTrader` 默认是本地模拟模式：市价单使用显式 `paper_prices`，限价单仅记录为待处理，尚不提供订单簿撮合。真实模式必须显式设置 `test_mode=False` 并提供本机凭据；交易所测试网由独立的 `sandbox` 控制。真实模式仅有替身测试，尚未完成真实环境验收。

原 `live_trading.py` 保留兼容，不代表生产级交易闭环；部分成交恢复、持久化对账和完整风控仍在 [TODO.md](TODO.md)。KAMA 内置实现仍为原 Sys 的 SMA 近似，KDJ 使用 Stochastic 近似，不能视为已校验的标准指标实现。

旧运行数据库、Excel 结果和 IDE 文件不再跟踪。Sys 数据库默认为本机 `quant_trading.db`，旧工具使用 `quanttrade.db`；没有自动合并或覆盖个人运行数据。

## 开发与验收

```bash
python -m pip install -r requirements.lock
python -m pip check
python scripts/check_source.py
python scripts/check_publication.py
python -m pytest -q
```

发布检查针对当前 Git 索引，不代替全历史凭据审计。历史代码曾包含嵌入式凭据样式字串，本次已移除；如对应真实密钥，应在服务端轮换。

合并来源、取舍和范围见 [合并记录](docs/consolidation/MERGE_PLAN.md)，本次验证及未验证项见 [验收记录](docs/consolidation/ACCEPTANCE.md)。原 Sys 的其他文档按历史参考保留，不能作为本次复测证据。

## License

MIT，保留 QuantTradeSys 原许可与版权声明，见 [LICENSE](LICENSE)。
