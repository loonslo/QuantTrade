# -*- coding: utf-8 -*-
"""
持仓监控模块
实时监控持仓状态、限额预警、流动性检查
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from utils.core.logger_manager import get_logger


class AlertLevel(Enum):
    """预警级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Position:
    """持仓数据结构"""
    symbol: str
    quantity: float           # 数量
    avg_price: float           # 平均成本
    current_price: float      # 当前价格
    market_value: float        # 市值
    unrealized_pnl: float      # 浮动盈亏
    unrealized_pnl_pct: float  # 盈亏比例
    weight: float              # 占比
    sector: str = ""           # 行业


@dataclass 
class RiskAlert:
    """风险预警"""
    level: AlertLevel
    code: str                  # 预警代码
    message: str               # 预警信息
    symbol: Optional[str]      # 涉及标的
    current_value: float       # 当前值
    threshold: float           # 阈值
    timestamp: datetime = field(default_factory=datetime.now)


class PositionMonitor:
    """持仓监控器"""

    # 风控阈值配置
    DEFAULTS = {
        "max_single_weight": 0.30,       # 单标的最高仓位占比 30%
        "max_sector_weight": 0.50,        # 单行业最高占比 50%
        "max_leverage": 1.0,              # 最大杠杆（美股现货为1.0）
        "max_drawdown_alert": 0.15,       # 回撤预警 15%
        "max_var_1d": 0.05,               # 1日VaR上限 5%
        "minLiquidityRatio": 0.001,        # 最低流动性（成交额/持仓市值）
        "max_crypto_leverage": 3.0,       # 加密货币最大杠杆
    }

    def __init__(self, thresholds: Dict[str, float] = None):
        """
        初始化持仓监控器
        
        Args:
            thresholds: 自定义阈值，覆盖默认值
        """
        self.logger = get_logger("position_monitor")
        self.t = {**self.DEFAULTS, **(thresholds or {})}
        self.alerts: List[RiskAlert] = []
        self.positions: Dict[str, Position] = {}

    def update_positions(
        self,
        raw_positions: Dict[str, Dict[str, float]],
        prices: Dict[str, float],
        sector_map: Dict[str, str] = None
    ) -> List[Position]:
        """
        更新持仓状态
        
        Args:
            raw_positions: {symbol: {quantity, avg_price}}
            prices: {symbol: current_price}
            sector_map: {symbol: sector_name}
            
        Returns:
            Position 对象列表
        """
        self.positions = {}
        total_value = sum(
            raw_positions.get(s, {}).get("quantity", 0) * prices.get(s, 0)
            for s in raw_positions
        )
        
        for symbol, data in raw_positions.items():
            qty = data.get("quantity", 0)
            avg = data.get("avg_price", 0)
            current = prices.get(symbol, 0)
            mv = qty * current
            pnl = (current - avg) * qty
            pnl_pct = (current - avg) / avg if avg > 0 else 0
            weight = mv / total_value if total_value > 0 else 0
            
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=qty,
                avg_price=avg,
                current_price=current,
                market_value=mv,
                unrealized_pnl=pnl,
                unrealized_pnl_pct=pnl_pct,
                weight=weight,
                sector=sector_map.get(symbol, "") if sector_map else ""
            )
        
        return list(self.positions.values())

    def check_all(self) -> List[RiskAlert]:
        """
        执行全部风控检查
        
        Returns:
            预警列表
        """
        self.alerts = []
        
        # 1. 仓位集中度检查
        self._check_concentration()
        
        # 2. 行业集中度检查
        self._check_sector_concentration()
        
        # 3. 流动性检查
        self._check_liquidity()
        
        # 4. 杠杆率检查（区分现货/合约）
        self._check_leverage()
        
        return self.alerts

    def _check_concentration(self):
        """检查单标的仓位集中度"""
        for pos in self.positions.values():
            if pos.weight > self.t["max_single_weight"]:
                self.alerts.append(RiskAlert(
                    level=AlertLevel.WARNING,
                    code="CONCENTRATION",
                    message=f"{pos.symbol} 仓位占比 {pos.weight:.1%} 超过限制 {self.t['max_single_weight']:.1%}",
                    symbol=pos.symbol,
                    current_value=pos.weight,
                    threshold=self.t["max_single_weight"]
                ))

    def _check_sector_concentration(self):
        """检查行业集中度"""
        sector_weights: Dict[str, float] = {}
        for pos in self.positions.values():
            if pos.sector:
                sector_weights[pos.sector] = sector_weights.get(pos.sector, 0) + pos.weight
        
        for sector, weight in sector_weights.items():
            if weight > self.t["max_sector_weight"]:
                self.alerts.append(RiskAlert(
                    level=AlertLevel.WARNING,
                    code="SECTOR_CONCENTRATION",
                    message=f"行业 {sector} 占比 {weight:.1%} 超过限制 {self.t['max_sector_weight']:.1%}",
                    symbol=None,
                    current_value=weight,
                    threshold=self.t["max_sector_weight"]
                ))

    def _check_liquidity(self):
        """流动性检查（需外部传入成交量数据）"""
        # 注意：流动性需要实时成交量数据，这里做基础校验
        for pos in self.positions.values():
            if pos.market_value > 0 and pos.current_price > 0:
                # 基础检查：价格不能为负或零
                if pos.current_price <= 0:
                    self.alerts.append(RiskAlert(
                        level=AlertLevel.CRITICAL,
                        code="INVALID_PRICE",
                        message=f"{pos.symbol} 当前价格异常: {pos.current_price}",
                        symbol=pos.symbol,
                        current_value=pos.current_price,
                        threshold=0.01
                    ))

    def _check_leverage(self):
        """检查杠杆率"""
        total_weight = sum(p.weight for p in self.positions.values())
        leverage = total_weight  # 简化：现货无杠杆，合约有杠杆
        
        is_crypto = any(
            s in symbol.upper() 
            for symbol in self.positions.keys()
            for s in ["BTC", "ETH", "USDT", "USDC"]
        )
        max_lev = self.t["max_crypto_leverage"] if is_crypto else self.t["max_leverage"]
        
        if leverage > max_lev:
            self.alerts.append(RiskAlert(
                level=AlertLevel.ERROR,
                code="LEVERAGE_EXCEEDED",
                message=f"杠杆率 {leverage:.2f}x 超过限制 {max_lev:.2f}x",
                symbol=None,
                current_value=leverage,
                threshold=max_lev
            ))

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取组合汇总"""
        total_value = sum(p.market_value for p in self.positions.values())
        total_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_market_value": round(total_value, 2),
            "total_unrealized_pnl": round(total_pnl, 2),
            "position_count": len(self.positions),
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": round(p.quantity, 4),
                    "avg_price": round(p.avg_price, 2),
                    "current_price": round(p.current_price, 2),
                    "market_value": round(p.market_value, 2),
                    "unrealized_pnl": round(p.unrealized_pnl, 2),
                    "unrealized_pnl_pct": round(p.unrealized_pnl_pct, 4),
                    "weight": round(p.weight, 4),
                    "sector": p.sector
                }
                for p in self.positions.values()
            ],
            "alerts": [
                {
                    "level": a.level.value,
                    "code": a.code,
                    "message": a.message,
                    "symbol": a.symbol,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in self.alerts
            ]
        }
