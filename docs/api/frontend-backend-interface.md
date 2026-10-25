# Frontend-Backend API Interface Specification

## Overview

This document defines the API interface contract between the QuantTradeSys frontend (Vue.js) and backend (FastAPI) applications. It ensures consistent communication and data exchange between the two layers.

## Base Configuration

### API Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.yourdomain.com`
- **Test**: `http://localhost:8000`

### Request/Response Format
- **Content-Type**: `application/json`
- **Character Encoding**: UTF-8
- **HTTP Methods**: GET, POST, PUT, DELETE
- **Authentication**: Bearer token (when implemented)

### Standard Response Format

All API responses follow this standard format:

```json
{
  "success": boolean,
  "data": object | array | null,
  "message": string,
  "error": string | null,
  "timestamp": string (ISO 8601),
  "request_id": string (UUID)
}
```

#### Success Response Example
```json
{
  "success": true,
  "data": {
    "symbol": "BTC",
    "price": 45000.00,
    "change_24h": 2.5
  },
  "message": "Data retrieved successfully",
  "error": null,
  "timestamp": "2025-01-01T12:00:00Z",
  "request_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### Error Response Example
```json
{
  "success": false,
  "data": null,
  "message": "Symbol not found",
  "error": "SYMBOL_NOT_FOUND",
  "timestamp": "2025-01-01T12:00:00Z",
  "request_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## API Endpoints

### 1. Market Data Endpoints

#### 1.1 Get 24-Hour Trend Data
```
GET /api/market-data/trend/24h/{symbol}
```

**Parameters:**
- `symbol` (path): Cryptocurrency symbol (e.g., "BTC", "ETH")
- `interval` (query): Time interval ("1h", "4h", "1d") - default: "1h"

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC",
    "interval": "1h",
    "data_points": [
      {
        "timestamp": "2025-01-01T00:00:00Z",
        "price": 45000.00,
        "volume": 1234567.89
      }
    ]
  }
}
```

#### 1.2 Get Batch Prices
```
POST /api/market-data/batch/prices
```

**Request Body:**
```json
{
  "symbols": ["BTC", "ETH", "BNB"],
  "include_24h_change": true,
  "include_market_cap": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "BTC": {
      "price": 45000.00,
      "change_24h": 2.5,
      "market_cap": 850000000000
    },
    "ETH": {
      "price": 3000.00,
      "change_24h": 1.8,
      "market_cap": 360000000000
    }
  }
}
```

#### 1.3 Get Market Overview
```
POST /api/market-data/advanced/overview
```

**Request Body:**
```json
{
  "symbols": "BTC,ETH,BNB",
  "include_24h_change": true,
  "include_market_cap": true,
  "include_dominance": true,
  "include_price": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_market_cap": 2500000000000,
    "total_volume_24h": 85000000000,
    "btc_dominance": 42.5,
    "eth_dominance": 18.2,
    "coins": {
      "BTC": {
        "price": 45000.00,
        "change_24h": 2.5,
        "market_cap": 850000000000,
        "dominance": 42.5
      }
    }
  }
}
```

#### 1.4 Get Fear & Greed Index
```
GET /api/market-data/advanced/fear-greed
```

**Response:**
```json
{
  "success": true,
  "data": {
    "value": 65,
    "classification": "Greed",
    "timestamp": "2025-01-01T12:00:00Z",
    "historical": [
      {
        "date": "2025-01-01",
        "value": 65
      }
    ]
  }
}
```

### 2. Market Analysis Endpoints

#### 2.1 Get Technical Analysis
```
GET /api/market-analysis/technical/{symbol}
```

**Parameters:**
- `symbol` (path): Cryptocurrency symbol
- `timeframe` (query): Time frame ("1h", "4h", "1d") - default: "1h"
- `period` (query): Analysis period (integer) - default: 14
- `indicators` (query): Comma-separated indicators ("rsi,macd,bollinger")

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC",
    "timeframe": "1h",
    "indicators": {
      "rsi": {
        "value": 65.5,
        "signal": "neutral",
        "overbought_threshold": 70,
        "oversold_threshold": 30
      },
      "macd": {
        "macd_line": 125.5,
        "signal_line": 120.0,
        "histogram": 5.5,
        "signal": "bullish"
      },
      "bollinger": {
        "upper_band": 46000.00,
        "middle_band": 45000.00,
        "lower_band": 44000.00,
        "position": "middle"
      }
    }
  }
}
```

#### 2.2 Get Support/Resistance Levels
```
GET /api/market-analysis/support-resistance/{symbol}
```

**Parameters:**
- `timeframe` (query): Time frame - default: "1h"
- `lookback_period` (query): Lookback period - default: 100
- `min_touches` (query): Minimum touches - default: 2

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC",
    "support_levels": [
      {
        "price": 44000.00,
        "strength": 0.85,
        "touches": 3,
        "last_touch": "2025-01-01T10:00:00Z"
      }
    ],
    "resistance_levels": [
      {
        "price": 46000.00,
        "strength": 0.92,
        "touches": 4,
        "last_touch": "2025-01-01T11:00:00Z"
      }
    ]
  }
}
```

#### 2.3 Run Strategy Backtest
```
POST /api/market-analysis/strategy/backtest
```

**Request Body:**
```json
{
  "strategy_name": "ma_crossover",
  "symbol": "BTC",
  "timeframe": "1h",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "parameters": {
    "fast_ma": 10,
    "slow_ma": 20
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "strategy_name": "ma_crossover",
    "symbol": "BTC",
    "period": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "performance": {
      "total_return": 25.5,
      "annual_return": 25.5,
      "max_drawdown": -8.2,
      "sharpe_ratio": 1.85,
      "win_rate": 0.65,
      "total_trades": 45
    },
    "trades": [
      {
        "entry_date": "2024-01-15T10:00:00Z",
        "exit_date": "2024-01-20T14:00:00Z",
        "entry_price": 42000.00,
        "exit_price": 43500.00,
        "quantity": 0.1,
        "pnl": 150.00,
        "type": "long"
      }
    ]
  }
}
```

#### 2.4 Get Available Strategies
```
GET /api/market-analysis/strategies
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "name": "ma_crossover",
      "display_name": "Moving Average Crossover",
      "description": "Simple moving average crossover strategy",
      "parameters": [
        {
          "name": "fast_ma",
          "type": "integer",
          "default": 10,
          "min": 5,
          "max": 50
        },
        {
          "name": "slow_ma",
          "type": "integer",
          "default": 20,
          "min": 10,
          "max": 100
        }
      ]
    }
  ]
}
```

## Error Codes

### Standard HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource not found)
- `422` - Unprocessable Entity (validation error)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error
- `503` - Service Unavailable

### Custom Error Codes
- `SYMBOL_NOT_FOUND` - Cryptocurrency symbol not supported
- `INVALID_TIMEFRAME` - Invalid timeframe parameter
- `INSUFFICIENT_DATA` - Not enough data for analysis
- `STRATEGY_NOT_FOUND` - Strategy not available
- `BACKTEST_FAILED` - Backtest execution failed
- `RATE_LIMIT_EXCEEDED` - API rate limit exceeded

## Rate Limiting

### Limits
- **General API**: 100 requests per minute per IP
- **Market Data**: 60 requests per minute per IP
- **Analysis**: 30 requests per minute per IP
- **Backtest**: 10 requests per minute per IP

### Headers
Rate limit information is included in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Authentication (Future Implementation)

### Bearer Token Authentication
```
Authorization: Bearer <jwt_token>
```

### Token Response Format
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## WebSocket Interface (Future Implementation)

### Connection
```
ws://localhost:8000/ws/market-data
```

### Message Format
```json
{
  "type": "subscribe",
  "channel": "price_updates",
  "symbols": ["BTC", "ETH"]
}
```

### Real-time Updates
```json
{
  "type": "price_update",
  "data": {
    "symbol": "BTC",
    "price": 45123.45,
    "timestamp": "2025-01-01T12:00:00Z"
  }
}
```

## Frontend Implementation Guidelines

### API Service Usage

```javascript
// Import the unified API service
import apiService from '@/services/apiService'

// Get market overview
const marketData = await apiService.getMarketOverview(['BTC', 'ETH'])

// Get technical analysis
const analysis = await apiService.getTechnicalAnalysis('BTC', '1h', 14, 'rsi,macd')

// Run backtest
const backtest = await apiService.runStrategyBacktest({
  strategy_name: 'ma_crossover',
  symbol: 'BTC',
  timeframe: '1h',
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  initial_capital: 10000,
  parameters: { fast_ma: 10, slow_ma: 20 }
})
```

### Error Handling

```javascript
try {
  const response = await apiService.getMarketOverview()
  if (response.success) {
    // Handle successful response
    this.marketData = response.data
  } else {
    // Handle API error
    this.showError(response.message)
  }
} catch (error) {
  // Handle network error
  this.showError('Network error occurred')
}
```

### Loading States

```javascript
// In Vue component
data() {
  return {
    loading: false,
    error: null,
    data: null
  }
},

async methods: {
  async fetchData() {
    this.loading = true
    this.error = null
    
    try {
      const response = await apiService.getMarketOverview()
      if (response.success) {
        this.data = response.data
      } else {
        this.error = response.message
      }
    } catch (error) {
      this.error = 'Failed to fetch data'
    } finally {
      this.loading = false
    }
  }
}
```

## Testing

### API Testing
- Use Postman or similar tools for manual testing
- Implement automated API tests using Jest or Vitest
- Mock API responses for frontend unit tests

### Mock Data
For development and testing, use mock data that follows the same response format:

```javascript
// Mock service for testing
export const mockApiService = {
  async getMarketOverview() {
    return {
      success: true,
      data: {
        total_market_cap: 2500000000000,
        coins: {
          BTC: { price: 45000, change_24h: 2.5 }
        }
      },
      message: 'Mock data',
      error: null
    }
  }
}
```

## Versioning

### API Versioning
- Current version: v1
- Version in URL: `/api/v1/...`
- Backward compatibility maintained for at least 2 versions

### Breaking Changes
- Major version increment for breaking changes
- Deprecation notices for 3 months before removal
- Migration guides provided for version upgrades

## Performance Considerations

### Caching
- Client-side caching for static data (strategies, symbols)
- Cache TTL based on data volatility
- Cache invalidation on user actions

### Pagination
For large datasets, use pagination:

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1000,
    "total_pages": 20
  }
}
```

### Compression
- Enable gzip compression for API responses
- Minimize payload size for mobile clients
- Use appropriate data types (avoid unnecessary precision)

## Security

### Input Validation
- Validate all input parameters
- Sanitize user inputs
- Use parameterized queries for database operations

### CORS Configuration
```javascript
// Allowed origins for CORS
const allowedOrigins = [
  'http://localhost:5173',  // Development
  'https://yourdomain.com'  // Production
]
```

### Rate Limiting
- Implement rate limiting per IP and user
- Use exponential backoff for retry logic
- Monitor for abuse patterns

This specification ensures consistent and reliable communication between the frontend and backend components of the QuantTradeSys application.