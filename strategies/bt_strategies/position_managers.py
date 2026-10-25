"""
仓位管理模块
提供多种仓位管理策略，用于控制交易时的买入和卖出数量
每种策略都有不同的风险收益特征，适用于不同的市场环境
"""

import math
import backtrader as bt
from utils.core.config_manager import BACKTEST_CONFIG


class BasePositionMixin:
    """
    仓位管理基类
    定义统一的仓位管理接口和共同功能
    
    主要功能：
    1. 统一的数量验证和四舍五入
    2. 定义抽象方法供子类实现
    3. 处理最小交易数量和精度限制
    """
    
    def __init__(self, min_qty=0.00001, precision=5):
        """
        初始化仓位管理基类
        
        Args:
            min_qty: 最小交易数量（交易所限制）
            precision: 数量精度（小数位数）
        """
        self.min_qty = min_qty
        self.precision = int(precision)  # 确保精度为整数
    
    def get_buy_size(self, cash, price, commission=0.001):
        """
        计算买入数量 - 子类必须实现
        
        Args:
            cash: 可用资金
            price: 当前价格
            commission: 手续费率
            
        Returns:
            float: 买入数量
        """
        raise NotImplementedError("子类必须实现get_buy_size方法")
    
    def get_sell_size(self, position):
        """
        计算卖出数量 - 子类必须实现
        
        Args:
            position: 当前持仓数量
            
        Returns:
            float: 卖出数量
        """
        raise NotImplementedError("子类必须实现get_sell_size方法")
    
    def reset_position(self):
        """
        重置仓位状态 - 子类可选实现
        用于在策略切换或重置时清理状态
        """
        pass
    
    def _round_size(self, size):
        """
        统一的数量向下取整处理（避免超额导致保证金不足）
        
        Args:
            size: 原始数量
            
        Returns:
            float: 按精度向下取整后的数量
        """
        factor = 10 ** self.precision
        return math.floor(max(size, 0.0) * factor) / factor
    
    def _validate_size(self, size):
        """
        统一的数量验证
        
        Args:
            size: 待验证的数量
            
        Returns:
            float: 验证后的数量，小于最小数量时返回0
        """
        if size < self.min_qty:
            return 0.0
        return float(size)

    def _effective_cost_rate(self, commission: float) -> float:
        """
        计算实际成交成本比例：1 + 手续费 + 滑点 + 安全缓冲
        """
        try:
            slippage = float(BACKTEST_CONFIG.get('slippage', 0.0) or 0.0)
        except Exception:
            slippage = 0.0
        safety_buffer = 0.0001  # 1个基点，避免边界导致保证金不足
        return 1.0 + float(commission or 0.0) + slippage + safety_buffer


class AllInPositionMixin(BasePositionMixin):
    """
    全仓管理策略
    每次买入全部资金，卖出全部持仓
    
    特点：
    - 最大化资金利用率
    - 风险较高，适合强势市场
    - 简单直接，易于理解
    """
    
    def __init__(self, min_qty=0.00001, precision=5):
        super().__init__(min_qty, precision)
    
    def get_buy_size(self, cash, price, commission=0.001):
        """
        计算买入数量：使用全部可用资金
        
        Args:
            cash: 可用资金
            price: 当前价格
            commission: 手续费率
            
        Returns:
            float: 买入数量
        """
        # 考虑手续费，计算可买入的数量
        cost_rate = self._effective_cost_rate(commission)
        size = cash / (price * cost_rate)
        size = self._round_size(size)  # 四舍五入到指定精度
        return self._validate_size(size)  # 验证最小数量
    
    def get_sell_size(self, position):
        """
        计算卖出数量：卖出全部持仓
        
        Args:
            position: 当前持仓数量
            
        Returns:
            float: 卖出数量
        """
        size = self._round_size(position)  # 四舍五入到指定精度
        return self._validate_size(size)  # 验证最小数量


class TwoThreeFivePositionMixin(BasePositionMixin):
    """
    2-3-5仓位管理策略
    分批建仓：第一次买入20%，第二次30%，第三次50%
    
    特点：
    - 分散风险，降低单次交易影响
    - 适合震荡市场
    - 需要多次信号确认
    """
    
    def __init__(self, min_qty=0.00001, precision=5):
        super().__init__(min_qty, precision)
        self.position_count = 0  # 记录建仓次数
    
    def get_buy_size(self, cash, price, commission=0.001):
        """
        计算买入数量：按2-3-5比例分批建仓
        
        Args:
            cash: 可用资金
            price: 当前价格
            commission: 手续费率
            
        Returns:
            float: 买入数量
        """
        # 根据建仓次数确定比例
        if self.position_count == 0:
            ratio = 0.2  # 第一次买入20%
        elif self.position_count == 1:
            ratio = 0.3  # 第二次买入30%
        else:
            ratio = 0.5  # 第三次买入50%
        
        # 计算本次买入的资金量
        buy_cash = cash * ratio
        cost_rate = self._effective_cost_rate(commission)
        size = buy_cash / (price * cost_rate)
        size = self._round_size(size)
        
        # 如果买入成功，增加建仓次数
        if size >= self.min_qty:
            self.position_count += 1
        
        return self._validate_size(size)
    
    def get_sell_size(self, position):
        """
        计算卖出数量：卖出全部持仓
        
        Args:
            position: 当前持仓数量
            
        Returns:
            float: 卖出数量
        """
        size = self._round_size(position)
        return self._validate_size(size)
    
    def reset_position(self):
        """重置建仓计数器"""
        self.position_count = 0


class FixedRatioPositionMixin(BasePositionMixin):
    """
    固定比例仓位管理策略
    每次买入固定比例的资金（如20%、30%等）
    
    特点：
    - 风险可控，适合稳健投资
    - 资金利用率适中
    - 适合各种市场环境
    """
    
    def __init__(self, min_qty=0.00001, precision=5, ratio=0.2):
        """
        初始化固定比例仓位管理
        
        Args:
            min_qty: 最小交易数量
            precision: 数量精度
            ratio: 固定买入比例（0-1之间）
        """
        super().__init__(min_qty, precision)
        self.ratio = ratio
    
    def get_buy_size(self, cash, price, commission=0.001):
        """
        计算买入数量：使用固定比例的资金
        
        Args:
            cash: 可用资金
            price: 当前价格
            commission: 手续费率
            
        Returns:
            float: 买入数量
        """
        # 使用固定比例的资金
        buy_cash = cash * self.ratio
        cost_rate = self._effective_cost_rate(commission)
        size = buy_cash / (price * cost_rate)
        size = self._round_size(size)
        return self._validate_size(size)
    
    def get_sell_size(self, position):
        """
        计算卖出数量：卖出全部持仓
        
        Args:
            position: 当前持仓数量
            
        Returns:
            float: 卖出数量
        """
        size = self._round_size(position)
        return self._validate_size(size)


class PyramidAllPositionMixin(BasePositionMixin):
    """
    金字塔仓位管理策略
    分批建仓，每次买入数量递增（如10%、20%、30%、40%）
    
    特点：
    - 趋势跟踪，越涨越买
    - 适合强势上涨市场
    - 风险较高，需要严格止损
    """
    
    def __init__(self, min_qty=0.00001, precision=5):
        super().__init__(min_qty, precision)
        self.position_count = 0  # 记录建仓次数
    
    def get_buy_size(self, cash, price, commission=0.001):
        """
        计算买入数量：金字塔式递增
        
        Args:
            cash: 可用资金
            price: 当前价格
            commission: 手续费率
            
        Returns:
            float: 买入数量
        """
        # 金字塔比例：10%, 20%, 30%, 40%
        ratios = [0.1, 0.2, 0.3, 0.4]
        
        if self.position_count < len(ratios):
            ratio = ratios[self.position_count]
        else:
            ratio = 0.1  # 超过4次后使用10%
        
        buy_cash = cash * ratio
        cost_rate = self._effective_cost_rate(commission)
        size = buy_cash / (price * cost_rate)
        size = self._round_size(size)
        
        if size >= self.min_qty:
            self.position_count += 1
        
        return self._validate_size(size)
    
    def get_sell_size(self, position):
        """
        计算卖出数量：卖出全部持仓
        
        Args:
            position: 当前持仓数量
            
        Returns:
            float: 卖出数量
        """
        size = self._round_size(position)
        return self._validate_size(size)
    
    def reset_position(self):
        """重置建仓计数器"""
        self.position_count = 0


class MartingalePositionMixin(BasePositionMixin):
    """
    马丁格尔仓位管理策略
    亏损后加倍买入，盈利后重置
    
    特点：
    - 高风险高收益
    - 适合震荡市场
    - 需要充足资金支持
    """
    
    def __init__(self, min_qty=0.00001, precision=5, multiplier=2.0):
        super().__init__(min_qty, precision)
        self.multiplier = multiplier  # 加倍倍数
        self.base_size = None  # 基础买入数量
        self.current_multiplier = 1.0  # 当前倍数
    
    def get_buy_size(self, cash, price, commission=0.001):
        """
        计算买入数量：马丁格尔策略
        
        Args:
            cash: 可用资金
            price: 当前价格
            commission: 手续费率
            
        Returns:
            float: 买入数量
        """
        # 计算基础买入数量
        if self.base_size is None:
            self.base_size = cash * 0.1 / (price * (1 + commission))
        
        # 应用当前倍数
        size = self.base_size * self.current_multiplier
        size = self._round_size(size)
        
        return self._validate_size(size)
    
    def get_sell_size(self, position):
        """
        计算卖出数量：卖出全部持仓
        
        Args:
            position: 当前持仓数量
            
        Returns:
            float: 卖出数量
        """
        size = self._round_size(position)
        return self._validate_size(size)
    
    def on_loss(self):
        """亏损后加倍"""
        self.current_multiplier *= self.multiplier
    
    def on_profit(self):
        """盈利后重置"""
        self.current_multiplier = 1.0
    
    def reset_position(self):
        """重置策略状态"""
        self.base_size = None
        self.current_multiplier = 1.0


class KellyPositionMixin(BasePositionMixin):
    """
    凯利公式仓位管理策略
    根据胜率和盈亏比计算最优仓位比例
    
    特点：
    - 数学上最优的仓位管理
    - 需要准确的胜率和盈亏比估计
    - 适合有稳定交易系统的策略
    """
    
    def __init__(self, min_qty=0.00001, precision=5, win_rate=0.5, win_loss_ratio=2.0, max_ratio=0.25):
        """
        初始化凯利公式仓位管理
        
        Args:
            min_qty: 最小交易数量
            precision: 数量精度
            win_rate: 胜率（0-1）
            win_loss_ratio: 盈亏比
            max_ratio: 最大仓位比例（防止过度杠杆）
        """
        super().__init__(min_qty, precision)
        self.win_rate = win_rate
        self.win_loss_ratio = win_loss_ratio
        self.max_ratio = max_ratio
    
    def get_buy_size(self, cash, price, commission=0.001):
        """
        计算买入数量：凯利公式
        
        Args:
            cash: 可用资金
            price: 当前价格
            commission: 手续费率
            
        Returns:
            float: 买入数量
        """
        # 凯利公式：f = (bp - q) / b
        # 其中：b = 盈亏比，p = 胜率，q = 1-p
        b = self.win_loss_ratio
        p = self.win_rate
        q = 1 - p
        
        kelly_ratio = (b * p - q) / b
        
        # 限制最大仓位比例
        kelly_ratio = min(kelly_ratio, self.max_ratio)
        kelly_ratio = max(kelly_ratio, 0)  # 不能为负数
        
        buy_cash = cash * kelly_ratio
        cost_rate = self._effective_cost_rate(commission)
        size = buy_cash / (price * cost_rate)
        size = self._round_size(size)
        
        return self._validate_size(size)
    
    def get_sell_size(self, position):
        """
        计算卖出数量：卖出全部持仓
        
        Args:
            position: 当前持仓数量
            
        Returns:
            float: 卖出数量
        """
        size = self._round_size(position)
        return self._validate_size(size)


class VolatilityPositionMixin(BasePositionMixin):
    """
    波动率调整仓位管理策略
    根据价格波动率调整仓位大小
    
    特点：
    - 高波动时减少仓位，低波动时增加仓位
    - 适应市场波动性变化
    - 需要计算历史波动率
    """
    
    def __init__(self, min_qty=0.00001, precision=5, volatility_window=20, base_ratio=0.2):
        """
        初始化波动率调整仓位管理
        
        Args:
            min_qty: 最小交易数量
            precision: 数量精度
            volatility_window: 波动率计算窗口
            base_ratio: 基础仓位比例
        """
        super().__init__(min_qty, precision)
        self.volatility_window = volatility_window
        self.base_ratio = base_ratio
        self.price_history = []  # 价格历史
    
    def get_buy_size(self, cash, price, commission=0.001):
        """
        计算买入数量：根据波动率调整
        
        Args:
            cash: 可用资金
            price: 当前价格
            commission: 手续费率
            
        Returns:
            float: 买入数量
        """
        # 更新价格历史
        self.price_history.append(price)
        if len(self.price_history) > self.volatility_window:
            self.price_history.pop(0)
        
        # 计算波动率
        if len(self.price_history) >= 2:
            returns = [(self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1] 
                      for i in range(1, len(self.price_history))]
            volatility = sum(abs(ret) for ret in returns) / len(returns)
        else:
            volatility = 0.02  # 默认波动率
        
        # 根据波动率调整仓位比例
        # 波动率高时减少仓位，波动率低时增加仓位
        adjusted_ratio = self.base_ratio * (0.02 / max(volatility, 0.001))
        adjusted_ratio = min(adjusted_ratio, 0.5)  # 限制最大仓位
        adjusted_ratio = max(adjusted_ratio, 0.05)  # 限制最小仓位
        
        buy_cash = cash * adjusted_ratio
        cost_rate = self._effective_cost_rate(commission)
        size = buy_cash / (price * cost_rate)
        size = self._round_size(size)
        
        return self._validate_size(size)
    
    def get_sell_size(self, position):
        """
        计算卖出数量：卖出全部持仓
        
        Args:
            position: 当前持仓数量
            
        Returns:
            float: 卖出数量
        """
        size = self._round_size(position)
        return self._validate_size(size)
    
    def reset_position(self):
        """重置价格历史"""
        self.price_history = [] 