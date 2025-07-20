class PositionManager:
    def on_buy_signal(self, capital, position, price, commission):
        raise NotImplementedError
    def on_sell_signal(self, capital, position, price, commission):
        raise NotImplementedError
    def reset(self):
        pass

class TwoThreeFivePositionManager(PositionManager):
    """2-3-5仓位管理：最多三次加仓，分别用20%、30%、50%资金"""
    def __init__(self):
        self.ratios = [0.2, 0.3, 0.5]
        self.count = 0
    def on_buy_signal(self, capital, position, price, commission):
        if self.count < len(self.ratios):
            ratio = self.ratios[self.count]
            buy_capital = capital * ratio
            shares = buy_capital / (price * (1 + commission))
            cost = shares * price * (1 + commission)
            self.count += 1
            return shares, cost
        return 0, 0
    def on_sell_signal(self, capital, position, price, commission):
        # 卖出全部持仓
        revenue = position * price * (1 - commission)
        self.reset()
        return position, revenue
    def reset(self):
        self.count = 0

class FixedRatioPositionManager(PositionManager):
    """固定比例管理：每次买入/卖出固定比例"""
    def __init__(self, ratio=0.2):
        self.ratio = ratio
    def on_buy_signal(self, capital, position, price, commission):
        buy_capital = capital * self.ratio
        shares = buy_capital / (price * (1 + commission))
        cost = shares * price * (1 + commission)
        return shares, cost
    def on_sell_signal(self, capital, position, price, commission):
        sell_shares = position * self.ratio
        revenue = sell_shares * price * (1 - commission)
        return sell_shares, revenue
    def reset(self):
        pass

class PyramidAllPositionManager(PositionManager):
    """金字塔加仓+倒金字塔减仓：加仓比例递减，减仓比例递增，均可自定义，默认各5次"""
    def __init__(self, add_ratios=None, reduce_ratios=None):
        self.add_ratios = add_ratios or [0.3, 0.25, 0.2, 0.15, 0.1]
        self.reduce_ratios = reduce_ratios or [0.1, 0.15, 0.2, 0.25, 0.3]
        self.add_count = 0
        self.reduce_count = 0
    def on_buy_signal(self, capital, position, price, commission):
        if self.add_count < len(self.add_ratios):
            ratio = self.add_ratios[self.add_count]
            buy_capital = capital * ratio
            shares = buy_capital / (price * (1 + commission))
            cost = shares * price * (1 + commission)
            self.add_count += 1
            self.reduce_count = 0
            return shares, cost
        return 0, 0
    def on_sell_signal(self, capital, position, price, commission):
        if self.reduce_count < len(self.reduce_ratios):
            ratio = self.reduce_ratios[self.reduce_count]
            sell_shares = position * ratio
            revenue = sell_shares * price * (1 - commission)
            self.reduce_count += 1
            self.add_count = 0
            return sell_shares, revenue
        return 0, 0
    def reset(self):
        self.add_count = 0
        self.reduce_count = 0

class AllInPositionManager(PositionManager):
    """全仓管理：每次买入全部资金，卖出全部持仓"""
    def on_buy_signal(self, capital, position, price, commission):
        shares = capital / (price * (1 + commission))
        cost = shares * price * (1 + commission)
        return shares, cost
    def on_sell_signal(self, capital, position, price, commission):
        revenue = position * price * (1 - commission)
        return position, revenue
    def reset(self):
        pass 