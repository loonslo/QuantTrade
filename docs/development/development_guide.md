# QuantTradeSys 开发指南

本指南介绍了QuantTradeSys v2.0.0新架构的开发规范和最佳实践。

## 架构概览

QuantTradeSys采用分层架构设计，主要包含以下层次：

```
┌─────────────────────────────────────┐
│              API Layer              │  ← 接口层
├─────────────────────────────────────┤
│            Service Layer            │  ← 业务逻辑层
├─────────────────────────────────────┤
│           Repository Layer          │  ← 数据访问层
├─────────────────────────────────────┤
│         Infrastructure Layer        │  ← 基础设施层
└─────────────────────────────────────┘
```

## 目录结构

```
app/
├── api/                    # API接口层
│   ├── v1/                # API版本1
│   ├── middleware/        # 中间件
│   ├── utils/            # API工具
│   └── compatibility/    # 兼容性管理
├── core/                 # 核心业务层
│   ├── services/         # 业务服务
│   ├── repositories/     # 数据仓储
│   ├── models/          # 数据模型
│   ├── interfaces/      # 接口定义
│   └── base/           # 基础类
└── infrastructure/      # 基础设施层
    ├── config/         # 配置管理
    ├── logging/        # 日志管理
    ├── di/            # 依赖注入
    └── migration/     # 数据迁移
```

## 开发规范

### 1. 命名规范

#### 文件和目录命名
- 使用小写字母和下划线: `market_data_service.py`
- 目录名使用复数形式: `services/`, `repositories/`
- 测试文件以`test_`开头: `test_market_data_service.py`

#### 类命名
- 使用PascalCase: `MarketDataService`
- 接口以`I`开头: `IMarketDataRepository`
- 异常以`Exception`结尾: `ValidationException`

#### 方法和变量命名
- 使用snake_case: `get_market_data()`
- 私有方法以下划线开头: `_validate_symbol()`
- 常量使用大写: `MAX_RETRY_COUNT`

### 2. 代码组织

#### 服务类结构
```python
class MarketDataService(BaseService):
    """市场数据服务"""
    
    def __init__(
        self,
        repository: IMarketDataRepository,
        logger: ILogger,
        config: IConfigManager
    ):
        super().__init__(logger, config)
        self.repository = repository
    
    async def get_symbols(self) -> List[Symbol]:
        """获取交易对列表"""
        try:
            # 1. 参数验证
            # 2. 业务逻辑
            # 3. 数据访问
            # 4. 结果处理
            pass
        except Exception as e:
            self.logger.error(f"获取交易对失败: {e}")
            raise DataProviderException("获取交易对失败")
```

#### 仓储类结构
```python
class MarketDataRepository(BaseRepository, IMarketDataRepository):
    """市场数据仓储"""
    
    def __init__(self, db_manager: IDatabaseManager, logger: ILogger):
        super().__init__(db_manager, logger)
    
    async def get_symbols(self) -> List[Symbol]:
        """获取交易对列表"""
        query = "SELECT * FROM symbols WHERE active = 1"
        return await self.fetch_all(query, Symbol)
```

### 3. 依赖注入

#### 服务注册
```python
# 在应用启动时注册服务
container = DIContainer()

# 注册基础设施服务
container.register_singleton(ILogger, StructuredLogger)
container.register_singleton(IConfigManager, ConfigManager)
container.register_singleton(IDatabaseManager, DatabaseManager)

# 注册仓储服务
container.register_singleton(IMarketDataRepository, MarketDataRepository)

# 注册业务服务
container.register_singleton(IMarketDataService, MarketDataService)
```

#### 服务使用
```python
# 在API端点中使用服务
@router.get("/symbols")
async def get_symbols(
    service: IMarketDataService = Depends(get_market_data_service)
):
    try:
        symbols = await service.get_symbols()
        return create_success_response(symbols)
    except Exception as e:
        return create_error_response(str(e))
```

### 4. 异常处理

#### 异常层次结构
```python
QuantTradeException
├── ValidationException
├── DataProviderException
├── StrategyException
├── ResourceNotFoundException
└── ConfigurationException
```

#### 异常使用示例
```python
# 在服务层抛出业务异常
if not self.validate_symbol(symbol):
    raise ValidationException(
        message="无效的交易对符号",
        error_code="INVALID_SYMBOL",
        details={"symbol": symbol}
    )

# 在API层处理异常
try:
    result = await service.get_market_data(symbol)
    return create_success_response(result)
except ValidationException as e:
    return create_error_response(
        message=e.message,
        error_code=e.error_code,
        status_code=400
    )
```

### 5. 配置管理

#### 配置文件结构
```json
{
  "app": {
    "name": "QuantTradeSys",
    "version": "2.0.0",
    "debug": false
  },
  "database": {
    "path": "quanthub.db",
    "max_workers": 4
  },
  "market_data": {
    "max_limit": 1000,
    "cache_ttl": 300
  }
}
```

#### 配置使用
```python
class MarketDataService(BaseService):
    def __init__(self, config: IConfigManager, ...):
        super().__init__(config, ...)
        self.max_limit = config.get("market_data.max_limit", 1000)
        self.cache_ttl = config.get("market_data.cache_ttl", 300)
```

### 6. 日志记录

#### 日志级别
- `DEBUG`: 详细的调试信息
- `INFO`: 一般信息记录
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

#### 日志使用
```python
class MarketDataService(BaseService):
    async def get_market_data(self, symbol: str):
        self.logger.info(f"开始获取市场数据: {symbol}")
        
        try:
            data = await self.repository.get_market_data(symbol)
            self.logger.info(f"成功获取市场数据: {symbol}, 记录数: {len(data)}")
            return data
        except Exception as e:
            self.logger.error(f"获取市场数据失败: {symbol}, 错误: {e}")
            raise
```

## 开发流程

### 1. 新功能开发

#### 步骤1: 定义接口
```python
# 在 app/core/interfaces/ 中定义接口
class INewFeatureService(ABC):
    @abstractmethod
    async def new_method(self, param: str) -> Result:
        pass
```

#### 步骤2: 实现服务
```python
# 在 app/core/services/ 中实现服务
class NewFeatureService(BaseService, INewFeatureService):
    async def new_method(self, param: str) -> Result:
        # 实现业务逻辑
        pass
```

#### 步骤3: 注册服务
```python
# 在依赖注入容器中注册
container.register_singleton(INewFeatureService, NewFeatureService)
```

#### 步骤4: 创建API端点
```python
# 在 app/api/v1/ 中创建端点
@router.post("/new-feature")
async def new_feature_endpoint(
    param: str,
    service: INewFeatureService = Depends(get_new_feature_service)
):
    result = await service.new_method(param)
    return create_success_response(result)
```

### 2. 数据模型开发

#### 定义模型
```python
# 在 app/core/models/ 中定义模型
@dataclass
class MarketData:
    symbol: str
    price: Decimal
    volume: Decimal
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": str(self.price),
            "volume": str(self.volume),
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        return cls(
            symbol=data["symbol"],
            price=Decimal(data["price"]),
            volume=Decimal(data["volume"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
```

### 3. 数据访问开发

#### 定义仓储接口
```python
class IMarketDataRepository(ABC):
    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Optional[MarketData]:
        pass
    
    @abstractmethod
    async def save(self, data: MarketData) -> MarketData:
        pass
```

#### 实现仓储
```python
class MarketDataRepository(BaseRepository, IMarketDataRepository):
    async def get_by_symbol(self, symbol: str) -> Optional[MarketData]:
        query = "SELECT * FROM market_data WHERE symbol = ?"
        row = await self.fetch_one(query, (symbol,))
        return MarketData.from_dict(row) if row else None
    
    async def save(self, data: MarketData) -> MarketData:
        query = """
            INSERT INTO market_data (symbol, price, volume, timestamp)
            VALUES (?, ?, ?, ?)
        """
        await self.execute(query, (
            data.symbol, data.price, data.volume, data.timestamp
        ))
        return data
```

## 测试指南

### 1. 单元测试

#### 服务测试
```python
class TestMarketDataService:
    @pytest.fixture
    def service(self):
        mock_repo = Mock(spec=IMarketDataRepository)
        mock_logger = Mock(spec=ILogger)
        mock_config = Mock(spec=IConfigManager)
        return MarketDataService(mock_repo, mock_logger, mock_config)
    
    async def test_get_symbols_success(self, service):
        # 准备测试数据
        expected_symbols = [Symbol("BTCUSDT"), Symbol("ETHUSDT")]
        service.repository.get_symbols.return_value = expected_symbols
        
        # 执行测试
        result = await service.get_symbols()
        
        # 验证结果
        assert result == expected_symbols
        service.repository.get_symbols.assert_called_once()
```

#### API测试
```python
class TestMarketDataAPI:
    async def test_get_symbols_endpoint(self, client):
        response = await client.get("/api/v1/market-data/symbols")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
```

### 2. 集成测试

```python
class TestMarketDataIntegration:
    async def test_full_flow(self, app):
        # 测试完整的数据流
        # API -> Service -> Repository -> Database
        pass
```

### 3. 性能测试

```python
class TestPerformance:
    async def test_api_response_time(self, client):
        start_time = time.time()
        response = await client.get("/api/v1/market-data/symbols")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 0.5  # 响应时间小于500ms
```

## 部署指南

### 1. 环境配置

#### 开发环境
```bash
# 设置环境变量
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG

# 启动应用
python main.py
```

#### 生产环境
```bash
# 设置环境变量
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export SECRET_KEY=your-production-secret-key

# 启动应用
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### 2. 数据库迁移

```bash
# 运行数据迁移
python scripts/run_migration.py all

# 验证迁移结果
python scripts/run_migration.py validate
```

### 3. 健康检查

```python
# 添加健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }
```

## 最佳实践

### 1. 代码质量

- 使用类型注解
- 编写文档字符串
- 遵循PEP 8规范
- 保持函数简洁（<50行）
- 避免深层嵌套（<4层）

### 2. 性能优化

- 使用异步编程
- 实现适当的缓存
- 优化数据库查询
- 避免N+1查询问题
- 使用连接池

### 3. 安全考虑

- 验证所有输入数据
- 使用参数化查询
- 实现适当的认证授权
- 记录安全相关事件
- 定期更新依赖包

### 4. 监控和日志

- 记录关键业务事件
- 监控系统性能指标
- 设置适当的告警
- 定期分析日志
- 实现分布式追踪

## 常见问题

### Q1: 如何添加新的API端点？
A1: 按照开发流程，先定义接口，实现服务，注册依赖，最后创建API端点。

### Q2: 如何处理数据库迁移？
A2: 使用提供的迁移工具，先备份数据，然后运行迁移脚本。

### Q3: 如何进行性能调优？
A3: 使用性能分析工具，识别瓶颈，优化数据库查询和缓存策略。

### Q4: 如何确保代码质量？
A4: 编写单元测试，使用代码检查工具，进行代码审查。

## 工具和资源

### 开发工具
- IDE: PyCharm, VSCode
- 代码格式化: black, isort
- 代码检查: flake8, mypy
- 测试框架: pytest, pytest-asyncio

### 监控工具
- 日志: structlog
- 性能: py-spy, memory_profiler
- 数据库: sqlite3 CLI

### 文档工具
- API文档: FastAPI自动生成
- 代码文档: Sphinx
- 架构图: PlantUML, Mermaid

---

*本指南会随着项目的发展持续更新，请定期查看最新版本。*