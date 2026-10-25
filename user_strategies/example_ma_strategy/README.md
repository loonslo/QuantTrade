# 示例移动平均策略

这是一个基于移动平均线和RSI指标的示例交易策略，演示如何在QuantTradeSys系统中实现自定义策略。

## 策略概述

### 策略逻辑
- **移动平均策略**: 当价格在SMA均线上方时产生买入信号，在均线下方时产生卖出信号
- **RSI策略**: 当RSI低于30时产生买入信号，高于70时产生卖出信号
- **信号强度**: RSI信号强度为0.9，移动平均信号强度为0.8

### 技术指标
- **SMA (简单移动平均)**: 默认周期20
- **EMA (指数移动平均)**: 默认周期20  
- **RSI (相对强弱指数)**: 默认周期14

## 文件结构

```
example_ma_strategy/
├── strategy.py          # 策略实现文件
├── config.json          # 策略配置文件
├── run_strategy.py      # 策略运行脚本
├── README.md           # 说明文档
└── logs/               # 日志目录
```

## 配置参数

### 策略参数
```json
{
  "sma_period": 20,           // SMA周期
  "ema_period": 20,           // EMA周期
  "rsi_period": 14,           // RSI周期
  "rsi_oversold": 30,         // RSI超卖阈值
  "rsi_overbought": 70,       // RSI超买阈值
  "position_size": 0.1,       // 仓位大小比例
  "enable_signal_logging": true  // 启用信号日志
}
```

### 回测配置
```json
{
  "start_date": "2023-01-01",    // 回测开始日期
  "end_date": "2023-12-31",      // 回测结束日期
  "symbols": ["BTC/USDT"],        // 交易对
  "timeframe": "1h",              // 时间周期
  "initial_capital": 10000.0,     // 初始资金
  "commission": 0.001             // 手续费率
}
```

## 使用方法

### 1. 直接运行策略

```bash
cd user_strategies/example_ma_strategy
python run_strategy.py
```

### 2. 在代码中使用

```python
from user_strategies.example_ma_strategy.strategy import ExampleMAStrategy
from core.strategy_interface import StrategyContext

# 创建策略实例
strategy = ExampleMAStrategy(
    name="my_ma_strategy",
    params={
        'sma_period': 20,
        'rsi_period': 14,
        'position_size': 0.1
    }
)

# 创建策略上下文
context = StrategyContext(
    initial_cash=10000.0,
    symbol="BTC/USDT"
)

# 初始化策略
strategy.initialize(context)

# 处理K线数据
signal = strategy.on_bar(context, bar_data)
```

### 3. 自定义参数

```python
# 自定义策略参数
custom_params = {
    'sma_period': 50,        # 使用50周期SMA
    'rsi_period': 21,        # 使用21周期RSI
    'rsi_oversold': 25,      # 更严格的超卖阈值
    'rsi_overbought': 75,    # 更严格的超买阈值
    'position_size': 0.05    # 更小的仓位
}

strategy = ExampleMAStrategy(params=custom_params)
```

## 策略特点

### 优点
- **简单易懂**: 基于经典技术指标，逻辑清晰
- **参数可调**: 所有指标参数都可以自定义
- **风险可控**: 支持仓位大小控制
- **日志完善**: 提供详细的信号和交易日志

### 注意事项
- **趋势市场**: 在趋势明显的市场中表现较好
- **震荡市场**: 在震荡市场中可能产生频繁交易
- **参数优化**: 建议根据具体市场调整参数
- **风险管理**: 建议结合止损和止盈机制

## 扩展建议

### 1. 添加止损止盈
```python
def _generate_signal(self, bar_data: Dict[str, Any], context: StrategyContext) -> Optional[Signal]:
    # 现有逻辑...
    
    # 添加止损逻辑
    if self._should_stop_loss(context, current_price):
        return Signal(
            symbol=context.symbol,
            signal_type='sell',
            price=current_price,
            datetime=current_time,
            strength=1.0
        )
```

### 2. 添加仓位管理
```python
from strategies.position.position_managers import FixedRatioPositionManager

# 使用仓位管理器
position_manager = FixedRatioPositionManager("ma_position", {'position_ratio': 0.1})
position_size = position_manager.calculate_position_size(context, signal)
```

### 3. 添加更多指标
```python
def _calculate_indicators(self, data: pd.DataFrame) -> None:
    # 现有指标...
    
    # 添加MACD
    macd_data = self._calculate_macd(data, 12, 26, 9)
    data['macd'] = macd_data['macd']
    data['macd_signal'] = macd_data['signal']
    data['macd_histogram'] = macd_data['histogram']
```

## 性能优化

### 1. 缓存计算结果
```python
def _calculate_indicators(self, data: pd.DataFrame) -> None:
    # 使用缓存避免重复计算
    if not hasattr(self, '_indicator_cache'):
        self._indicator_cache = {}
    
    cache_key = f"{len(data)}_{data.index[-1]}"
    if cache_key in self._indicator_cache:
        return self._indicator_cache[cache_key]
```

### 2. 向量化计算
```python
def _calculate_rsi_vectorized(self, data: pd.DataFrame, period: int) -> pd.Series:
    # 使用pandas向量化操作提高性能
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
```

## 故障排除

### 常见问题

1. **导入错误**
   ```
   ModuleNotFoundError: No module named 'strategies'
   ```
   解决方案: 确保项目根目录在Python路径中

2. **数据格式错误**
   ```
   KeyError: 'close'
   ```
   解决方案: 确保数据包含必要的OHLCV字段

3. **指标计算错误**
   ```
   ValueError: min_periods must be <= window
   ```
   解决方案: 确保数据长度足够计算指标

### 调试技巧

1. **启用详细日志**
   ```python
   strategy.params['enable_signal_logging'] = True
   ```

2. **检查数据质量**
   ```python
   print(f"数据长度: {len(data)}")
   print(f"数据列: {data.columns.tolist()}")
   print(f"缺失值: {data.isnull().sum()}")
   ```

3. **验证信号生成**
   ```python
   signal = strategy._generate_signal(bar_data, context)
   if signal:
       print(f"信号: {signal.signal_type} 价格: {signal.price}")
   ```

## 版本历史

- **v1.0.0**: 初始版本，支持SMA和RSI策略
- **v1.1.0**: 添加EMA指标和参数验证
- **v1.2.0**: 改进信号生成逻辑和错误处理

## 贡献指南

欢迎提交Issue和Pull Request来改进这个策略：

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。 