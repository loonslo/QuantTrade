"""
投资组合管理器
实现多标的投资组合管理，确保现金与持仓一致性
支持最小交易额/步长/精度校验，组合价值计算
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from utils.core.logger_manager import get_logger
from utils.validation.exceptions import PortfolioException
from .position_interface import Position
from .trading_engine import TradingEngine


@dataclass
class PortfolioState:
    """投资组合状态"""
    timestamp: datetime
    total_value: float  # 总价值 = 现金 + 持仓市值
    cash: float  # 可用现金
    positions_value: float  # 持仓市值
    positions: Dict[str, Position] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_value': self.total_value,
            'cash': self.cash,
            'positions_value': self.positions_value,
            'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()}
        }


@dataclass
class TradingConstraints:
    """交易约束"""
    min_notional: float  # 最小名义金额
    min_qty: float  # 最小数量
    qty_step: float  # 数量步长
    price_tick: float  # 价格最小变动单位
    
    def validate_order(self, quantity: float, price: float) -> Tuple[bool, str]:
        """
        验证订单是否符合约束
        
        Args:
            quantity: 数量
            price: 价格
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检查最小数量
        if quantity < self.min_qty:
            return False, f"数量 {quantity} 小于最小数量 {self.min_qty}"
        
        # 检查数量步长
        if self.qty_step > 0:
            # 使用更宽松的精度容差，并检查是否为步长的整数倍
            remainder = quantity % self.qty_step
            # 增加精度容差，处理浮点数精度问题
            if abs(remainder) > 1e-8:  # 从 1e-10 增加到 1e-8
                # 额外检查：尝试四舍五入到最近的步长
                rounded_quantity = round(quantity / self.qty_step) * self.qty_step
                if abs(quantity - rounded_quantity) > 1e-8:
                    return False, f"数量 {quantity} 不符合步长 {self.qty_step} 要求"
        
        # 检查最小名义金额
        notional = quantity * price
        if notional < self.min_notional:
            return False, f"名义金额 {notional} 小于最小要求 {self.min_notional}"
        
        # 检查价格精度
        if self.price_tick > 0:
            price_remainder = price % self.price_tick
            if abs(price_remainder) > 1e-8:  # 同样增加精度容差
                return False, f"价格 {price} 不符合精度 {self.price_tick} 要求"
        
        return True, ""


class PortfolioManager:
    """投资组合管理器"""
    
    def __init__(self, initial_cash: float = 100000.0, trading_engine: Optional[TradingEngine] = None):
        """
        初始化投资组合管理器
        
        Args:
            initial_cash: 初始现金
            trading_engine: 可选的交易引擎（回测或实盘），使管理器不需要区分回测/实盘
        """
        self.logger = get_logger('portfolio_manager')
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.trading_constraints: Dict[str, TradingConstraints] = {}
        self.history: List[PortfolioState] = []
        self.trading_engine = trading_engine  # 交易引擎引用
        
        # 记录初始状态
        self._record_state()
        
        self.logger.info(f"🔄 投资组合管理器初始化完成，初始现金: {initial_cash:,.2f}"
                        + (f", 交易引擎: {type(trading_engine).__name__}" if trading_engine else ""))
    
    def add_trading_constraints(self, symbol: str, constraints: TradingConstraints):
        """
        添加交易约束
        
        Args:
            symbol: 交易对
            constraints: 交易约束
        """
        self.trading_constraints[symbol] = constraints
        self.logger.info(f"📋 为 {symbol} 添加交易约束: 最小金额={constraints.min_notional}, 步长={constraints.qty_step}")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """获取所有持仓"""
        return self.positions.copy()
    
    def get_cash(self) -> float:
        """获取可用现金"""
        return self.cash
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """
        计算总价值
        
        Args:
            current_prices: 当前价格字典 {symbol: price}
            
        Returns:
            float: 总价值
        """
        positions_value = 0.0
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position.update_pnl(current_price)
                positions_value += position.quantity * current_price
            else:
                # 如果没有当前价格，使用平均成本
                positions_value += position.quantity * position.avg_price
        
        total_value = self.cash + positions_value
        return total_value
    
    def validate_buy_order(self, symbol: str, quantity: float, price: float, 
                          commission_rate: float = 0.001) -> Tuple[bool, str]:
        """
        验证买入订单
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检查交易约束
        if symbol in self.trading_constraints:
            is_valid, error_msg = self.trading_constraints[symbol].validate_order(quantity, price)
            if not is_valid:
                return False, error_msg
        
        # 计算总成本（含手续费）
        total_cost = quantity * price * (1 + commission_rate)
        
        # 检查现金是否足够
        if total_cost > self.cash:
            return False, f"现金不足: 需要 {total_cost:.2f}, 可用 {self.cash:.2f}"
        
        return True, ""
    
    def validate_sell_order(self, symbol: str, quantity: float, price: float,
                           commission_rate: float = 0.001) -> Tuple[bool, str]:
        """
        验证卖出订单
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检查交易约束
        if symbol in self.trading_constraints:
            is_valid, error_msg = self.trading_constraints[symbol].validate_order(quantity, price)
            if not is_valid:
                return False, error_msg
        
        # 检查持仓是否足够
        position = self.positions.get(symbol)
        if not position or position.quantity < quantity:
            return False, f"持仓不足: 需要 {quantity}, 持有 {position.quantity if position else 0}"
        
        return True, ""
    
    def execute_buy_order(self, symbol: str, quantity: float, price: float,
                         commission_rate: float = 0.001, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        执行买入订单
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            timestamp: 时间戳
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 验证订单
        is_valid, error_msg = self.validate_buy_order(symbol, quantity, price, commission_rate)
        if not is_valid:
            raise PortfolioException(f"买入订单验证失败: {error_msg}")
        
        timestamp = timestamp or datetime.now()
        
        # 计算成本和手续费
        base_cost = quantity * price
        commission = base_cost * commission_rate
        total_cost = base_cost + commission
        
        # 更新现金
        old_cash = self.cash
        self.cash -= total_cost
        
        # 更新或创建持仓
        if symbol in self.positions:
            position = self.positions[symbol]
            # 计算新的平均价格
            total_quantity = position.quantity + quantity
            total_value = position.quantity * position.avg_price + base_cost
            new_avg_price = total_value / total_quantity
            
            position.quantity = total_quantity
            position.avg_price = new_avg_price
        else:
            # 创建新持仓
            position = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                entry_time=timestamp
            )
            self.positions[symbol] = position
        
        # 记录状态
        self._record_state()
        
        # 记录交易日志
        self.logger.info(
            f"✅ 买入执行: {symbol} | 数量: {quantity:.6f} | 价格: {price:.6f} | "
            f"成本: {base_cost:.2f} | 手续费: {commission:.2f} | "
            f"现金: {old_cash:.2f} → {self.cash:.2f}"
        )
        
        return {
            'symbol': symbol,
            'side': 'buy',
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'total_cost': total_cost,
            'timestamp': timestamp,
            'cash_before': old_cash,
            'cash_after': self.cash
        }
    
    def execute_sell_order(self, symbol: str, quantity: float, price: float,
                          commission_rate: float = 0.001, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        执行卖出订单
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            timestamp: 时间戳
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 验证订单
        is_valid, error_msg = self.validate_sell_order(symbol, quantity, price, commission_rate)
        if not is_valid:
            raise PortfolioException(f"卖出订单验证失败: {error_msg}")
        
        timestamp = timestamp or datetime.now()
        
        # 计算收入和手续费
        base_revenue = quantity * price
        commission = base_revenue * commission_rate
        net_revenue = base_revenue - commission
        
        # 更新现金
        old_cash = self.cash
        self.cash += net_revenue
        
        # 更新持仓
        position = self.positions[symbol]
        old_quantity = position.quantity
        position.quantity -= quantity
        
        # 计算已实现盈亏
        realized_pnl = (price - position.avg_price) * quantity
        position.realized_pnl += realized_pnl
        
        # 如果持仓为0，删除持仓记录
        if position.quantity <= 0:
            del self.positions[symbol]
        
        # 记录状态
        self._record_state()
        
        # 记录交易日志
        self.logger.info(
            f"✅ 卖出执行: {symbol} | 数量: {quantity:.6f} | 价格: {price:.6f} | "
            f"收入: {base_revenue:.2f} | 手续费: {commission:.2f} | "
            f"已实现盈亏: {realized_pnl:.2f} | "
            f"现金: {old_cash:.2f} → {self.cash:.2f}"
        )
        
        return {
            'symbol': symbol,
            'side': 'sell',
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'net_revenue': net_revenue,
            'realized_pnl': realized_pnl,
            'timestamp': timestamp,
            'cash_before': old_cash,
            'cash_after': self.cash
        }
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        获取投资组合摘要
        
        Args:
            current_prices: 当前价格字典
            
        Returns:
            Dict[str, Any]: 投资组合摘要
        """
        total_value = self.get_total_value(current_prices)
        positions_value = total_value - self.cash
        
        # 计算各持仓的当前价值
        position_details = {}
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.avg_price)
            position.update_pnl(current_price)
            
            position_details[symbol] = {
                'quantity': position.quantity,
                'avg_price': position.avg_price,
                'current_price': current_price,
                'market_value': position.quantity * current_price,
                'unrealized_pnl': position.unrealized_pnl,
                'realized_pnl': position.realized_pnl,
                'pnl_ratio': position.get_pnl_ratio(current_price)
            }
        
        return {
            'total_value': total_value,
            'cash': self.cash,
            'positions_value': positions_value,
            'cash_ratio': self.cash / total_value if total_value > 0 else 0,
            'positions_ratio': positions_value / total_value if total_value > 0 else 0,
            'position_details': position_details,
            'total_unrealized_pnl': sum(pos.unrealized_pnl for pos in self.positions.values()),
            'total_realized_pnl': sum(pos.realized_pnl for pos in self.positions.values()),
            'return_ratio': (total_value - self.initial_cash) / self.initial_cash if self.initial_cash > 0 else 0
        }
    
    def _record_state(self):
        """记录当前状态"""
        state = PortfolioState(
            timestamp=datetime.now(),
            total_value=self.cash,  # 暂时只计算现金，价格更新时再计算总价值
            cash=self.cash,
            positions_value=0.0,
            positions=self.positions.copy()
        )
        self.history.append(state)
    
    def get_history(self) -> List[PortfolioState]:
        """获取历史状态"""
        return self.history.copy()
    
    def reset(self, new_cash: Optional[float] = None):
        """重置投资组合"""
        self.cash = new_cash if new_cash is not None else self.initial_cash
        self.positions.clear()
        self.history.clear()
        if self.trading_engine is not None:
            self.trading_engine.reset(new_cash)
        self._record_state()
        self.logger.info(f"🔄 投资组合已重置，现金: {self.cash:,.2f}")
    
    def validate_consistency(self, current_prices: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        验证现金与持仓一致性
        
        Args:
            current_prices: 当前价格字典
            
        Returns:
            Tuple[bool, List[str]]: (是否一致, 错误列表)
        """
        errors = []
        
        # 计算理论总价值
        calculated_total = self.cash
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                calculated_total += position.quantity * current_prices[symbol]
            else:
                calculated_total += position.quantity * position.avg_price
        
        # 检查现金是否为负数
        if self.cash < 0:
            errors.append(f"现金为负数: {self.cash:.2f}")
        
        # 检查持仓数量是否为负数
        for symbol, position in self.positions.items():
            if position.quantity < 0:
                errors.append(f"{symbol} 持仓数量为负数: {position.quantity:.6f}")
        
        # 检查总价值是否合理
        if calculated_total < 0:
            errors.append(f"总价值为负数: {calculated_total:.2f}")
        
        # 检查现金是否超过总价值
        if self.cash > calculated_total:
            errors.append(f"现金超过总价值: 现金={self.cash:.2f}, 总价值={calculated_total:.2f}")
        
        is_consistent = len(errors) == 0
        
        if is_consistent:
            self.logger.info("✅ 投资组合一致性检查通过")
        else:
            self.logger.warning(f"⚠️ 投资组合一致性检查失败: {errors}")
        
        return is_consistent, errors 