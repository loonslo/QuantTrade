# API兼容性指南

本文档描述了QuantTradeSys API的兼容性策略和最佳实践。

## 版本控制策略

### 版本命名规范

- **主版本 (Major)**: 包含破坏性变更，如 v1 -> v2
- **次版本 (Minor)**: 向后兼容的功能添加
- **修订版本 (Patch)**: 向后兼容的问题修复

### 支持的版本

当前支持的API版本：
- **v1**: 当前稳定版本，完全支持
- **v2**: 计划中的下一个主版本

## 废弃策略

### 废弃流程

1. **警告阶段** (3个月)
   - 在响应头中添加废弃警告
   - 更新文档标记废弃状态
   - 提供迁移指南

2. **废弃阶段** (3个月)
   - 继续提供功能但标记为废弃
   - 在日志中记录使用情况
   - 推荐使用新的替代方案

3. **移除阶段**
   - 完全移除废弃的功能
   - 返回410 Gone状态码
   - 提供新端点的重定向信息

### 废弃通知

废弃的API端点会在HTTP响应头中包含以下信息：

```
X-API-Deprecated: true
X-API-Deprecation-Message: 此端点已废弃，请使用新端点
X-API-New-Endpoint: /api/v1/new-endpoint
X-API-Removal-Date: 2024-06-01
```

## 向后兼容性

### 兼容性保证

我们承诺在同一主版本内保持以下兼容性：

1. **端点路径**: 现有端点路径不会改变
2. **请求格式**: 现有请求参数和格式保持不变
3. **响应结构**: 现有响应字段不会被移除
4. **HTTP状态码**: 相同情况下返回相同的状态码

### 允许的变更

在不破坏兼容性的前提下，我们可能会：

1. **添加新的端点**
2. **添加新的请求参数**（可选）
3. **添加新的响应字段**
4. **改进错误消息**
5. **优化性能**

### 破坏性变更

以下变更被视为破坏性变更，需要升级主版本：

1. **移除或重命名端点**
2. **移除或重命名请求参数**
3. **移除或重命名响应字段**
4. **改变数据类型**
5. **改变HTTP状态码的语义**

## 迁移指南

### 从旧API迁移到v1

#### 端点映射

| 旧端点 | 新端点 | 说明 |
|--------|--------|------|
| `/symbols` | `/api/v1/market-data/symbols` | 获取交易对列表 |
| `/klines` | `/api/v1/market-data/klines` | 获取K线数据 |
| `/ticker` | `/api/v1/market-data/ticker` | 获取价格行情 |

#### 响应格式变更

**旧格式**:
```json
{
  "symbol": "BTCUSDT",
  "price": "50000",
  "timestamp": 1640995200
}
```

**新格式**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "price": "50000",
    "created_at": "2022-01-01T00:00:00Z",
    "timestamp": 1640995200  // 保留以兼容旧客户端
  },
  "message": "success"
}
```

### 迁移步骤

1. **更新端点URL**
   ```python
   # 旧代码
   response = requests.get("http://api.example.com/symbols")
   
   # 新代码
   response = requests.get("http://api.example.com/api/v1/market-data/symbols")
   ```

2. **更新响应处理**
   ```python
   # 旧代码
   data = response.json()
   symbols = data
   
   # 新代码
   data = response.json()
   if data["success"]:
       symbols = data["data"]
   ```

3. **添加错误处理**
   ```python
   response = requests.get("http://api.example.com/api/v1/market-data/symbols")
   data = response.json()
   
   if not data.get("success", False):
       print(f"API错误: {data.get('message', '未知错误')}")
       return
   
   symbols = data["data"]
   ```

## 测试兼容性

### 自动化测试

我们提供了兼容性测试工具来验证API的向后兼容性：

```python
from BackEnd.api import run_compatibility_tests

# 运行兼容性测试
summary = await run_compatibility_tests()
print(f"兼容性测试通过率: {summary['success_rate']:.1f}%")
```

### 手动测试

您也可以手动测试API兼容性：

1. **检查废弃警告**
   ```bash
   curl -I http://localhost:8000/old-endpoint
   # 查看响应头中的 X-API-Deprecated 字段
   ```

2. **比较响应格式**
   ```bash
   # 测试旧端点
   curl http://localhost:8000/old-endpoint
   
   # 测试新端点
   curl http://localhost:8000/api/v1/new-endpoint
   ```

## 最佳实践

### 客户端开发

1. **使用版本化的端点**
   ```python
   # 推荐：明确指定版本
   url = "http://api.example.com/api/v1/market-data/symbols"
   
   # 不推荐：使用无版本的端点
   url = "http://api.example.com/symbols"
   ```

2. **处理废弃警告**
   ```python
   response = requests.get(url)
   
   if response.headers.get("X-API-Deprecated") == "true":
       print(f"警告: {response.headers.get('X-API-Deprecation-Message')}")
       new_endpoint = response.headers.get("X-API-New-Endpoint")
       if new_endpoint:
           print(f"请迁移到: {new_endpoint}")
   ```

3. **优雅降级**
   ```python
   def get_symbols():
       # 尝试新端点
       try:
           response = requests.get("/api/v1/market-data/symbols")
           if response.status_code == 200:
               return response.json()["data"]
       except:
           pass
       
       # 回退到旧端点
       try:
           response = requests.get("/symbols")
           if response.status_code == 200:
               return response.json()
       except:
           pass
       
       raise Exception("无法获取符号列表")
   ```

### 服务端开发

1. **渐进式废弃**
   - 先添加新端点
   - 标记旧端点为废弃
   - 提供足够的迁移时间
   - 最后移除旧端点

2. **保持响应格式兼容**
   ```python
   # 在新响应中保留旧字段
   response_data = {
       "symbol": symbol,
       "created_at": timestamp_iso,
       "timestamp": timestamp_unix  # 保留旧字段
   }
   ```

3. **记录API使用情况**
   ```python
   # 记录废弃端点的使用
   if is_deprecated_endpoint(request.path):
       logger.warning(f"废弃端点被调用: {request.path}")
   ```

## 联系我们

如果您在API迁移过程中遇到问题，请：

1. 查看本文档的迁移指南
2. 运行兼容性测试工具
3. 查看API变更日志
4. 联系技术支持团队

---

*本文档会随着API的演进持续更新，请定期查看最新版本。*