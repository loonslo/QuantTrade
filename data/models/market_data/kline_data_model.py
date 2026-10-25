"""
K线数据模型
定义K线数据的SQLAlchemy模型结构
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, Boolean
from data.models.base.base_model import BaseModel


class KlineDataBase(BaseModel):
    """K线数据基类"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    symbol = Column(String(20), nullable=False, index=True, comment='交易对符号')
    timeframe = Column(String(10), nullable=False, comment='时间周期')
    timestamp = Column(String(50), nullable=False, index=True, comment='K线时间（字符串存储）')
    open_price = Column(Float, nullable=False, comment='开盘价')
    high_price = Column(Float, nullable=False, comment='最高价')
    low_price = Column(Float, nullable=False, comment='最低价')
    close_price = Column(Float, nullable=False, comment='收盘价')
    volume = Column(Float, nullable=False, comment='成交量')
    
    is_valid = Column(Boolean, default=True, nullable=False, comment='数据是否有效')
    source = Column(String(20), default='binance', nullable=False, comment='数据源')
    
    def __init__(self, **kwargs):
        # 设置默认数据源
        if 'source' not in kwargs:
            kwargs['source'] = 'binance'
        super().__init__(**kwargs)
    
    def get_ohlcv(self):
        """获取OHLCV数据"""
        return {
            'timestamp': self.timestamp,
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume
        }


class KlineData1m(KlineDataBase):
    """1分钟K线数据表"""
    __tablename__ = 'kline_data_1m'

    def __init__(self, **kwargs):
        kwargs['timeframe'] = '1m'
        super().__init__(**kwargs)

    __table_args__ = (
        Index('idx_kline_data_1m_symbol', 'symbol'),
        Index('idx_kline_data_1m_timestamp', 'timestamp'),
        Index('idx_kline_data_1m_valid', 'is_valid'),
        Index('idx_kline_data_1m_source', 'source'),
        Index('idx_kline_data_1m_symbol_time', 'symbol', 'timestamp'),
        Index('idx_unique_kline_1m', 'symbol', 'timeframe', 'timestamp', unique=True),
        {'comment': '1分钟粒度K线数据表'}
    )


class KlineData5m(KlineDataBase):
    """5分钟K线数据表"""
    __tablename__ = 'kline_data_5m'

    def __init__(self, **kwargs):
        kwargs['timeframe'] = '5m'
        super().__init__(**kwargs)

    __table_args__ = (
        Index('idx_kline_data_5m_symbol', 'symbol'),
        Index('idx_kline_data_5m_timestamp', 'timestamp'),
        Index('idx_kline_data_5m_valid', 'is_valid'),
        Index('idx_kline_data_5m_source', 'source'),
        Index('idx_kline_data_5m_symbol_time', 'symbol', 'timestamp'),
        Index('idx_unique_kline_5m', 'symbol', 'timeframe', 'timestamp', unique=True),
        {'comment': '5分钟粒度K线数据表'}
    )


## 注意：按需求移除3m时间周期表定义，避免创建 kline_data_3m 表


class KlineData15m(KlineDataBase):
    """15分钟K线数据表"""
    __tablename__ = 'kline_data_15m'

    def __init__(self, **kwargs):
        kwargs['timeframe'] = '15m'
        super().__init__(**kwargs)

    __table_args__ = (
        Index('idx_kline_data_15m_symbol', 'symbol'),
        Index('idx_kline_data_15m_timestamp', 'timestamp'),
        Index('idx_kline_data_15m_valid', 'is_valid'),
        Index('idx_kline_data_15m_source', 'source'),
        Index('idx_kline_data_15m_symbol_time', 'symbol', 'timestamp'),
        Index('idx_unique_kline_15m', 'symbol', 'timeframe', 'timestamp', unique=True),
        {'comment': '15分钟粒度K线数据表'}
    )


class KlineData1h(KlineDataBase):
    """1小时K线数据表"""
    __tablename__ = 'kline_data_1h'

    def __init__(self, **kwargs):
        kwargs['timeframe'] = '1h'
        super().__init__(**kwargs)

    __table_args__ = (
        Index('idx_kline_data_1h_symbol', 'symbol'),
        Index('idx_kline_data_1h_timestamp', 'timestamp'),
        Index('idx_kline_data_1h_valid', 'is_valid'),
        Index('idx_kline_data_1h_source', 'source'),
        Index('idx_kline_data_1h_symbol_time', 'symbol', 'timestamp'),
        Index('idx_unique_kline_1h', 'symbol', 'timeframe', 'timestamp', unique=True),
        {'comment': '1小时粒度K线数据表'}
    )


class KlineData4h(KlineDataBase):
    """4小时K线数据表"""
    __tablename__ = 'kline_data_4h'

    def __init__(self, **kwargs):
        kwargs['timeframe'] = '4h'
        super().__init__(**kwargs)

    __table_args__ = (
        Index('idx_kline_data_4h_symbol', 'symbol'),
        Index('idx_kline_data_4h_timestamp', 'timestamp'),
        Index('idx_kline_data_4h_valid', 'is_valid'),
        Index('idx_kline_data_4h_source', 'source'),
        Index('idx_kline_data_4h_symbol_time', 'symbol', 'timestamp'),
        Index('idx_unique_kline_4h', 'symbol', 'timeframe', 'timestamp', unique=True),
        {'comment': '4小时粒度K线数据表'}
    )


class KlineData1d(KlineDataBase):
    """1天K线数据表"""
    __tablename__ = 'kline_data_1d'

    def __init__(self, **kwargs):
        kwargs['timeframe'] = '1d'
        super().__init__(**kwargs)

    __table_args__ = (
        Index('idx_kline_data_1d_symbol', 'symbol'),
        Index('idx_kline_data_1d_timestamp', 'timestamp'),
        Index('idx_kline_data_1d_valid', 'is_valid'),
        Index('idx_kline_data_1d_source', 'source'),
        Index('idx_kline_data_1d_symbol_time', 'symbol', 'timestamp'),
        Index('idx_unique_kline_1d', 'symbol', 'timeframe', 'timestamp', unique=True),
        {'comment': '1天粒度K线数据表'}
    )


class CryptoMarketRankings(BaseModel):
    """加密货币市场排行表"""
    __tablename__ = 'crypto_market_rankings'

    id = Column(Integer, primary_key=True, comment='主键ID')
    symbol = Column(String(20), nullable=False, index=True, comment='币种/交易对符号')
    quote_asset = Column(String(10), nullable=False, index=True, comment='计价货币，例如 USDT')
    
    # 价格信息
    price = Column(Float, nullable=False, comment='当前价格')
    change_24h = Column(Float, comment='24小时涨跌幅(%)')
    change_amount = Column(Float, comment='24小时价格变动金额')
    
    # 成交量信息
    volume_24h = Column(Float, comment='24小时成交量')
    
    # 市值信息
    market_cap = Column(Float, comment='市值')
    
    # 排名信息
    market_cap_rank = Column(Integer, index=True, comment='市值排名')
    
    # 时间和状态
    data_timestamp = Column(DateTime, nullable=False, index=True, comment='数据更新时间')
    is_valid = Column(Boolean, default=True, nullable=False, comment='数据是否有效')

    def __init__(self, **kwargs):
        # 设置默认数据源
        if 'source' not in kwargs:
            kwargs['source'] = 'coingecko'
        super().__init__(**kwargs)

    __table_args__ = (
        Index('idx_crypto_rankings_quote_mcap_rank', 'quote_asset', 'market_cap_rank'),
        Index('idx_crypto_rankings_valid_time', 'is_valid', 'data_timestamp'),
        Index('idx_crypto_rankings_symbol_quote', 'symbol', 'quote_asset'),
        Index('idx_crypto_rankings_change_24h', 'change_24h'),
        Index('idx_crypto_rankings_market_cap', 'market_cap'),
        {'comment': '加密货币市场排行与行情数据表'}
    )