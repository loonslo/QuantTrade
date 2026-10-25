"""
量化交易系统 - 海龟交易策略
========================================

策略说明：

    海龟交易策略
    经典的趋势跟踪策略，突破入场，突破出场
    
    策略原理：
    - 价格 > 入场高点：趋势确认，买入信号
    - 价格 < 出场低点：趋势结束，卖出信号
    - 适合大趋势市场
    

作者：量化交易团队
版本：1.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy
from ..position_utils import get_position_mixin

class TurtleStrategy(BaseCryptoStrategy):
    """
    海龟交易策略
    经典的趋势跟踪策略，突破入场，突破出场
    
    策略原理：
    - 价格 > 入场高点：趋势确认，买入信号
    - 价格 < 出场低点：趋势结束，卖出信号
    - 适合大趋势市场
    """
    
    params = (
        ('min_qty', 0.00001),
        ('precision', 5),
        ('entry_window', 18),   # 入场窗口
        ('exit_window', 12),    # 出场窗口
        ('position_type', 'all_in'),
        ('position_params', {}),
    )
    
    def __init__(self, **kwargs):
        """初始化海龟策略"""
        # 过滤掉bt.Strategy不认识的参数
        bt_params = {}
        for key, value in kwargs.items():
            if hasattr(self.p, key) or key in ['min_qty', 'precision', 'entry_window', 'exit_window', 'position_type', 'position_params']:
                bt_params[key] = value
        
        # 调用父类初始化
        super().__init__()
        
        position_mixin = get_position_mixin(self.p.position_type, **self.p.position_params)
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position
        
        # 创建海龟交易指标
        self.entry_high = bt.indicators.Highest(self.datas[0], period=self.p.entry_window)
        self.exit_low = bt.indicators.Lowest(self.datas[0], period=self.p.exit_window)
    
    def predict_next_signal(self):
        """预测下一个信号"""
        current_price = self.data.close[0]
        entry_high = self.entry_high[0]
        exit_low = self.exit_low[0]
        
        if not self.position:
            # 预测买入信号（突破入场高点）
            if current_price > entry_high:
                return '买入', current_price
            else:
                return '买入', entry_high
        else:
            # 预测卖出信号（跌破出场低点）
            if current_price < exit_low:
                return '卖出', current_price
            else:
                return '卖出', exit_low
    
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
        
        # 交易逻辑：突破入场高点买入，跌破出场低点卖出
        if not self.position and price > self.entry_high[0] and self.data.close[-1] <= self.entry_high[-1]:
            self.print_signal(dt, '买入', price)
            size = self.get_buy_size(cash, price, commission)
            if size <= 0:
                from utils.core.logger_manager import get_logger
                logger = get_logger('strategy')
                logger.warning(f"{dt} 下单数量无效: {size}")
            else:
                self.print_order(dt, '买入', size, price, cash)
                self.buy(size=size)
        elif self.position and price < self.exit_low[0] and self.data.close[-1] >= self.exit_low[-1]:
            self.print_signal(dt, '卖出', price)
            self.print_order(dt, '卖出', self.position.size, price, cash, self.position.size)
            self.close()
            self.reset_position()
        
        self.print_status(dt, self.position.size, cash, total_value)


# KDJ信号策略

