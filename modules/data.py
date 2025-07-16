import ccxt
import pandas as pd
from config import Config

class DataLoader:
    def __init__(self, exchange=None, env='development'):
        """
        初始化数据加载器
        :param exchange: 交易所对象，如果为None则自动创建
        :param env: 环境类型 ('development', 'test', 'production')
        """
        if exchange is None:
            config = Config(env=env)
            self.exchange = ccxt.binance(config.get_public_config())
        else:
            self.exchange = exchange

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 500):
        """
        使用ccxt获取币安K线数据
        
        支持的时间框架：
        1m - 1分钟
        3m - 3分钟
        5m - 5分钟
        15m - 15分钟
        30m - 30分钟
        1h - 1小时
        2h - 2小时
        4h - 4小时
        6h - 6小时
        8h - 8小时
        12h - 12小时
        1d - 1天
        3d - 3天
        1w - 1周
        1M - 1个月
        """
        return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    def to_dataframe(self, ohlcv):
        """
        将K线数据转换为pandas DataFrame
        """
        df = pd.DataFrame(ohlcv, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        return df 