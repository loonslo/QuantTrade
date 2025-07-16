import pandas as pd

class Strategy:
    @staticmethod
    def ma_cross(df: pd.DataFrame, short_window=5, long_window=20):
        """
        简单均线交叉策略，只在交叉点给信号
        """
        # 计算移动平均线
        df['sma_short'] = df['close'].rolling(window=short_window).mean()
        df['sma_long'] = df['close'].rolling(window=long_window).mean()
        prev_short = df['sma_short'].shift(1)
        prev_long = df['sma_long'].shift(1)
        # 只在交叉点给信号
        signals = pd.Series(0, index=df.index)
        signals[(prev_short <= prev_long) & (df['sma_short'] > df['sma_long'])] = 1   # 金叉买入
        signals[(prev_short >= prev_long) & (df['sma_short'] < df['sma_long'])] = -1  # 死叉卖出
        return signals

    @staticmethod
    def rsi_signal(df: pd.DataFrame, period=14, overbought=70, oversold=30):
        """
        RSI超买超卖策略
        """
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 生成信号
        signals = pd.Series(0, index=df.index)
        signals[df['rsi'] < oversold] = 1   # 超卖买入
        signals[df['rsi'] > overbought] = -1  # 超买卖出
        
        return signals 