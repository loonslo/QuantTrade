# coding=utf-8



import ccxt
print (ccxt.exchanges)

# # 创建币安交易所对象，verbose=True会输出详细请求日志，便于调试
# binance = ccxt.binance({
#     'apiKey': 'yBRGbWLRGxPfxTE4BxQO8LPzZ7GISRgrlhkJdNg95FIqjDf7Is0p3EHP6hZkUFQC',
#     'secret': 'fnocUgpR443EliLmjV3lTIgU0Sb3UNERprE2GZQJR8kK6gWzDKxWbyAWTt592TPl',
#     'verbose': True
# })
#
# # 加载币安的所有交易对市场信息
# binance_markets = binance.load_markets()
#
# # 打印币安的ID和市场信息
# print(binance.id, binance_markets)
