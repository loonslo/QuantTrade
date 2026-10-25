"""
分析模块
提供策略性能分析、风险分析等功能
"""

from .performance.unified_metrics import UnifiedPerformanceAnalyzer, PerformanceMetrics


def __getattr__(name):
    if name == 'StrategyAnalyzer':
        from .strategy_analyzer import StrategyAnalyzer
        return StrategyAnalyzer
    if name == 'TechnicalAnalyzer':
        from .technical_analysis import TechnicalAnalyzer
        return TechnicalAnalyzer
    raise AttributeError(name)

__all__ = [
    'UnifiedPerformanceAnalyzer',
    'PerformanceMetrics',
    'StrategyAnalyzer',
    'TechnicalAnalyzer']
