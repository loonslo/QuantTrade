import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from modules.data import DataLoader

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class Order:
    """订单数据结构"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    status: str = "pending"
    created_at: float = None
    filled_at: Optional[float] = None
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    commission: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

@dataclass
class Position:
    """持仓数据结构"""
    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_commission: float = 0.0

class RiskManager:
    """风险管理器"""
    
    def __init__(self, max_position_size: float = 0.1, max_daily_loss: float = 0.05):
        self.max_position_size = max_position_size  # 最大仓位比例
        self.max_daily_loss = max_daily_loss  # 最大日亏损
        self.daily_pnl = 0.0
        self.last_reset_date = None
    
    def can_trade(self, capital: float, position_value: float, trade_value: float) -> Tuple[bool, str]:
        """检查是否可以交易"""
        # 检查仓位限制
        if position_value + trade_value > capital * self.max_position_size:
            return False, f"仓位超过限制: {self.max_position_size * 100}%"
        
        # 检查日亏损限制
        current_date = pd.Timestamp.now().date()
        if self.last_reset_date != current_date:
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
        
        if self.daily_pnl < -capital * self.max_daily_loss:
            return False, f"日亏损超过限制: {self.max_daily_loss * 100}%"
        
        return True, "交易允许"
    
    def update_daily_pnl(self, pnl: float):
        """更新日盈亏"""
        self.daily_pnl += pnl

class OrderManager:
    """订单管理器"""
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0
    
    def create_order(self, symbol: str, side: OrderSide, order_type: OrderType, 
                    quantity: float, price: Optional[float] = None) -> Order:
        """创建订单"""
        order_id = f"order_{self.order_counter}_{int(time.time())}"
        self.order_counter += 1
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        
        self.orders[order_id] = order
        logger.info(f"创建订单: {order_id} {side.value} {quantity} {symbol} @ {price}")
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)
    
    def update_order(self, order_id: str, **kwargs):
        """更新订单状态"""
        if order_id in self.orders:
            for key, value in kwargs.items():
                if hasattr(self.orders[order_id], key):
                    setattr(self.orders[order_id], key, value)
    
    def get_pending_orders(self) -> List[Order]:
        """获取待处理订单"""
        return [order for order in self.orders.values() if order.status == "pending"]

class PositionManager:
    """持仓管理器"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
    
    def update_position(self, symbol: str, quantity: float, price: float, commission: float = 0.0):
        """更新持仓"""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol, quantity=0, avg_price=0)
        
        position = self.positions[symbol]
        
        if quantity > 0:  # 买入
            if position.quantity == 0:
                position.avg_price = price
            else:
                # 计算新的平均价格
                total_cost = position.quantity * position.avg_price + quantity * price
                position.avg_price = total_cost / (position.quantity + quantity)
            position.quantity += quantity
        else:  # 卖出
            if abs(quantity) > position.quantity:
                raise ValueError(f"卖出数量 {abs(quantity)} 超过持仓数量 {position.quantity}")
            
            # 计算已实现盈亏
            realized_pnl = (price - position.avg_price) * abs(quantity)
            position.realized_pnl += realized_pnl
            position.quantity += quantity  # quantity为负数
            
            if position.quantity == 0:
                position.avg_price = 0
        
        position.total_commission += commission
        logger.info(f"更新持仓: {symbol} 数量={position.quantity} 均价={position.avg_price:.4f}")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """获取所有持仓"""
        return self.positions.copy()

class Trader:
    """实际交易执行器"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, test_mode: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.test_mode = test_mode
        
        self.order_manager = OrderManager()
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager()
        
        # 初始化数据加载器（用于API调用）
        self.data_loader = DataLoader()
        
        # 模拟账户余额（仅测试模式使用）
        self.simulated_balance = {
            'USDT': 10000.0,
            'BTC': 0.0,
            'ETH': 0.0
        }
        
        logger.info(f"交易器初始化完成 - 测试模式: {test_mode}")
    
    def get_balance(self, currency: str = 'USDT') -> float:
        """获取余额"""
        if self.test_mode:
            # 测试模式：返回模拟余额
            return self.simulated_balance.get(currency, 0.0)
        else:
            # 实盘模式：通过API查询真实余额
            try:
                balance = self._fetch_real_balance(currency)
                logger.info(f"查询真实余额: {currency} = {balance}")
                return balance
            except Exception as e:
                logger.error(f"查询余额失败: {e}")
                return 0.0
    
    def _fetch_real_balance(self, currency: str) -> float:
        """通过API获取真实余额"""
        try:
            # 使用DataLoader中的exchange实例查询余额
            if hasattr(self.data_loader, 'exchange') and self.data_loader.exchange:
                balance = self.data_loader.exchange.fetch_balance()
                if currency in balance['total']:
                    return float(balance['total'][currency])
                else:
                    return 0.0
            else:
                logger.warning("未配置交易所API，无法查询真实余额")
                return 0.0
        except Exception as e:
            logger.error(f"API查询余额失败: {e}")
            return 0.0
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        if self.test_mode:
            # 测试模式：返回模拟价格
            base_prices = {
                'BTC/USDT': 45000.0,
                'ETH/USDT': 3000.0,
                'BNB/USDT': 300.0
            }
            return base_prices.get(symbol, 100.0)
        else:
            # 实盘模式：通过API获取真实价格
            try:
                ticker = self.data_loader.exchange.fetch_ticker(symbol)
                return float(ticker['last'])
            except Exception as e:
                logger.error(f"获取价格失败: {e}")
                return 0.0
    
    def place_market_order(self, symbol: str, side: OrderSide, quantity: float) -> Order:
        """下市价单"""
        current_price = self.get_current_price(symbol)
        
        # 风险检查
        trade_value = quantity * current_price
        can_trade, message = self.risk_manager.can_trade(
            self.get_balance('USDT'),
            self._get_total_position_value(),
            trade_value if side == OrderSide.BUY else 0
        )
        
        if not can_trade:
            raise ValueError(f"风险检查失败: {message}")
        
        # 创建订单
        order = self.order_manager.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=current_price
        )
        
        # 模拟订单执行
        self._execute_order(order, current_price)
        
        return order
    
    def place_limit_order(self, symbol: str, side: OrderSide, quantity: float, price: float) -> Order:
        """下限价单"""
        # 风险检查
        trade_value = quantity * price
        can_trade, message = self.risk_manager.can_trade(
            self.get_balance('USDT'),
            self._get_total_position_value(),
            trade_value if side == OrderSide.BUY else 0
        )
        
        if not can_trade:
            raise ValueError(f"风险检查失败: {message}")
        
        # 创建订单
        order = self.order_manager.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
        
        # 限价单需要等待价格达到条件
        logger.info(f"下限价单: {order.id} {side.value} {quantity} {symbol} @ {price}")
        
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        order = self.order_manager.get_order(order_id)
        if order and order.status == "pending":
            self.order_manager.update_order(order_id, status="cancelled")
            logger.info(f"取消订单: {order_id}")
            return True
        return False
    
    def _execute_order(self, order: Order, execution_price: float):
        """执行订单"""
        commission_rate = 0.001  # 0.1%手续费
        commission = order.quantity * execution_price * commission_rate
        
        # 更新订单状态
        self.order_manager.update_order(
            order.id,
            status="filled",
            filled_at=time.time(),
            filled_price=execution_price,
            filled_quantity=order.quantity,
            commission=commission
        )
        
        # 更新持仓
        base_currency = order.symbol.split('/')[0]
        if order.side == OrderSide.BUY:
            # 买入：减少USDT，增加币种
            cost = order.quantity * execution_price + commission
            if self.test_mode:
                # 测试模式：更新模拟余额
                if self.simulated_balance['USDT'] >= cost:
                    self.simulated_balance['USDT'] -= cost
                    self.simulated_balance[base_currency] = self.simulated_balance.get(base_currency, 0) + order.quantity
                    self.position_manager.update_position(order.symbol, order.quantity, execution_price, commission)
                    logger.info(f"买入成功: {order.quantity} {base_currency} @ {execution_price}")
                else:
                    raise ValueError("余额不足")
            else:
                # 实盘模式：这里应该调用真实的API下单
                logger.info(f"实盘买入: {order.quantity} {base_currency} @ {execution_price}")
                # TODO: 实现真实的API下单逻辑
                self.position_manager.update_position(order.symbol, order.quantity, execution_price, commission)
        else:
            # 卖出：增加USDT，减少币种
            revenue = order.quantity * execution_price - commission
            if self.test_mode:
                # 测试模式：更新模拟余额
                if self.simulated_balance.get(base_currency, 0) >= order.quantity:
                    self.simulated_balance['USDT'] += revenue
                    self.simulated_balance[base_currency] -= order.quantity
                    self.position_manager.update_position(order.symbol, -order.quantity, execution_price, commission)
                    logger.info(f"卖出成功: {order.quantity} {base_currency} @ {execution_price}")
                else:
                    raise ValueError("持仓不足")
            else:
                # 实盘模式：这里应该调用真实的API下单
                logger.info(f"实盘卖出: {order.quantity} {base_currency} @ {execution_price}")
                # TODO: 实现真实的API下单逻辑
                self.position_manager.update_position(order.symbol, -order.quantity, execution_price, commission)
    
    def _get_total_position_value(self) -> float:
        """获取总持仓价值"""
        total_value = 0.0
        for symbol, position in self.position_manager.get_all_positions().items():
            if position.quantity > 0:
                current_price = self.get_current_price(symbol)
                total_value += position.quantity * current_price
        return total_value
    
    def get_account_summary(self) -> Dict:
        """获取账户摘要"""
        total_position_value = self._get_total_position_value()
        usdt_balance = self.get_balance('USDT')
        total_balance = usdt_balance + total_position_value
        
        return {
            'total_balance': total_balance,
            'usdt_balance': usdt_balance,
            'position_value': total_position_value,
            'positions': self.position_manager.get_all_positions(),
            'daily_pnl': self.risk_manager.daily_pnl
        }
    
    def print_account_summary(self):
        """打印账户摘要"""
        summary = self.get_account_summary()
        print("\n💰 账户摘要")
        print("=" * 50)
        print(f"总资产: ${summary['total_balance']:.2f}")
        print(f"USDT余额: ${summary['usdt_balance']:.2f}")
        print(f"持仓价值: ${summary['position_value']:.2f}")
        print(f"日盈亏: ${summary['daily_pnl']:.2f}")
        
        if summary['positions']:
            print("\n📊 当前持仓:")
            for symbol, position in summary['positions'].items():
                if position.quantity > 0:
                    current_price = self.get_current_price(symbol)
                    unrealized_pnl = (current_price - position.avg_price) * position.quantity
                    print(f"  {symbol}: {position.quantity:.6f} @ ${position.avg_price:.2f} "
                          f"(当前: ${current_price:.2f}, 盈亏: ${unrealized_pnl:.2f})")
        print("=" * 50) 