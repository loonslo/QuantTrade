"""
量化交易系统 - 动量策略
========================================

策略说明：

    动量策略
    当价格动量超过阈值时买入，低于负阈值时卖出
    
    策略原理：
    - 价格动量 > 阈值：上涨趋势，买入信号
    - 价格动量 < -阈值：下跌趋势，卖出信号
    - 适合趋势明显的市场
    

作者：量化交易团队
版本：1.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy
from ..position_utils import get_position_mixin

class MomentumStrategy(BaseCryptoStrategy):
    """
    动量策略
    当价格动量超过阈值时买入，低于负阈值时卖出
    
    策略原理：
    - 价格动量 > 阈值：上涨趋势，买入信号
    - 价格动量 < -阈值：下跌趋势，卖出信号
    - 适合趋势明显的市场
    """
    
    params = (
        ('min_qty', 0.00001),
        ('precision', 5),
        ('window', 10),         # 动量计算窗口
        ('threshold', 0.025),   # 动量阈值
        ('position_type', 'all_in'),
        ('position_params', {}),
    )
    
    def __init__(self, **kwargs):
        """初始化动量策略"""
        # 过滤掉bt.Strategy不认识的参数
        bt_params = {}
        for key, value in kwargs.items():
            if hasattr(self.p, key) or key in ['min_qty', 'precision', 'window', 'threshold', 'position_type', 'position_params']:
                bt_params[key] = value
        
        # 调用父类初始化
        super().__init__()
        
        position_mixin = get_position_mixin(self.p.position_type, **self.p.position_params)
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position
        
        # 创建动量指标
        self.momentum = bt.indicators.MomentumOscillator(self.datas[0], period=self.p.window)
        self.pct_change = bt.indicators.PercentChange(self.datas[0].close, period=self.p.window)
    
    def predict_next_signal(self):
        """预测下一个信号"""
        current_price = self.data.close[0]
        pct_change = self.pct_change[0]
        
        if not self.position:
            # 预测买入信号
            if pct_change > self.p.threshold:
                return '买入', current_price
            else:
                # 计算触发买入的价格
                trigger_price = current_price * (1 + self.p.threshold)
                return '买入', trigger_price
        else:
            # 预测卖出信号
            if pct_change < -self.p.threshold:
                return '卖出', current_price
            else:
                # 计算触发卖出的价格
                trigger_price = current_price * (1 - self.p.threshold)
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
        
        # 交易逻辑：动量超过阈值买入，低于负阈值卖出
        if not self.position and self.pct_change[0] > self.p.threshold:
            self.print_signal(dt, '买入', price)
            size = self.get_buy_size(cash, price, commission)
            if size <= 0:
                from utils.core.logger_manager import get_logger
                logger = get_logger('strategy')
                logger.warning(f"{dt} 下单数量无效: {size}")
            else:
                self.print_order(dt, '买入', size, price, cash)
                self.buy(size=size)
        elif self.position and self.pct_change[0] < -self.p.threshold:
            self.print_signal(dt, '卖出', price)
            self.print_order(dt, '卖出', self.position.size, price, cash, self.position.size)
            self.close()
            self.reset_position()
        
        self.print_status(dt, self.position.size, cash, total_value)


# 均值回归策略

