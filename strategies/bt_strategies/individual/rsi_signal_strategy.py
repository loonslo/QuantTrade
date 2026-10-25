"""
量化交易系统 - RSI信号策略
========================================

策略说明：

    RSI超买超卖策略
    当RSI低于超卖线时买入，高于超买线时卖出
    
    策略原理：
    - RSI < 30：超卖区域，买入信号
    - RSI > 70：超买区域，卖出信号
    - 适合震荡市场，不适合单边趋势
    

作者：量化交易团队
版本：1.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy
from ..position_utils import get_position_mixin

class RsiSignalStrategy(BaseCryptoStrategy):
    """
    RSI超买超卖策略
    当RSI低于超卖线时买入，高于超买线时卖出
    
    策略原理：
    - RSI < 30：超卖区域，买入信号
    - RSI > 70：超买区域，卖出信号
    - 适合震荡市场，不适合单边趋势
    """
    
    params = (
        ('min_qty', 0.00001),
        ('precision', 5),
        ('period', 14),         # RSI计算周期
        ('overbought', 70),     # 超买线
        ('oversold', 30),       # 超卖线
        ('position_type', 'all_in'),
        ('position_params', {}),
    )
    
    def __init__(self, **kwargs):
        """初始化RSI策略"""
        # 过滤掉bt.Strategy不认识的参数
        bt_params = {}
        for key, value in kwargs.items():
            if hasattr(self.p, key) or key in ['min_qty', 'precision', 'period', 'oversold', 'overbought', 'position_type', 'position_params']:
                bt_params[key] = value
        
        # 调用父类初始化
        super().__init__()
        
        position_mixin = get_position_mixin(self.p.position_type, **self.p.position_params)
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position
        
        # 创建RSI指标
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.p.period, safediv=True)
    
    def predict_next_signal(self):
        """预测下一个信号"""
        current_price = self.data.close[0]
        rsi_value = self.rsi[0]
        
        if not self.position:
            # 预测买入信号
            if rsi_value < self.p.oversold:
                return '买入', current_price
            else:
                # 计算触发买入的价格（RSI超卖）
                trigger_price = current_price * 0.95  # 简单估算
                return '买入', trigger_price
        else:
            # 预测卖出信号
            if rsi_value > self.p.overbought:
                return '卖出', current_price
            else:
                # 计算触发卖出的价格（RSI超买）
                trigger_price = current_price * 1.05  # 简单估算
                return '卖出', trigger_price
    
    def next(self):
        """策略主逻辑"""
        cash = self.broker.getcash()
        price = self.data.close[0]
        commission = self.broker.getcommissioninfo(self.datas[0]).p.commission
        dt = self.datas[0].datetime.datetime(0)
        total_value = self.position.size * price + cash
        
        # 预测下一个信号
        signal_type, trigger_price = self.predict_next_signal()
        if signal_type:
            self.print_prediction(dt, signal_type, trigger_price, price)
        
        # 交易逻辑：RSI超卖买入，超买卖出
        if not self.position and self.rsi[0] < self.p.oversold:
            self.print_signal(dt, '买入', price)
            size = self.get_buy_size(cash, price, commission)
            if size <= 0:
                from utils.core.logger_manager import get_logger
                logger = get_logger('strategy')
                logger.warning(f"{dt} 下单数量无效: {size}")
            else:
                self.print_order(dt, '买入', size, price, cash)
                self.buy(size=size)
        elif self.position and self.rsi[0] > self.p.overbought:
            self.print_signal(dt, '卖出', price)
            self.print_order(dt, '卖出', self.position.size, price, cash, self.position.size)
            self.close()
            self.reset_position()
        
        self.print_status(dt, self.position.size, cash, total_value)


# 布林带突破策略

