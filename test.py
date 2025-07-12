# coding=utf-8

import ccxt
from config import Config

# 创建配置实例
config = Config(env='development')  # 可选: 'development', 'test', 'production'

# 创建币安交易所对象，使用配置文件
binance = ccxt.binance(config.get_public_config())

# balance = binance.fetch_balance()
# print(balance)

# # 加载币安的所有交易对市场信息
# binance_markets = binance.load_markets()
#
# # 打印币安的ID和市场信息
# print(binance.id, binance_markets)
#
symbol = 'BTCUSDT'
while True:
    ticker_data = binance.fapipublic_get_ticker_price({'symbol': symbol})
    print(ticker_data)

