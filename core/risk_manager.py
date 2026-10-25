"""
风险管理模块
提供风险控制功能，包括仓位控制、止损止盈、回撤限制等
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
from utils.validation.exceptions import RiskException
from utils.core.logger_manager import get_logger


class RiskConfig:
    """风险配置"""
    
    def __init__(self, 
                 max_position_size: float = 0.1,
                 max_drawdown: float = 0.2,
                 stop_loss: float = 0.05,
                 take_profit: float = 0.1,
                 max_trades_per_day: int = 10,
                 max_trades_per_symbol: int = 5,
                 min_interval_between_trades: int = 5):
        """
        初始化风险配置
        
        Args:
            max_position_size: 最大仓位比例
            max_drawdown: 最大回撤限制
            stop_loss: 止损比例
            take_profit: 止盈比例
            max_trades_per_day: 每日最大交易次数
            max_trades_per_symbol: 每个交易对最大交易次数
            min_interval_between_trades: 交易间隔（分钟）
        """
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.max_trades_per_day = max_trades_per_day
        self.max_trades_per_symbol = max_trades_per_symbol
        self.min_interval_between_trades = min_interval_between_trades


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: RiskConfig):
        """
        初始化风险管理器
        
        Args:
            config: 风险配置
        """
        self.config = config
        self.logger = get_logger('risk')
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_trades: Dict[str, int] = {}
        self.symbol_trades: Dict[str, int] = {}
        self.last_trade_time: Optional[datetime] = None
        
        # 打印风控参数配置
        self.logger.info(f"🛡️ 风控配置: 仓位{self.config.max_position_size:.0%} | 回撤{self.config.max_drawdown:.0%} | 止损{self.config.stop_loss:.0%} | 止盈{self.config.take_profit:.0%} | 日交易{self.config.max_trades_per_day} | 对交易{self.config.max_trades_per_symbol} | 间隔{self.config.min_interval_between_trades}分钟")
        
    def check_position_size(self, cash: float, price: float, 
                           quantity: float) -> bool:
        """
        检查仓位大小是否合规
        
        Args:
            cash: 可用资金
            price: 当前价格
            quantity: 计划购买数量
            
        Returns:
            bool: 是否合规
        """
        position_value = price * quantity
        if cash == 0:
            self.logger.warning("账户价值为0，无法计算仓位比例")
            position_ratio = 0
        else:
            position_ratio = position_value / cash
        
        self.logger.debug(f"🛡️ 仓位检查: 资金{cash:.0f} | 价格{price:.0f} | 数量{quantity:.4f} | 比例{position_ratio:.0%} | 限制{self.config.max_position_size:.0%}")
        
        if position_ratio > self.config.max_position_size:
            self.logger.warning(f"仓位过大: {position_ratio:.2%} > {self.config.max_position_size:.2%}")
            return False
        
        return True
    
    def check_drawdown(self, initial_value: float, current_value: float) -> bool:
        """
        检查回撤是否合规
        
        Args:
            initial_value: 初始资金
            current_value: 当前资金
            
        Returns:
            bool: 是否合规
        """
        if initial_value <= 0:
            return True
            
        if initial_value == 0:
            self.logger.warning("初始资金为0，无法计算回撤")
            return True

        drawdown = (initial_value - current_value) / initial_value
        
        self.logger.debug(f"🛡️ 回撤检查: 初始{initial_value:.0f} | 当前{current_value:.0f} | 回撤{drawdown:.0%} | 限制{self.config.max_drawdown:.0%}")
        
        if drawdown > self.config.max_drawdown:
            self.logger.warning(f"回撤过大: {drawdown:.2%} > {self.config.max_drawdown:.2%}")
            return False
        
        return True
    
    def check_stop_loss(self, entry_price: float, current_price: float, 
                       side: str) -> bool:
        """
        检查止损条件
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            side: 交易方向 ('buy' 或 'sell')
            
        Returns:
            bool: 是否触发止损
        """
        if entry_price == 0:
            self.logger.warning("入场价格为0，无法计算止损比例")
            return False

        if current_price == 0:
            self.logger.warning("当前价格为0，无法计算止损比例")
            return False

        if side == 'buy':
            loss_ratio = (entry_price - current_price) / entry_price
        else:
            loss_ratio = (current_price - entry_price) / entry_price
        
        self.logger.debug(f"🛡️ 止损检查: 入场{entry_price:.0f} | 当前{current_price:.0f} | 方向{side} | 亏损{loss_ratio:.0%} | 止损线{self.config.stop_loss:.0%}")
        
        if loss_ratio > self.config.stop_loss:
            self.logger.warning(f"触发止损: {loss_ratio:.2%} > {self.config.stop_loss:.2%}")
            return True
        
        return False
    
    def check_take_profit(self, entry_price: float, current_price: float, 
                         side: str) -> bool:
        """
        检查止盈条件
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            side: 交易方向 ('buy' 或 'sell')
            
        Returns:
            bool: 是否触发止盈
        """
        if entry_price == 0:
            self.logger.warning("入场价格为0，无法计算止盈比例")
            return False

        if current_price == 0:
            self.logger.warning("当前价格为0，无法计算止盈比例")
            return False

        if side == 'buy':
            profit_ratio = (current_price - entry_price) / entry_price
        else:
            profit_ratio = (entry_price - current_price) / entry_price
        
        self.logger.debug(f"🛡️ 止盈检查: 入场{entry_price:.0f} | 当前{current_price:.0f} | 方向{side} | 盈利{profit_ratio:.0%} | 止盈线{self.config.take_profit:.0%}")
        
        if profit_ratio > self.config.take_profit:
            self.logger.info(f"触发止盈: {profit_ratio:.2%} > {self.config.take_profit:.2%}")
            return True
        
        return False
    
    def check_trade_frequency(self, symbol: str, current_time: datetime) -> bool:
        """
        检查交易频率是否合规
        
        Args:
            symbol: 交易对
            current_time: 当前时间
            
        Returns:
            bool: 是否合规
        """
        # 检查每日交易次数
        today = current_time.strftime('%Y-%m-%d')
        daily_count = self.daily_trades.get(today, 0)
        
        # 检查每个交易对的交易次数
        symbol_count = self.symbol_trades.get(symbol, 0)
        
        self.logger.debug(f"🛡️ 交易频率检查: {symbol} | 日期{today} | 日交易{daily_count}/{self.config.max_trades_per_day} | 对交易{symbol_count}/{self.config.max_trades_per_symbol}")
        
        if daily_count >= self.config.max_trades_per_day:
            self.logger.warning(f"每日交易次数超限: {daily_count} >= {self.config.max_trades_per_day}")
            return False
        
        if symbol_count >= self.config.max_trades_per_symbol:
            self.logger.warning(f"交易对交易次数超限: {symbol_count} >= {self.config.max_trades_per_symbol}")
            return False
        
        # 检查交易间隔
        if self.last_trade_time:
            time_diff = (current_time - self.last_trade_time).total_seconds() / 60
            self.logger.debug(f"🛡️ 交易间隔检查: {time_diff:.1f}分钟 | 最小间隔{self.config.min_interval_between_trades}分钟")
            
            if time_diff < self.config.min_interval_between_trades:
                self.logger.warning(f"交易间隔过短: {time_diff:.1f}分钟 < {self.config.min_interval_between_trades}分钟")
                return False
        
        return True
    
    def record_trade(self, trade: Dict[str, Any]):
        """
        记录交易
        
        Args:
            trade: 交易信息
        """
        self.trade_history.append(trade)
        
        # 更新每日交易次数
        trade_time = trade.get('datetime', datetime.now())
        today = trade_time.strftime('%Y-%m-%d')
        self.daily_trades[today] = self.daily_trades.get(today, 0) + 1
        
        # 更新交易对交易次数
        symbol = trade.get('symbol', '')
        self.symbol_trades[symbol] = self.symbol_trades.get(symbol, 0) + 1
        
        # 更新最后交易时间
        self.last_trade_time = trade_time
        
        self.logger.info(f"记录交易: {trade}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        获取风险指标
        
        Returns:
            Dict[str, Any]: 风险指标
        """
        if not self.trade_history:
            return {}
        
        # 计算胜率
        total_trades = len(self.trade_history)
        won_trades = sum(1 for trade in self.trade_history if trade.get('pnl', 0) > 0)
        win_rate = won_trades / total_trades if total_trades > 0 else 0
        
        # 计算平均盈亏
        pnls = [trade.get('pnl', 0) for trade in self.trade_history]
        avg_pnl = sum(pnls) / len(pnls) if pnls else 0
        
        # 计算最大回撤
        cumulative_pnl = 0
        max_drawdown = 0
        peak_value = 0
        
        for trade in self.trade_history:
            cumulative_pnl += trade.get('pnl', 0)
            if cumulative_pnl > peak_value:
                peak_value = cumulative_pnl
            
            if peak_value > 0:
                drawdown = (peak_value - cumulative_pnl) / peak_value
                max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'max_drawdown': max_drawdown,
            'daily_trades': self.daily_trades,
            'symbol_trades': self.symbol_trades
        }
    
    def reset_daily_limits(self):
        """重置每日限制"""
        self.daily_trades.clear()
        self.logger.info("重置每日交易限制")
    
    def reset_symbol_limits(self):
        """重置交易对限制"""
        self.symbol_trades.clear()
        self.logger.info("重置交易对交易限制")
    
    def validate_signal(self, signal: Dict[str, Any], 
                       context: Dict[str, Any]) -> bool:
        """
        验证交易信号
        
        Args:
            signal: 交易信号
            context: 回测上下文
            
        Returns:
            bool: 信号是否有效
        """
        try:
            # 检查仓位大小 - 修复cash获取方式
            cash = context.get('current_cash', 0) if isinstance(context, dict) else getattr(context, 'current_cash', 0)
            price = signal.get('price', 0) if isinstance(signal, dict) else getattr(signal, 'price', 0)
            # 对于信号验证，我们不需要quantity，因为仓位大小由仓位管理器计算
            quantity = 0.1  # 使用一个默认值进行验证
            
            if not self.check_position_size(cash, price, quantity):
                self.logger.warning("信号验证失败: 仓位大小检查未通过")
                return False
            
            # 检查交易频率
            symbol = signal.get('symbol', '') if isinstance(signal, dict) else getattr(signal, 'symbol', '')
            current_time = context.get('current_time', datetime.now()) if isinstance(context, dict) else getattr(context, 'current_time', datetime.now())
            
            if not self.check_trade_frequency(symbol, current_time):
                self.logger.warning("信号验证失败: 交易频率检查未通过")
                return False
            
            # 检查回撤
            initial_value = context.get('initial_cash', cash) if isinstance(context, dict) else getattr(context, 'initial_cash', cash)
            current_value = context.get('current_cash', cash) if isinstance(context, dict) else getattr(context, 'current_cash', cash)
            
            if not self.check_drawdown(initial_value, current_value):
                self.logger.warning("信号验证失败: 回撤检查未通过")
                return False
            return True
            
        except Exception as e:
            self.logger.error(f"信号验证失败: {e}")
            return False
    
    def should_close_position(self, position: Dict[str, Any], 
                            current_price: float) -> bool:
        """
        判断是否应该平仓
        
        Args:
            position: 持仓信息
            current_price: 当前价格
            
        Returns:
            bool: 是否应该平仓
        """
        entry_price = position.get('entry_price', 0)
        side = position.get('side', 'buy')
        
        # 检查止损
        if self.check_stop_loss(entry_price, current_price, side):
            self.logger.info(f"🛡️ 触发止损: {position.get('symbol', '')} | 入场{entry_price:.0f} | 当前{current_price:.0f} | 方向{side}")
            return True
        
        # 检查止盈
        if self.check_take_profit(entry_price, current_price, side):
            self.logger.info(f"🛡️ 触发止盈: {position.get('symbol', '')} | 入场{entry_price:.0f} | 当前{current_price:.0f} | 方向{side}")
            return True
        return False 