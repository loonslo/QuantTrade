"""
量化交易系统 - 布林带突破策略
========================================

策略说明：

    布林带突破策略
    当价格突破上轨时买入，跌破下轨时卖出
    
    策略原理：
    - 价格 > 上轨：突破上涨，买入信号
    - 价格 < 下轨：突破下跌，卖出信号
    - 适合波动较大的市场
    

作者：量化交易团队
版本：1.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy
from ..position_utils import get_position_mixin

class BollingerBreakoutStrategy(BaseCryptoStrategy):
    """
    布林带突破策略
    当价格突破上轨时买入，跌破下轨时卖出
    
    策略原理：
    - 价格 > 上轨：突破上涨，买入信号
    - 价格 < 下轨：突破下跌，卖出信号
    - 适合波动较大的市场
    """
    
    params = (
        ('min_qty', 0.00001),
        ('precision', 5),
        ('period', 20),         # 布林带周期
        ('devfactor', 2),       # 标准差倍数
        ('position_type', 'all_in'),
        ('position_params', {}),
    )
    
    def __init__(self, **kwargs):
        """初始化布林带策略"""
        # 过滤掉bt.Strategy不认识的参数
        bt_params = {}
        for key, value in kwargs.items():
            if hasattr(self.p, key) or key in ['min_qty', 'precision', 'period', 'devfactor', 'position_type', 'position_params']:
                bt_params[key] = value
        
        # 调用父类初始化
        super().__init__()
        
        position_mixin = get_position_mixin(self.p.position_type, **self.p.position_params)
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position
        
        # 创建布林带指标
        self.bbands = bt.indicators.BollingerBands(self.datas[0], period=self.p.period, devfactor=self.p.devfactor)
    
    def predict_next_signal(self):
        """预测下一个信号"""
        current_price = self.data.close[0]
        upper_band = self.bbands.lines.top[0]
        lower_band = self.bbands.lines.bot[0]
        
        if not self.position:
            # 预测买入信号（突破上轨）
            if current_price > upper_band:
                return '买入', current_price
            else:
                return '买入', upper_band
        else:
            # 预测卖出信号（跌破下轨）
            if current_price < lower_band:
                return '卖出', current_price
            else:
                return '卖出', lower_band
    
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
        
        # 交易逻辑：突破上轨买入，跌破下轨卖出
        if not self.position and price > self.bbands.lines.top[0]:
            self.print_signal(dt, '买入', price)
            size = self.get_buy_size(cash, price, commission)
            if size <= 0:
                from utils.core.logger_manager import get_logger
                logger = get_logger('strategy')
                logger.warning(f"{dt} 下单数量无效: {size}")
            else:
                self.print_order(dt, '买入', size, price, cash)
                self.buy(size=size)
        elif self.position and price < self.bbands.lines.bot[0]:
            self.print_signal(dt, '卖出', price)
            self.print_order(dt, '卖出', self.position.size, price, cash, self.position.size)
            self.close()
            self.reset_position()
        
        self.print_status(dt, self.position.size, cash, total_value)


# 动量策略

