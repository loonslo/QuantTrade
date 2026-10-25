"""
策略对比模块

支持多个策略的回测结果对比分析。

功能：
- 多策略对比
- 排名和评分
- 可视化对比
- 对比报告生成

使用示例：
    from analytics.comparison import StrategyComparer, create_comparison_report

    # 方式1：使用对比器
    comparer = StrategyComparer()
    comparer.add_result('策略1', result1)
    comparer.add_result('策略2', result2)
    report = comparer.compare()
    comparer.print_report()

    # 方式2：快速对比
    results = [result1, result2]
    names = ['均线策略', 'MACD策略']
    report = create_comparison_report(results, names)
"""

from .comparer import (
    StrategyResult,
    StrategyComparer,
    create_comparison_report
)

__all__ = [
    'StrategyResult',
    'StrategyComparer',
    'create_comparison_report',
]
