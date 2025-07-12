import ccxt
import pandas as pd
import asyncio
import websockets
import json
from typing import List
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
            self.exchange = ccxt.binance(config.get_binance_config())
        else:
            self.exchange = exchange
        self.ws_url = 'wss://ws-api.binance.com:443/ws-api/v3'

    async def fetch_ohlcv_ws(self, symbol: str, interval: str = '1h', limit: int = 500) -> List[list]:
        """
        通过币安WebSocket API获取K线数据
        """
        # 币安WebSocket symbol格式如BTCUSDT
        symbol_ws = symbol.replace('/', '').upper()
        req = {
            "id": 1,
            "method": "klines",
            "params": {
                "symbol": symbol_ws,
                "interval": interval,
                "limit": limit
            }
        }
        async with websockets.connect(self.ws_url) as ws:
            await ws.send(json.dumps(req))
            resp = await ws.recv()
            data = json.loads(resp)
            if 'result' in data:
                return data['result']
            else:
                raise Exception(f"WebSocket获取K线失败: {data}")

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 500):
        """
        获取币安K线数据，优先用WebSocket，失败则用ccxt REST
        """
        try:
            return asyncio.get_event_loop().run_until_complete(
                self.fetch_ohlcv_ws(symbol, timeframe, limit)
            )
        except Exception as e:
            print(f"WebSocket获取失败，降级为REST: {e}")
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