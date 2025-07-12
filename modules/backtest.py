import pandas as pd

class Backtester:
    def __init__(self, strategy_func):
        self.strategy_func = strategy_func

    def run(self, df: pd.DataFrame):
        """
        执行回测
        """
        pass

    def stats(self):
        """
        统计回测结果
        """
        pass 