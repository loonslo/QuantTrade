# -*- coding: utf-8 -*-
"""
风控指标计算模块
计算持仓风险、VaR、最大回撤、暴露度等指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RiskMetrics:
    """风险指标数据结构"""
    total_value: float                    # 总市值
    cash: float                           # 现金
    total_exposure: float                 # 总仓位暴露
    leverage: float                       # 杠杆率
    var_1d: float                         # 1日VaR (95%置信)
    max_drawdown: float                   # 最大回撤
    sharpe_ratio: float                   # 夏普比率
    volatility: float                     # 波动率
    concentration: Dict[str, float]       # 各持仓占比


class RiskCalculator:
    """风险指标计算器"""

    def __init__(self, risk_free_rate: float = 0.04):
        """
        初始化风控计算器
        
        Args:
            risk_free_rate: 无风险利率（年化），默认 4%
        """
        self.risk_free_rate = risk_free_rate

    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        计算 Value at Risk（风险价值）
        
        Args:
            returns: 收益率序列
            confidence: 置信度，默认 95%
            
        Returns:
            VaR 值（负数表示损失）
        """
        if len(returns) < 2:
            return 0.0
        return float(np.percentile(returns, (1 - confidence) * 100))

    def calculate_max_drawdown(self, equity_curve: np.ndarray) -> float:
        """
        计算最大回撤
        
        Args:
            equity_curve: 资金曲线
            
        Returns:
            最大回撤（正数，如 0.15 表示 15%）
        """
        if len(equity_curve) < 2:
            return 0.0
        
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        return float(np.min(drawdown))

    def calculate_sharpe_ratio(self, returns: np.ndarray, periods_per_year: int = 252) -> float:
        """
        计算夏普比率
        
        Args:
            returns: 收益率序列
            periods_per_year: 年化周期，日数据为 252
            
        Returns:
            夏普比率
        """
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - self.risk_free_rate / periods_per_year
        if np.std(excess_returns) == 0:
            return 0.0
        
        return float(
            np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(periods_per_year)
        )

    def calculate_volatility(self, returns: np.ndarray, periods_per_year: int = 252) -> float:
        """
        计算年化波动率
        
        Args:
            returns: 收益率序列
            periods_per_year: 年化周期
            
        Returns:
            年化波动率
        """
        if len(returns) < 2:
            return 0.0
        return float(np.std(returns) * np.sqrt(periods_per_year))

    def calculate_concentration(self, positions: Dict[str, float]) -> Dict[str, float]:
        """
        计算各持仓集中度
        
        Args:
            positions: {symbol: 市值} 字典
            
        Returns:
            {symbol: 占比} 字典
        """
        total = sum(positions.values())
        if total == 0:
            return {k: 0.0 for k in positions}
        return {k: v / total for k, v in positions.items()}

    def calculate_leverage(self, total_value: float, cash: float) -> float:
        """
        计算杠杆率
        
        Args:
            total_value: 总市值（含现金）
            cash: 现金
        """
        exposure = total_value - cash
        if total_value == 0:
            return 0.0
        return exposure / total_value

    def assess_risk_level(self, var_pct: float, max_dd: float, concentration: float) -> str:
        """
        评估风险等级
        
        Args:
            var_pct: VaR 百分比（正数）
            max_dd: 最大回撤（正数）
            concentration: 最大持仓占比
            
        Returns:
            风险等级: LOW / MEDIUM / HIGH / CRITICAL
        """
        score = 0
        
        # VaR 评分
        if var_pct > 0.05:
            score += 3
        elif var_pct > 0.03:
            score += 2
        elif var_pct > 0.015:
            score += 1
        
        # 回撤评分
        if abs(max_dd) > 0.25:
            score += 3
        elif abs(max_dd) > 0.15:
            score += 2
        elif abs(max_dd) > 0.08:
            score += 1
        
        # 集中度评分
        if concentration > 0.4:
            score += 2
        elif concentration > 0.25:
            score += 1
        
        if score >= 6:
            return "CRITICAL"
        elif score >= 4:
            return "HIGH"
        elif score >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    def full_risk_assessment(
        self,
        positions: Dict[str, float],
        cash: float,
        returns: Optional[np.ndarray] = None,
        equity_curve: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        完整风险评估
        
        Args:
            positions: {symbol: 市值}
            cash: 现金
            returns: 收益率序列（可选）
            equity_curve: 资金曲线（可选）
            
        Returns:
            完整风险报告
        """
        total_value = sum(positions.values()) + cash
        leverage = self.calculate_leverage(total_value, cash)
        concentration = self.calculate_concentration(positions)
        max_concentration = max(concentration.values()) if concentration else 0.0
        
        # 计算 VaR
        var = 0.0
        if returns is not None and len(returns) >= 2:
            var = self.calculate_var(returns)
        
        # 计算最大回撤
        max_dd = 0.0
        if equity_curve is not None and len(equity_curve) >= 2:
            max_dd = self.calculate_max_drawdown(equity_curve)
        
        # 计算夏普
        sharpe = 0.0
        if returns is not None and len(returns) >= 2:
            sharpe = self.calculate_sharpe_ratio(returns)
        
        # 计算波动率
        vol = 0.0
        if returns is not None and len(returns) >= 2:
            vol = self.calculate_volatility(returns)
        
        risk_level = self.assess_risk_level(abs(var), abs(max_dd), max_concentration)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_value": round(total_value, 2),
            "cash": round(cash, 2),
            "exposure": round(total_value - cash, 2),
            "leverage": round(leverage, 4),
            "var_1d_95": round(var, 4),
            "var_pct": round(abs(var) / total_value if total_value > 0 else 0, 4),
            "max_drawdown": round(max_dd, 4),
            "sharpe_ratio": round(sharpe, 2),
            "volatility_annual": round(vol, 4),
            "concentration": {k: round(v, 4) for k, v in concentration.items()},
            "max_concentration": round(max_concentration, 4),
            "risk_level": risk_level
        }
