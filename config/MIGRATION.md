# 配置管理器整合迁移说明

## 变更概述

为了消除重复代码和提高维护性，我们对配置管理系统进行了整合：

## 主要变更

### 1. 删除重复的配置管理器
- ❌ 删除了 `config/core/config_manager.py`
- ✅ 保留 `utils/core/config_manager.py` 作为统一的配置管理器

### 2. 配置文件整合
- ❌ 删除了 `config/base.json`
- ✅ 将其内容合并到根目录的 `config.json` 中

### 3. 专用配置管理器简化
- ✅ `ServiceConfigManager` 现在基于主配置管理器
- ✅ `LLMConfigManager` 现在基于主配置管理器
- ✅ 减少了重复的配置加载逻辑

## 迁移指南

### 对于开发者

1. **导入变更**：
   ```python
   # 旧方式
   from config.core.config_manager import ConfigManager
   
   # 新方式
   from utils.core.config_manager import ConfigManager
   ```

2. **配置文件路径**：
   - 主配置文件现在统一为根目录的 `config.json`
   - 环境特定配置仍在 `config/environments/` 目录下

3. **服务配置获取**：
   ```python
   # 推荐方式
   from utils.services import get_config_manager
   service_config = get_config_manager()
   
   # 或直接使用主配置管理器
   from utils.core.config_manager import config_manager
   value = config_manager.get("service.key", default_value)
   ```

### 配置结构

新的统一配置文件 `config.json` 包含以下主要部分：

- `app`: 应用基本信息
- `server`: 服务器配置
- `database`: 数据库配置
- `api`: API配置
- `logging`: 日志配置
- `backtest`: 回测配置
- `llm`: LLM提供商配置
- `risk`: 风险管理配置
- `strategy`: 策略配置

## 优势

1. **减少重复**：消除了多个配置管理器的重复实现
2. **统一接口**：所有配置都通过统一的接口访问
3. **更好的维护性**：只需要维护一个配置管理器
4. **向后兼容**：保持了原有的API接口

## 修复的导入问题

在整合过程中，我们修复了以下导入问题：

1. **重命名冲突的类**：
   - `services/llm/llm_config_manager.py` 中的 `LLMConfigManager` 重命名为 `LLMServiceConfigManager`
   - 避免与 `utils/services/llm_config_manager.py` 中的 `LLMConfigManager` 冲突

2. **修复配置路径**：
   - `config.python.` → `config.python_config.`
   - 修复了 scheduler_config 和 settings 的导入路径

3. **修复函数调用**：
   - `services/llm/llm_config.py` 中的 `get_config()` → `config_manager.load_config()`
   - `services/llm/providers.py` 中的 `.config` → `.llm_config`

## 注意事项

- 配置的内存更新不会自动持久化到文件
- 如需持久化配置更改，需要额外实现配置保存逻辑
- 环境变量覆盖功能仍然可用
- 所有导入问题已修复，项目应该可以正常运行