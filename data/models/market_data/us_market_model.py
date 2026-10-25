"""
美国市场数据库模型
存储纳斯达克、标普500指数和美元人民币汇率数据
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, Boolean
from data.models.base.base_model import BaseModel


class USMarketIndex(BaseModel):
    """美国市场指数数据表"""
    __tablename__ = 'us_market_index'

    id = Column(Integer, primary_key=True, comment='主键ID')
    symbol = Column(String(20), nullable=False, index=True, comment='指数代码(NASDAQ/SP500)')
    name = Column(String(100), comment='指数名称')
    price = Column(Float, comment='当前价格')
    change = Column(Float, comment='涨跌额')
    change_percent = Column(Float, comment='涨跌幅(%)')
    open_price = Column(Float, comment='开盘价')
    high_price = Column(Float, comment='最高价')
    low_price = Column(Float, comment='最低价')
    volume = Column(Float, comment='成交量')
    data_timestamp = Column(DateTime, nullable=False, index=True, comment='数据时间')
    is_valid = Column(Boolean, default=True, nullable=False, comment='数据是否有效')

    __table_args__ = (
        Index('idx_us_index_symbol_time', 'symbol', 'data_timestamp'),
        Index('idx_us_index_valid', 'is_valid', 'data_timestamp'),
        {'comment': '美国市场指数数据表（纳斯达克、标普500）'}
    )

    def __init__(self, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'yahoo_finance'
        super().__init__(**kwargs)


class ExchangeRate(BaseModel):
    """汇率数据表"""
    __tablename__ = 'exchange_rate'

    id = Column(Integer, primary_key=True, comment='主键ID')
    symbol = Column(String(20), nullable=False, index=True, comment='汇率代码(USDCNY)')
    name = Column(String(100), comment='汇率名称')
    rate = Column(Float, comment='汇率')
    change = Column(Float, comment='涨跌额')
    change_percent = Column(Float, comment='涨跌幅(%)')
    open_rate = Column(Float, comment='开盘汇率')
    high_rate = Column(Float, comment='最高汇率')
    low_rate = Column(Float, comment='最低汇率')
    data_timestamp = Column(DateTime, nullable=False, index=True, comment='数据时间')
    is_valid = Column(Boolean, default=True, nullable=False, comment='数据是否有效')

    __table_args__ = (
        Index('idx_exchange_rate_symbol_time', 'symbol', 'data_timestamp'),
        Index('idx_exchange_rate_valid', 'is_valid', 'data_timestamp'),
        {'comment': '汇率数据表（美元人民币等）'}
    )

    def __init__(self, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'yahoo_finance'
        super().__init__(**kwargs)
