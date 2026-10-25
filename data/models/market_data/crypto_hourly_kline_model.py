# -*- coding: utf-8 -*-
"""
加密货币小时K线数据模型
存储加密货币的1H/4H K线数据
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from data.models.base.base_model import BaseModel


class CryptoHourlyKline(BaseModel):
    """加密货币小时K线数据表"""
    __tablename__ = 'crypto_hourly_kline'

    id = Column(Integer, primary_key=True, comment='主键ID')
    symbol = Column(String(20), nullable=False, index=True, comment='交易对符号(如BTC/USDT)')
    timestamp = Column(DateTime, nullable=False, index=True, comment='K线时间')
    interval = Column(String(10), nullable=False, default='1h', comment='时间周期(1h/4h)')
    open_price = Column(Float, comment='开盘价')
    high_price = Column(Float, comment='最高价')
    low_price = Column(Float, comment='最低价')
    close_price = Column(Float, comment='收盘价')
    volume = Column(Float, comment='成交量')

    __table_args__ = (
        Index('idx_crypto_hourly_symbol_interval_time', 'symbol', 'interval', 'timestamp'),
        Index('idx_crypto_hourly_symbol', 'symbol'),
        Index('idx_crypto_hourly_timestamp', 'timestamp'),
        {'comment': '加密货币小时K线数据表(1H/4H)'}
    )

    def __init__(self, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'binance'
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
