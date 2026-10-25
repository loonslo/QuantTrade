"""
仓位管理接口
定义仓位管理的标准接口，支持多种仓位管理策略
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from utils.core.logger_manager import get_logger
from .strategy_interface import Signal, StrategyContext


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: float
    avg_price: float
    entry_time: datetime
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'entry_time': self.entry_time,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl
        }
    
    def update_pnl(self, current_price: float):
        """
        更新未实现盈亏
        口径说明：此处为毛盈亏（不含手续费）。净盈亏请以交易记录的 PnL 为准。
        """
        if self.quantity != 0:
            self.unrealized_pnl = (current_price - self.avg_price) * self.quantity
        else:
            self.unrealized_pnl = 0.0
    
    def get_pnl_ratio(self, current_price: float) -> float:
        """获取盈亏比例"""
        if self.avg_price == 0:
            return 0.0
        return (current_price - self.avg_price) / self.avg_price


class PositionManager(ABC):
    """仓位管理接口"""
    
    def __init__(self, name: str = "default",
                 min_notional: Optional[float] = None,
                 min_qty: Optional[float] = None,
                 qty_step: Optional[float] = None,
                 price_tick: Optional[float] = None):
        """
        初始化仓位管理器
        
        Args:
            name: 管理器名称
            min_notional: 最小名义金额（如交易所 minNotional 规则）
            min_qty: 最小数量（如交易所 minQty 规则）
            qty_step: 数量步长（如交易所 stepSize 规则）
            price_tick: 价格最小变动单位（tickSize）
        """
        self.name = name
        self.logger = get_logger('position_manager')
        self.positions: Dict[str, Position] = {}
        # 可选交易规则约束
        self.min_notional = min_notional
        self.min_qty = min_qty
        self.qty_step = qty_step
        self.price_tick = price_tick
    
    @abstractmethod
    def calculate_position_size(self, context: StrategyContext, 
                              signal: Signal, 
                              current_price: float) -> float:
        """
        计算仓位大小
        
        Args:
            context: 策略上下文
            signal: 交易信号
            current_price: 当前价格
            
        Returns:
            float: 仓位大小
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现calculate_position_size方法")
    
    @abstractmethod
    def should_close_position(self, context: StrategyContext, 
                            position: Position, 
                            current_price: float) -> bool:
        """
        判断是否应该平仓
        
        Args:
            context: 策略上下文
            position: 持仓信息
            current_price: 当前价格
            
        Returns:
            bool: 是否应该平仓
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现should_close_position方法")
    
    def open_position(self, symbol: str, quantity: float, 
                     price: float, timestamp: datetime) -> Position:
        """
        开仓
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            timestamp: 时间戳
            
        Returns:
            Position: 持仓信息
        """
        if symbol in self.positions:
            # 更新现有持仓
            position = self.positions[symbol]
            total_quantity = position.quantity + quantity
            total_value = position.quantity * position.avg_price + quantity * price
            position.avg_price = total_value / total_quantity
            position.quantity = total_quantity
        else:
            # 创建新持仓
            position = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                entry_time=timestamp
            )
            self.positions[symbol] = position
        
        self.logger.info(f"开仓: {symbol} {quantity} @ {price}")
        return position
    
    def close_position(self, symbol: str, quantity: float, 
                      price: float, timestamp: datetime) -> Optional[Position]:
        """
        平仓
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            timestamp: 时间戳
            
        Returns:
            Optional[Position]: 持仓信息（如果完全平仓则为None）
        """
        if symbol not in self.positions:
            self.logger.warning(f"尝试平仓不存在的持仓: {symbol}")
            return None
        
        position = self.positions[symbol]
        
        if quantity >= position.quantity:
            # 完全平仓
            realized_pnl = (price - position.avg_price) * position.quantity
            position.realized_pnl += realized_pnl
            self.logger.info(f"完全平仓: {symbol} {position.quantity} @ {price}, PnL: {realized_pnl:.2f}")
            del self.positions[symbol]
            return None
        else:
            # 部分平仓
            realized_pnl = (price - position.avg_price) * quantity
            position.realized_pnl += realized_pnl
            position.quantity -= quantity
            self.logger.info(f"部分平仓: {symbol} {quantity} @ {price}, PnL: {realized_pnl:.2f}")
            return position
    
    def update_positions(self, current_prices: Dict[str, float]):
        """
        更新所有持仓的盈亏
        
        Args:
            current_prices: 当前价格字典
        """
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.update_pnl(current_prices[symbol])
    
    def get_position_summary(self) -> Dict[str, Any]:
        """
        获取持仓摘要
        
        Returns:
            Dict[str, Any]: 持仓摘要
        """
        total_positions = len(self.positions)
        total_quantity = sum(pos.quantity for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        
        return {
            'total_positions': total_positions,
            'total_quantity': total_quantity,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': total_realized_pnl,
            'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()}
        }
    
    def get_position_risk_metrics(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        获取持仓风险指标
        
        Args:
            current_prices: 当前价格字典
            
        Returns:
            Dict[str, Any]: 风险指标
        """
        if not self.positions:
            return {}
        
        # 计算持仓集中度
        position_values = []
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                value = position.quantity * current_prices[symbol]
                position_values.append(value)
        
        if not position_values:
            return {}
        
        total_value = sum(position_values)
        max_position_value = max(position_values)
        concentration_ratio = max_position_value / total_value if total_value > 0 else 0
        
        # 计算盈亏分布
        pnls = [pos.unrealized_pnl for pos in self.positions.values()]
        avg_pnl = sum(pnls) / len(pnls) if pnls else 0
        max_loss = min(pnls) if pnls else 0
        max_profit = max(pnls) if pnls else 0
        
        return {
            'total_positions': len(self.positions),
            'concentration_ratio': concentration_ratio,
            'avg_pnl': avg_pnl,
            'max_loss': max_loss,
            'max_profit': max_profit,
            'total_unrealized_pnl': sum(pnls)
        }
    
    def validate_position_size(self, quantity: float, price: float, 
                             available_cash: float, commission_rate: float = 0.001) -> bool:
        """
        验证仓位大小是否合理（包含手续费）
        
        Args:
            quantity: 数量
            price: 价格
            available_cash: 可用资金
            commission_rate: 手续费率
            
        Returns:
            bool: 是否合理
        """
        required_cash = quantity * price
        commission = required_cash * commission_rate
        total_cost = required_cash + commission
        
        if total_cost > available_cash:
            self.logger.warning(f"仓位过大: 需要 {total_cost:.2f} (含手续费 {commission:.2f}), 可用 {available_cash:.2f}")
            return False
        
        if quantity <= 0:
            self.logger.warning(f"无效数量: {quantity}")
            return False
        
        if price <= 0:
            self.logger.warning(f"无效价格: {price}")
            return False

        # 交易规则约束（如果已配置）
        if self.min_qty is not None and quantity < self.min_qty:
            self.logger.warning(f"数量低于最小数量限制: {quantity} < {self.min_qty}")
            return False
        if self.min_notional is not None and required_cash < self.min_notional:
            self.logger.warning(f"名义金额低于最小限制: {required_cash:.2f} < {self.min_notional:.2f}")
            return False
        
        return True

    # 可选：数量/价格步长对齐辅助
    def _round_quantity(self, quantity: float) -> float:
        if self.qty_step and self.qty_step > 0:
            return (quantity // self.qty_step) * self.qty_step
        return quantity

    def _round_price(self, price: float) -> float:
        if self.price_tick and self.price_tick > 0:
            ticks = round(price / self.price_tick)
            return ticks * self.price_tick
        return price
    
    def calculate_commission(self, quantity: float, price: float, 
                           commission_rate: float = 0.001) -> float:
        """
        计算手续费
        
        Args:
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            
        Returns:
            float: 手续费金额
        """
        return quantity * price * commission_rate
    
    def calculate_total_cost(self, quantity: float, price: float, 
                           commission_rate: float = 0.001) -> tuple[float, float]:
        """
        计算总成本（包含手续费）
        
        Args:
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            
        Returns:
            tuple[float, float]: (总成本, 手续费)
        """
        gross_amount = quantity * price
        commission = gross_amount * commission_rate
        total_cost = gross_amount + commission
        return total_cost, commission
    
    def calculate_net_revenue(self, quantity: float, price: float, 
                            commission_rate: float = 0.001) -> tuple[float, float]:
        """
        计算净收入（扣除手续费）
        
        Args:
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            
        Returns:
            tuple[float, float]: (净收入, 手续费)
        """
        gross_revenue = quantity * price
        commission = gross_revenue * commission_rate
        net_revenue = gross_revenue - commission
        return net_revenue, commission
    
    def get_position_manager_info(self) -> Dict[str, Any]:
        """
        获取仓位管理器信息
        
        Returns:
            Dict[str, Any]: 管理器信息
        """
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'description': getattr(self, 'description', ''),
            'parameters': getattr(self, 'parameters', {})
        }
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        设置参数
        
        Args:
            parameters: 参数字典
        """
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.logger.info(f"设置参数 {key} = {value}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        获取参数
        
        Returns:
            Dict[str, Any]: 参数字典
        """
        parameters = {}
        for attr in dir(self):
            if not attr.startswith('_') and not callable(getattr(self, attr)):
                value = getattr(self, attr)
                if isinstance(value, (int, float, str, bool)):
                    parameters[attr] = value
        return parameters 