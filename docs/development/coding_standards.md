# BACKEND 开发规范 (优化后版本)

## 概述

本文档定义了 BACKEND 项目优化后的开发规范，确保代码质量、一致性和可维护性。

## 目录结构规范

### 1. 目录命名规范

- **使用 snake_case**: 所有目录名使用小写字母和下划线
- **使用复数形式**: 集合目录使用复数 (`services/`, `models/`, `tests/`)
- **描述性命名**: 目录名应清晰表达其用途
- **避免缩写**: 使用完整单词而非缩写

```
✅ 正确示例:
services/market_data/
data/repositories/
config/environments/

❌ 错误示例:
Services/MarketData/
data/repos/
cfg/env/
```

### 2. 文件命名规范

- **Python文件**: 使用 snake_case.py
- **配置文件**: 使用 snake_case.json
- **文档文件**: 使用 snake_case.md
- **脚本文件**: 使用 snake_case.py

```
✅ 正确示例:
market_data_service.py
binance_config.json
api_documentation.md

❌ 错误示例:
MarketDataService.py
binanceConfig.json
API-Documentation.md
```

## 代码组织规范

### 1. 导入顺序

```python
# 1. 标准库导入
import os
import sys
from typing import Dict, List, Optional

# 2. 第三方库导入
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
import pandas as pd

# 3. 本地导入 - 按层次组织
from api import MarketDataRequest
from services import MarketDataService
from data.repositories.market_data import MarketDataRepository
from utils.logger import get_logger
```

### 2. 类和函数组织

```python
class MarketDataService:
    """市场数据服务类
    
    提供市场数据的获取、处理和缓存功能
    """
    
    def __init__(self, repository: MarketDataRepository):
        """初始化服务
        
        Args:
            repository: 市场数据仓储实例
        """
        self.repository = repository
        self.logger = get_logger(__name__)
    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取市场数据
        
        Args:
            symbol: 交易对符号
            
        Returns:
            市场数据字典
            
        Raises:
            ValueError: 当符号无效时
        """
        if not symbol:
            raise ValueError("Symbol cannot be empty")
            
        return self.repository.get_by_symbol(symbol)
```

### 3. 模块结构

每个模块应包含：

```python
"""
模块文档字符串

描述模块的用途、主要功能和使用方法
"""

# 导入部分
from typing import Dict, Any

# 常量定义
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# 类定义
class ServiceClass:
    pass

# 函数定义
def utility_function():
    pass

# 模块级别的执行代码
if __name__ == "__main__":
    main()
```

## API 开发规范

### 1. API 端点设计

```python
from fastapi import APIRouter, Depends, HTTPException
from BackEnd.api import MarketDataRequest
from BackEnd.api import MarketDataResponse
from BackEnd.services import MarketDataService

router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])


@router.get("/latest-price/{symbol}")
async def get_latest_price(
        symbol: str,
        service: MarketDataService = Depends(get_market_data_service)
) -> MarketDataResponse:
    """获取最新价格
    
    Args:
        symbol: 交易对符号
        service: 市场数据服务
        
    Returns:
        包含最新价格的响应
    """
    try:
        data = await service.get_latest_price(symbol)
        return MarketDataResponse(success=True, data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 2. 响应格式规范

```python
# 成功响应
{
    "success": true,
    "data": {
        # 实际数据
    },
    "meta": {
        "timestamp": "2024-01-01T12:00:00Z",
        "request_id": "req_123456"
    }
}

# 错误响应
{
    "success": false,
    "error": {
        "code": "INVALID_PARAMETER",
        "message": "Invalid symbol parameter",
        "details": {
            "parameter": "symbol",
            "value": "INVALID"
        }
    },
    "meta": {
        "timestamp": "2024-01-01T12:00:00Z",
        "request_id": "req_123456"
    }
}
```

## 服务层开发规范

### 1. 服务类设计

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseService(ABC):
    """服务基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"services.{name}")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化服务"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass

class MarketDataService(BaseService):
    """市场数据服务"""
    
    def __init__(self, repository: MarketDataRepository):
        super().__init__("market_data")
        self.repository = repository
    
    async def initialize(self) -> bool:
        """初始化服务"""
        self.logger.info("Initializing market data service")
        return True
    
    async def cleanup(self) -> None:
        """清理资源"""
        self.logger.info("Cleaning up market data service")
```

### 2. 依赖注入规范

```python
# api/dependencies.py
from functools import lru_cache
from BackEnd.services import MarketDataService
from data.repositories.market_data import MarketDataRepository


@lru_cache()
def get_market_data_repository() -> MarketDataRepository:
    """获取市场数据仓储实例"""
    return MarketDataRepository()


@lru_cache()
def get_market_data_service() -> MarketDataService:
    """获取市场数据服务实例"""
    repository = get_market_data_repository()
    return MarketDataService(repository)
```

## 数据层开发规范

### 1. 数据模型设计

```python
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MarketData(Base):
    """市场数据模型"""
    
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume
        }
```

### 2. 仓储模式实现

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseRepository(ABC):
    """仓储基类"""
    
    def __init__(self, session):
        self.session = session
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        """根据ID获取实体"""
        pass
    
    @abstractmethod
    def create(self, entity: Any) -> Any:
        """创建实体"""
        pass
    
    @abstractmethod
    def update(self, entity: Any) -> Any:
        """更新实体"""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """删除实体"""
        pass

class MarketDataRepository(BaseRepository):
    """市场数据仓储"""
    
    def get_by_symbol(self, symbol: str) -> List[MarketData]:
        """根据符号获取市场数据"""
        return self.session.query(MarketData)\
            .filter(MarketData.symbol == symbol)\
            .order_by(MarketData.timestamp.desc())\
            .all()
```

## 配置管理规范

### 1. 配置文件结构

```json
// config/environments/development.json
{
    "debug": true,
    "log_level": "DEBUG",
    "database": {
        "type": "sqlite",
        "path": "quant_trading.db"
    },
    "api": {
        "host": "127.0.0.1",
        "port": 8000,
        "reload": true
    },
    "cache": {
        "enabled": true,
        "ttl": 300
    }
}
```

### 2. 配置加载规范

```python
from utils.config import ConfigManager
from typing import Dict, Any

class ServiceConfig:
    """服务配置类"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置"""
        env = os.getenv('ENVIRONMENT', 'development')
        self.env_config = self.config_manager.load_environment_config(env)
        self.service_configs = self.config_manager.load_service_configs()
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.env_config.get('database', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.env_config.get('api', {})
```

## 错误处理规范

### 1. 异常定义

```python
# utils/exceptions.py
class BACKENDException(Exception):
    """系统基础异常"""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(BACKENDException):
    """验证错误"""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")

class ServiceError(BACKENDException):
    """服务错误"""
    
    def __init__(self, message: str, service: str = None):
        self.service = service
        super().__init__(message, "SERVICE_ERROR")
```

### 2. 错误处理模式

```python
from utils.exceptions import ValidationError, ServiceError
from utils.logger import get_logger

logger = get_logger(__name__)

def process_market_data(symbol: str) -> Dict[str, Any]:
    """处理市场数据"""
    try:
        # 验证输入
        if not symbol or len(symbol) < 3:
            raise ValidationError("Invalid symbol format", "symbol")
        
        # 业务逻辑
        data = fetch_market_data(symbol)
        
        if not data:
            raise ServiceError("No data available", "market_data")
        
        return data
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}", extra={
            "field": e.field,
            "symbol": symbol
        })
        raise
    
    except ServiceError as e:
        logger.error(f"Service error: {e.message}", extra={
            "service": e.service,
            "symbol": symbol
        })
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "symbol": symbol
        })
        raise ServiceError("Internal processing error")
```

## 日志记录规范

### 1. 日志配置

```python
# utils/logger.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """结构化日志格式器"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        return json.dumps(log_entry, ensure_ascii=False)

def get_logger(name: str) -> logging.Logger:
    """获取结构化日志器"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
```

### 2. 日志使用规范

```python
from utils.logger import get_logger

logger = get_logger(__name__)

def process_request(symbol: str, user_id: str):
    """处理请求"""
    # 记录请求开始
    logger.info("Processing request", extra={
        "symbol": symbol,
        "user_id": user_id,
        "action": "process_request_start"
    })
    
    try:
        result = perform_processing(symbol)
        
        # 记录成功
        logger.info("Request processed successfully", extra={
            "symbol": symbol,
            "user_id": user_id,
            "action": "process_request_success",
            "result_count": len(result)
        })
        
        return result
        
    except Exception as e:
        # 记录错误
        logger.error("Request processing failed", extra={
            "symbol": symbol,
            "user_id": user_id,
            "action": "process_request_error",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise
```

## 测试规范

### 1. 测试文件组织

```
tests/
├── unit/                         # 单元测试
│   ├── api/
│   │   ├── test_market_data_api.py
│   │   └── test_strategy_api.py
│   ├── services/
│   │   ├── test_market_data_service.py
│   │   └── test_strategy_service.py
│   └── repositories/
│       ├── test_market_data_repository.py
│       └── test_strategy_repository.py
├── integration/                  # 集成测试
│   ├── test_api_integration.py
│   └── test_service_integration.py
└── e2e/                          # 端到端测试
    └── test_full_workflow.py
```

### 2. 测试编写规范

```python
import pytest
from unittest.mock import Mock, patch
from BackEnd.services import MarketDataService
from data.repositories.market_data import MarketDataRepository


class TestMarketDataService:
    """市场数据服务测试类"""

    @pytest.fixture
    def mock_repository(self):
        """模拟仓储"""
        return Mock(spec=MarketDataRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """服务实例"""
        return MarketDataService(mock_repository)

    def test_get_market_data_success(self, service, mock_repository):
        """测试获取市场数据成功"""
        # Arrange
        symbol = "BTCUSDT"
        expected_data = {"price": 45000.0}
        mock_repository.get_by_symbol.return_value = expected_data

        # Act
        result = service.get_market_data(symbol)

        # Assert
        assert result == expected_data
        mock_repository.get_by_symbol.assert_called_once_with(symbol)

    def test_get_market_data_invalid_symbol(self, service):
        """测试无效符号"""
        # Act & Assert
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            service.get_market_data("")
```

## 性能优化规范

### 1. 数据库查询优化

```python
# ✅ 使用索引和批量查询
def get_market_data_batch(symbols: List[str]) -> List[MarketData]:
    """批量获取市场数据"""
    return session.query(MarketData)\
        .filter(MarketData.symbol.in_(symbols))\
        .order_by(MarketData.timestamp.desc())\
        .limit(1000)\
        .all()

# ❌ 避免N+1查询
def get_market_data_inefficient(symbols: List[str]) -> List[MarketData]:
    """低效的查询方式"""
    results = []
    for symbol in symbols:  # N+1查询问题
        data = session.query(MarketData)\
            .filter(MarketData.symbol == symbol)\
            .first()
        results.append(data)
    return results
```

### 2. 缓存使用规范

```python
from functools import lru_cache
from typing import Dict, Any

class MarketDataService:
    """市场数据服务"""
    
    @lru_cache(maxsize=1000)
    def get_cached_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取缓存的市场数据"""
        return self.repository.get_by_symbol(symbol)
    
    async def get_market_data_with_cache(self, symbol: str) -> Dict[str, Any]:
        """使用缓存获取市场数据"""
        cache_key = f"market_data:{symbol}"
        
        # 尝试从缓存获取
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # 从数据库获取
        data = self.repository.get_by_symbol(symbol)
        
        # 存入缓存
        await self.cache.set(cache_key, data, ttl=300)
        
        return data
```

## 安全规范

### 1. 输入验证

```python
from pydantic import BaseModel, validator
from typing import Optional

class MarketDataRequest(BaseModel):
    """市场数据请求模型"""
    
    symbol: str
    timeframe: str
    limit: Optional[int] = 100
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """验证交易对符号"""
        if not v or len(v) < 3:
            raise ValueError('Symbol must be at least 3 characters')
        if not v.replace('/', '').isalnum():
            raise ValueError('Symbol contains invalid characters')
        return v.upper()
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        """验证时间周期"""
        valid_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        if v not in valid_timeframes:
            raise ValueError(f'Invalid timeframe. Must be one of: {valid_timeframes}')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        """验证数量限制"""
        if v is not None and (v < 1 or v > 1000):
            raise ValueError('Limit must be between 1 and 1000')
        return v
```

### 2. 敏感信息处理

```python
import os
from typing import Optional

class ConfigManager:
    """配置管理器"""
    
    def get_api_key(self, service: str) -> Optional[str]:
        """获取API密钥"""
        # 优先从环境变量获取
        env_key = f"{service.upper()}_API_KEY"
        api_key = os.getenv(env_key)
        
        if api_key:
            # 记录日志时脱敏
            masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
            logger.info(f"Loaded API key for {service}: {masked_key}")
            return api_key
        
        logger.warning(f"No API key found for {service}")
        return None
```

## 文档规范

### 1. 代码文档

```python
def calculate_technical_indicator(
    data: List[float], 
    period: int = 14,
    indicator_type: str = "RSI"
) -> List[float]:
    """计算技术指标
    
    Args:
        data: 价格数据列表
        period: 计算周期，默认14
        indicator_type: 指标类型，支持 RSI, MACD, SMA
        
    Returns:
        计算结果列表
        
    Raises:
        ValueError: 当数据不足或参数无效时
        
    Example:
        >>> prices = [100, 102, 101, 103, 105]
        >>> rsi = calculate_technical_indicator(prices, 14, "RSI")
        >>> print(rsi)
        [50.0, 52.1, 48.9, 55.2, 58.7]
    """
    pass
```

### 2. API文档

```python
@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    service: StrategyService = Depends(get_strategy_service)
) -> BacktestResponse:
    """运行策略回测
    
    运行指定策略的历史数据回测，返回详细的性能指标和交易记录。
    
    Args:
        request: 回测请求参数
        service: 策略服务实例
        
    Returns:
        回测结果，包含性能指标和交易记录
        
    Raises:
        HTTPException: 当参数无效或回测失败时
        
    Example:
        ```json
        {
            "strategy_id": "ma_cross",
            "symbol": "BTC/USDT",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "initial_capital": 10000
        }
        ```
    """
    pass
```

---

*本规范确保 BACKEND 项目的代码质量和一致性，所有开发者都应遵循这些规范。*