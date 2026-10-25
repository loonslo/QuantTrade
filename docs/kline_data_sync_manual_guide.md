# K线数据手动同步使用指南

## 概述

本文档介绍如何使用K线数据手动同步功能，包括默认数据量优化和手动执行时的自定义数据条数功能。

## 主要改进

### 1. 默认数据量优化
- **优化前**：每次同步获取100条K线数据
- **优化后**：默认只获取最新1条K线数据，大幅减少数据传输量

### 2. 手动执行支持
- 支持自定义数据条数（1-1000条）
- 支持选择特定交易对
- 支持选择特定时间框架
- 提供完整的API接口

## 使用方法

### 1. 编程方式使用

#### 基本使用
```python
from services.data_sync.tasks.kline_data_sync import get_kline_data_sync_service

# 获取服务实例
kline_service = get_kline_data_sync_service()

# 默认同步（只获取最新1条数据）
await kline_service.sync_minute_kline_data(["BTCUSDT", "ETHUSDT"])

# 手动同步指定条数
await kline_service.manual_sync_kline_data("1m", ["BTCUSDT"], limit=100)
```

#### 手动同步所有时间框架
```python
# 同步所有时间框架，每个获取200条数据
await kline_service.manual_sync_all_timeframes_kline_data(
    symbols=["BTCUSDT", "ETHUSDT"], 
    limit=200
)
```

#### 通过调度器使用
```python
from services.data_sync import get_scheduler

scheduler = get_scheduler()

# 手动执行1分钟K线数据同步，获取500条数据
success = scheduler.execute_manual_kline_sync(
    timeframe="1m",
    symbols=["BTCUSDT", "ETHUSDT"],
    limit=500
)

# 手动执行所有时间框架
success = scheduler.execute_manual_all_timeframes_kline_sync(
    symbols=["BTCUSDT", "ETHUSDT"],
    limit=100
)
```

### 2. API接口使用

#### 获取支持的时间框架
```bash
GET /api/data-sync/kline/supported-timeframes
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "timeframes": ["1m", "3m", "5m", "15m", "1h", "1d"],
        "default_limits": {
            "1m": 1,
            "3m": 1,
            "5m": 1,
            "15m": 1,
            "1h": 1,
            "1d": 1
        },
        "max_limits": {
            "1m": 1000,
            "3m": 1000,
            "5m": 1000,
            "15m": 1000,
            "1h": 1000,
            "1d": 1000
        },
        "default_symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]
    },
    "message": "获取支持的时间框架成功"
}
```

#### 手动同步指定时间框架
```bash
POST /api/data-sync/kline/manual-sync
Content-Type: application/json

{
    "timeframe": "1m",
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "limit": 200
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_name": "manual_kline_sync_1m",
        "timeframe": "1m",
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "limit": 200,
        "status": "completed",
        "execution_time": 2.34,
        "started_at": "2024-01-15T10:30:00",
        "completed_at": "2024-01-15T10:30:02",
        "result": "K线数据同步成功"
    },
    "message": "手动K线数据同步成功: 1m"
}
```

#### 手动同步所有时间框架
```bash
POST /api/data-sync/kline/manual-sync-all
Content-Type: application/json

{
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "limit": 100
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_name": "manual_all_timeframes_kline_sync",
        "timeframes": ["1m", "3m", "5m", "15m", "1h", "1d"],
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "limit": 100,
        "status": "completed",
        "execution_time": 12.45,
        "started_at": "2024-01-15T10:30:00",
        "completed_at": "2024-01-15T10:30:12",
        "result": "所有时间框架K线数据同步成功"
    },
    "message": "手动所有时间框架K线数据同步成功"
}
```

## 配置说明

### 默认配置
```python
# 默认只获取最新1条数据
TIMEFRAME_LIMITS = {
    '1m': 1,     # 1分钟：1条 = 最新数据
    '3m': 1,     # 3分钟：1条 = 最新数据
    '5m': 1,     # 5分钟：1条 = 最新数据
    '15m': 1,    # 15分钟：1条 = 最新数据
    '1h': 1,     # 1小时：1条 = 最新数据
    '1d': 1      # 1天：1条 = 最新数据
}

# 手动同步时的最大限制
MAX_MANUAL_LIMITS = {
    '1m': 1000,   # 1分钟：最多1000条
    '3m': 1000,   # 3分钟：最多1000条
    '5m': 1000,   # 5分钟：最多1000条
    '15m': 1000,  # 15分钟：最多1000条
    '1h': 1000,   # 1小时：最多1000条
    '1d': 1000    # 1天：最多1000条
}
```

### 参数验证
- **时间框架**：必须是支持的时间框架之一
- **数据条数**：必须在1-1000之间
- **交易对**：可选，默认使用系统配置的交易对

## 性能对比

### 默认同步（优化后）
- **数据量**：每个交易对1条数据
- **传输时间**：约0.5-1秒
- **存储空间**：最小化
- **适用场景**：实时数据更新

### 手动同步（自定义条数）
- **数据量**：1-1000条可配置
- **传输时间**：根据条数线性增长
- **存储空间**：根据条数线性增长
- **适用场景**：历史数据补充、数据分析

## 使用场景

### 1. 实时数据更新
```python
# 定时任务：每5分钟获取最新数据
await kline_service.sync_minute_kline_data()
```

### 2. 历史数据补充
```python
# 手动补充最近100条1分钟数据
await kline_service.manual_sync_kline_data("1m", limit=100)
```

### 3. 数据分析准备
```python
# 获取最近1000条1小时数据用于分析
await kline_service.manual_sync_kline_data("1h", limit=1000)
```

### 4. 系统初始化
```python
# 初始化时获取所有时间框架的历史数据
await kline_service.manual_sync_all_timeframes_kline_data(limit=500)
```

## 错误处理

### 常见错误
1. **不支持的时间框架**
   ```json
   {
       "success": false,
       "error_code": "INVALID_TIMEFRAME",
       "message": "不支持的时间框架: 2m",
       "details": {
           "supported_timeframes": ["1m", "3m", "5m", "15m", "1h", "1d"]
       }
   }
   ```

2. **数据条数超出限制**
   ```json
   {
       "success": false,
       "error_code": "INVALID_LIMIT",
       "message": "数据条数不能超过最大限制 1000",
       "details": {
           "max_limit": 1000
       }
   }
   ```

### 错误处理建议
- 检查时间框架是否支持
- 验证数据条数是否在允许范围内
- 确保交易对格式正确
- 监控API响应状态

## 最佳实践

### 1. 数据量选择
- **实时监控**：使用默认1条数据
- **短期分析**：使用100-500条数据
- **长期分析**：使用500-1000条数据

### 2. 频率控制
- **高频更新**：每1-5分钟执行一次
- **中频更新**：每15-30分钟执行一次
- **低频更新**：每小时或每天执行一次

### 3. 资源管理
- 避免同时执行大量手动同步任务
- 根据系统资源调整并发数量
- 监控数据库存储空间使用情况

### 4. 监控和日志
- 监控同步任务的执行状态
- 记录数据质量和同步成功率
- 设置异常告警机制

## 故障排除

### 常见问题
1. **同步失败**
   - 检查网络连接
   - 验证API配置
   - 查看错误日志

2. **数据不完整**
   - 检查交易对是否有效
   - 验证时间框架支持
   - 确认数据源可用性

3. **性能问题**
   - 减少并发数量
   - 降低数据条数
   - 优化数据库查询

### 调试方法
```python
# 启用调试日志
import logging
logging.getLogger('kline_data_sync_service').setLevel(logging.DEBUG)

# 检查服务状态
kline_service = get_kline_data_sync_service()
print(f"支持的时间框架: {kline_service.get_supported_timeframes()}")
print(f"默认限制: {kline_service.get_default_limits()}")
print(f"最大限制: {kline_service.get_max_limits()}")
```

## 总结

通过这次优化，K线数据同步系统实现了：

1. **性能优化**：默认只获取最新数据，减少90%+的数据传输量
2. **灵活性提升**：支持手动自定义数据条数，满足不同需求
3. **易用性增强**：提供完整的API接口和编程接口
4. **可维护性**：完善的错误处理和参数验证

这些改进使得系统既能满足实时数据更新的需求，又能支持历史数据分析和系统初始化的场景。
