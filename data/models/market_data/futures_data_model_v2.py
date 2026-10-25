# -*- coding: utf-8 -*-
"""
期货概览数据模型
直接存储最新持仓量和资金费率数据
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, Boolean, UniqueConstraint
from data.models.base.base_model import BaseModel


class CryptoFuturesOverview(BaseModel):
    """币种期货概览表（最新数据快照）

    直接存储最新的持仓量和资金费率数据
    """
    __tablename__ = 'crypto_futures_overview'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True, comment='交易对符号')

    # 最新期货数据
    latest_open_interest = Column(Float, comment='最新持仓量')
    latest_funding_rate = Column(Float, comment='最新资金费率')
    next_funding_time = Column(String(50), comment='下次资金费率结算时间')

    # 24小时变化
    oi_change_24h = Column(Float, comment='24小时持仓量变化')
    oi_change_percent = Column(Float, comment='24小时持仓量变化百分比')
    fr_change_24h = Column(Float, comment='24小时资金费率变化')

    # 时间信息
    last_update = Column(DateTime, nullable=False, index=True, comment='最后更新时间')

    # 市场信息
    is_active = Column(Boolean, default=True, comment='是否活跃交易对')

    def get_futures_data(self):
        """获取期货数据字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'latest_open_interest': self.latest_open_interest,
            'latest_funding_rate': self.latest_funding_rate,
            'next_funding_time': self.next_funding_time,
            'oi_change_24h': self.oi_change_24h,
            'oi_change_percent': self.oi_change_percent,
            'fr_change_24h': self.fr_change_24h,
            'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None,
            'is_active': self.is_active
        }

    def to_trend_data(self):
        """转换为趋势图数据格式"""
        return {
            'latest_open_interest': self.latest_open_interest,
            'latest_funding_rate': self.latest_funding_rate,
            'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None
        }

    __table_args__ = (
        Index('idx_overview_symbol', 'symbol'),
        Index('idx_overview_update', 'last_update'),
        Index('idx_overview_active', 'is_active'),
        UniqueConstraint('symbol', name='uq_overview_symbol'),
        {'comment': '币种期货概览表 - 持仓量和资金费率数据'}
    )

