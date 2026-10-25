# -*- coding: utf-8 -*-
"""
策略模型
用于管理交易策略的配置信息、元数据和版本
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, Index
from sqlalchemy.sql import func
from data.models.base.base_model import BaseModel


class Strategy(BaseModel):
    """策略表"""
    __tablename__ = 'strategies'

    # 基本信息
    id = Column(Integer, primary_key=True, autoincrement=True, comment='策略ID')
    strategy_id = Column(String(50), unique=True, nullable=False, index=True, comment='策略唯一标识符')
    strategy_name = Column(String(100), nullable=False, comment='策略名称')
    description = Column(Text, comment='策略描述')

    # 分类信息
    strategy_source = Column(String(20), nullable=False, default='system', comment='策略来源: system/user/api')
    strategy_category = Column(String(30), nullable=False, default='technical', comment='策略分类: technical/quant/manual/ml')

    # 版本信息
    version = Column(String(20), nullable=False, default='1.0', comment='版本号')
    author = Column(String(50), comment='策略作者')

    # 参数配置
    parameters = Column(Text, comment='策略参数字段(JSON字符串)')
    default_parameters = Column(Text, comment='默认参数字段(JSON字符串)')

    # 状态信息
    is_active = Column(Boolean, default=True, comment='是否激活')
    is_default = Column(Boolean, default=False, comment='是否默认策略')
    is_public = Column(Boolean, default=False, comment='是否公开策略')

    # 性能指标
    total_signals = Column(Integer, default=0, comment='总信号数')
    success_rate = Column(Float, comment='成功率(0-1)')
    avg_confidence = Column(Float, comment='平均置信度')
    avg_return = Column(Float, comment='平均收益率')
    max_drawdown = Column(Float, comment='最大回撤')
    sharpe_ratio = Column(Float, comment='夏普比率')

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 备注
    notes = Column(Text, comment='备注信息')

    __table_args__ = (
        Index('idx_strategy_id', 'strategy_id'),
        Index('idx_strategy_source', 'strategy_source'),
        Index('idx_strategy_category', 'strategy_category'),
        Index('idx_strategy_active', 'is_active'),
        Index('idx_strategy_default', 'is_default'),
        {'comment': '策略配置表'}
    )

    def __repr__(self):
        return f"<Strategy(id={self.id}, name={self.strategy_name}, source={self.strategy_source}, category={self.strategy_category}, version={self.version})>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'description': self.description,
            'strategy_source': self.strategy_source,
            'strategy_category': self.strategy_category,
            'version': self.version,
            'author': self.author,
            'parameters': self.parameters,
            'default_parameters': self.default_parameters,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'is_public': self.is_public,
            'total_signals': self.total_signals,
            'success_rate': self.success_rate,
            'avg_confidence': self.avg_confidence,
            'avg_return': self.avg_return,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'notes': self.notes,
        }

    def get_parameters_dict(self):
        """获取参数字典"""
        import json
        if self.parameters:
            try:
                return json.loads(self.parameters)
            except:
                return {}
        return {}

    def get_default_parameters_dict(self):
        """获取默认参数字典"""
        import json
        if self.default_parameters:
            try:
                return json.loads(self.default_parameters)
            except:
                return {}
        return {}

    def update_performance_metrics(self, total_signals: int, success_rate: float = None,
                                  avg_confidence: float = None, avg_return: float = None,
                                  max_drawdown: float = None, sharpe_ratio: float = None):
        """更新性能指标"""
        self.total_signals = total_signals
        if success_rate is not None:
            self.success_rate = success_rate
        if avg_confidence is not None:
            self.avg_confidence = avg_confidence
        if avg_return is not None:
            self.avg_return = avg_return
        if max_drawdown is not None:
            self.max_drawdown = max_drawdown
        if sharpe_ratio is not None:
            self.sharpe_ratio = sharpe_ratio
        self.updated_at = func.now()
