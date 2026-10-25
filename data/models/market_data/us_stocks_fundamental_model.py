# -*- coding: utf-8 -*-
"""
美股基本面数据模型
存储美股的基本面指标数据（估值、盈利能力、成长性等）
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from data.models.base.base_model import BaseModel


class USStockFundamental(BaseModel):
    """美股基本面数据表"""
    __tablename__ = 'us_stock_fundamental'

    id = Column(Integer, primary_key=True, comment='主键ID')
    symbol = Column(String(20), nullable=False, index=True, comment='股票代码(如AAPL)')
    timestamp = Column(DateTime, nullable=False, index=True, comment='数据更新时间')

    # 估值指标
    pe_ratio = Column(Float, comment='市盈率(PE)')
    pb_ratio = Column(Float, comment='市净率(PB)')
    ps_ratio = Column(Float, comment='市销率(PS)')

    # 盈利能力
    roe = Column(Float, comment='净资产收益率(ROE)')
    roa = Column(Float, comment='资产收益率(ROA)')
    profit_margin = Column(Float, comment='净利润率')

    # 成长性
    revenue_growth = Column(Float, comment='营收增长率(%)')
    earnings_growth = Column(Float, comment='盈利增长率(%)')

    # 股息
    dividend_yield = Column(Float, comment='股息率(%)')

    # 市值相关
    market_cap = Column(Float, comment='市值')
    price = Column(Float, comment='当前价格')
    beta = Column(Float, comment='Beta系数')

    source = Column(String(20), default='finnhub', comment='数据来源')

    __table_args__ = (
        Index('idx_us_fundamental_symbol', 'symbol'),
        Index('idx_us_fundamental_timestamp', 'timestamp'),
        Index('idx_us_fundamental_symbol_timestamp', 'symbol', 'timestamp'),
        {'comment': '美股基本面数据表'}
    )

    def __init__(self, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'finnhub'
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
