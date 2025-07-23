import ccxt
import pandas as pd
from config import Config

class DataLoader:
    def __init__(self, exchange=None, env='development', config: dict = None):
        """
        初始化数据加载器
        :param exchange: 交易所对象，如果为None则自动创建
        :param env: 环境类型 ('development', 'test', 'production')
        :param config: 直接传入ccxt配置dict，优先级最高
        """
        self.env = env
        self._user_config = config

        if exchange is not None:
            self.exchange = exchange
        else:
            if config is not None:
                ccxt_config = config
            else:
                ccxt_config = Config(env=env).get_public_config()
            print("ccxt最终配置:", ccxt_config)  # 便于调试
            self.exchange = ccxt.binance(ccxt_config)

    def set_config(self, config: dict):
        """
        运行时切换ccxt配置
        """
        print("切换ccxt配置:", config)
        self.exchange = ccxt.binance(config)

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
        将K线数据转换为pandas DataFrame，并统一为东八区（北京时间）
        """
        df = pd.DataFrame(ohlcv, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        # 统一index为东八区
        if df.index.tz is None or df.index.tz is pd.NaT:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('Asia/Shanghai')
        df = df.astype(float)
        return df 