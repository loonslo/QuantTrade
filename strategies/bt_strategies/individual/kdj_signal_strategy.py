"""
量化交易系统 - KDJ信号策略
========================================

策略说明：

    KDJ指标策略
    当K线上穿D线时买入，下穿时卖出
    
    策略原理：
    - K线 > D线：上升趋势，买入信号
    - K线 < D线：下降趋势，卖出信号
    - KDJ是震荡指标，适合震荡市场
    

作者：量化交易团队
版本：1.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy
from ..position_utils import get_position_mixin

class KdjSignalStrategy(BaseCryptoStrategy):
    """
    KDJ指标策略
    当K线上穿D线时买入，下穿时卖出
    
    策略原理：
    - K线 > D线：上升趋势，买入信号
    - K线 < D线：下降趋势，卖出信号
    - KDJ是震荡指标，适合震荡市场
    """
    
    params = (
        ('min_qty', 0.00001),
        ('precision', 5),
        ('n', 9),              # KDJ计算周期
        ('k_period', 3),       # K线平滑周期
        ('d_period', 3),       # D线平滑周期
        ('position_type', 'all_in'),
        ('position_params', {}),
    )
    
    def __init__(self, **kwargs):
        """初始化KDJ策略"""
        # 过滤掉bt.Strategy不认识的参数
        bt_params = {}
        for key, value in kwargs.items():
            if hasattr(self.p, key) or key in ['min_qty', 'precision', 'k_period', 'd_period', 'j_period', 'position_type', 'position_params']:
                bt_params[key] = value
        
        # 调用父类初始化
        super().__init__()
        
        position_mixin = get_position_mixin(self.p.position_type, **self.p.position_params)
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position
        
        # 创建KDJ指标（使用Stochastic作为近似）
        self.stoch = bt.indicators.Stochastic(self.datas[0], period=self.p.k_period, safediv=True)
    
    def predict_next_signal(self):
        """预测下一个信号"""
        current_price = self.data.close[0]
        k_value = self.stoch.percK[0]
        d_value = self.stoch.percD[0]
        
        if not self.position:
            # 预测买入信号（K线上穿D线）
            if k_value > d_value:
                return '买入', current_price
            else:
                # 计算触发买入的价格
                trigger_price = current_price * 0.98  # 简单估算
                return '买入', trigger_price
        else:
            # 预测卖出信号（K线下穿D线）
            if k_value < d_value:
                return '卖出', current_price
            else:
                # 计算触发卖出的价格
                trigger_price = current_price * 1.02  # 简单估算
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
        
        # 获取前一个周期的K、D值
        prev_k = self.stoch.percK[-1]
        prev_d = self.stoch.percD[-1]
        
        # 交易逻辑：K线上穿D线买入，下穿卖出
        if not self.position and prev_k <= prev_d and self.stoch.percK[0] > self.stoch.percD[0]:
            self.print_signal(dt, '买入', price)
            size = self.get_buy_size(cash, price, commission)
            if size <= 0:
                from utils.core.logger_manager import get_logger
                logger = get_logger('strategy')
                logger.warning(f"{dt} 下单数量无效: {size}")
            else:
                self.print_order(dt, '买入', size, price, cash)
                self.buy(size=size)
        elif self.position and prev_k >= prev_d and self.stoch.percK[0] < self.stoch.percD[0]:
            self.print_signal(dt, '卖出', price)
            self.print_order(dt, '卖出', self.position.size, price, cash, self.position.size)
            self.close()
            self.reset_position()
        
        self.print_status(dt, self.position.size, cash, total_value)


# KAMA均线交叉策略（用MA近似）

