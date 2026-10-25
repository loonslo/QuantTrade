"""
市场概览数据库模型
存储市场宏观数据，包括总市值、主导率、恐惧贪婪指数等
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, Boolean
from data.models.base.base_model import BaseModel


class MarketOverview(BaseModel):
    """市场概览数据表"""
    __tablename__ = 'market_overview'  

    id = Column(Integer, primary_key=True, comment='主键ID')
    total_market_cap = Column(Float, comment='总市值')
    total_volume_24h = Column(Float, comment='24小时总成交量')
    market_trend = Column(String(20), comment='市场趋势(bullish/bearish/neutral)')
    risk_level = Column(String(20), comment='风险等级(low/medium/high)')
    btc_dominance = Column(Float, comment='BTC 主导率(%)')
    eth_dominance = Column(Float, comment='ETH 主导率(%)')
    fear_greed_value = Column(Integer, comment='恐惧贪婪值')
    fear_greed_classification = Column(String(20), comment='恐惧贪婪分类')
    data_timestamp = Column(DateTime, nullable=False, index=True, comment='数据时间')
    is_valid = Column(Boolean, default=True, nullable=False, comment='数据是否有效')

    __table_args__ = (
        Index('idx_market_data_valid_time', 'is_valid', 'data_timestamp'),
        Index('idx_market_data_trend', 'market_trend'),
        {'comment': '市场宏观概览与主导率快照表'}
    )

    def __init__(self, **kwargs):
        # 设置默认数据源
        if 'source' not in kwargs:
            kwargs['source'] = 'aggregated'
        super().__init__(**kwargs)
