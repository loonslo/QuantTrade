import pandas as pd

class Strategy:
    @staticmethod
    def ma_cross(df: pd.DataFrame, short_window=5, long_window=20):
        """
        简单均线交叉策略
        """
        pass

    @staticmethod
    def rsi_signal(df: pd.DataFrame, period=14, overbought=70, oversold=30):
        """
        RSI超买超卖策略
        """
        pass 