"""
量化交易系统 - 均值回归策略
========================================

策略说明：

    均值回归策略
    当价格偏离均值过多时反向操作
    
    策略原理：
    - 价格 < 均值 - 阈值：超跌，买入信号
    - 价格 > 均值 + 阈值：超涨，卖出信号
    - 适合震荡市场，不适合单边趋势
    

作者：量化交易团队
版本：1.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy
from ..position_utils import get_position_mixin

class MeanReversionStrategy(BaseCryptoStrategy):
    """
    均值回归策略
    当价格偏离均值过多时反向操作
    
    策略原理：
    - 价格 < 均值 - 阈值：超跌，买入信号
    - 价格 > 均值 + 阈值：超涨，卖出信号
    - 适合震荡市场，不适合单边趋势
    """
    
    params = (
        ('min_qty', 0.00001),
        ('precision', 5),
        ('window', 100),        # 均值计算窗口
        ('threshold', 1.5),     # 偏离阈值（标准差倍数）
        ('position_type', 'all_in'),
        ('position_params', {}),
    )
    
    def __init__(self, **kwargs):
        """初始化均值回归策略"""
        # 过滤掉bt.Strategy不认识的参数
        bt_params = {}
        for key, value in kwargs.items():
            if hasattr(self.p, key) or key in ['min_qty', 'precision', 'period', 'threshold', 'position_type', 'position_params']:
                bt_params[key] = value
        
        # 调用父类初始化
        super().__init__()
        
        position_mixin = get_position_mixin(self.p.position_type, **self.p.position_params)
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position
        
        # 创建均值和标准差指标
        self.ma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.p.window)
        self.std = bt.indicators.StandardDeviation(self.datas[0], period=self.p.window)
    
    def predict_next_signal(self):
        """预测下一个信号"""
        current_price = self.data.close[0]
        ma_value = self.ma[0]
        std_value = self.std[0]
        zscore = (current_price - ma_value) / std_value if std_value > 0 else 0
        
        if not self.position:
            # 预测买入信号（价格低于均值）
            if zscore < -self.p.threshold:
                return '买入', current_price
            else:
                # 计算触发买入的价格
                trigger_price = ma_value - self.p.threshold * std_value
                return '买入', trigger_price
        else:
            # 预测卖出信号（价格高于均值）
            if zscore > self.p.threshold:
                return '卖出', current_price
            else:
                # 计算触发卖出的价格
                trigger_price = ma_value + self.p.threshold * std_value
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
        
        # 计算Z分数
        zscore = (price - self.ma[0]) / self.std[0] if self.std[0] > 0 else 0
        
        # 交易逻辑：超跌买入，超买卖出
        if not self.position and zscore < -self.p.threshold:
            self.print_signal(dt, '买入', price)
            size = self.get_buy_size(cash, price, commission)
            if size <= 0:
                from utils.core.logger_manager import get_logger
                logger = get_logger('strategy')
                logger.warning(f"{dt} 下单数量无效: {size}")
            else:
                self.print_order(dt, '买入', size, price, cash)
                self.buy(size=size)
        elif self.position and zscore > self.p.threshold:
            self.print_signal(dt, '卖出', price)
            self.print_order(dt, '卖出', self.position.size, price, cash, self.position.size)
            self.close()
            self.reset_position()
        
        self.print_status(dt, self.position.size, cash, total_value)


# 突破策略

