"""
QDII基金数据库模型
存储场内QDII基金数据（纳斯达克和标普相关）
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, Boolean, Date
from data.models.base.base_model import BaseModel


class QDIIFund(BaseModel):
    """QDII基金数据表"""
    __tablename__ = 'qdii_fund'

    id = Column(Integer, primary_key=True, comment='主键ID')
    fund_code = Column(String(20), nullable=False, index=True, comment='基金代码')
    fund_name = Column(String(200), comment='基金简称')
    establishment_date = Column(Date, comment='成立日期')
    asset_scale = Column(Float, comment='资产规模(亿元)')
    net_value = Column(Float, comment='单位净值')
    accumulated_value = Column(Float, comment='累计净值')
    change_percent = Column(Float, comment='净值变化百分比(%)')
    purchase_fee = Column(Float, comment='购买手续费(%)')
    management_fee = Column(Float, comment='管理费率(%)')
    custodian_fee = Column(Float, comment='托管费率(%)')
    sales_service_fee = Column(Float, comment='销售服务费率(%)')
    total_fee = Column(Float, comment='综合费率(%)')
    benchmark = Column(String(200), comment='业绩比较基准')
    trading_status = Column(String(50), comment='交易状态')
    purchase_limit = Column(String(100), comment='购买限制')
    tracking_error = Column(Float, comment='基金追踪偏差(%)')
    fund_type = Column(String(50), comment='基金类型(NASDAQ/SP500)')
    data_timestamp = Column(DateTime, nullable=False, index=True, comment='数据时间')
    is_valid = Column(Boolean, default=True, nullable=False, comment='数据是否有效')

    __table_args__ = (
        Index('idx_qdii_fund_code_time', 'fund_code', 'data_timestamp'),
        Index('idx_qdii_fund_type', 'fund_type'),
        Index('idx_qdii_fund_valid', 'is_valid', 'data_timestamp'),
        {'comment': 'QDII基金数据表（纳斯达克和标普相关）'}
    )

    def __init__(self, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'eastmoney'
        super().__init__(**kwargs)
