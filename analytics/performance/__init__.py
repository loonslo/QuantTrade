"""
性能分析模块
提供各种性能指标和风险指标的计算
"""

from .unified_metrics import UnifiedPerformanceAnalyzer, PerformanceMetrics

def calculate_unified_metrics(trades, equity_curve, initial_cash, final_cash, **kwargs):
    """
    统一指标计算接口
    供CLI和API调用，确保指标计算一致性
    
    Args:
        trades: 交易记录列表
        equity_curve: 权益曲线数据
        initial_cash: 初始资金
        final_cash: 最终资金
        **kwargs: 其他参数
        
    Returns:
        PerformanceMetrics: 统一性能指标
    """
    analyzer = UnifiedPerformanceAnalyzer(**kwargs)
    returns = equity_curve.pct_change().fillna(0)
    realized = [trade for trade in trades if trade.get('pnl') is not None]
    return analyzer.calculate_all_metrics(returns, trades=realized)

__all__ = [
    'UnifiedPerformanceAnalyzer',
    'PerformanceMetrics',
    'calculate_unified_metrics',  # 新增统一接口
]
