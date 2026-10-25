"""
策略参数优化模块

提供多种参数优化算法：
1. 网格搜索 (GridSearchOptimizer) - 穷举所有参数组合
2. 遗传算法 (GeneticAlgorithmOptimizer) - 智能搜索最优参数
3. 随机搜索 (RandomSearchOptimizer) - 随机采样参数组合
4. 贝叶斯优化 (BayesianOptimizer) - 高效探索参数空间

使用示例：
    from analytics.optimization import (
        GridSearchOptimizer,
        GeneticAlgorithmOptimizer,
        RandomSearchOptimizer
    )

    # 定义回测函数
    def backtest_func(**params):
        # 调用回测引擎，返回性能指标
        return backtest_result.sharpe_ratio

    # 网格搜索
    optimizer = GridSearchOptimizer(backtest_func, param_grid)
    result = optimizer.optimize()

    # 遗传算法
    optimizer = GeneticAlgorithmOptimizer(backtest_func, param_bounds)
    result = optimizer.optimize(generations=50)
"""

from .optimizer import (
    BaseOptimizer,
    GridSearchOptimizer,
    RandomSearchOptimizer,
    GeneticAlgorithmOptimizer,
    BayesianOptimizer,
    OptimizationResult
)

# 向后兼容
from .genetic_algorithm import GeneticOptimizer
from .grid_search import GridSearchOptimizer

__all__ = [
    'BaseOptimizer',
    'GridSearchOptimizer',
    'RandomSearchOptimizer',
    'GeneticAlgorithmOptimizer',
    'BayesianOptimizer',
    'OptimizationResult',
    # 向后兼容
    'GeneticOptimizer',
    'GridSearchOptimizer',
]
