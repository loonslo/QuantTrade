# LLM (Large Language Model) 集成模块

## 概述

LLM模块提供了统一的大模型API集成接口，支持多种主流大模型服务商，包括：

- **OpenAI** - GPT-4, GPT-3.5等模型
- **Anthropic Claude** - Claude 3系列模型  
- **SiliconFlow** - 通义千问等开源模型
- **本地模型** - Ollama、vLLM等本地部署模型

## 架构设计

```
api/llm/
├── __init__.py          # 模块初始化
├── base.py              # 抽象基类定义
├── providers/           # 具体提供商实现
├── manager.py           # LLM管理器
├── config.py            # 配置管理
└── README.md            # 本文档
```

### 核心组件

1. **BaseLLMProvider** - 所有LLM提供商的抽象基类
2. **LLMManager** - 统一管理多个LLM提供商
3. **具体提供商实现** - 各API的具体调用逻辑
4. **配置管理** - 环境变量和配置的统一管理

## 快速开始

### 1. 环境配置

编辑项目根目录的 `config.json` 文件，在 `llm` 部分配置API密钥：

```json
{
  "llm": {
    "default_provider": "siliconflow",
    "providers": {
      "openai": {
        "enabled": true,
        "api_key": "sk-your-openai-key",
        "base_url": "https://api.openai.com/v1"
      },
      "claude": {
        "enabled": true,
        "api_key": "sk-ant-your-claude-key"
      },
      "siliconflow": {
        "enabled": true,
        "api_key": "your-siliconflow-key",
        "base_url": "https://api.siliconflow.com"
      },
      "local": {
        "enabled": false,
        "base_url": "http://localhost:11434",
        "model": "llama2"
      }
    },
    "default_parameters": {
      "temperature": 0.7,
      "max_tokens": 2000,
      "top_p": 0.9
    }
  }
}
```

### 2. 基本使用

```python
from api import llm_manager

# 分析市场数据
result = await llm_manager.analyze_with_llm(
    data_frames=[{"symbol": "BTCUSDT", "data": "..."}],
    analysis_type="market_trend",
    provider_name="siliconflow"  # 可选，指定提供商
)

if result["success"]:
    print(f"分析完成，使用提供商: {result['provider']}")
    print(f"分析结果: {result['analysis']}")
else:
    print(f"分析失败: {result['error']}")
```

### 3. 故障转移

LLM管理器支持自动故障转移：

```python
# 如果首选提供商失败，会自动尝试其他可用提供商
result = await llm_manager.analyze_with_llm(
    data_frames=data,
    analysis_type="risk_assessment",
    provider_name="openai",  # 首选
    fallback_providers=["siliconflow", "claude"]  # 故障转移顺序
)
```

## 配置选项

### 配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `llm.default_provider` | 默认LLM提供商 | `siliconflow` |
| `llm.providers.openai.enabled` | 是否启用OpenAI | `false` |
| `llm.providers.openai.api_key` | OpenAI API密钥 | `""` |
| `llm.providers.openai.base_url` | OpenAI API地址 | `https://api.openai.com/v1` |
| `llm.providers.claude.enabled` | 是否启用Claude | `false` |
| `llm.providers.claude.api_key` | Claude API密钥 | `""` |
| `llm.providers.siliconflow.enabled` | 是否启用SiliconFlow | `true` |
| `llm.providers.siliconflow.api_key` | SiliconFlow API密钥 | `""` |
| `llm.providers.siliconflow.base_url` | SiliconFlow API地址 | `https://api.siliconflow.com` |
| `llm.providers.local.enabled` | 是否启用本地模型 | `false` |
| `llm.providers.local.base_url` | 本地模型地址 | `http://localhost:11434` |
| `llm.providers.local.model` | 本地模型名称 | `llama2` |
| `llm.default_parameters.temperature` | 默认温度参数 | `0.7` |
| `llm.default_parameters.max_tokens` | 默认最大token数 | `2000` |
| `llm.default_parameters.top_p` | 默认top_p参数 | `0.9` |

### 模型参数

```python
# 自定义模型参数
parameters = {
    "temperature": 0.3,      # 降低随机性
    "max_tokens": 4000,      # 增加输出长度
    "top_p": 0.8            # 调整采样策略
}

response = await provider.generate_response(
    prompt="分析请求",
    parameters=parameters
)
```

## 扩展新的LLM提供商

### 1. 继承基类

```python
from .llm_provider_base import BaseLLMProvider

class NewProvider(BaseLLMProvider):
    def __init__(self, api_key: str, **kwargs):
        super().__init__("new_provider", api_key, **kwargs)
    
    async def generate_response(self, prompt: str, context=None, parameters=None):
        # 实现具体的API调用逻辑
        pass
    
    def get_model_info(self):
        return {
            "provider": "NewProvider",
            "capabilities": ["chat", "analysis"]
        }
    
    async def test_connection(self):
        # 实现连接测试
        pass
```

### 2. 注册到管理器

```python
# 在 manager.py 中添加
from .providers import NewProvider

# 在 _load_config 方法中添加
if new_provider_enabled:
    self.providers["new_provider"] = NewProvider(api_key)
```

## 错误处理

### 连接状态管理

每个提供商都会维护自己的连接状态：

```python
provider = llm_manager.get_provider("openai")

# 检查服务状态
if provider.is_service_available():
    print("服务正常")
else:
    print(f"服务异常: {provider.get_last_error()}")
```

### 批量测试

```python
# 测试所有提供商连接
status = await llm_manager.test_all_connections()
for provider, is_healthy in status.items():
    print(f"{provider}: {'正常' if is_healthy else '异常'}")
```

## 性能优化

### 1. 连接池管理

提供商会自动管理HTTP连接池，避免重复创建连接。

### 2. 超时控制

```python
# 配置超时参数
LLM_REQUEST_TIMEOUT=30      # 请求超时30秒
LLM_MAX_RETRIES=3          # 最大重试3次
LLM_RETRY_DELAY=1.0        # 重试延迟1秒
```

### 3. 并发控制

LLM管理器支持并发请求，但建议控制并发数量以避免API限制。

## 监控和日志

### 日志级别

- `INFO` - 正常操作信息
- `WARNING` - 警告信息（如故障转移）
- `ERROR` - 错误信息

### 状态监控

```python
# 获取详细状态
status = await mcp_service.get_detailed_status()
print(f"总提供商数: {status['total_providers']}")
print(f"可用提供商数: {status['available_providers']}")

# 获取提供商信息
providers_info = await mcp_service.get_llm_providers_info()
for name, info in providers_info["providers"].items():
    print(f"{name}: {info['status']}")
```

## 最佳实践

### 1. 提供商选择

- 根据任务类型选择合适的提供商
- 设置合理的故障转移顺序
- 监控各提供商的使用情况和成本

### 2. 提示词优化

- 使用清晰的系统提示词
- 根据分析类型定制提示词模板
- 避免过于复杂的多轮对话

### 3. 错误处理

- 实现适当的重试机制
- 记录详细的错误日志
- 提供用户友好的错误信息

### 4. 成本控制

- 监控token使用量
- 设置合理的max_tokens限制
- 考虑使用更经济的模型

## 故障排除

### 常见问题

1. **API密钥无效**
   - 检查环境变量是否正确设置
   - 验证API密钥是否有效

2. **连接超时**
   - 检查网络连接
   - 调整超时参数
   - 考虑使用代理

3. **配额限制**
   - 检查API使用配额
   - 实现请求频率限制
   - 考虑升级API计划

### 调试模式

```python
import logging
logging.getLogger("api.llm").setLevel(logging.DEBUG)
```

## 更新日志

### v2.0.0
- 重构为模块化架构
- 支持多种LLM提供商
- 实现故障转移机制
- 统一配置管理

### v1.0.0
- 初始版本
- 仅支持SiliconFlow API
