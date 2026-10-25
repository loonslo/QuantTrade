"""
量化交易系统 - 策略基类
========================================

这是所有交易策略的基类，提供通用的功能和接口。
包含日志记录、信号打印、订单通知等通用功能。

主要功能：
1. 统一的信号打印格式
2. 详细的订单状态跟踪
3. 持仓和资金状态监控
4. 信号预测功能
5. 模板方法模式减少重复代码

作者：量化交易团队
版本：2.0.0
"""

from utils.core.logger_manager import get_logger
import backtrader as bt


def get_position_mixin(position_type, **kwargs):
    """
    根据仓位类型获取对应的仓位管理Mixin

    Args:
        position_type: 仓位管理类型
        **kwargs: 仓位管理参数

    Returns:
        BasePositionMixin: 对应的仓位管理实例
    """
    from .position_managers import (
        AllInPositionMixin, TwoThreeFivePositionMixin, FixedRatioPositionMixin,
        PyramidAllPositionMixin, MartingalePositionMixin, KellyPositionMixin,
        VolatilityPositionMixin
    )
    position_mixins = {
        'all_in': AllInPositionMixin,
        'two_three_five': TwoThreeFivePositionMixin,
        'fixed_ratio': FixedRatioPositionMixin,
        'pyramid': PyramidAllPositionMixin,
        'martingale': MartingalePositionMixin,
        'kelly': KellyPositionMixin,
        'volatility': VolatilityPositionMixin,
    }
    return position_mixins.get(position_type, AllInPositionMixin)(**kwargs)


class BaseCryptoStrategy(bt.Strategy):
    """
    加密货币交易策略基类

    所有具体策略都应该继承此类，并实现必要的抽象方法。
    此类提供了交易过程中的通用功能和日志记录。

    设计模式：
    - 模板方法模式：定义算法框架，让子类实现具体步骤
    - 策略模式：封装不同的交易策略

    子类只需要实现以下方法：
    - _init_indicators(): 初始化技术指标
    - _check_buy_signal(): 检查买入条件（返回bool）
    - _check_sell_signal(): 检查卖出条件（返回bool）
    - _get_buy_trigger_price(): 获取买入触发价格
    - _get_sell_trigger_price(): 获取卖出触发价格

    使用示例：
        class MyStrategy(BaseCryptoStrategy):
            def _init_indicators(self):
                self.sma = bt.indicators.SimpleMovingAverage(...)

            def _check_buy_signal(self):
                return self.data.close[0] > self.sma[0]

            def _check_sell_signal(self):
                return self.data.close[0] < self.sma[0]

            def _get_buy_trigger_price(self):
                return self.sma[0]

            def _get_sell_trigger_price(self):
                return self.sma[0]
    """

    # 默认参数
    params = (
        ('min_qty', 0.00001),      # 最小交易数量
        ('precision', 5),           # 数量精度
        ('position_type', 'all_in'),  # 仓位管理类型
        ('position_params', {}),    # 仓位管理参数
    )

    def __init__(self):
        """初始化策略基类"""
        super().__init__()

        # 初始化仓位管理
        position_mixin = get_position_mixin(
            self.p.position_type,
            **self.p.position_params
        )
        self.get_buy_size = position_mixin.get_buy_size
        self.get_sell_size = position_mixin.get_sell_size
        self.reset_position = position_mixin.reset_position

        # 子类初始化指标
        self._init_indicators()

        # 获取日志器
        self._logger = get_logger('strategy')

    def _init_indicators(self):
        """
        初始化技术指标 - 子类需要重写
        """
        pass

    def _check_buy_signal(self) -> bool:
        """
        检查买入条件 - 子类需要重写

        Returns:
            bool: 是否满足买入条件
        """
        return False

    def _check_sell_signal(self) -> bool:
        """
        检查卖出条件 - 子类需要重写

        Returns:
            bool: 是否满足卖出条件
        """
        return False

    def _get_buy_trigger_price(self) -> float:
        """
        获取买入触发价格 - 子类需要重写

        Returns:
            float: 触发买入的价格
        """
        return self.data.close[0]

    def _get_sell_trigger_price(self) -> float:
        """
        获取卖出触发价格 - 子类需要重写

        Returns:
            float: 触发卖出的价格
        """
        return self.data.close[0]

    def _get_commission(self) -> float:
        """获取手续费率"""
        return self.broker.getcommissioninfo(self.datas[0]).p.commission

    def _get_current_price(self) -> float:
        """获取当前价格"""
        return self.data.close[0]

    def _get_dt(self):
        """获取当前时间"""
        return self.datas[0].datetime.datetime(0)

    def _get_state(self) -> tuple:
        """获取当前状态，返回 (cash, price, position, total_value)"""
        cash = self.broker.getcash()
        price = self.data.close[0]
        position = self.position.size
        total_value = position * price + cash
        return cash, price, position, total_value

    def _predict_signal(self) -> tuple:
        """
        预测下一个信号 - 默认实现

        Returns:
            tuple: (信号类型, 触发价格) 或 (None, None)
        """
        current_price = self._get_current_price()

        if not self.position:
            # 无持仓，预测买入
            if self._check_buy_signal():
                return '买入', current_price
            return '买入', self._get_buy_trigger_price()
        else:
            # 有持仓，预测卖出
            if self._check_sell_signal():
                return '卖出', current_price
            return '卖出', self._get_sell_trigger_price()

    # ========== 模板方法模式 - 统一的next逻辑 ==========

    def next(self):
        """
        策略主逻辑 - 模板方法

        统一的交易逻辑，子类只需实现 _check_buy_signal 和 _check_sell_signal
        """
        cash, price, position, total_value = self._get_state()
        dt = self._get_dt()
        commission = self._get_commission()

        # 预测下一个信号
        signal_type, trigger_price = self._predict_signal()
        if signal_type:
            self._print_prediction(dt, signal_type, trigger_price, price)

        # 交易逻辑
        if not position:
            # 无持仓，满足买入条件则买入
            if self._check_buy_signal():
                self._print_signal(dt, '买入', price)
                size = self.get_buy_size(cash, price, commission)
                if size > 0:
                    self._print_order(dt, '买入', size, price, cash)
                    self.buy(size=size)
        else:
            # 有持仓，满足卖出条件则卖出
            if self._check_sell_signal():
                self._print_signal(dt, '卖出', price)
                self._print_order(dt, '卖出', position, price, cash, position)
                self.close()
                self.reset_position()

        # 打印当前状态
        self._print_status(dt, position, cash, total_value)

    # ========== 通用日志方法 ==========

    def _print_signal(self, dt, signal, price):
        """打印交易信号"""
        from utils.time.time_utils import to_beijing_time
        time_str = to_beijing_time(dt)

        cash, _, position, total_value = self._get_state()

        signal_emoji = "📈" if signal == '买入' else "📉"
        signal_type = "BUY" if signal == '买入' else "SELL"

        self._logger.info(
            f"{signal_emoji} 信号: {signal_type} BTC/USDT | "
            f"时间: {time_str} | 价格: {price:.0f} | "
            f"现金: {cash:.0f} | 持仓: {position:.6f} | 总值: {total_value:.0f}"
        )

    def _print_order(self, dt, action, size, price, cash, position=None):
        """打印订单信息"""
        if action == '买入':
            self._logger.info(f"{dt} 买入下单: 数量={size:.5f} 价格={price:.2f} 余额={cash:.2f}")
        else:
            self._logger.info(f"{dt} 卖出下单: 数量={size:.5f} 价格={price:.2f} 持仓={position:.5f}")

    def _print_status(self, dt, position, cash, total_value):
        """打印当前状态"""
        self._logger.info(f"{dt} 持仓={position:.5f} 余额={cash:.2f} 当前总额={total_value:.2f}")

    def _print_prediction(self, dt, signal_type, trigger_price, current_price):
        """打印信号预测"""
        if signal_type == '买入':
            self._logger.info(
                f"{dt} 🔮 买入信号预测: 当前价格={current_price:.2f}, 触发价格={trigger_price:.2f}"
            )
        elif signal_type == '卖出':
            self._logger.info(
                f"{dt} 🔮 卖出信号预测: 当前价格={current_price:.2f}, 触发价格={trigger_price:.2f}"
            )

    def predict_next_signal(self):
        """
        预测下一个信号 - 兼容旧接口

        Returns:
            tuple: (信号类型, 触发价格) 或 (None, None)
        """
        return self._predict_signal()

    def notify_order(self, order):
        """订单状态通知回调函数"""
        dt = self._get_dt()
        price = self._get_current_price()
        cash = self.broker.getcash()
        total_value = self.position.size * price + cash

        if order.status in [order.Submitted]:
            self._logger.info(f"订单已提交: 时间={dt}")
        elif order.status in [order.Accepted]:
            self._logger.info(f"订单已接受: 时间={dt}")
        elif order.status in [order.Completed]:
            if order.isbuy():
                self._logger.info(
                    f"买入成交: 时间={dt} 数量={order.executed.size:.5f} "
                    f"价格={order.executed.price:.2f} 手续费={order.executed.comm:.6f} "
                    f"余额={cash:.2f} 持仓={self.position.size:.5f} 当前总额={total_value:.2f}"
                )
            elif order.issell():
                self._logger.info(
                    f"卖出成交: 时间={dt} 数量={order.executed.size:.5f} "
                    f"价格={order.executed.price:.2f} 手续费={order.executed.comm:.6f} "
                    f"余额={cash:.2f} 持仓={self.position.size:.5f} 当前总额={total_value:.2f}"
                )
        elif order.status in [order.Canceled]:
            self._logger.info(f"订单已取消: 时间={dt}")
        elif order.status in [order.Margin]:
            self._logger.warning(f"订单保证金不足: 时间={dt}")
        elif order.status in [order.Rejected]:
            self._logger.error(f"订单被拒绝: 时间={dt}")

    # Compatibility methods used by the split Sys strategies.
    def print_signal(self, *args):
        return self._print_signal(*args)

    def print_order(self, *args):
        return self._print_order(*args)

    def print_status(self, *args):
        return self._print_status(*args)

    def print_prediction(self, *args):
        return self._print_prediction(*args)

    def stop(self):
        """Leave end-of-data positions open and value them at the final close."""
        if self.position.size:
            self._logger.info("Backtest ended with an open position; equity is marked to market")
