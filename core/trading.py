"""
独立实盘交易模块

可以直接从 core.trading 导入，避免循环导入问题。

功能：
- 交易所工厂模式
- Binance 实时交易
- 订单管理
- 持仓同步
- 风险管理

使用示例：
    from core.trading import create_exchange_trader

    trader = create_exchange_trader('binance', {
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret'
    })

    balance = trader.get_balance()
    order = trader.buy('BTCUSDT', quantity=0.001, price=50000)
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

from .trading_engine import TradingEngine

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIAL_FILLED = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Side(Enum):
    """买卖方向"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """订单数据类"""
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float = None
    filled_quantity: float = 0
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    commission: float = 0

    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity


@dataclass
class Position:
    """持仓数据类"""
    symbol: str
    quantity: float
    avg_price: float = 0
    current_price: float = 0
    pnl: float = 0
    pnl_percent: float = 0


class ExchangeTrader(ABC):
    """交易所交易器抽象基类"""

    @abstractmethod
    def get_balance(self, asset: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def buy(self, symbol: str, quantity: float, price: float = None,
            order_type: str = 'limit') -> Dict[str, Any]:
        pass

    @abstractmethod
    def sell(self, symbol: str, quantity: float, price: float = None,
             order_type: str = 'limit') -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        pass

    @abstractmethod
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_open_orders(self, symbol: str = None) -> list:
        pass

    @abstractmethod
    def get_position(self, symbol: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def close(self):
        pass


class BinanceTrader(ExchangeTrader, TradingEngine):
    """Spot adapter with an entirely local paper mode and explicit live mode."""

    def __init__(self, config: Dict[str, Any]):
        from .backtest_engine import BacktestEngine
        self.config = config
        self.test_mode = config.get('test_mode', True)
        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        self._paper = BacktestEngine(config.get('initial_cash', 10000), config.get('commission', 0.001))
        self._paper_prices = dict(config.get('paper_prices', {}))
        self._paper_orders = {}
        self._client = None
        if not self.test_mode:
            import ccxt
            if not config.get('api_key') or not config.get('api_secret'):
                raise ValueError('Live mode requires locally supplied API credentials')
            self._client = ccxt.binance({
                'apiKey': config['api_key'], 'secret': config['api_secret'],
                'enableRateLimit': True, 'options': {'defaultType': 'spot'},
            })
            if config.get('sandbox', False):
                self._client.set_sandbox_mode(True)

    def get_balance(self, asset: str = None) -> Dict[str, Any]:
        if self.test_mode:
            totals = {'USDT': self._paper.get_balance()['cash']}
            for position in self._paper.get_positions():
                base = position['symbol'].split('/')[0].removesuffix('USDT')
                totals[base] = totals.get(base, 0) + position['quantity']
            balance = {'free': totals.copy(), 'used': {}, 'total': totals}
        else:
            balance = self._client.fetch_balance()
        if asset:
            return {kind: balance.get(kind, {}).get(asset, 0) for kind in ('free', 'used', 'total')}
        return balance

    def _submit(self, symbol, quantity, price, order_type, side):
        import math
        from uuid import uuid4
        if not math.isfinite(quantity) or quantity <= 0:
            raise ValueError('Order quantity must be finite and positive')
        order_type = order_type or ('market' if price is None else 'limit')
        if order_type not in {'market', 'limit'}:
            raise ValueError('Only market and limit orders are supported')
        if price is not None and (not math.isfinite(price) or price <= 0):
            raise ValueError('Order price must be finite and positive')
        if order_type == 'limit' and price is None:
            raise ValueError('A limit order requires a price')
        if not self.test_mode:
            return self._client.create_order(symbol, order_type, side, quantity, price)
        order = {
            'id': f'paper_{uuid4().hex}', 'symbol': symbol, 'type': order_type,
            'side': side, 'amount': quantity, 'price': price, 'filled': 0.0,
            'status': 'open', 'test_mode': True,
        }
        if order_type == 'market':
            execution_price = self._paper_prices.get(symbol)
            if execution_price is None:
                raise ValueError('Paper market orders require paper_prices for the symbol')
            result = getattr(self._paper, side)(symbol, quantity, execution_price)
            if not result['success']:
                raise ValueError(result['error'])
            order.update(status='closed', filled=quantity, average=execution_price,
                         fee={'cost': result['commission'], 'currency': 'USDT'})
        self._paper_orders[order['id']] = order
        return order.copy()

    def buy(self, symbol, quantity, price=None, order_type=None):
        return self._submit(symbol, quantity, price, order_type, 'buy')

    def sell(self, symbol, quantity, price=None, order_type=None):
        return self._submit(symbol, quantity, price, order_type, 'sell')

    def cancel_order(self, symbol, order_id):
        if self.test_mode:
            order = self._paper_orders[order_id]
            if order['symbol'] != symbol or order['status'] != 'open':
                return False
            order['status'] = 'canceled'
            return True
        self._client.cancel_order(order_id, symbol)
        return True

    def get_order(self, symbol, order_id):
        if self.test_mode:
            order = self._paper_orders[order_id]
            if order['symbol'] != symbol:
                raise ValueError('Order symbol mismatch')
            return order.copy()
        return self._client.fetch_order(order_id, symbol)

    def get_open_orders(self, symbol=None):
        if self.test_mode:
            return [order.copy() for order in self._paper_orders.values()
                    if order['status'] == 'open' and (symbol is None or order['symbol'] == symbol)]
        return self._client.fetch_open_orders(symbol)

    def get_position(self, symbol=None):
        if self.test_mode:
            positions = {p['symbol']: p for p in self._paper.get_positions()}
        else:
            balance = self._client.fetch_balance()
            positions = {}
            for market in self.symbols:
                base = market.split('/')[0].removesuffix('USDT')
                quantity = balance['total'].get(base, 0)
                if quantity > 0:
                    positions[market] = {'symbol': market, 'quantity': quantity,
                                         'price': self.get_ticker(market)['last']}
        return positions if symbol is None else positions.get(symbol, {})

    def get_positions(self):
        return list(self.get_position().values())

    def get_ticker(self, symbol):
        if self.test_mode:
            if symbol not in self._paper_prices:
                raise ValueError('No paper quote configured for this symbol')
            return {'symbol': symbol, 'last': self._paper_prices[symbol]}
        return self._client.fetch_ticker(symbol)

    def reset(self, initial_cash=None):
        if not self.test_mode:
            raise ValueError('Live account state cannot be reset locally')
        self._paper.reset(initial_cash)
        self._paper_orders.clear()

    def close(self):
        if self._client is not None and hasattr(self._client, 'close'):
            self._client.close()


class OrderManager:
    """订单管理器"""

    def __init__(self, trader):
        self.trader = trader
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []

    def create_order(self, symbol: str, side: str, quantity: float,
                     price: float = None, order_type: str = None) -> Order:
        result = self.trader.buy(symbol, quantity, price, order_type) if side == 'buy' else \
            self.trader.sell(symbol, quantity, price, order_type)

        if 'error' in result:
            raise Exception(f"创建订单失败: {result['error']}")

        order = Order(
            order_id=result.get('id', str(datetime.now().timestamp())),
            symbol=symbol, side=side, order_type=order_type,
            quantity=quantity, price=result.get('average') or result.get('price'),
            filled_quantity=float(result.get('filled') or 0),
            status=result.get('status', OrderStatus.OPEN.value),
            commission=float((result.get('fee') or {}).get('cost') or 0)
        )
        self.orders[order.order_id] = order
        logger.info(f"创建订单: {order}")
        return order

    def cancel(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if not order:
            return False
        success = self.trader.cancel_order(order.symbol, order_id)
        if success:
            order.status = OrderStatus.CANCELLED.value
            self.order_history.append(order)
        return success

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.orders.get(order_id)

    def get_open_orders(self, symbol: str = None) -> List[Order]:
        orders = [o for o in self.orders.values() if o.status in ['open', 'pending']]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders


class PositionSync:
    """持仓同步器"""

    def __init__(self, trader, symbols: List[str] = None):
        self.trader = trader
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT']
        self.positions: Dict[str, Position] = {}
        self.last_sync_time = None
        self._init_positions()

    def _init_positions(self):
        for symbol in self.symbols:
            self.positions[symbol] = Position(symbol=symbol, quantity=0)

    def sync(self) -> Dict[str, Position]:
        try:
            exchange_positions = self.trader.get_position()
            for symbol in self.symbols:
                pos = exchange_positions.get(symbol, {}) if isinstance(exchange_positions, dict) else {}
                quantity = pos.get('quantity', 0)
                if symbol not in self.positions:
                    self.positions[symbol] = Position(symbol=symbol, quantity=quantity)
                else:
                    self.positions[symbol].quantity = quantity
                self.positions[symbol].avg_price = pos.get('avg_price', self.positions[symbol].avg_price)
                # 更新价格
                ticker = self.trader.get_ticker(symbol)
                if 'error' not in ticker:
                    self.positions[symbol].current_price = ticker.get('last', 0)
                    if self.positions[symbol].avg_price:
                        self.positions[symbol].pnl = (ticker.get('last', 0) -
                                                      self.positions[symbol].avg_price) * quantity
            self.last_sync_time = datetime.now()
            return self.positions
        except Exception as e:
            logger.error(f"持仓同步失败: {e}")
            return self.positions

    def get_all_positions(self) -> List[Position]:
        return [p for p in self.positions.values() if p.quantity > 0]

    def get_total_value(self) -> float:
        return sum(p.quantity * p.current_price for p in self.positions.values())

    def get_total_pnl(self) -> float:
        return sum(p.pnl for p in self.positions.values())


class LiveTradingManager(TradingEngine):
    """实盘交易管理器 - 整合版 - 实现 TradingEngine 接口"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.symbols = config.get('symbols', ['BTCUSDT', 'ETHUSDT'])
        self.test_mode = config.get('test_mode', True)
        self.is_running = False
        self._init_components()

    def _init_components(self):
        self.trader = create_exchange_trader(
            self.config.get('exchange', 'binance'),
            {'api_key': self.config.get('api_key', ''),
             'api_secret': self.config.get('api_secret', ''),
             'test_mode': self.test_mode, 'symbols': self.symbols,
             'initial_cash': self.config.get('initial_cash', 10000),
             'paper_prices': self.config.get('paper_prices', {}),
             'sandbox': self.config.get('sandbox', False)}
        )
        self.order_manager = OrderManager(self.trader)
        self.position_sync = PositionSync(self.trader, self.symbols)
        logger.info("实盘交易管理器初始化完成")

    def start(self):
        self.is_running = True
        self.position_sync.sync()
        logger.info("实盘交易管理器已启动")

    def stop(self):
        self.is_running = False
        self.trader.close()
        logger.info("实盘交易管理器已停止")

    def get_balance(self, asset: str = None):
        return self.trader.get_balance(asset)

    def buy(self, symbol: str, quantity: float, price: float = None):
        order = self.order_manager.create_order(symbol, 'buy', quantity, price)
        return {'success': True, **asdict(order)}

    def sell(self, symbol: str, quantity: float, price: float = None):
        order = self.order_manager.create_order(symbol, 'sell', quantity, price)
        return {'success': True, **asdict(order)}

    def get_positions(self) -> List[Dict[str, Any]]:
        return [
            {'symbol': p.symbol, 'quantity': p.quantity,
             'current_price': p.current_price, 'pnl': p.pnl}
            for p in self.position_sync.get_all_positions()
        ]

    def get_status(self) -> Dict[str, Any]:
        return {
            'is_running': self.is_running, 'test_mode': self.test_mode,
            'symbols': self.symbols, 'positions_count': len(self.get_positions())
        }

    def reset(self, initial_cash: float = None):
        """
        重置管理器状态
        
        Args:
            initial_cash: 初始资金（实盘模式下会被忽略，余额由交易所决定）
        """
        self.trader.reset(initial_cash)
        self.order_manager.orders.clear()
        self.order_manager.order_history.clear()
        self.position_sync.sync()


def create_exchange_trader(exchange: str, config: Dict[str, Any]) -> ExchangeTrader:
    """创建交易所交易器"""
    exchange = exchange.lower()
    if exchange == 'binance':
        return BinanceTrader(config)
    else:
        raise ValueError(f"不支持的交易所: {exchange}")
