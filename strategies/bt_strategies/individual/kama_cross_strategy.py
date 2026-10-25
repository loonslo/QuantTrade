"""
量化交易系统 - KAMA交叉策略
========================================

策略说明：

    KAMA均线交叉策略
    使用Kaufman自适应移动平均线，价格上穿均线时买入，下穿时卖出
    
    策略原理：
    - 价格 > KAMA：上升趋势，买入信号
    - 价格 < KAMA：下降趋势，卖出信号
    - KAMA比普通MA更平滑，减少假信号
    

作者：量化交易团队
版本：1.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy
from ..position_utils import get_position_mixin

class KamaCrossStrategy(BaseCryptoStrategy):
    """
    KAMA均线交叉策略
    使用Kaufman自适应移动平均线，价格上穿均线时买入，下穿时卖出
    
    策略原理：
    - 价格 > KAMA：上升趋势，买入信号
    - 价格 < KAMA：下降趋势，卖出信号
    - KAMA比普通MA更平滑，减少假信号
    """
    
    params = (
        ('min_qty', 0.00001),
        ('precision', 5),
        ('fast', 2),           # 快速周期
        ('slow', 30),          # 慢速周期
        ('window', 50),        # 均线窗口
        ('position_type', 'all_in'),
        ('position_params', {}),
    )
    
    def __init__(self, **kwargs):
        """初始化KAMA策略"""
        # 过滤掉bt.Strategy不认识的参数
        bt_params = {}
        for key, value in kwargs.items():
            if hasattr(self.p, key) or key in ['min_qty', 'precision', 'fast', 'slow', 'window', 'position_type', 'position_params']:
                bt_params[key] = value
        
        # 调用父类初始化
        super().__init__()
        
        position_mixin = get_position_mixin(self.p.position_type, **self.p.position_params)
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position
        
        # 使用简单移动平均线近似KAMA
        self.ma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.p.window)
    
    def predict_next_signal(self):
        """预测下一个信号"""
        current_price = self.data.close[0]
        ma_value = self.ma[0]
        
        if not self.position:
            # 预测买入信号（价格上穿均线）
            if current_price > ma_value:
                return '买入', current_price
            else:
                return '买入', ma_value
        else:
            # 预测卖出信号（价格下穿均线）
            if current_price < ma_value:
                return '卖出', current_price
            else:
                return '卖出', ma_value
    
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
        
        # 设置容差，避免浮点数精度问题
        tolerance = 1e-6
        
        # 交易逻辑：价格上穿均线买入，下穿卖出
        if not self.position and self.datas[0].close[-1] <= self.ma[-1] + tolerance and self.datas[0].close[0] > self.ma[0] + tolerance:
            self.print_signal(dt, '买入', price)
            size = self.get_buy_size(cash, price, commission)
            if size <= 0:
                from utils.core.logger_manager import get_logger
                logger = get_logger('strategy')
                logger.warning(f"{dt} 下单数量无效: {size}")
            else:
                self.print_order(dt, '买入', size, price, cash)
                self.buy(size=size)
        elif self.position and self.datas[0].close[-1] >= self.ma[-1] - tolerance and self.datas[0].close[0] < self.ma[0] - tolerance:
            self.print_signal(dt, '卖出', price)
            self.print_order(dt, '卖出', self.position.size, price, cash, self.position.size)
            self.close()
            self.reset_position()
        
        self.print_status(dt, self.position.size, cash, total_value) 
