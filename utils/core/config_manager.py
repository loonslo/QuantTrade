"""
配置管理器 - 统一配置文件加载和验证
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from .interfaces import ConfigManagerInterface, ToolConfig

logger = logging.getLogger(__name__)

class ConfigManager(ConfigManagerInterface):
    """统一配置管理器"""
    
    def __init__(self, config_dir: str = "config", environment: str = "development"):
        # 初始化基类
        config = ToolConfig(
            name="ConfigManager",
            version="1.0.0",
            enabled=True,
            config={"config_dir": config_dir, "environment": environment}
        )
        super().__init__(config)
        
        self.config_dir = Path(config_dir)
        self.environment = environment
        self._config_cache = {}
    
    def load_config(self, config_name: str = "base") -> Dict[str, Any]:
        """加载配置文件"""
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        # 加载基础配置
        base_config = self._load_base_config()
        
        # 加载环境特定配置
        env_config = self._load_environment_config()
        
        # 合并配置
        merged_config = self._merge_configs(base_config, env_config)
        
        # 应用默认值
        final_config = self._apply_defaults(merged_config)
        
        # 验证配置
        self._validate_config(final_config)
        
        # 缓存配置
        self._config_cache[config_name] = final_config
        
        return final_config
    
    def _load_base_config(self) -> Dict[str, Any]:
        """加载基础配置"""
        # 首先尝试加载根目录的config.json
        root_config_file = Path("config.json")
        if root_config_file.exists():
            return self._load_json_file(root_config_file)
        
        # 如果不存在，尝试加载config目录下的base.json（向后兼容）
        base_file = self.config_dir / "base.json"
        return self._load_json_file(base_file)
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """加载环境配置"""
        env_file = self.config_dir / "environments" / f"{self.environment}.json"
        return self._load_json_file(env_file)
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON文件"""
        if not file_path.exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误 {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"加载配置文件失败 {file_path}: {e}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用默认值"""
        defaults_file = self.config_dir / "validation" / "defaults.json"
        defaults = self._load_json_file(defaults_file)
        
        merged = self._merge_configs(defaults, config)
        
        # 应用环境变量替换
        return self._substitute_env_vars(merged)
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        # 这里可以添加配置验证逻辑
        # 例如使用jsonschema库验证配置格式
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = self.load_config()
        keys = key.split('.')
        
        current = config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """递归替换环境变量"""
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # 替换 ${VAR_NAME} 格式的环境变量
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))  # 如果环境变量不存在，保持原样
            
            return re.sub(pattern, replace_var, config)
        else:
            return config
    
    def reload(self):
        """重新加载配置"""
        self._config_cache.clear()
    
    def get_environment(self) -> str:
        """获取当前环境"""
        return self.environment
    
    def set_environment(self, environment: str):
        """设置环境"""
        if environment != self.environment:
            self.environment = environment
            self.reload()
    
    def initialize(self) -> bool:
        """初始化配置管理器"""
        try:
            # 验证配置目录是否存在
            if not self.config_dir.exists():
                logger.warning(f"配置目录不存在: {self.config_dir}")
                return False
            
            # 尝试加载基础配置
            self.load_config()
            self._initialized = True
            logger.info("配置管理器初始化成功")
            return True
        except Exception as e:
            logger.error(f"配置管理器初始化失败: {e}")
            return False
    
    def cleanup(self) -> bool:
        """清理配置管理器资源"""
        try:
            self._config_cache.clear()
            self._initialized = False
            logger.info("配置管理器清理完成")
            return True
        except Exception as e:
            logger.error(f"配置管理器清理失败: {e}")
            return False

# 全局配置管理器实例
config_manager = ConfigManager(
    environment=os.getenv('ENVIRONMENT', 'development')
)

# 回测配置常量
BACKTEST_CONFIG = {
    'timeframe': '1h',
    'start_cash': 10000,
    'commission': 0.001,
    'slippage': 0.0,
    'symbol': 'BTC/USDT',
    'start_date': '2023-01-01',
    'end_date': '2024-01-01'
}

# 默认交易对
DEFAULT_SYMBOL = 'BTC/USDT'

# 可用策略列表
AVAILABLE_STRATEGIES = [
    'MaCrossStrategy',
    'MacdCrossStrategy', 
    'RsiSignalStrategy',
    'BollingerBreakoutStrategy',
    'MomentumStrategy',
    'MeanReversionStrategy',
    'BreakoutStrategy',
    'TurtleStrategy',
    'KdjSignalStrategy',
    'KamaCrossStrategy'
]

# 可用仓位管理类型
AVAILABLE_POSITION_TYPES = [
    'all_in',
    'two_three_five', 
    'fixed_ratio',
    'pyramid',
    'martingale',
    'kelly',
    'volatility'
]

def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    return config_manager
