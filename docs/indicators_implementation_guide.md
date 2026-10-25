# 技术指标实现指南

## 概述
本系统实现了完整的技术指标计算和存储方案，支持3分钟时间片的动态指标计算。

## 系统架构

### 1. 数据模型
- **基础K线表** (`kline_data_3m`): 存储3分钟K线数据
- **技术指标表** (`technical_indicators`): 存储计算后的技术指标

### 2. 核心服务
- **IndicatorsCalculator**: 指标计算器
- **IndicatorsService**: 指标服务
- **IndicatorsScheduler**: 定时调度器

### 3. API接口
- 指标计算接口
- 历史数据查询接口
- 数据验证接口
- 调度器管理接口

## 支持的指标

### EMA指标
- EMA20: 20期指数移动平均线
- EMA50: 50期指数移动平均线

### MACD指标
- MACD日内: 基于3分钟线的MACD
- MACD4小时: 基于4小时聚合线的MACD

### RSI指标
- RSI7: 7期相对强弱指数
- RSI14: 14期相对强弱指数

### ATR指标
- ATR3: 3期平均真实波幅
- ATR14: 14期平均真实波幅

### 合约指标
- 持仓量 (Open Interest)
- 资金费率 (Funding Rate)

## 使用方法

### 1. 启动调度器
```python
from services.analysis.indicators_scheduler import IndicatorsScheduler

scheduler = IndicatorsScheduler()
scheduler.start()  # 启动定时任务
```

### 2. 手动计算指标
```python
from services.analysis.indicators_service import IndicatorsService

service = IndicatorsService()
success = await service.process_single_timeslice('BTCUSDT', '2025-10-23 09:00:00')
```

### 3. 查询历史指标
```python
indicators = await service.get_indicators_history(
    'BTCUSDT', 
    '2025-10-23 00:00:00', 
    '2025-10-23 23:59:59'
)
```

## API接口使用

### 1. 计算指标
```bash
POST /api/indicators/calculate
{
    "symbol": "BTCUSDT",
    "timestamp": "2025-10-23 09:00:00"
}
```

### 2. 查询指标历史
```bash
POST /api/indicators/query
{
    "symbol": "BTCUSDT",
    "start_time": "2025-10-23 00:00:00",
    "end_time": "2025-10-23 23:59:59",
    "limit": 100
}
```

### 3. 补填历史数据
```bash
POST /api/indicators/backfill
{
    "symbol": "BTCUSDT",
    "start_time": "2025-10-23 00:00:00",
    "end_time": "2025-10-23 23:59:59"
}
```

### 4. 验证指标数据
```bash
GET /api/indicators/validate/BTCUSDT/2025-10-23 09:00:00
```


## 定时任务

### 1. 指标计算任务
- **触发时间**: 每3分钟执行一次
- **功能**: 计算所有交易对的最新指标
- **时间片**: 09:00:00, 09:03:00, 09:06:00...

### 2. 数据验证任务
- **触发时间**: 每小时执行一次
- **功能**: 验证指标数据的完整性和准确性

### 3. 历史补填任务
- **触发时间**: 每天凌晨2点执行
- **功能**: 补填缺失的历史指标数据

## 数据流程

### 1. 数据收集
```
交易所API → K线数据 → kline_data_3m表
```

### 2. 指标计算
```
K线数据 → 指标计算器 → technical_indicators表
```

### 3. 数据查询
```
API请求 → 指标服务 → 返回指标数据
```

## 监控和维护

### 1. 日志监控
- 指标计算日志
- 数据验证日志
- 错误处理日志

### 2. 数据完整性检查
- 时间片连续性检查
- 指标值合理性验证
- 缺失数据补填

### 3. 性能优化
- 数据库索引优化
- 批量处理优化
- 缓存机制

## 故障处理

### 1. 计算失败
- 检查基础K线数据是否存在
- 验证历史数据是否充足
- 检查计算参数是否正确

### 2. 数据缺失
- 使用补填功能恢复数据
- 检查调度器是否正常运行
- 验证数据源连接状态

### 3. 性能问题
- 检查数据库连接池
- 优化查询语句
- 调整批处理大小

## 扩展功能

### 1. 新增指标
在 `IndicatorsCalculator` 中添加新的计算方法

### 2. 新增交易对
在 `IndicatorsScheduler` 的 `symbols` 列表中添加

### 3. 自定义时间片
修改调度器的触发时间配置

## 注意事项

1. **数据一致性**: 确保基础K线数据和指标数据的时间戳完全一致
2. **计算顺序**: 先计算EMA，再计算MACD，最后计算RSI和ATR
3. **错误处理**: 计算失败时记录详细日志，便于问题排查
4. **资源管理**: 合理控制并发数量，避免数据库压力过大
5. **数据验证**: 定期检查指标值的合理性，及时发现异常数据
