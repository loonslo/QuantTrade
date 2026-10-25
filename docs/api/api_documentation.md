# QuantTradeSys API 文档

## 概述

QuantTradeSys API v2.0.0 提供了完整的量化交易数据和策略管理功能。本API采用RESTful设计，支持JSON格式的请求和响应。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: v1
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证

目前API暂不需要认证，后续版本将添加API密钥认证。

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {
    // 实际数据内容
  },
  "message": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {
      // 错误详细信息
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |

## API端点

### 1. 市场数据 API

#### 1.1 获取交易对列表

**端点**: `GET /api/v1/market-data/symbols`

**描述**: 获取所有可用的交易对列表

**请求参数**: 无

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "symbol": "BTCUSDT",
      "base_asset": "BTC",
      "quote_asset": "USDT",
      "status": "TRADING",
      "min_notional": "5.0"
    },
    {
      "symbol": "ETHUSDT",
      "base_asset": "ETH", 
      "quote_asset": "USDT",
      "status": "TRADING",
      "min_notional": "5.0"
    }
  ],
  "message": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 1.2 获取K线数据

**端点**: `GET /api/v1/market-data/klines`

**描述**: 获取指定交易对的K线数据

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号，如 BTCUSDT |
| interval | string | 是 | 时间间隔，如 1h, 1d |
| limit | integer | 否 | 返回数量，默认100，最大1000 |
| start_time | integer | 否 | 开始时间戳（毫秒） |
| end_time | integer | 否 | 结束时间戳（毫秒） |

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "symbol": "BTCUSDT",
      "interval": "1h",
      "open_time": 1640995200000,
      "close_time": 1640998799999,
      "open": "47000.00",
      "high": "47500.00",
      "low": "46800.00",
      "close": "47200.00",
      "volume": "123.45",
      "quote_volume": "5823456.78",
      "trades": 1234,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "message": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 1.3 获取实时价格

**端点**: `GET /api/v1/market-data/ticker`

**描述**: 获取交易对的实时价格信息

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| symbol | string | 否 | 交易对符号，不提供则返回所有 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "price": "47200.00",
    "price_change": "200.00",
    "price_change_percent": "0.42",
    "high_24h": "47800.00",
    "low_24h": "46500.00",
    "volume_24h": "12345.67",
    "quote_volume_24h": "582345678.90",
    "timestamp": 1640995200000,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 1.4 获取市场深度

**端点**: `GET /api/v1/market-data/depth`

**描述**: 获取交易对的订单簿深度数据

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号 |
| limit | integer | 否 | 深度档位，默认100 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "bids": [
      ["47100.00", "0.5"],
      ["47050.00", "1.2"]
    ],
    "asks": [
      ["47150.00", "0.8"],
      ["47200.00", "1.5"]
    ],
    "timestamp": 1640995200000
  },
  "message": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 1.5 获取最近成交

**端点**: `GET /api/v1/market-data/trades`

**描述**: 获取交易对的最近成交记录

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号 |
| limit | integer | 否 | 返回数量，默认100，最大1000 |

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 123456,
      "symbol": "BTCUSDT",
      "price": "47150.00",
      "quantity": "0.1",
      "time": 1640995200000,
      "is_buyer_maker": false
    }
  ],
  "message": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. 策略管理 API

#### 2.1 获取策略列表

**端点**: `GET /api/v1/strategies`

**描述**: 获取所有策略列表

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| limit | integer | 否 | 每页数量，默认10 |
| status | string | 否 | 策略状态筛选 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "strategies": [
      {
        "id": 1,
        "name": "移动平均策略",
        "description": "基于移动平均线的交易策略",
        "status": "active",
        "parameters": {
          "fast_period": 10,
          "slow_period": 20
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 1,
      "pages": 1
    }
  },
  "message": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 2.2 创建策略

**端点**: `POST /api/v1/strategies`

**描述**: 创建新的交易策略

**请求体**:
```json
{
  "name": "新策略",
  "description": "策略描述",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "新策略",
    "description": "策略描述",
    "status": "inactive",
    "parameters": {
      "param1": "value1",
      "param2": "value2"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "message": "策略创建成功",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 2.3 更新策略

**端点**: `PUT /api/v1/strategies/{strategy_id}`

**描述**: 更新指定策略

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| strategy_id | integer | 是 | 策略ID |

**请求体**:
```json
{
  "name": "更新后的策略名称",
  "description": "更新后的描述",
  "parameters": {
    "param1": "new_value1"
  }
}
```

#### 2.4 删除策略

**端点**: `DELETE /api/v1/strategies/{strategy_id}`

**描述**: 删除指定策略

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| strategy_id | integer | 是 | 策略ID |

### 3. 回测 API

#### 3.1 创建回测任务

**端点**: `POST /api/v1/backtest`

**描述**: 创建新的回测任务

**请求体**:
```json
{
  "strategy_id": 1,
  "symbol": "BTCUSDT",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "initial_capital": 10000,
  "parameters": {
    "custom_param": "value"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_123456",
    "status": "running",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "回测任务已创建",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 3.2 获取回测结果

**端点**: `GET /api/v1/backtest/{backtest_id}`

**描述**: 获取回测任务结果

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| backtest_id | string | 是 | 回测任务ID |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_123456",
    "status": "completed",
    "results": {
      "total_return": 0.15,
      "sharpe_ratio": 1.2,
      "max_drawdown": 0.08,
      "win_rate": 0.65,
      "total_trades": 45
    },
    "created_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T01:00:00Z"
  },
  "message": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 错误码参考

| 错误码 | 描述 |
|--------|------|
| VALIDATION_ERROR | 请求参数验证失败 |
| DATA_NOT_FOUND | 请求的数据不存在 |
| DATA_PROVIDER_ERROR | 数据提供商错误 |
| STRATEGY_NOT_FOUND | 策略不存在 |
| STRATEGY_EXECUTION_ERROR | 策略执行错误 |
| BACKTEST_ERROR | 回测执行错误 |
| RATE_LIMIT_EXCEEDED | 请求频率超限 |
| INTERNAL_ERROR | 服务器内部错误 |

## 限制和配额

- **请求频率**: 每分钟最多1200次请求
- **数据量限制**: 单次请求最多返回1000条记录
- **时间范围**: K线数据最多查询365天
- **并发连接**: 每个IP最多20个并发连接

## SDK和示例

### Python SDK 示例

```python
import requests

class QuantTradeAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_symbols(self):
        response = requests.get(f"{self.base_url}/api/v1/market-data/symbols")
        return response.json()
    
    def get_klines(self, symbol, interval, limit=100):
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        response = requests.get(
            f"{self.base_url}/api/v1/market-data/klines",
            params=params
        )
        return response.json()

# 使用示例
api = QuantTradeAPI()
symbols = api.get_symbols()
klines = api.get_klines("BTCUSDT", "1h", 100)
```

### JavaScript SDK 示例

```javascript
class QuantTradeAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async getSymbols() {
        const response = await fetch(`${this.baseUrl}/api/v1/market-data/symbols`);
        return await response.json();
    }
    
    async getKlines(symbol, interval, limit = 100) {
        const params = new URLSearchParams({
            symbol,
            interval,
            limit: limit.toString()
        });
        const response = await fetch(
            `${this.baseUrl}/api/v1/market-data/klines?${params}`
        );
        return await response.json();
    }
}

// 使用示例
const api = new QuantTradeAPI();
const symbols = await api.getSymbols();
const klines = await api.getKlines('BTCUSDT', '1h', 100);
```

## 版本历史

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础市场数据API
- 策略管理功能
- 回测功能

### v1.1.0 (计划中)
- 实时数据推送
- 高级技术指标
- 策略模板市场

## 支持和反馈

如果您在使用API过程中遇到问题：

1. 查看本文档的相关章节
2. 检查错误码和错误信息
3. 查看API变更日志
4. 联系技术支持团队

---

*本文档会随着API的更新持续维护，请定期查看最新版本。*