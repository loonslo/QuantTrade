"""
量化交易系统 - MACD交叉策略
========================================

策略说明：

    MACD交叉策略
    当MACD线上穿信号线时买入，下穿时卖出
    
    策略原理：
    - MACD线 > 信号线：上升趋势，买入信号
    - MACD线 < 信号线：下降趋势，卖出信号
    - MACD是趋势跟踪指标，适合中长期交易
    

作者：量化交易团队
版本：1.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy
from ..position_utils import get_position_mixin

class MacdCrossStrategy(BaseCryptoStrategy):
    """
    MACD交叉策略
    当MACD线上穿信号线时买入，下穿时卖出
    
    策略原理：
    - MACD线 > 信号线：上升趋势，买入信号
    - MACD线 < 信号线：下降趋势，卖出信号
    - MACD是趋势跟踪指标，适合中长期交易
    """
    
    params = (
        ('min_qty', 0.00001),
        ('precision', 5),
        ('fast', 12),           # 快线周期
        ('slow', 26),           # 慢线周期
        ('signal', 9),          # 信号线周期
        ('position_type', 'all_in'),
        ('position_params', {}),
    )
    
    def __init__(self, **kwargs):
        """初始化MACD策略"""
        # 过滤掉bt.Strategy不认识的参数
        bt_params = {}
        for key, value in kwargs.items():
            if hasattr(self.p, key) or key in ['min_qty', 'precision', 'fast', 'slow', 'signal', 'position_type', 'position_params']:
                bt_params[key] = value
        
        # 调用父类初始化
        super().__init__()
        
        position_mixin = get_position_mixin(self.p.position_type, **self.p.position_params)
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position
        
        # 创建MACD指标
        self.macd = bt.indicators.MACD(self.datas[0], period_me1=self.p.fast, period_me2=self.p.slow, period_signal=self.p.signal)
    
    def predict_next_signal(self):
        """预测下一个信号"""
        current_price = self.data.close[0]
        macd_line = self.macd.macd[0]
        signal_line = self.macd.signal[0]
        
        if not self.position:
            # 预测买入信号
            if macd_line > signal_line:
                return '买入', current_price
            else:
                # 计算触发买入的价格（MACD金叉）
                diff = signal_line - macd_line
                trigger_price = current_price * (1 + diff * 0.01)  # 简单估算
                return '买入', trigger_price
        else:
            # 预测卖出信号
            if macd_line < signal_line:
                return '卖出', current_price
            else:
                # 计算触发卖出的价格（MACD死叉）
                diff = macd_line - signal_line
                trigger_price = current_price * (1 - diff * 0.01)  # 简单估算
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
        
        # 交易逻辑：MACD金叉买入，死叉卖出
        if not self.position and self.macd.macd[0] > self.macd.signal[0] and self.macd.macd[-1] <= self.macd.signal[-1]:
            self.print_signal(dt, '买入', price)
            size = self.get_buy_size(cash, price, commission)
            if size <= 0:
                from utils.core.logger_manager import get_logger
                logger = get_logger('strategy')
                logger.warning(f"{dt} 下单数量无效: {size}")
            else:
                self.print_order(dt, '买入', size, price, cash)
                self.buy(size=size)
        elif self.position and self.macd.macd[0] < self.macd.signal[0] and self.macd.macd[-1] >= self.macd.signal[-1]:
            self.print_signal(dt, '卖出', price)
            self.print_order(dt, '卖出', self.position.size, price, cash, self.position.size)
            self.close()
            self.reset_position()
        
        self.print_status(dt, self.position.size, cash, total_value)


# RSI信号策略

