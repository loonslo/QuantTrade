# 简化策略框架使用指南

这个简化框架专注于核心交易逻辑，去除复杂的抽象层，让您专注于策略实现。

## 核心组件

### 1. SimpleStrategyBase
简化的策略基类，只需要实现一个方法：
```python
def generate_signal(self, data: pd.DataFrame, context: StrategyContext) -> Optional[Signal]:
    """生成交易信号"""
    pass
```

### 2. SimpleStrategyRunner
简化的策略运行器，提供简单的调用接口：
```python
signals = run_simple_strategy(strategy, data, symbol, initial_cash)
```

## 快速开始

### 1. 创建自定义策略

```python
from strategies.base.simple_strategy_base import SimpleStrategyBase
from core.strategy_interface import Signal, StrategyContext

class MyStrategy(SimpleStrategyBase):
    def __init__(self, name="my_strategy", params=None):
        default_params = {'period': 20}
        if params:
            default_params.update(params)
        super().__init__(name, default_params)
    
    def generate_signal(self, data: pd.DataFrame, context: StrategyContext) -> Optional[Signal]:
        # 您的策略逻辑
        current_price = data['close'].iloc[-1]
        sma = self.calculate_sma(data['close'], self.params['period']).iloc[-1]
        
        if current_price > sma:
            return self.create_signal(
                symbol=context.symbol,
                signal_type='buy',
                price=current_price,
                datetime=data['datetime'].iloc[-1],
                strength=0.8
            )
        return None
```

### 2. 运行策略

```python
from strategies.simple_strategy_runner import run_simple_strategy

# 创建策略实例
strategy = MyStrategy(params={'period': 20})

# 运行策略
signals = run_simple_strategy(
    strategy=strategy,
    data=your_data,  # DataFrame with OHLCV columns
    symbol="BTC/USDT",
    initial_cash=10000.0
)

# 查看结果
print(f"生成 {len(signals)} 个信号")
```

## 内置工具方法

### 技术指标计算
```python
# 简单移动平均
sma = self.calculate_sma(data['close'], period=20)

# 指数移动平均
ema = self.calculate_ema(data['close'], period=20)

# RSI指标
rsi = self.calculate_rsi(data['close'], period=14)
```

### 信号创建
```python
signal = self.create_signal(
    symbol="BTC/USDT",
    signal_type="buy",  # or "sell"
    price=50000.0,
    datetime=datetime.now(),
    strength=0.8  # 0-1之间的强度
)
```

### 数据验证
```python
if not self.validate_data(data):
    return None  # 数据无效
```

## 数据格式要求

您的数据DataFrame必须包含以下列：
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `datetime`: 时间戳（可选）

## 示例策略

### 移动平均策略
```python
def generate_signal(self, data: pd.DataFrame, context: StrategyContext) -> Optional[Signal]:
    if len(data) < self.params['period']:
        return None
    
    current_price = data['close'].iloc[-1]
    sma = self.calculate_sma(data['close'], self.params['period']).iloc[-1]
    
    if current_price > sma:
        return self.create_signal(
            symbol=context.symbol,
            signal_type='buy',
            price=current_price,
            datetime=data['datetime'].iloc[-1],
            strength=0.8
        )
    elif current_price < sma:
        return self.create_signal(
            symbol=context.symbol,
            signal_type='sell',
            price=current_price,
            datetime=data['datetime'].iloc[-1],
            strength=0.8
        )
    return None
```

### RSI策略
```python
def generate_signal(self, data: pd.DataFrame, context: StrategyContext) -> Optional[Signal]:
    if len(data) < 14:
        return None
    
    current_price = data['close'].iloc[-1]
    rsi = self.calculate_rsi(data['close'], 14).iloc[-1]
    
    if rsi < 30:  # 超卖
        return self.create_signal(
            symbol=context.symbol,
            signal_type='buy',
            price=current_price,
            datetime=data['datetime'].iloc[-1],
            strength=0.9
        )
    elif rsi > 70:  # 超买
        return self.create_signal(
            symbol=context.symbol,
            signal_type='sell',
            price=current_price,
            datetime=data['datetime'].iloc[-1],
            strength=0.9
        )
    return None
```

## 运行示例

```bash
cd user_strategies/example_ma_strategy
python simple_example.py
```

## 优势

1. **简单易用**: 只需要实现一个方法
2. **专注核心**: 去除复杂的抽象层
3. **快速开发**: 内置常用技术指标
4. **易于调试**: 清晰的日志输出
5. **灵活扩展**: 可以轻松添加新功能

## 注意事项

1. 确保数据包含必要的OHLCV列
2. 策略方法应该处理数据不足的情况
3. 使用内置的指标计算方法避免重复代码
4. 合理设置信号强度（0-1之间） 