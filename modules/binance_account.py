import ccxt

class BinanceAccount:
    """
    封装Binance账户的实盘操作，包括余额查询、买入、卖出、查询挂单、撤单等。
    用法示例：
        from config import Config
        config = Config()
        binance_config = config.get_binance_config()
        account = BinanceAccount(binance_config)
        usdt_balance = account.get_balance('USDT')
    """
    def __init__(self, config):
        self.exchange = ccxt.binance(config)

    def get_balance(self, asset='USDT'):
        """查询指定资产余额"""
        balance = self.exchange.fetch_balance()
        return balance['total'].get(asset, 0)

    def buy(self, symbol, amount):
        """市价买入 amount 单位为币的数量"""
        order = self.exchange.create_market_buy_order(symbol, amount)
        return order

    def sell(self, symbol, amount):
        """市价卖出 amount 单位为币的数量"""
        order = self.exchange.create_market_sell_order(symbol, amount)
        return order

    def get_open_orders(self, symbol=None):
        """查询当前挂单"""
        return self.exchange.fetch_open_orders(symbol) if symbol else self.exchange.fetch_open_orders()

    def cancel_order(self, order_id, symbol):
        """撤销指定订单"""
        return self.exchange.cancel_order(order_id, symbol)

if __name__ == '__main__':
    from config import Config
    config = Config()
    binance_config = config.get_binance_config()
    account = BinanceAccount(binance_config)
    usdt_balance = account.get_balance('USDT')
    print(f'当前USDT余额: {usdt_balance}')
    # 你可以取消下面的注释测试买入/卖出（注意风险！）
    # print(account.buy('ETH/USDT', 0.001))
    # print(account.sell('ETH/USDT', 0.001))
    # eth_balance = account.get_balance('ETH')
    # print(f'当前ETH余额: {eth_balance}')
    # open_orders = account.get_open_orders('ETH/USDT')
    # print(f'当前ETH/USDT挂单: {open_orders}')
    