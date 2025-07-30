import ccxt
import pandas as pd
from typing import List, Optional
from datetime import datetime
from config import Config


class DataLoader:
    def __init__(self, exchange=None, env='development', config: dict = None):
        """
        初始化数据加载器
        :param exchange: 交易所对象(可选)，默认创建Binance实例
        :param env: 运行环境('development'/'test'/'production')
        :param config: 可直接传入ccxt配置字典(最高优先级)
        """
        self.env = env
        self._user_config = config

        if exchange is not None:
            self.exchange = exchange
        else:
            ccxt_config = config if config else Config(env=env).get_public_config()
            print(f"初始化ccxt配置:{ccxt_config}")  # 调试日志
            self.exchange = ccxt.binance(ccxt_config)

    def set_config(self, config: dict):
        """动态更新ccxt配置"""
        print(f"更新ccxt配置:{config}")
        self.exchange = ccxt.binance(config)

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 500) -> List[list]:
        """
        智能获取K线数据(优先数据库，失败或不足时从交易所获取)

        支持的时间框架：
        1m,3m,5m,15m,30m - 分钟级
        1h,2h,4h,6h,8h,12h - 小时级
        1d,3d - 天级
        1w - 周级
        1M - 月级

        :param symbol: 交易对如'BTC/USDT'
        :param timeframe: K线周期
        :param limit: 获取条数
        :return: OHLCV数据列表
        """
        # 先尝试从数据库获取
        try:
            from modules.database import DatabaseManager  # 延迟导入避免循环依赖
            db_data = DatabaseManager().get_market_data(symbol, timeframe, limit)
            if db_data and len(db_data) >= limit * 0.9:  # 数据库数据足够
                print(f"从数据库获取{len(db_data)}条数据")
                return db_data
        except Exception as e:
            print(f"数据库查询异常:{e}")

        # 从交易所获取数据
        print("从交易所获取实时数据")
        return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    def to_dataframe(self, ohlcv: List[list]) -> pd.DataFrame:
        """
        将OHLCV数据转换为带时区的DataFrame

        :param ohlcv: 原始K线数据
        :return: 东八区(北京时间)的DataFrame
        """
        if not ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(ohlcv, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])

        # 时间戳处理(UTC→东八区)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # 健壮的时间转换处理
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('Asia/Shanghai')

        return df.astype({
            'open': float, 'high': float,
            'low': float, 'close': float,
            'volume': float
        })

    # 兼容旧版API
    def fetch_exchange_ohlcv(self, *args, **kwargs):
        """直接从交易所获取数据(兼容旧版)"""
        return self.exchange.fetch_ohlcv(*args, **kwargs)