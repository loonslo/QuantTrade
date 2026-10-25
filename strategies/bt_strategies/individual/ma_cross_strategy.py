"""
量化交易系统 - 移动平均线交叉策略
========================================

策略说明：

    移动平均线交叉策略
    当短期均线上穿长期均线时买入，下穿时卖出

    策略原理：
    - 短期均线 > 长期均线：上升趋势，买入信号
    - 短期均线 < 长期均线：下降趋势，卖出信号
    - 适合趋势明显的市场

使用示例：
    from strategies.bt_strategies.individual import MaCrossStrategy

    cerebro.addstrategy(MaCrossStrategy,
        short_window=5,
        long_window=20,
        position_type='all_in'
    )

作者：量化交易团队
版本：2.0.0
"""

import backtrader as bt
from ..base_strategy import BaseCryptoStrategy


class MaCrossStrategy(BaseCryptoStrategy):
    """
    移动平均线交叉策略
    当短期均线上穿长期均线时买入，下穿时卖出

    策略原理：
    - 短期均线 > 长期均线：上升趋势，买入信号
    - 短期均线 < 长期均线：下降趋势，卖出信号
    - 适合趋势明显的市场
    """

    params = (
        ('short_window', 5),   # 短期均线周期
        ('long_window', 20),    # 长期均线周期
        ('position_type', 'all_in'),
        ('position_params', {}),
    )

    def _init_indicators(self):
        """初始化技术指标"""
        self.sma_short = self._create_indicator(
            bt.indicators.SimpleMovingAverage,
            period=self.p.short_window,
            plotname='SMA Short'
        )
        self.sma_long = self._create_indicator(
            bt.indicators.SimpleMovingAverage,
            period=self.p.long_window,
            plotname='SMA Long'
        )

    def _create_indicator(self, indicator_class, **kwargs):
        """创建指标的辅助方法"""
        return indicator_class(self.datas[0], **kwargs)

    def _check_buy_signal(self) -> bool:
        """买入条件：短期均线上穿长期均线"""
        # 当前短期 > 长期，前一周期短期 <= 长期（金叉）
        return (self.sma_short[0] > self.sma_long[0] and
                self.sma_short[-1] <= self.sma_long[-1])

    def _check_sell_signal(self) -> bool:
        """卖出条件：短期均线下穿长期均线"""
        # 当前短期 < 长期，前一周期短期 >= 长期（死叉）
        return (self.sma_short[0] < self.sma_long[0] and
                self.sma_short[-1] >= self.sma_long[-1])

    def _get_buy_trigger_price(self) -> float:
        """买入触发价：当前短期均线"""
        return self.sma_short[0]

    def _get_sell_trigger_price(self) -> float:
        """卖出触发价：当前长期均线"""
        return self.sma_long[0]

    def _predict_signal(self):
        """预测下一个信号 - 重写以使用均线数据"""
        short_ma = self.sma_short[0]
        long_ma = self.sma_long[0]
        current_price = self.data.close[0]

        if not self.position:
            if short_ma > long_ma:
                return '买入', current_price
            else:
                trigger_price = long_ma + (long_ma - short_ma) * 0.1
                return '买入', trigger_price
        else:
            if short_ma < long_ma:
                return '卖出', current_price
            else:
                trigger_price = long_ma - (short_ma - long_ma) * 0.1
                return '卖出', trigger_price
