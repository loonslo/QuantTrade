# -*- coding: utf-8 -*-
"""
美股个股日K线数据模型
存储美股个股的日K线数据（OHLCV）
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, Boolean
from data.models.base.base_model import BaseModel


class USStockDailyKline(BaseModel):
    """美股个股日K线数据表"""
    __tablename__ = 'us_stock_daily_kline'

    id = Column(Integer, primary_key=True, comment='主键ID')
    symbol = Column(String(20), nullable=False, index=True, comment='股票代码(如AAPL)')
    timestamp = Column(DateTime, nullable=False, index=True, comment='K线日期')
    open_price = Column(Float, comment='开盘价')
    high_price = Column(Float, comment='最高价')
    low_price = Column(Float, comment='最低价')
    close_price = Column(Float, comment='收盘价')
    volume = Column(Float, comment='成交量')

    __table_args__ = (
        Index('idx_us_stock_symbol_time', 'symbol', 'timestamp'),
        Index('idx_us_stock_valid', 'is_valid', 'timestamp'),
        {'comment': '美股个股日K线数据表'}
    )

    def __init__(self, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'yahoo_finance'
        super().__init__(**kwargs)

    def to_dict(self):
        """转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        return result
