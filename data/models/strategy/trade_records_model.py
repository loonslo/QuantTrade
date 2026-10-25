"""
交易记录模型集合
包含SQLAlchemy数据库模型和数据类业务模型
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Float, DateTime, Text, Index

from data.models.base.base_model import BaseModel
from utils.core.logger_manager import get_logger
from utils.validation.exceptions import DataException


# SQLAlchemy 数据库模型
class TradeRecords(BaseModel):
    """交易记录表"""
    __tablename__ = 'trade_records'

    id = Column(String(50), primary_key=True, comment='交易记录ID（UUID）')
    symbol = Column(String(20), nullable=False, index=True, comment='交易对/标的')
    side = Column(String(10), nullable=False, comment='方向：buy/sell')
    quantity = Column(Float, nullable=False, comment='数量')
    price = Column(Float, nullable=False, comment='价格')
    trade_datetime = Column(DateTime, nullable=False, index=True, comment='成交时间')
    commission = Column(Float, nullable=False, default=0.0, comment='手续费')
    pnl = Column(Float, comment='盈亏（卖出时计算）')
    strategy_name = Column(String(100), default='', index=True, comment='策略名称')
    position_id = Column(String(50), index=True, comment='持仓/订单ID')
    extra_data = Column(Text, default='{}', comment='附加信息JSON')

    def __init__(self, **kwargs):
        # 设置默认数据源
        if 'source' not in kwargs:
            kwargs['source'] = 'trading_system'
        super().__init__(**kwargs)

    __table_args__ = (
        Index('idx_trade_records_symbol', 'symbol'),
        Index('idx_trade_records_datetime', 'trade_datetime'),
        Index('idx_trade_records_strategy', 'strategy_name'),
        Index('idx_trade_records_side', 'side'),
        Index('idx_trade_records_symbol_side', 'symbol', 'side'),
        {'comment': '策略回测/实盘的逐笔交易记录表'}
    )


 


# 数据类业务模型
@dataclass
class TradeRecordModel:
    """交易记录模型"""

    id: str
    symbol: str
    side: str  # 'buy', 'sell'
    quantity: float
    price: float
    timestamp: datetime
    commission: float
    pnl: Optional[float] = None
    strategy_name: str = ""
    position_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """数据验证"""
        self._validate_data()

    def _validate_data(self):
        """验证数据有效性"""
        if not self.id or not isinstance(self.id, str):
            raise DataException("无效的交易ID")

        if not self.symbol or not isinstance(self.symbol, str):
            raise DataException("无效的交易对")

        if self.side not in ['buy', 'sell']:
            raise DataException(f"无效的交易方向: {self.side}")

        if not isinstance(self.quantity, (int, float)) or self.quantity <= 0:
            raise DataException(f"无效的数量: {self.quantity}")

        if not isinstance(self.price, (int, float)) or self.price <= 0:
            raise DataException(f"无效的价格: {self.price}")

        if not isinstance(self.timestamp, datetime):
            raise DataException("无效的时间戳")

        if not isinstance(self.commission, (int, float)) or self.commission < 0:
            raise DataException(f"无效的手续费: {self.commission}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'timestamp': self.timestamp,
            'commission': self.commission,
            'pnl': self.pnl,
            'strategy_name': self.strategy_name,
            'position_id': self.position_id,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradeRecordModel':
        """从字典创建"""
        return cls(
            id=data['id'],
            symbol=data['symbol'],
            side=data['side'],
            quantity=data['quantity'],
            price=data['price'],
            timestamp=data['timestamp'],
            commission=data['commission'],
            pnl=data.get('pnl'),
            strategy_name=data.get('strategy_name', ''),
            position_id=data.get('position_id'),
            metadata=data.get('metadata', {})
        )

    @classmethod
    def create_trade(cls, symbol: str, side: str, quantity: float,
                     price: float, timestamp: datetime, commission: float = 0.0,
                     strategy_name: str = "", position_id: Optional[str] = None) -> 'TradeRecordModel':
        """创建交易记录"""
        trade_id = str(uuid.uuid4())

        return cls(
            id=trade_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            commission=commission,
            strategy_name=strategy_name,
            position_id=position_id
        )

    def get_total_value(self) -> float:
        """获取交易总价值"""
        return self.quantity * self.price

    def get_net_value(self) -> float:
        """获取交易净价值（扣除手续费）"""
        return self.get_total_value() - self.commission

    def is_buy(self) -> bool:
        """是否为买入交易"""
        return self.side == 'buy'

    def is_sell(self) -> bool:
        """是否为卖出交易"""
        return self.side == 'sell'

    def calculate_pnl(self, entry_price: float) -> float:
        """计算盈亏"""
        if self.is_buy():
            return 0.0

        pnl = (self.price - entry_price) * self.quantity - self.commission
        return pnl

    def get_pnl_pct(self, entry_price: float) -> float:
        """计算盈亏百分比"""
        if entry_price == 0 or self.is_buy():
            return 0.0

        pnl_pct = (self.price - entry_price) / entry_price * 100
        return pnl_pct

    def get_commission_pct(self) -> float:
        """获取手续费百分比"""
        total_value = self.get_total_value()
        if total_value == 0:
            return 0.0

        return (self.commission / total_value) * 100


class TradeRecordCollection:
    """交易记录集合"""

    def __init__(self):
        self.logger = get_logger('trade_record')
        self.trades: Dict[str, TradeRecordModel] = {}

    def add_trade(self, trade: TradeRecordModel):
        """添加交易记录"""
        self.trades[trade.id] = trade
        self.logger.info(f"添加交易记录: {trade.side} {trade.symbol} "
                         f"{trade.quantity} @ {trade.price}")

    def get_trade(self, trade_id: str) -> Optional[TradeRecordModel]:
        """获取交易记录"""
        return self.trades.get(trade_id)

    def get_trades_by_symbol(self, symbol: str) -> List[TradeRecordModel]:
        """获取指定交易对的交易记录"""
        return [trade for trade in self.trades.values() if trade.symbol == symbol]

    def get_trades_by_strategy(self, strategy_name: str) -> List[TradeRecordModel]:
        """获取指定策略的交易记录"""
        return [trade for trade in self.trades.values() if trade.strategy_name == strategy_name]

    def get_trades_by_time_range(self, start_time: datetime,
                                 end_time: datetime) -> List[TradeRecordModel]:
        """获取指定时间范围的交易记录"""
        return [trade for trade in self.trades.values()
                if start_time <= trade.timestamp <= end_time]

    def get_buy_trades(self) -> List[TradeRecordModel]:
        """获取买入交易"""
        return [trade for trade in self.trades.values() if trade.is_buy()]

    def get_sell_trades(self) -> List[TradeRecordModel]:
        """获取卖出交易"""
        return [trade for trade in self.trades.values() if trade.is_sell()]

    def get_total_trades(self) -> int:
        """获取总交易次数"""
        return len(self.trades)

    def get_total_volume(self) -> float:
        """获取总交易量"""
        return sum(trade.quantity for trade in self.trades.values())

    def get_total_commission(self) -> float:
        """获取总手续费"""
        return sum(trade.commission for trade in self.trades.values())

    def get_total_pnl(self) -> float:
        """获取总盈亏"""
        return sum(trade.pnl or 0 for trade in self.trades.values())

    def get_trade_summary(self) -> Dict[str, Any]:
        """获取交易摘要"""
        buy_trades = self.get_buy_trades()
        sell_trades = self.get_sell_trades()

        return {
            'total_trades': self.get_total_trades(),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_volume': self.get_total_volume(),
            'total_commission': self.get_total_commission(),
            'total_pnl': self.get_total_pnl(),
            'symbols': list(set(trade.symbol for trade in self.trades.values())),
            'strategies': list(set(trade.strategy_name for trade in self.trades.values() if trade.strategy_name))
        }

    def get_symbol_summary(self, symbol: str) -> Dict[str, Any]:
        """获取指定交易对的摘要"""
        symbol_trades = self.get_trades_by_symbol(symbol)

        if not symbol_trades:
            return {}

        buy_trades = [t for t in symbol_trades if t.is_buy()]
        sell_trades = [t for t in symbol_trades if t.is_sell()]

        total_buy_volume = sum(t.quantity for t in buy_trades)
        total_sell_volume = sum(t.quantity for t in sell_trades)
        total_buy_value = sum(t.get_total_value() for t in buy_trades)
        total_sell_value = sum(t.get_total_value() for t in sell_trades)

        return {
            'symbol': symbol,
            'total_trades': len(symbol_trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_buy_volume': total_buy_volume,
            'total_sell_volume': total_sell_volume,
            'total_buy_value': total_buy_value,
            'total_sell_value': total_sell_value,
            'net_volume': total_buy_volume - total_sell_volume,
            'total_commission': sum(t.commission for t in symbol_trades),
            'total_pnl': sum(t.pnl or 0 for t in symbol_trades)
        }