import pandas as pd

class Strategy:
    
    
    @staticmethod
    def predict_next_signals(df: pd.DataFrame, strategy_name: str, **kwargs):
        """
        预测下一个买入/卖出信号的触发价格
        :param df: 市场数据
        :param strategy_name: 策略名称
        :param kwargs: 策略参数
        :return: 预测的下一个信号价格
        """
        if strategy_name == 'ma_cross':
            return Strategy._predict_ma_cross_signals(df, **kwargs)
        elif strategy_name == 'rsi_signal':
            return Strategy._predict_rsi_signals(df, **kwargs)
        elif strategy_name == 'bollinger_breakout':
            return Strategy._predict_bollinger_signals(df, **kwargs)
        elif strategy_name == 'macd_cross':
            return Strategy._predict_macd_signals(df, **kwargs)
        elif strategy_name == 'momentum':
            return Strategy._predict_momentum_signals(df, **kwargs)
        elif strategy_name == 'mean_reversion':
            return Strategy._predict_mean_reversion_signals(df, **kwargs)
        elif strategy_name == 'breakout':
            return Strategy._predict_breakout_signals(df, **kwargs)
        elif strategy_name == 'turtle':
            return Strategy._predict_turtle_signals(df, **kwargs)
        elif strategy_name == 'kdj_signal':
            return Strategy._predict_kdj_signals(df, **kwargs)
        elif strategy_name == 'kama_cross':
            return Strategy._predict_kama_signals(df, **kwargs)
        else:
            return {'next_buy': None, 'next_sell': None, 'message': f'策略 {strategy_name} 暂不支持预测'}

    
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

    @staticmethod
    def bollinger_breakout(df: pd.DataFrame, window=20, num_std=2):
        """
        布林带突破策略：价格上穿上轨买入，下穿下轨卖出
        """
        df['ma'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        df['upper'] = df['ma'] + num_std * df['std']
        df['lower'] = df['ma'] - num_std * df['std']
        signals = pd.Series(0, index=df.index)
        signals[(df['close'].shift(1) <= df['upper'].shift(1)) & (df['close'] > df['upper'])] = 1  # 上穿上轨买入
        signals[(df['close'].shift(1) >= df['lower'].shift(1)) & (df['close'] < df['lower'])] = -1 # 下穿下轨卖出
        return signals

    @staticmethod
    def macd_cross(df: pd.DataFrame, fast=12, slow=26, signal=9):
        """
        MACD金叉死叉策略
        """
        df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
        df['macd'] = df['ema_fast'] - df['ema_slow']
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        prev_macd = df['macd'].shift(1)
        prev_signal = df['macd_signal'].shift(1)
        signals = pd.Series(0, index=df.index)
        signals[(prev_macd <= prev_signal) & (df['macd'] > df['macd_signal'])] = 1   # 金叉买入
        signals[(prev_macd >= prev_signal) & (df['macd'] < df['macd_signal'])] = -1  # 死叉卖出
        return signals

    @staticmethod
    def momentum(df: pd.DataFrame, window=10, threshold=0):
        """
        动量策略：收益率大于阈值买入，小于-阈值卖出
        """
        df['momentum'] = df['close'].pct_change(periods=window)
        signals = pd.Series(0, index=df.index)
        signals[df['momentum'] > threshold] = 1
        signals[df['momentum'] < -threshold] = -1
        return signals 

    @staticmethod
    def mean_reversion(df: pd.DataFrame, window=20, threshold=1.5):
        """
        均值回归策略：价格偏离均值一定倍数时反向操作
        """
        df['ma'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        zscore = (df['close'] - df['ma']) / df['std']
        signals = pd.Series(0, index=df.index)
        signals[zscore > threshold] = -1  # 高于均值上阈值，做空
        signals[zscore < -threshold] = 1  # 低于均值下阈值，做多
        return signals

    @staticmethod
    def breakout(df: pd.DataFrame, window=20):
        """
        突破策略：价格突破N日高点买入，跌破N日低点卖出
        """
        df['high_max'] = df['high'].rolling(window=window).max()
        df['low_min'] = df['low'].rolling(window=window).min()
        signals = pd.Series(0, index=df.index)
        signals[(df['close'].shift(1) <= df['high_max'].shift(1)) & (df['close'] > df['high_max'])] = 1  # 突破新高买入
        signals[(df['close'].shift(1) >= df['low_min'].shift(1)) & (df['close'] < df['low_min'])] = -1   # 跌破新低卖出
        return signals

    @staticmethod
    def turtle(df: pd.DataFrame, entry_window=18, exit_window=12):
        """
        海龟交易法则：突破N日高点买入，跌破M日低点卖出
        """
        df['entry_high'] = df['high'].rolling(window=entry_window).max()
        df['exit_low'] = df['low'].rolling(window=exit_window).min()
        signals = pd.Series(0, index=df.index)
        signals[(df['close'].shift(1) <= df['entry_high'].shift(1)) & (df['close'] > df['entry_high'])] = 1  # 突破入场
        signals[(df['close'].shift(1) >= df['exit_low'].shift(1)) & (df['close'] < df['exit_low'])] = -1     # 跌破止损
        return signals

    @staticmethod
    def kdj_signal(df: pd.DataFrame, n=9, k_period=3, d_period=3):
        """
        KDJ策略：K线上穿D线买入，下穿D线卖出
        """
        low_min = df['low'].rolling(window=n).min()
        high_max = df['high'].rolling(window=n).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        df['K'] = rsv.ewm(com=k_period-1, adjust=False).mean()
        df['D'] = df['K'].ewm(com=d_period-1, adjust=False).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        prev_k = df['K'].shift(1)
        prev_d = df['D'].shift(1)
        signals = pd.Series(0, index=df.index)
        signals[(prev_k <= prev_d) & (df['K'] > df['D'])] = 1   # K线上穿D线买入
        signals[(prev_k >= prev_d) & (df['K'] < df['D'])] = -1  # K线下穿D线卖出
        return signals 

    @staticmethod
    def kama_cross(df: pd.DataFrame, fast=2, slow=30, window=10):
        """
        KAMA自适应均线交叉策略
        """
        change = abs(df['close'] - df['close'].shift(window))
        volatility = df['close'].diff().abs().rolling(window=window).sum()
        er = change / volatility
        sc = (er * (2/(fast+1) - 2/(slow+1)) + 2/(slow+1)) ** 2
        kama = [df['close'].iloc[0]]
        for i in range(1, len(df)):
            kama.append(kama[-1] + sc.iloc[i] * (df['close'].iloc[i] - kama[-1]))
        df['kama'] = kama
        df['ma'] = df['close'].rolling(window=window).mean()
        signals = pd.Series(0, index=df.index)
        signals[(df['kama'].shift(1) <= df['ma'].shift(1)) & (df['kama'] > df['ma'])] = 1
        signals[(df['kama'].shift(1) >= df['ma'].shift(1)) & (df['kama'] < df['ma'])] = -1
        return signals 

    @staticmethod
    def _predict_ma_cross_signals(df, short_window=5, long_window=20):
        """预测均线交叉信号"""
        current_price = df['close'].iloc[-1]
        sma_short = df['close'].rolling(window=short_window).mean().iloc[-1]
        sma_long = df['close'].rolling(window=long_window).mean().iloc[-1]
        
        if sma_short < sma_long:
            # 预测金叉：短均线需要上穿长均线
            # 简化计算：假设价格需要上涨到使短均线等于长均线
            buy_price = current_price * (sma_long / sma_short) if sma_short > 0 else None
            return {'next_buy': buy_price, 'next_sell': None}
        else:
            # 预测死叉：短均线需要下穿长均线
            sell_price = current_price * (sma_long / sma_short) if sma_short > 0 else None
            return {'next_buy': None, 'next_sell': sell_price}

    @staticmethod
    def _predict_rsi_signals(df, period=14, overbought=70, oversold=30):
        """预测RSI信号"""
        # 计算当前RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean().iloc[-1]
        rs = gain / loss if loss > 0 else 0
        current_rsi = 100 - (100 / (1 + rs))
        
        if current_rsi > overbought:
            # 当前超买，预测卖出价格（RSI需要回到超买线以下）
            return {'next_buy': None, 'next_sell': df['close'].iloc[-1] * 0.95}  # 简化：假设下跌5%
        elif current_rsi < oversold:
            # 当前超卖，预测买入价格（RSI需要回到超卖线以上）
            return {'next_buy': df['close'].iloc[-1] * 1.05, 'next_sell': None}  # 简化：假设上涨5%
        else:
            return {'next_buy': None, 'next_sell': None}

    @staticmethod
    def _predict_bollinger_signals(df, window=20, num_std=2):
        """预测布林带突破信号"""
        current_price = df['close'].iloc[-1]
        ma = df['close'].rolling(window=window).mean().iloc[-1]
        std = df['close'].rolling(window=window).std().iloc[-1]
        upper = ma + num_std * std
        lower = ma - num_std * std
        
        if current_price < upper:
            # 预测上穿上轨买入
            return {'next_buy': upper, 'next_sell': None}
        else:
            # 预测下穿下轨卖出
            return {'next_buy': None, 'next_sell': lower}

    @staticmethod
    def _predict_macd_signals(df, fast=12, slow=26, signal=9):
        """预测MACD交叉信号"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean().iloc[-1]
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean().iloc[-1]
        macd = ema_fast - ema_slow
        macd_signal = df['close'].ewm(span=signal, adjust=False).mean().iloc[-1]  # 简化计算
        
        if macd < macd_signal:
            # 预测金叉
            return {'next_buy': df['close'].iloc[-1] * 1.02, 'next_sell': None}  # 简化：假设上涨2%
        else:
            # 预测死叉
            return {'next_buy': None, 'next_sell': df['close'].iloc[-1] * 0.98}  # 简化：假设下跌2%}

    @staticmethod
    def _predict_momentum_signals(df, window=10, threshold=0):
        """预测动量信号"""
        current_momentum = df['close'].pct_change(periods=window).iloc[-1]
        
        if current_momentum < threshold:
            # 预测买入（动量需要超过阈值）
            return {'next_buy': df['close'].iloc[-1] * (1 + threshold), 'next_sell': None}
        else:
            # 预测卖出（动量需要低于-阈值）
            return {'next_buy': None, 'next_sell': df['close'].iloc[-1] * (1 - threshold)}

    @staticmethod
    def _predict_mean_reversion_signals(df, window=20, threshold=1.5):
        """预测均值回归信号"""
        current_price = df['close'].iloc[-1]
        ma = df['close'].rolling(window=window).mean().iloc[-1]
        std = df['close'].rolling(window=window).std().iloc[-1]
        zscore = (current_price - ma) / std if std > 0 else 0
        
        if zscore > threshold:
            # 当前高于均值，预测做空
            return {'next_buy': None, 'next_sell': ma}
        elif zscore < -threshold:
            # 当前低于均值，预测做多
            return {'next_buy': ma, 'next_sell': None}
        else:
            return {'next_buy': None, 'next_sell': None}

    @staticmethod
    def _predict_breakout_signals(df, window=20):
        """预测突破信号"""
        current_price = df['close'].iloc[-1]
        high_max = df['high'].rolling(window=window).max().iloc[-1]
        low_min = df['low'].rolling(window=window).min().iloc[-1]
        
        if current_price < high_max:
            # 预测突破新高买入
            return {'next_buy': high_max, 'next_sell': None}
        else:
            # 预测跌破新低卖出
            return {'next_buy': None, 'next_sell': low_min}

    @staticmethod
    def _predict_turtle_signals(df, entry_window=18, exit_window=12):
        """预测海龟信号"""
        current_price = df['close'].iloc[-1]
        entry_high = df['high'].rolling(window=entry_window).max().iloc[-1]
        exit_low = df['low'].rolling(window=exit_window).min().iloc[-1]
        
        if current_price < entry_high:
            # 预测突破入场
            return {'next_buy': entry_high, 'next_sell': None}
        else:
            # 预测跌破止损
            return {'next_buy': None, 'next_sell': exit_low}

    @staticmethod
    def _predict_kdj_signals(df, n=9, k_period=3, d_period=3):
        """预测KDJ信号"""
        # 计算当前K、D值
        low_min = df['low'].rolling(window=n).min().iloc[-1]
        high_max = df['high'].rolling(window=n).max().iloc[-1]
        rsv = (df['close'].iloc[-1] - low_min) / (high_max - low_min) * 100 if (high_max - low_min) > 0 else 50
        k = rsv  # 简化计算
        d = rsv  # 简化计算
        
        if k < d:
            # 预测K线上穿D线买入
            return {'next_buy': df['close'].iloc[-1] * 1.01, 'next_sell': None}  # 简化：假设上涨1%
        else:
            # 预测K线下穿D线卖出
            return {'next_buy': None, 'next_sell': df['close'].iloc[-1] * 0.99}  # 简化：假设下跌1%}

    @staticmethod
    def _predict_kama_signals(df, fast=2, slow=30, window=10):
        """预测KAMA交叉信号"""
        # 简化计算：假设KAMA接近当前价格
        current_price = df['close'].iloc[-1]
        ma = df['close'].rolling(window=window).mean().iloc[-1]
        
        if current_price < ma:
            # 预测KAMA上穿MA买入
            return {'next_buy': ma, 'next_sell': None}
        else:
            # 预测KAMA下穿MA卖出
            return {'next_buy': None, 'next_sell': ma} 