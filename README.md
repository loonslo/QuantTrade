# QuantTrade 量化交易系统

基于币安API的BTC/ETH量化分析系统，支持历史回测、实时信号提示和**实际交易执行**。

## 项目结构

```
QuantTrade/
├── main.py              # 主程序入口
├── live_trading.py      # 实时交易执行
├── demo_trading.py      # 交易功能演示
├── test_commission.py   # 手续费分析
├── config.py            # 配置文件管理
├── key_manager.py       # 密钥管理工具
├── env_example.txt      # 环境变量示例
├── modules/             # 功能模块
│   ├── data.py         # 数据获取与处理
│   ├── strategy.py     # 策略实现
│   ├── backtest.py     # 回测框架
│   ├── position_manager.py # 仓位管理
│   ├── trader.py       # 实际交易执行
│   ├── signal.py       # 信号推送
│   └── plot.py         # 可视化
├── charts/             # 图表输出目录
├── backtest_results.xlsx # 回测结果记录
└── README.md           # 项目说明
```

## 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或者单独安装核心依赖
pip install ccxt pandas numpy matplotlib websockets cryptography openpyxl
```

## 配置说明

### 1. 环境变量配置（推荐）

复制 `env_example.txt` 为 `.env` 文件，并填入你的API密钥：

```bash
# 主网API密钥
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET=your_secret_here

# 环境设置
ENVIRONMENT=development  # development, test, production
```

### 2. 加密配置（更安全）

使用密钥管理工具安全保存API密钥：

```bash
# 交互式保存API密钥（加密存储）
python key_manager.py save

# 验证API密钥
python key_manager.py validate

# 查看密钥状态
python key_manager.py status

# 清除保存的密钥
python key_manager.py clear
```

### 3. 代理配置

如果使用代理，在 `.env` 文件中设置：

```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

## 使用方法

### 1. 基础回测

```python
python main.py
```

### 2. 实时交易执行

```python
# 启动实时交易（测试模式）
python live_trading.py

# 或直接运行演示
python demo_trading.py
```

### 3. 手续费分析

```python
# 分析各种策略的手续费成本
python test_commission.py
```

### 4. 切换环境

在代码中修改环境配置：

```python
from config import Config

# 开发环境
config = Config(env='development')

# 测试网环境
config = Config(env='test')

# 生产环境
config = Config(env='production')
```

## 功能特性

### 🔄 回测系统
- ✅ 多策略支持（均线交叉、RSI、布林带、MACD等）
- ✅ 仓位管理（固定比例、金字塔加仓、倒金字塔减仓）
- ✅ 手续费计算
- ✅ 详细统计报告
- ✅ Excel结果导出

### 🚀 实际交易
- ✅ **实时交易执行**
- ✅ **订单管理**（市价单、限价单）
- ✅ **风险管理**（仓位限制、日亏损限制）
- ✅ **持仓跟踪**（实时盈亏计算）
- ✅ **账户管理**（余额、持仓、交易历史）

### 📊 策略库
- ✅ 趋势策略：均线交叉、MACD、动量
- ✅ 震荡策略：RSI、KDJ、均值回归
- ✅ 突破策略：布林带、海龟交易
- ✅ 自适应策略：KAMA
- ✅ **信号预测**（下一个买入/卖出触发价格）

### 📈 可视化
- ✅ K线图 + 交易信号
- ✅ 权益曲线
- ✅ 交易分析图表
- ✅ 自动保存到charts目录

### 🔐 安全特性
- 🔐 环境变量优先级
- 🔐 加密文件存储
- 🔐 密钥验证机制
- 🔐 交互式密钥管理
- 🔐 测试模式保护

## 交易功能详解

### 1. 实时交易系统

```python
from modules.trader import Trader, OrderSide
from modules.strategy import Strategy

# 创建交易器
trader = Trader(test_mode=True)  # 测试模式

# 市价买入
order = trader.place_market_order('BTC/USDT', OrderSide.BUY, 0.001)

# 限价卖出
order = trader.place_limit_order('BTC/USDT', OrderSide.SELL, 0.001, 50000)

# 查看账户状态
trader.print_account_summary()
```

### 2. 风险管理

```python
# 自动风险控制
- 最大仓位限制（默认10%）
- 日亏损限制（默认5%）
- 余额检查
- 持仓检查
```

### 3. 策略交易

```python
# 自动执行策略信号
python live_trading.py

# 配置参数
symbol = 'BTC/USDT'
strategy_func = Strategy.mean_reversion
check_interval = 60  # 检查间隔（秒）
```

## 注意事项

1. **API密钥安全**：
   - 🔐 使用环境变量或加密存储，避免硬编码
   - 🔐 定期更换API密钥
   - 🔐 设置API密钥的IP白名单
   - 🔐 仅授予必要的权限

2. **实盘交易风险**：
   - ⚠️ **强烈建议先在测试模式验证策略**
   - ⚠️ 实盘交易前请充分测试
   - ⚠️ 设置合理的风险控制参数
   - ⚠️ 监控交易执行情况

3. **网络环境**：国内用户可能需要配置代理才能访问币安API

4. **API限频**：注意币安API调用频率限制，避免被封禁

5. **文件安全**：确保 `.env`、`.encrypted_config`、`.secret_key` 等敏感文件不被提交到版本控制系统

## 开发计划

- [ ] 更多技术指标
- [ ] 机器学习策略
- [ ] 高级风险管理
- [ ] 多交易所支持
- [ ] Web界面
- [ ] 移动端推送
- [ ] 策略组合优化 