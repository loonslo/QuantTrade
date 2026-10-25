# -*- coding: utf-8 -*-
"""
统一策略服务
提供策略管理、验证和配置功能
"""

from typing import Dict, Any, List
import json
from pathlib import Path

from services.base.base_service import BaseService, ServiceMixin
from services.base.interfaces.services import IStrategyService
from utils.core.logger_manager import get_logger
from utils.validation.exceptions import StrategyException

# 为了向后兼容，提供别名
StrategyValidationError = StrategyException

class StrategyService(BaseService, ServiceMixin, IStrategyService):
    """
    策略服务
    提供策略管理、验证和配置功能
    """

    def __init__(self):
        """初始化策略服务"""
        super().__init__()
        self.logger = get_logger('strategy_service')
        self.strategies_dir = Path("user_strategies")

    async def get_strategy_list(self) -> List[Dict[str, Any]]:
        """
        获取策略列表

        Returns:
            List[Dict[str, Any]]: 策略列表
        """
        try:
            strategies = []

            if not self.strategies_dir.exists():
                return strategies

            for strategy_dir in self.strategies_dir.iterdir():
                if strategy_dir.is_dir():
                    config_file = strategy_dir / "config.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                config = json.load(f)

                            strategies.append({
                                "name": strategy_dir.name,
                                "description": config.get("description", ""),
                                "category": config.get("category", "unknown"),
                                "version": config.get("version", "1.0.0"),
                                "timeframes": config.get("timeframes", []),
                                "parameters_count": len(config.get("parameters", {}))
                            })
                        except Exception as e:
                            self.logger.warning(f"读取策略配置失败 {strategy_dir.name}: {e}")

            return strategies

        except Exception as e:
            self.logger.error(f"获取策略列表失败: {e}")
            raise StrategyValidationError(f"获取策略列表失败: {e}")

    async def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        获取策略配置

        Args:
            strategy_name: 策略名称

        Returns:
            Dict[str, Any]: 策略配置
        """
        try:
            strategy_dir = self.strategies_dir / strategy_name
            config_file = strategy_dir / "config.json"

            if not config_file.exists():
                raise StrategyValidationError(f"策略 {strategy_name} 不存在")

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            return config

        except Exception as e:
            self.logger.error(f"获取策略配置失败 {strategy_name}: {e}")
            raise StrategyValidationError(f"获取策略配置失败: {e}")

    async def validate_strategy_parameters(self, strategy_name: str, parameters: Dict[str, Any]) -> bool:
        """
        验证策略参数

        Args:
            strategy_name: 策略名称
            parameters: 参数字典

        Returns:
            bool: 验证结果
        """
        try:
            config = await self.get_strategy_config(strategy_name)
            param_configs = config.get("parameters", {})

            for param_name, param_value in parameters.items():
                if param_name not in param_configs:
                    raise StrategyValidationError(
                        f"未知参数: {param_name}",
                        strategy_name,
                        {"param": param_name, "available_params": list(param_configs.keys())}
                    )

                param_config = param_configs[param_name]
                expected_type = param_config.get("type", "str")

                # 验证参数类型
                if expected_type == "int" and not isinstance(param_value, int):
                    raise StrategyValidationError(
                        f"参数类型错误: {param_name} 应为整数",
                        strategy_name,
                        {"param": param_name, "expected_type": "int", "actual_type": type(param_value).__name__}
                    )
                elif expected_type == "float" and not isinstance(param_value, (int, float)):
                    raise StrategyValidationError(
                        f"参数类型错误: {param_name} 应为数字",
                        strategy_name,
                        {"param": param_name, "expected_type": "float", "actual_type": type(param_value).__name__}
                    )
                elif expected_type == "str" and not isinstance(param_value, str):
                    raise StrategyValidationError(
                        f"参数类型错误: {param_name} 应为字符串",
                        strategy_name,
                        {"param": param_name, "expected_type": "str", "actual_type": type(param_value).__name__}
                    )

                # 验证参数范围
                if "min" in param_config and param_value < param_config["min"]:
                    raise StrategyValidationError(
                        f"参数值过小: {param_name} 不能小于 {param_config['min']}",
                        strategy_name,
                        {"param": param_name, "value": param_value, "min": param_config["min"]}
                    )

                if "max" in param_config and param_value > param_config["max"]:
                    raise StrategyValidationError(
                        f"参数值过大: {param_name} 不能大于 {param_config['max']}",
                        strategy_name,
                        {"param": param_name, "value": param_value, "max": param_config["max"]}
                    )

            return True

        except Exception as e:
            self.logger.error(f"验证策略参数失败 {strategy_name}: {e}")
            raise StrategyValidationError(f"验证策略参数失败: {e}")

    async def create_strategy(self, strategy_name: str, config: Dict[str, Any]) -> bool:
        """
        创建策略

        Args:
            strategy_name: 策略名称
            config: 策略配置

        Returns:
            bool: 创建结果
        """
        try:
            strategy_dir = self.strategies_dir / strategy_name
            strategy_dir.mkdir(exist_ok=True)

            config_file = strategy_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.logger.info(f"策略 {strategy_name} 创建成功")
            return True

        except Exception as e:
            self.logger.error(f"创建策略失败 {strategy_name}: {e}")
            raise StrategyValidationError(f"创建策略失败: {e}")

    async def update_strategy(self, strategy_name: str, config: Dict[str, Any]) -> bool:
        """
        更新策略

        Args:
            strategy_name: 策略名称
            config: 策略配置

        Returns:
            bool: 更新结果
        """
        try:
            strategy_dir = self.strategies_dir / strategy_name
            if not strategy_dir.exists():
                raise StrategyValidationError(f"策略 {strategy_name} 不存在")

            config_file = strategy_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.logger.info(f"策略 {strategy_name} 更新成功")
            return True

        except Exception as e:
            self.logger.error(f"更新策略失败 {strategy_name}: {e}")
            raise StrategyValidationError(f"更新策略失败: {e}")

    async def delete_strategy(self, strategy_name: str) -> bool:
        """
        删除策略

        Args:
            strategy_name: 策略名称

        Returns:
            bool: 删除结果
        """
        try:
            strategy_dir = self.strategies_dir / strategy_name
            if not strategy_dir.exists():
                raise StrategyValidationError(f"策略 {strategy_name} 不存在")

            import shutil
            shutil.rmtree(strategy_dir)

            self.logger.info(f"策略 {strategy_name} 删除成功")
            return True

        except Exception as e:
            self.logger.error(f"删除策略失败 {strategy_name}: {e}")
            raise StrategyValidationError(f"删除策略失败: {e}")

# 全局实例
_strategy_service = None

def get_strategy_service() -> StrategyService:
    """获取策略服务实例"""
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategyService()
    return _strategy_service