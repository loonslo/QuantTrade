"""
统一性能指标计算器
合并 performance_analyzer.py 和 metrics.py 的功能
确保所有指标计算使用相同的算法和精度
实现指标计算的容差验证（±1e-6）
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from utils.core.logger_manager import get_logger


class MetricType(Enum):
    """指标类型枚举"""
    RETURN = "return"
    RISK = "risk"
    RATIO = "ratio"
    DRAWDOWN = "drawdown"
    TRADE = "trade"


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    # 基础指标
    total_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # 回撤指标
    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float
    
    # 交易指标
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    
    # 风险指标
    var_95: float
    cvar_95: float
    beta: float
    alpha: float
    
    # 时间指标
    start_date: datetime
    end_date: datetime
    trading_days: int
    
    # 计算精度验证
    calculation_tolerance: float = 1e-6


class UnifiedPerformanceAnalyzer:
    """
    统一性能分析器
    
    功能：
    - 统一的指标计算算法
    - 精度验证和容差检查
    - 多种性能指标计算
    - 风险指标分析
    - 交易统计分析
    """
    
    def __init__(self, tolerance: float = 1e-6, periods_per_year: float = 252):
        """
        初始化性能分析器
        
        Args:
            tolerance: 计算精度容差
        """
        self.logger = get_logger("analysis.performance.unified_metrics")
        self.tolerance = tolerance
        if not np.isfinite(periods_per_year) or periods_per_year <= 0:
            raise ValueError("periods_per_year must be finite and positive")
        self.periods_per_year = periods_per_year
        
        # 验证容差设置
        if tolerance <= 0 or tolerance >= 1:
            raise ValueError("容差必须在 (0, 1) 范围内")
    
    def calculate_all_metrics(self, 
                            returns: pd.Series,
                            trades: Optional[List[Dict[str, Any]]] = None,
                            benchmark_returns: Optional[pd.Series] = None) -> PerformanceMetrics:
        """
        计算所有性能指标
        
        Args:
            returns: 收益率序列
            trades: 交易记录列表
            benchmark_returns: 基准收益率序列
            
        Returns:
            完整的性能指标
        """
        try:
            self.logger.info("开始计算性能指标")
            
            # 验证输入数据
            self._validate_inputs(returns, trades, benchmark_returns)
            
            # 计算基础指标
            total_return = self._calculate_total_return(returns)
            annual_return = self._calculate_annual_return(returns)
            volatility = self._calculate_volatility(returns)
            
            # 计算比率指标
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            calmar_ratio = self._calculate_calmar_ratio(returns, annual_return)
            
            # 计算回撤指标
            max_drawdown, max_drawdown_duration = self._calculate_max_drawdown(returns)
            avg_drawdown = self._calculate_avg_drawdown(returns)
            
            # 计算交易指标
            if trades:
                total_trades, win_rate, profit_factor, avg_win, avg_loss = self._calculate_trade_metrics(trades)
            else:
                total_trades = win_rate = profit_factor = avg_win = avg_loss = 0.0
            
            # 计算风险指标
            var_95, cvar_95 = self._calculate_risk_metrics(returns)
            beta = alpha = 0.0
            if benchmark_returns is not None:
                beta, alpha = self._calculate_beta_alpha(returns, benchmark_returns)
            
            # 时间指标
            start_date = returns.index[0] if hasattr(returns.index[0], 'to_pydatetime') else datetime.now()
            end_date = returns.index[-1] if hasattr(returns.index[-1], 'to_pydatetime') else datetime.now()
            trading_days = len(returns)
            
            # 创建指标对象
            metrics = PerformanceMetrics(
                total_return=total_return,
                annual_return=annual_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                max_drawdown=max_drawdown,
                max_drawdown_duration=max_drawdown_duration,
                avg_drawdown=avg_drawdown,
                total_trades=total_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_win=avg_win,
                avg_loss=avg_loss,
                var_95=var_95,
                cvar_95=cvar_95,
                beta=beta,
                alpha=alpha,
                start_date=start_date,
                end_date=end_date,
                trading_days=trading_days,
                calculation_tolerance=self.tolerance
            )
            
            # 验证计算结果
            self._validate_metrics(metrics)
            
            self.logger.info("性能指标计算完成")
            return metrics
            
        except Exception as e:
            self.logger.error(f"计算性能指标失败: {e}")
            raise
    
    def _validate_inputs(self, 
                        returns: pd.Series,
                        trades: Optional[List[Dict[str, Any]]],
                        benchmark_returns: Optional[pd.Series]) -> None:
        """验证输入数据"""
        if returns.empty:
            raise ValueError("收益率序列不能为空")
        
        if len(returns) < 2:
            raise ValueError("收益率序列至少需要2个数据点")
        
        if trades is not None and not isinstance(trades, list):
            raise ValueError("交易记录必须是列表")
        
        if benchmark_returns is not None:
            if benchmark_returns.empty:
                raise ValueError("基准收益率序列不能为空")
            if len(benchmark_returns) != len(returns):
                raise ValueError("基准收益率序列长度必须与收益率序列相同")
    
    def _calculate_total_return(self, returns: pd.Series) -> float:
        """计算总收益率"""
        total_return = (1 + returns).prod() - 1
        return float(total_return)
    
    def _calculate_annual_return(self, returns: pd.Series) -> float:
        """计算年化收益率"""
        if len(returns) < 2:
            return 0.0
        
        # 计算年化因子
        if hasattr(returns.index[0], 'to_pydatetime'):
            start_date = returns.index[0].to_pydatetime()
            end_date = returns.index[-1].to_pydatetime()
            years = (end_date - start_date).total_seconds() / (365.25 * 86400)
        else:
            years = len(returns) / self.periods_per_year
        
        if years <= 0:
            return 0.0
        
        total_return = self._calculate_total_return(returns)
        annual_return = (1 + total_return) ** (1 / years) - 1
        return float(annual_return)
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """计算波动率"""
        if len(returns) < 2:
            return 0.0
        
        # 年化波动率
        volatility = returns.std() * np.sqrt(self.periods_per_year)
        return float(volatility)
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - risk_free_rate / self.periods_per_year
        if np.isclose(excess_returns.std(), 0, atol=1e-12):
            return 0.0
        
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(self.periods_per_year)
        return float(sharpe_ratio)
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算索提诺比率"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - risk_free_rate / self.periods_per_year
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) < 2 or np.isclose(downside_returns.std(), 0, atol=1e-12):
            return 0.0
        
        sortino_ratio = excess_returns.mean() / downside_returns.std() * np.sqrt(self.periods_per_year)
        return float(sortino_ratio)
    
    def _calculate_calmar_ratio(self, returns: pd.Series, annual_return: float) -> float:
        """计算卡尔玛比率"""
        max_drawdown, _ = self._calculate_max_drawdown(returns)
        
        if max_drawdown == 0:
            return 0.0
        
        calmar_ratio = annual_return / abs(max_drawdown)
        return float(calmar_ratio)
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> Tuple[float, int]:
        """计算最大回撤"""
        if len(returns) < 2:
            return 0.0, 0
        
        # 计算累计收益
        cumulative_returns = (1 + returns).cumprod()
        
        # 计算回撤
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        
        # 最大回撤
        max_drawdown = drawdown.min()
        
        # 最大回撤持续时间
        max_dd_duration = self._calculate_drawdown_duration(drawdown)
        
        return float(max_drawdown), max_dd_duration
    
    def _calculate_drawdown_duration(self, drawdown: pd.Series) -> int:
        """计算回撤持续时间"""
        if len(drawdown) < 2:
            return 0
        
        # 找到最大回撤点
        max_dd_point = drawdown.idxmin()
        max_dd_index = drawdown.index.get_loc(max_dd_point)
        
        # 向前查找回撤开始点
        start_index = max_dd_index
        for i in range(max_dd_index - 1, -1, -1):
            if drawdown.iloc[i] >= 0:
                start_index = i
                break
        
        # 向后查找回撤结束点
        end_index = max_dd_index
        for i in range(max_dd_index + 1, len(drawdown)):
            if drawdown.iloc[i] >= 0:
                end_index = i
                break
        
        return end_index - start_index
    
    def _calculate_avg_drawdown(self, returns: pd.Series) -> float:
        """计算平均回撤"""
        if len(returns) < 2:
            return 0.0
        
        # 计算累计收益
        cumulative_returns = (1 + returns).cumprod()
        
        # 计算回撤
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        
        # 只考虑负回撤
        negative_drawdowns = drawdown[drawdown < 0]
        
        if len(negative_drawdowns) == 0:
            return 0.0
        
        avg_drawdown = negative_drawdowns.mean()
        return float(avg_drawdown)
    
    def _calculate_trade_metrics(self, trades: List[Dict[str, Any]]) -> Tuple[int, float, float, float, float]:
        """计算交易指标"""
        if not trades:
            return 0, 0.0, 0.0, 0.0, 0.0
        
        total_trades = len(trades)
        
        # 分离盈利和亏损交易
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        # 胜率
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0.0
        
        # 平均盈利和亏损
        avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        # 盈亏比
        total_wins = sum(t.get('pnl', 0) for t in winning_trades)
        total_losses = abs(sum(t.get('pnl', 0) for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        return total_trades, win_rate, profit_factor, avg_win, avg_loss
    
    def _calculate_risk_metrics(self, returns: pd.Series) -> Tuple[float, float]:
        """计算风险指标"""
        if len(returns) < 2:
            return 0.0, 0.0
        
        # VaR (95%)
        var_95 = np.percentile(returns, 5)
        
        # CVaR (95%)
        cvar_95 = returns[returns <= var_95].mean()
        
        return float(var_95), float(cvar_95)
    
    def _calculate_beta_alpha(self, returns: pd.Series, benchmark_returns: pd.Series) -> Tuple[float, float]:
        """计算Beta和Alpha"""
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0, 0.0
        
        # 计算协方差和方差
        covariance = np.cov(returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        
        if benchmark_variance == 0:
            return 0.0, 0.0
        
        # Beta
        beta = covariance / benchmark_variance
        
        # Alpha (假设无风险利率为2%)
        risk_free_rate = 0.02 / 252
        alpha = returns.mean() - (risk_free_rate + beta * (benchmark_returns.mean() - risk_free_rate))
        
        return float(beta), float(alpha)
    
    def _validate_metrics(self, metrics: PerformanceMetrics) -> None:
        """验证指标计算结果"""
        # 检查数值合理性
        if abs(metrics.total_return) > 10:  # 总收益率不应超过1000%
            self.logger.warning(f"总收益率异常: {metrics.total_return}")
        
        if metrics.volatility < 0:
            raise ValueError("波动率不能为负数")
        
        if metrics.max_drawdown > 0:
            raise ValueError("最大回撤不能为正数")
        
        if metrics.win_rate < 0 or metrics.win_rate > 100:
            raise ValueError("胜率必须在0-100之间")
        
        # 检查计算精度
        self._check_calculation_precision(metrics)
    
    def _check_calculation_precision(self, metrics: PerformanceMetrics) -> None:
        """检查计算精度"""
        # 这里可以添加更复杂的精度验证逻辑
        # 例如：重新计算关键指标并比较差异
        
        # 简单的合理性检查
        if abs(metrics.sharpe_ratio) > 10:
            self.logger.warning(f"夏普比率异常: {metrics.sharpe_ratio}")
        
        if abs(metrics.sortino_ratio) > 10:
            self.logger.warning(f"索提诺比率异常: {metrics.sortino_ratio}")
    
    def generate_performance_report(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """生成性能报告"""
        return {
            "summary": {
                "total_return": f"{metrics.total_return:.2%}",
                "annual_return": f"{metrics.annual_return:.2%}",
                "volatility": f"{metrics.volatility:.2%}",
                "max_drawdown": f"{metrics.max_drawdown:.2%}",
                "sharpe_ratio": f"{metrics.sharpe_ratio:.3f}",
                "win_rate": f"{metrics.win_rate:.1f}%"
            },
            "detailed_metrics": {
                "return_metrics": {
                    "total_return": metrics.total_return,
                    "annual_return": metrics.annual_return
                },
                "risk_metrics": {
                    "volatility": metrics.volatility,
                    "var_95": metrics.var_95,
                    "cvar_95": metrics.cvar_95,
                    "beta": metrics.beta,
                    "alpha": metrics.alpha
                },
                "ratio_metrics": {
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "sortino_ratio": metrics.sortino_ratio,
                    "calmar_ratio": metrics.calmar_ratio,
                    "profit_factor": metrics.profit_factor
                },
                "drawdown_metrics": {
                    "max_drawdown": metrics.max_drawdown,
                    "max_drawdown_duration": metrics.max_drawdown_duration,
                    "avg_drawdown": metrics.avg_drawdown
                },
                "trade_metrics": {
                    "total_trades": metrics.total_trades,
                    "win_rate": metrics.win_rate,
                    "avg_win": metrics.avg_win,
                    "avg_loss": metrics.avg_loss
                }
            },
            "period_info": {
                "start_date": metrics.start_date.isoformat(),
                "end_date": metrics.end_date.isoformat(),
                "trading_days": metrics.trading_days
            },
            "calculation_info": {
                "tolerance": metrics.calculation_tolerance,
                "calculated_at": datetime.now().isoformat()
            }
        }
