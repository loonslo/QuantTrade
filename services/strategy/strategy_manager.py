# -*- coding: utf-8 -*-
"""
策略管理器
负责策略的初始化、管理和更新
"""

from typing import Dict, Any, List, Optional
import json
from utils.core.logger_manager import get_logger
from services.orm.strategies_orm import get_strategies_service_orm
from data.models.market_data.strategies_model import Strategy


class StrategyManager:
    """策略管理器"""

    def __init__(self):
        self.logger = get_logger('strategy_manager')
        self.strategies_service = get_strategies_service_orm()

    def initialize_default_strategies(self) -> bool:
        """初始化系统默认策略"""
        try:
            self.logger.info("开始初始化系统默认策略...")

            # 定义系统默认策略
            default_strategies = [
                {
                    'strategy_id': 'rsi_tech_v1',
                    'strategy_name': 'RSI超买超卖策略',
                    'description': '基于RSI指标的超买超卖交易策略，适合震荡市场',
                    'strategy_source': 'system',
                    'strategy_category': 'technical',
                    'version': '1.0',
                    'author': 'System',
                    'parameters': json.dumps({
                        'rsi_period': 14,
                        'oversold_threshold': 30,
                        'overbought_threshold': 70,
                        'support_tolerance_pct': 2.0,
                        'resistance_tolerance_pct': 2.0,
                        'min_confidence': 0.5
                    }),
                    'default_parameters': json.dumps({
                        'rsi_period': 14,
                        'oversold_threshold': 30,
                        'overbought_threshold': 70
                    }),
                    'is_active': True,
                    'is_default': True,
                    'is_public': True,
                },
                {
                    'strategy_id': 'macd_tech_v1',
                    'strategy_name': 'MACD金叉死叉策略',
                    'description': '基于MACD指标的金叉死叉交易策略，适合趋势市场',
                    'strategy_source': 'system',
                    'strategy_category': 'technical',
                    'version': '1.0',
                    'author': 'System',
                    'parameters': json.dumps({
                        'fast_period': 12,
                        'slow_period': 26,
                        'signal_period': 9,
                        'min_confidence': 0.5,
                        'trend_verification': True
                    }),
                    'default_parameters': json.dumps({
                        'fast_period': 12,
                        'slow_period': 26,
                        'signal_period': 9
                    }),
                    'is_active': True,
                    'is_default': True,
                    'is_public': True,
                },
                {
                    'strategy_id': 'trend_tech_v1',
                    'strategy_name': '趋势反转策略',
                    'description': '基于趋势方向变化的反转交易策略',
                    'strategy_source': 'system',
                    'strategy_category': 'technical',
                    'version': '1.0',
                    'author': 'System',
                    'parameters': json.dumps({
                        'trend_lookback': 5,
                        'min_trend_strength': 0.5,
                        'min_confidence': 0.5,
                        'confirmation_required': True
                    }),
                    'default_parameters': json.dumps({
                        'trend_lookback': 5,
                        'min_trend_strength': 0.5
                    }),
                    'is_active': True,
                    'is_default': True,
                    'is_public': True,
                },
                {
                    'strategy_id': 'breakout_tech_v1',
                    'strategy_name': '突破策略',
                    'description': '基于支撑阻力位突破的交易策略',
                    'strategy_source': 'system',
                    'strategy_category': 'technical',
                    'version': '1.0',
                    'author': 'System',
                    'parameters': json.dumps({
                        'breakout_threshold_pct': 1.0,
                        'volume_confirmation': True,
                        'volume_threshold': 1.2,
                        'min_strength_score': 60,
                        'min_confidence': 0.5
                    }),
                    'default_parameters': json.dumps({
                        'breakout_threshold_pct': 1.0,
                        'volume_confirmation': True,
                        'volume_threshold': 1.2
                    }),
                    'is_active': True,
                    'is_default': True,
                    'is_public': True,
                },
            ]

            created_count = 0
            updated_count = 0

            for strategy_data in default_strategies:
                strategy_id = strategy_data['strategy_id']

                # 检查策略是否已存在
                existing = self.strategies_service.get_strategy_by_id(strategy_id)

                if existing:
                    # 更新策略
                    self.logger.info(f"更新策略: {strategy_id}")
                    self.strategies_service.update_strategy(strategy_id, strategy_data)
                    updated_count += 1
                else:
                    # 创建策略
                    self.logger.info(f"创建策略: {strategy_id}")
                    self.strategies_service.create_strategy(strategy_data)
                    created_count += 1

            self.logger.info(f"策略初始化完成: 新建 {created_count} 个, 更新 {updated_count} 个")
            return True

        except Exception as e:
            self.logger.error(f"策略初始化失败: {e}", exc_info=True)
            return False

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """获取策略"""
        return self.strategies_service.get_strategy_by_id(strategy_id)

    def get_active_strategies(self, source: Optional[str] = None,
                             category: Optional[str] = None) -> List[Strategy]:
        """获取激活的策略"""
        return self.strategies_service.get_active_strategies(source, category)

    def create_user_strategy(self, strategy_data: Dict[str, Any]) -> Optional[Strategy]:
        """创建用户策略"""
        # 设置默认值
        strategy_data.setdefault('strategy_source', 'user')
        strategy_data.setdefault('strategy_category', 'quant')
        strategy_data.setdefault('version', '1.0')
        strategy_data.setdefault('is_active', True)
        strategy_data.setdefault('is_default', False)
        strategy_data.setdefault('is_public', False)

        # 确保参数是JSON字符串
        if 'parameters' in strategy_data and isinstance(strategy_data['parameters'], dict):
            strategy_data['parameters'] = json.dumps(strategy_data['parameters'])

        if 'default_parameters' in strategy_data and isinstance(strategy_data['default_parameters'], dict):
            strategy_data['default_parameters'] = json.dumps(strategy_data['default_parameters'])

        return self.strategies_service.create_strategy(strategy_data)

    def update_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]) -> Optional[Strategy]:
        """更新策略"""
        # 确保参数是JSON字符串
        if 'parameters' in strategy_data and isinstance(strategy_data['parameters'], dict):
            strategy_data['parameters'] = json.dumps(strategy_data['parameters'])

        if 'default_parameters' in strategy_data and isinstance(strategy_data['default_parameters'], dict):
            strategy_data['default_parameters'] = json.dumps(strategy_data['default_parameters'])

        return self.strategies_service.update_strategy(strategy_id, strategy_data)

    def delete_strategy(self, strategy_id: str) -> bool:
        """删除策略"""
        return self.strategies_service.delete_strategy(strategy_id)

    def update_strategy_performance(self, strategy_id: str, metrics: Dict[str, Any]) -> bool:
        """更新策略性能指标"""
        return self.strategies_service.update_performance_metrics(strategy_id, metrics)

    def get_strategies_performance_stats(self) -> Dict[str, Any]:
        """获取策略性能统计"""
        return self.strategies_service.get_strategies_performance_stats()

    def get_strategy_config_for_signal(self, strategy_id: str) -> Dict[str, Any]:
        """获取策略配置，用于交易信号生成"""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            self.logger.warning(f"策略不存在: {strategy_id}")
            return {}

        config = {
            'strategy_id': strategy.strategy_id,
            'strategy_name': strategy.strategy_name,
            'strategy_source': strategy.strategy_source,
            'strategy_category': strategy.strategy_category,
            'version': strategy.version,
            'parameters': strategy.get_parameters_dict(),
            'default_parameters': strategy.get_default_parameters_dict(),
        }

        return config


# 全局实例
_strategy_manager: Optional[StrategyManager] = None


def get_strategy_manager() -> StrategyManager:
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager
