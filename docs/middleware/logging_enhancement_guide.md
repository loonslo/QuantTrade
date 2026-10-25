# 增强的日志中间件使用说明

## 🎯 功能概述

优化后的日志中间件现在可以记录详细的请求参数和响应参数，方便调试和问题排查。

## 📊 新增功能

### 1. 详细的请求参数记录
- **路径参数**: 记录URL路径中的参数
- **查询参数**: 记录URL查询字符串参数
- **请求体**: 记录POST/PUT/PATCH请求的请求体内容
- **请求头**: 记录非敏感的请求头信息
- **敏感信息过滤**: 自动过滤Authorization、Cookie等敏感信息

### 2. 详细的响应参数记录
- **响应头**: 记录非敏感的响应头信息
- **响应体**: 记录JSON响应内容
- **内容截断**: 自动截断过长的内容，避免日志过长

### 3. 配置选项
- **log_details**: 控制是否记录详细参数（默认：True）
- **format_responses**: 控制是否格式化响应（默认：True）

## 🔧 配置方法

### 环境变量配置
```bash
# 启用详细日志记录（默认）
export API_LOG_DETAILS=true

# 禁用详细日志记录（生产环境推荐）
export API_LOG_DETAILS=false

# 启用响应格式化（默认）
export API_FORMAT_RESPONSES=true

# 禁用响应格式化
export API_FORMAT_RESPONSES=false
```

### 配置文件配置
在 `config/python/settings.py` 中：
```python
@dataclass
class APIConfig:
    log_details: bool = True  # 是否记录详细的请求和响应参数
    format_responses: bool = True  # 是否格式化响应
```

## 📝 日志格式示例

### 请求开始日志
```
2025-10-15 17:57:05,464 - middleware.logging - INFO - 请求开始 - ID: cef57941-99c5-49f4-ba52-4cb3a15d4200, 方法: GET, 路径: /api/mcp/status, 查询参数: {}, 客户端IP: 127.0.0.1, 用户代理: Mozilla/5.0...
```

### 请求参数日志（新增）
```
2025-10-15 17:57:05,465 - middleware.logging - INFO - 请求参数 - ID: cef57941-99c5-49f4-ba52-4cb3a15d4200, 参数: {'query_params': {'page': '1', 'size': '10'}, 'headers': {'content-type': 'application/json', 'user-agent': 'Mozilla/5.0...'}}
```

### 请求完成日志
```
2025-10-15 17:57:05,466 - middleware.logging - INFO - 请求完成 - ID: cef57941-99c5-49f4-ba52-4cb3a15d4200, 状态码: 200, 处理时间: 0.002s, 响应大小: 1024 bytes
```

### 响应内容日志（新增）
```
2025-10-15 17:57:05,467 - middleware.logging - INFO - 响应内容 - ID: cef57941-99c5-49f4-ba52-4cb3a15d4200, 内容: {'headers': {'content-type': 'application/json'}, 'body': {'success': True, 'data': {...}, 'message': '请求成功'}}
```

## 🧪 测试方法

### 1. 运行测试服务器
```bash
python test_logging_middleware.py
```

### 2. 测试简单GET请求
```bash
curl http://localhost:8001/api/test/simple
```

### 3. 测试复杂POST请求
```bash
curl -X POST http://localhost:8001/api/test/complex \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "value": 123}'
```

### 4. 测试错误请求
```bash
curl http://localhost:8001/api/test/error
```

## 🔍 日志查看技巧

### 1. 按请求ID过滤
```bash
grep "cef57941-99c5-49f4-ba52-4cb3a15d4200" logs/api.log
```

### 2. 查看请求参数
```bash
grep "请求参数" logs/api.log
```

### 3. 查看响应内容
```bash
grep "响应内容" logs/api.log
```

### 4. 查看错误请求
```bash
grep "请求异常" logs/api.log
```

## ⚙️ 性能考虑

### 1. 生产环境建议
- 设置 `API_LOG_DETAILS=false` 减少日志量
- 定期清理日志文件
- 使用日志轮转避免文件过大

### 2. 开发环境建议
- 保持 `API_LOG_DETAILS=true` 便于调试
- 使用日志级别 `DEBUG` 获取更多信息

### 3. 内容截断
- 请求体超过500字符会自动截断
- 响应内容超过1000字符会自动截断
- 敏感信息自动过滤

## 🛠️ 自定义配置

### 修改截断长度
在 `api/middleware/error_handler.py` 中：
```python
def _truncate_content(self, content, max_length: int = 1000) -> any:
    # 修改 max_length 参数
```

### 添加敏感字段
在 `_get_request_params` 方法中：
```python
sensitive_headers = ['authorization', 'cookie', 'x-api-key', 'your-custom-header']
```

## 📈 监控和告警

### 1. 错误率监控
```bash
grep "请求异常" logs/api.log | wc -l
```

### 2. 响应时间监控
```bash
grep "处理时间" logs/api.log | awk '{print $NF}' | sort -n
```

### 3. 请求量统计
```bash
grep "请求开始" logs/api.log | wc -l
```

## 🔧 故障排查

### 1. 请求参数问题
- 查看"请求参数"日志确认参数是否正确传递
- 检查请求头是否包含必要信息

### 2. 响应问题
- 查看"响应内容"日志确认响应格式
- 检查响应头是否正确设置

### 3. 性能问题
- 查看"处理时间"日志识别慢请求
- 分析请求参数大小是否过大

---

*最后更新: 2025-10-15*
