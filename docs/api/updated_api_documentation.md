# QuantTradeSys API 文档 (优化后版本)

## 概述

本文档描述了 QuantTradeSys 项目目录结构优化后的 API 接口。优化后的 API 层采用统一的结构设计，提供更好的可维护性和扩展性。

## API 架构

### 新架构特点

1. **统一的 API 层**: 所有 API 相关代码集中在 `api/` 目录
2. **版本化管理**: 支持 API 版本控制 (`v1/`, `v2/` 等)
3. **分层设计**: 清晰的中间件、服务、模型分层
4. **标准化响应**: 统一的响应格式和错误处理
5. **依赖注入**: 现代化的依赖管理

### 目录结构

```
api/
├── v1/                           # API版本1
│   ├── market_data.py            # 市场数据API
│   ├── strategy.py               # 策略API
│   ├── analysis.py               # 分析API
│   └── mcp.py                   # MCP服务API
├── middleware/                   # API中间件
│   ├── auth.py                  # 认证中间件
│   ├── cors.py                  # CORS中间件
│   ├── error_handler.py         # 错误处理中间件
│   └── logging.py               # 日志中间件
├── models/                       # API数据模型
│   ├── requests.py              # 请求模型
│   ├── responses.py             # 响应模型
│   └── schemas.py               # 数据模式
├── services/                     # API服务层
│   ├── market_data_api.py       # 市场数据API服务
│   ├── strategy_api.py          # 策略API服务
│   └── analysis_api.py          # 分析API服务
├── utils/                        # API工具
│   ├── responses.py             # 响应工具
│   ├── validation.py            # 验证工具
│   └── pagination.py            # 分页工具
├── dependencies.py               # 依赖注入
├── exceptions.py                 # API异常
└── app.py                       # FastAPI应用
```

## API 端点

### 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: `v1`
- **内容类型**: `application/json`
- **认证方式**: Bearer Token (可选)

### 健康检查

#### GET /health
检查API服务状态

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "2.0.0",
  "uptime": 3600
}
```

### 市场数据 API

#### GET /api/v1/market-data
获取市场数据

**参数**:
- `symbol` (string): 交易对符号，如 "BTC/USDT"
- `timeframe` (string): 时间周期，如 "1h", "1d"
- `limit` (integer): 数据条数限制，默认100
- `start_time` (string, optional): 开始时间 (ISO 8601)
- `end_time` (string, optional): 结束时间 (ISO 8601)

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "open": 45000.0,
      "high": 45500.0,
      "low": 44800.0,
      "close": 45200.0,
      "volume": 1234.56
    }
  ],
  "meta": {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "count": 100,
    "total": 1000
  }
}
```

#### GET /api/v1/market-data/latest-price/{symbol}
获取最新价格

**路径参数**:
- `symbol` (string): 交易对符号

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "price": 45200.0,
    "timestamp": "2024-01-01T12:00:00Z",
    "change_24h": 2.5,
    "change_percent_24h": 5.86
  }
}
```

#### GET /api/v1/market-data/market-info/{symbol}
获取市场信息

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "base_asset": "BTC",
    "quote_asset": "USDT",
    "price": 45200.0,
    "volume_24h": 12345.67,
    "high_24h": 46000.0,
    "low_24h": 44000.0,
    "market_cap": 890000000000,
    "circulating_supply": 19700000
  }
}
```

#### GET /api/v1/market-data/coin-details
获取币种详情

**参数**:
- `symbol` (string): 币种符号
- `include_market_data` (boolean): 是否包含市场数据

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "description": "Bitcoin is a decentralized digital currency...",
    "website": "https://bitcoin.org",
    "market_data": {
      "current_price": 45200.0,
      "market_cap": 890000000000,
      "total_volume": 12345.67
    }
  }
}
```

### 策略 API

#### GET /api/v1/strategy/list
获取策略列表

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "ma_cross",
      "name": "Moving Average Cross",
      "description": "Simple moving average crossover strategy",
      "parameters": {
        "fast_period": 10,
        "slow_period": 20
      },
      "risk_level": "medium"
    }
  ]
}
```

#### POST /api/v1/strategy/backtest
运行策略回测

**请求体**:
```json
{
  "strategy_id": "ma_cross",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "initial_capital": 10000,
  "parameters": {
    "fast_period": 10,
    "slow_period": 20
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_123456",
    "status": "completed",
    "results": {
      "total_return": 15.5,
      "sharpe_ratio": 1.2,
      "max_drawdown": -8.3,
      "win_rate": 0.65,
      "total_trades": 45
    },
    "equity_curve": [
      {"date": "2024-01-01", "value": 10000},
      {"date": "2024-01-02", "value": 10150}
    ]
  }
}
```

#### GET /api/v1/strategy/allocation
获取策略配置建议

**参数**:
- `strategy_type` (string): 策略类型 ("conservative", "moderate", "aggressive")
- `risk_tolerance` (string): 风险承受度

**响应示例**:
```json
{
  "success": true,
  "data": {
    "strategy_type": "moderate",
    "allocation": {
      "BTC": 40,
      "ETH": 30,
      "BNB": 20,
      "USDT": 10
    },
    "rebalance_frequency": "weekly",
    "risk_metrics": {
      "expected_return": 12.5,
      "volatility": 18.2,
      "max_drawdown": 15.0
    }
  }
}
```

### 分析 API

#### POST /api/v1/analysis/technical
技术分析

**请求体**:
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "indicators": ["RSI", "MACD", "BB"],
  "period": 100
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "analysis": {
      "RSI": {
        "value": 65.5,
        "signal": "neutral",
        "description": "RSI is in neutral zone"
      },
      "MACD": {
        "macd": 120.5,
        "signal": 115.2,
        "histogram": 5.3,
        "signal": "bullish"
      },
      "BB": {
        "upper": 46000,
        "middle": 45000,
        "lower": 44000,
        "position": "middle",
        "signal": "neutral"
      }
    },
    "overall_signal": "neutral",
    "confidence": 0.7
  }
}
```

#### GET /api/v1/analysis/market-overview
市场概览分析

**响应示例**:
```json
{
  "success": true,
  "data": {
    "market_sentiment": "bullish",
    "fear_greed_index": 65,
    "top_gainers": [
      {"symbol": "BTC", "change": 5.2},
      {"symbol": "ETH", "change": 3.8}
    ],
    "top_losers": [
      {"symbol": "ADA", "change": -2.1}
    ],
    "market_cap_total": 2500000000000,
    "volume_24h": 85000000000
  }
}
```

### MCP 服务 API

#### GET /api/v1/mcp/status
获取MCP服务状态

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "active",
    "connected_servers": 3,
    "available_tools": [
      "binance_data",
      "coingecko_api",
      "technical_analysis"
    ],
    "last_sync": "2024-01-01T12:00:00Z"
  }
}
```

## 响应格式

### 成功响应

所有成功的API响应都遵循以下格式：

```json
{
  "success": true,
  "data": {
    // 实际数据内容
  },
  "meta": {
    // 元数据信息（可选）
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_123456"
  }
}
```

### 错误响应

所有错误响应都遵循以下格式：

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid symbol parameter",
    "details": {
      "parameter": "symbol",
      "value": "INVALID",
      "expected": "Valid trading pair symbol"
    }
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_123456"
  }
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| `INVALID_PARAMETER` | 400 | 无效参数 |
| `MISSING_PARAMETER` | 400 | 缺少必需参数 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 禁止访问 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

## 认证和授权

### API密钥认证

对于需要认证的端点，使用Bearer Token：

```http
Authorization: Bearer your_api_key_here
```

### 请求限制

- **频率限制**: 每分钟最多100个请求
- **并发限制**: 每个API密钥最多10个并发请求
- **数据限制**: 单次请求最多返回1000条记录

## WebSocket API

### 连接地址

```
ws://localhost:8000/ws
```

### 实时市场数据

**订阅消息**:
```json
{
  "action": "subscribe",
  "channel": "market_data",
  "symbol": "BTC/USDT"
}
```

**数据推送**:
```json
{
  "channel": "market_data",
  "symbol": "BTC/USDT",
  "data": {
    "price": 45200.0,
    "volume": 1.5,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## SDK 和客户端库

### Python SDK

```python
from quanttradesys import QuantTradeSysAPI

# 初始化客户端
client = QuantTradeSysAPI(
    base_url="http://localhost:8000",
    api_key="your_api_key"
)

# 获取市场数据
data = client.market_data.get_ohlcv("BTC/USDT", "1h", limit=100)

# 运行回测
result = client.strategy.backtest(
    strategy_id="ma_cross",
    symbol="BTC/USDT",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### JavaScript SDK

```javascript
import { QuantTradeSysAPI } from 'quanttradesys-js';

// 初始化客户端
const client = new QuantTradeSysAPI({
  baseURL: 'http://localhost:8000',
  apiKey: 'your_api_key'
});

// 获取市场数据
const data = await client.marketData.getOHLCV('BTC/USDT', '1h', { limit: 100 });

// 运行回测
const result = await client.strategy.backtest({
  strategyId: 'ma_cross',
  symbol: 'BTC/USDT',
  startDate: '2024-01-01',
  endDate: '2024-01-31'
});
```

## 迁移指南

### 从旧版本迁移

#### 端点变更

| 旧端点 | 新端点 | 变更说明 |
|--------|--------|----------|
| `/market-data` | `/api/v1/market-data` | 添加版本前缀 |
| `/latest-price/{symbol}` | `/api/v1/market-data/latest-price/{symbol}` | 移动到market-data下 |
| `/backtest/run` | `/api/v1/strategy/backtest` | 重命名并移动 |

#### 响应格式变更

**旧格式**:
```json
{
  "data": [...],
  "status": "success"
}
```

**新格式**:
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 错误处理变更

**旧格式**:
```json
{
  "error": "Invalid parameter",
  "status": "error"
}
```

**新格式**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid parameter",
    "details": {...}
  }
}
```

## 性能优化

### 缓存策略

- **市场数据**: 缓存1分钟
- **币种信息**: 缓存1小时
- **策略列表**: 缓存24小时

### 分页支持

对于大量数据的端点，支持分页：

```http
GET /api/v1/market-data?page=1&limit=100
```

响应包含分页信息：

```json
{
  "success": true,
  "data": [...],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 100,
      "total": 1000,
      "pages": 10
    }
  }
}
```

## 监控和日志

### 健康检查端点

- `/health`: 基础健康检查
- `/health/detailed`: 详细健康状态
- `/metrics`: Prometheus指标

### 日志格式

所有API请求都会记录结构化日志：

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "method": "GET",
  "path": "/api/v1/market-data",
  "status_code": 200,
  "response_time": 150,
  "user_agent": "QuantTradeSys-Python/1.0",
  "request_id": "req_123456"
}
```

## 开发和测试

### 本地开发

```bash
# 启动开发服务器
python run_server.py

# 或使用uvicorn
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### API测试

```bash
# 运行API测试
python -m pytest tests/api/

# 生成API文档
python scripts/dev/generate_api_docs.py
```

### 交互式文档

访问 `http://localhost:8000/docs` 查看Swagger UI文档
访问 `http://localhost:8000/redoc` 查看ReDoc文档

---

*本文档描述了QuantTradeSys优化后的API接口，为开发者提供完整的API使用指南。*