"""
技术分析模块 - 压力位阻力位分析
实现基于K线数据的支撑阻力位识别、突破概率计算和交易信号生成
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from utils.core.logger_manager import get_logger
from utils.validation.exceptions import AnalysisException


@dataclass
class SupportResistanceLevel:
    """支撑/阻力位数据结构"""
    price: float                    # 价格水平
    level_type: str                # 'support' 或 'resistance'
    strength: float                # 强度 (0-1)
    touch_count: int               # 触及次数
    last_touch_time: datetime      # 最后触及时间
    volume_profile: float          # 成交量分布
    breakout_probability: float    # 突破概率
    confidence: float              # 置信度
    
    
@dataclass
class TradingSignal:
    """交易信号数据结构"""
    symbol: str
    signal_type: str               # 'BUY' 或 'SELL'
    entry_price: float             # 入场价格
    stop_loss: float               # 止损价格
    take_profit: float             # 止盈价格
    confidence: float              # 信号置信度
    trigger_probability: float     # 触发概率
    expected_return: float         # 预期收益率
    risk_reward_ratio: float       # 风险收益比
    timestamp: datetime
    reasoning: str                 # 信号原因


class TechnicalAnalyzer:
    """技术分析器 - 核心分析引擎"""
    
    def __init__(self, lookback_period: int = 100, min_touches: int = 2):
        """
        初始化技术分析器
        
        Args:
            lookback_period: 回看周期
            min_touches: 最小触及次数
        """
        self.lookback_period = lookback_period
        self.min_touches = min_touches
        self.logger = get_logger('technical_analyzer')
        
        # 存储分析结果
        self.support_levels: List[SupportResistanceLevel] = []
        self.resistance_levels: List[SupportResistanceLevel] = []
        self.trading_signals: List[TradingSignal] = []
        
    def analyze_support_resistance(self, data: pd.DataFrame) -> Dict[str, List[SupportResistanceLevel]]:
        """
        分析支撑阻力位
        
        Args:
            data: OHLCV数据
            
        Returns:
            Dict: 包含支撑位和阻力位的字典
        """
        try:
            self.logger.info("开始分析支撑阻力位")
            
            # 重置结果
            self.support_levels = []
            self.resistance_levels = []
            
            # 获取最近的数据
            recent_data = data.tail(self.lookback_period).copy()
            
            if len(recent_data) < 20:
                raise AnalysisException("数据不足，无法进行支撑阻力位分析")
            
            # 识别支撑位
            self._identify_support_levels(recent_data)
            
            # 识别阻力位
            self._identify_resistance_levels(recent_data)
            
            # 计算突破概率
            self._calculate_breakout_probabilities(recent_data)
            
            self.logger.info(f"识别到 {len(self.support_levels)} 个支撑位，{len(self.resistance_levels)} 个阻力位")
            
            return {
                'support_levels': self.support_levels,
                'resistance_levels': self.resistance_levels
            }
            
        except Exception as e:
            self.logger.error(f"支撑阻力位分析失败: {e}")
            raise AnalysisException(f"支撑阻力位分析失败: {e}")
    
    def _identify_support_levels(self, data: pd.DataFrame):
        """识别支撑位"""
        # 寻找局部低点
        lows = self._find_local_extremes(data, 'low', 'min')
        
        for low_price in lows:
            # 计算触及次数
            touch_count = self._count_touches(data, low_price, 'support')
            
            if touch_count >= self.min_touches:
                # 计算强度
                strength = self._calculate_level_strength(data, low_price, 'support')
                
                # 获取最后触及时间
                last_touch = self._get_last_touch_time(data, low_price, 'support')
                
                # 计算成交量分布
                volume_profile = self._calculate_volume_profile(data, low_price)
                
                # 计算置信度
                confidence = self._calculate_confidence(touch_count, strength, volume_profile)
                
                support_level = SupportResistanceLevel(
                    price=low_price,
                    level_type='support',
                    strength=strength,
                    touch_count=touch_count,
                    last_touch_time=last_touch,
                    volume_profile=volume_profile,
                    breakout_probability=0.0,  # 稍后计算
                    confidence=confidence
                )
                
                self.support_levels.append(support_level)
    
    def _identify_resistance_levels(self, data: pd.DataFrame):
        """识别阻力位"""
        # 寻找局部高点
        highs = self._find_local_extremes(data, 'high', 'max')
        
        for high_price in highs:
            # 计算触及次数
            touch_count = self._count_touches(data, high_price, 'resistance')
            
            if touch_count >= self.min_touches:
                # 计算强度
                strength = self._calculate_level_strength(data, high_price, 'resistance')
                
                # 获取最后触及时间
                last_touch = self._get_last_touch_time(data, high_price, 'resistance')
                
                # 计算成交量分布
                volume_profile = self._calculate_volume_profile(data, high_price)
                
                # 计算置信度
                confidence = self._calculate_confidence(touch_count, strength, volume_profile)
                
                resistance_level = SupportResistanceLevel(
                    price=high_price,
                    level_type='resistance',
                    strength=strength,
                    touch_count=touch_count,
                    last_touch_time=last_touch,
                    volume_profile=volume_profile,
                    breakout_probability=0.0,  # 稍后计算
                    confidence=confidence
                )
                
                self.resistance_levels.append(resistance_level)
    
    def _find_local_extremes(self, data: pd.DataFrame, column: str, extremum_type: str) -> List[float]:
        """寻找局部极值点"""
        extremes = []
        window = 5  # 局部极值窗口
        
        for i in range(window, len(data) - window):
            current_value = data.iloc[i][column]
            window_data = data.iloc[i-window:i+window+1][column]
            
            if extremum_type == 'min':
                if current_value == window_data.min():
                    extremes.append(current_value)
            else:  # max
                if current_value == window_data.max():
                    extremes.append(current_value)
        
        return extremes
    
    def _count_touches(self, data: pd.DataFrame, price: float, level_type: str) -> int:
        """计算价格触及次数"""
        tolerance = price * 0.001  # 0.1% 容差
        
        if level_type == 'support':
            # 支撑位：计算低点触及次数
            touches = ((data['low'] <= price + tolerance) & 
                      (data['low'] >= price - tolerance)).sum()
        else:  # resistance
            # 阻力位：计算高点触及次数
            touches = ((data['high'] >= price - tolerance) & 
                      (data['high'] <= price + tolerance)).sum()
        
        return touches
    
    def _calculate_level_strength(self, data: pd.DataFrame, price: float, level_type: str) -> float:
        """计算支撑/阻力位强度"""
        tolerance = price * 0.001
        
        if level_type == 'support':
            # 支撑位强度：基于反弹力度
            touches = data[(data['low'] <= price + tolerance) & 
                         (data['low'] >= price - tolerance)]
            if len(touches) == 0:
                return 0.0
            
            # 计算平均反弹幅度
            rebounds = []
            for idx in touches.index:
                if idx < len(data) - 1:
                    rebound = (data.iloc[idx+1]['high'] - price) / price
                    rebounds.append(rebound)
            
            strength = np.mean(rebounds) if rebounds else 0.0
            
        else:  # resistance
            # 阻力位强度：基于回落力度
            touches = data[(data['high'] >= price - tolerance) & 
                         (data['high'] <= price + tolerance)]
            if len(touches) == 0:
                return 0.0
            
            # 计算平均回落幅度
            pullbacks = []
            for idx in touches.index:
                if idx < len(data) - 1:
                    pullback = (price - data.iloc[idx+1]['low']) / price
                    pullbacks.append(pullback)
            
            strength = np.mean(pullbacks) if pullbacks else 0.0
        
        return max(0.0, min(1.0, strength))
    
    def _get_last_touch_time(self, data: pd.DataFrame, price: float, level_type: str) -> datetime:
        """获取最后触及时间"""
        tolerance = price * 0.001
        
        if level_type == 'support':
            touches = data[(data['low'] <= price + tolerance) & 
                         (data['low'] >= price - tolerance)]
        else:  # resistance
            touches = data[(data['high'] >= price - tolerance) & 
                         (data['high'] <= price + tolerance)]
        
        if len(touches) > 0:
            return touches.index[-1]
        else:
            return datetime.now()
    
    def _calculate_volume_profile(self, data: pd.DataFrame, price: float) -> float:
        """计算成交量分布"""
        tolerance = price * 0.001
        
        # 计算价格附近的成交量
        nearby_volume = data[
            (data['low'] <= price + tolerance) & 
            (data['high'] >= price - tolerance)
        ]['volume'].sum()
        
        total_volume = data['volume'].sum()
        
        return nearby_volume / total_volume if total_volume > 0 else 0.0
    
    def _calculate_confidence(self, touch_count: int, strength: float, volume_profile: float) -> float:
        """计算置信度"""
        # 基于触及次数、强度和成交量分布计算置信度
        touch_score = min(1.0, touch_count / 5.0)  # 最多5次触及
        strength_score = strength
        volume_score = min(1.0, volume_profile * 10)  # 成交量权重
        
        confidence = (touch_score * 0.4 + strength_score * 0.4 + volume_score * 0.2)
        return max(0.0, min(1.0, confidence))
    
    def _calculate_breakout_probabilities(self, data: pd.DataFrame):
        """计算突破概率"""
        current_price = data['close'].iloc[-1]
        
        # 计算支撑位突破概率
        for support in self.support_levels:
            if current_price <= support.price:
                # 价格在支撑位附近或以下，计算向下突破概率
                distance = abs(current_price - support.price) / support.price
                strength_factor = 1.0 - support.strength
                volume_factor = support.volume_profile
                
                breakout_prob = min(0.9, distance * 2 + strength_factor * 0.3 + volume_factor * 0.2)
                support.breakout_probability = breakout_prob
        
        # 计算阻力位突破概率
        for resistance in self.resistance_levels:
            if current_price >= resistance.price:
                # 价格在阻力位附近或以上，计算向上突破概率
                distance = abs(current_price - resistance.price) / resistance.price
                strength_factor = 1.0 - resistance.strength
                volume_factor = resistance.volume_profile
                
                breakout_prob = min(0.9, distance * 2 + strength_factor * 0.3 + volume_factor * 0.2)
                resistance.breakout_probability = breakout_prob
    
    def generate_trading_signals(self, data: pd.DataFrame, symbol: str = "BTCUSDT") -> List[TradingSignal]:
        """
        生成交易信号
        
        Args:
            data: OHLCV数据
            symbol: 交易对符号
            
        Returns:
            List[TradingSignal]: 交易信号列表
        """
        try:
            self.logger.info("开始生成交易信号")
            
            # 重置信号
            self.trading_signals = []
            
            # 分析支撑阻力位
            self.analyze_support_resistance(data)
            
            current_price = data['close'].iloc[-1]
            current_time = datetime.now()
            
            # 生成买入信号（支撑位反弹）
            for support in self.support_levels:
                if (support.confidence > 0.6 and 
                    abs(current_price - support.price) / support.price < 0.02 and
                    support.breakout_probability < 0.3):
                    
                    # 计算止损和止盈
                    stop_loss = support.price * 0.98  # 2% 止损
                    take_profit = current_price * 1.06  # 6% 止盈
                    
                    # 计算风险收益比
                    risk = current_price - stop_loss
                    reward = take_profit - current_price
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    
                    signal = TradingSignal(
                        symbol=symbol,
                        signal_type='BUY',
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        confidence=support.confidence,
                        trigger_probability=1.0 - support.breakout_probability,
                        expected_return=(take_profit - current_price) / current_price,
                        risk_reward_ratio=risk_reward_ratio,
                        timestamp=current_time,
                        reasoning=f"支撑位反弹信号，支撑位价格: {support.price:.2f}，触及次数: {support.touch_count}"
                    )
                    
                    self.trading_signals.append(signal)
            
            # 生成卖出信号（阻力位回落）
            for resistance in self.resistance_levels:
                if (resistance.confidence > 0.6 and 
                    abs(current_price - resistance.price) / resistance.price < 0.02 and
                    resistance.breakout_probability < 0.3):
                    
                    # 计算止损和止盈
                    stop_loss = resistance.price * 1.02  # 2% 止损
                    take_profit = current_price * 0.94  # 6% 止盈
                    
                    # 计算风险收益比
                    risk = stop_loss - current_price
                    reward = current_price - take_profit
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    
                    signal = TradingSignal(
                        symbol=symbol,
                        signal_type='SELL',
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        confidence=resistance.confidence,
                        trigger_probability=1.0 - resistance.breakout_probability,
                        expected_return=(current_price - take_profit) / current_price,
                        risk_reward_ratio=risk_reward_ratio,
                        timestamp=current_time,
                        reasoning=f"阻力位回落信号，阻力位价格: {resistance.price:.2f}，触及次数: {resistance.touch_count}"
                    )
                    
                    self.trading_signals.append(signal)
            
            self.logger.info(f"生成了 {len(self.trading_signals)} 个交易信号")
            return self.trading_signals
            
        except Exception as e:
            self.logger.error(f"交易信号生成失败: {e}")
            raise AnalysisException(f"交易信号生成失败: {e}")
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            'support_levels_count': len(self.support_levels),
            'resistance_levels_count': len(self.resistance_levels),
            'trading_signals_count': len(self.trading_signals),
            'strongest_support': max(self.support_levels, key=lambda x: x.strength) if self.support_levels else None,
            'strongest_resistance': max(self.resistance_levels, key=lambda x: x.strength) if self.resistance_levels else None,
            'highest_confidence_signal': max(self.trading_signals, key=lambda x: x.confidence) if self.trading_signals else None
        }


def analyze_technical_levels(data: pd.DataFrame, symbol: str = "BTCUSDT") -> TechnicalAnalyzer:
    """
    便捷函数：进行技术分析
    
    Args:
        data: OHLCV数据
        symbol: 交易对符号
        
    Returns:
        TechnicalAnalyzer: 分析器实例
    """
    analyzer = TechnicalAnalyzer()
    analyzer.analyze_support_resistance(data)
    analyzer.generate_trading_signals(data, symbol)
    return analyzer