"""
策略层模块
提供两种类型的策略：
1. Backtrader策略：基于Backtrader框架的复杂策略
2. 用户自定义策略：继承SimpleStrategyBase，专注于信号生成
"""

# ========== 用户自定义策略（简化功能） ==========
from .base.simple_strategy_base import SimpleStrategyBase
from .simple_strategy_runner import SimpleStrategyRunner, run_simple_strategy
from .enhanced_strategy_runner import EnhancedStrategyRunner, run_enhanced_strategy

__all__ = [
    # ========== 用户自定义策略（简化功能） ==========
    # 简化策略基类
    'SimpleStrategyBase',
    
    # 策略运行器
    'SimpleStrategyRunner',
    'run_simple_strategy',
    'EnhancedStrategyRunner',
    'run_enhanced_strategy'
] 