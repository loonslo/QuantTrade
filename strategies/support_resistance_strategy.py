"""
支撑阻力位交易策略
基于技术分析识别的支撑阻力位进行交易决策
"""

import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
import backtrader as bt

from analytics.technical_analysis import (
    TechnicalAnalyzer, SignalGenerator, ProfitCalculator,
    TradingSignal
)
from strategies.bt_strategies.strategies import BaseCryptoStrategy
from utils.core.logger_manager import get_logger


class SupportResistanceStrategy(BaseCryptoStrategy):
    """
    支撑阻力位交易策略
    
    策略逻辑：
    1. 识别关键支撑阻力位
    2. 计算突破概率和反弹概率
    3. 在高概率点位生成交易信号
    4. 动态管理止盈止损
    """
    
    params = (
        ('lookback_period', 100),       # 回看周期
        ('min_touches', 2),             # 最小触及次数
        ('min_confidence', 0.5),        # 最小置信度
        ('min_probability', 0.6),       # 最小触发概率
        ('risk_reward_ratio', 2.0),     # 风险收益比
        ('position_size_pct', 0.1),     # 仓位大小百分比
        ('max_positions', 3),           # 最大持仓数
        ('update_interval', 10),        # 更新间隔（K线数）
    )
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger('sr_strategy')
        
        # 初始化分析器
        self.analyzer = TechnicalAnalyzer(
            lookback_period=self.p.lookback_period,
            min_touches=self.p.min_touches
        )
        
        self.signal_generator = SignalGenerator(
            risk_reward_ratio=self.p.risk_reward_ratio
        )
        
        self.profit_calculator = ProfitCalculator()
        
        # 策略状态
        self.levels = []
        self.active_signals = []
        self.last_update = 0
        self.position_count = 0
        
        # 数据缓存
        self.price_data = []
        
    def next(self):
        """策略主逻辑"""
        try:
            # 收集价格数据
            self._collect_data()
            
            # 定期更新分析
            if len(self.price_data) - self.last_update >= self.p.update_interval:
                self._update_analysis()
                self.last_update = len(self.price_data)
            
            # 检查信号触发
            self._check_signals()
            
            # 更新持仓
            self._update_positions()
            
            # 记录状态
            self._log_status()
            
        except Exception as e:
            self.logger.error(f"策略执行失败: {e}")
    
    def _collect_data(self):
        """收集价格数据"""
        current_bar = {
            'datetime': self.datas[0].datetime.datetime(0),
            'open': self.data.open[0],
            'high': self.data.high[0],
            'low': self.data.low[0],
            'close': self.data.close[0],
            'volume': self.data.volume[0]
        }
        
        self.price_data.append(current_bar)
        
        # 保持数据长度
        if len(self.price_data) > self.p.lookback_period * 2:
            self.price_data = self.price_data[-self.p.lookback_period * 2:]
    
    def _update_analysis(self):
        """更新技术分析"""
        try:
            if len(self.price_data) < self.p.lookback_period:
                return
            
            # 转换为DataFrame
            df = pd.DataFrame(self.price_data)
            df.set_index('datetime', inplace=True)
            
            # 识别支撑阻力位
            self.levels = self.analyzer.identify_support_resistance(df)
            
            # 生成交易信号
            new_signals = self.signal_generator.generate_signals(
                symbol='BTC/USDT',  # 可以从数据中获取
                df=df,
                levels=self.levels
            )
            
            # 更新活跃信号
            self._update_active_signals(new_signals)
            
            self.logger.info(f"更新分析: {len(self.levels)} 个关键位, {len(self.active_signals)} 个活跃信号")
            
        except Exception as e:
            self.logger.error(f"更新分析失败: {e}")
    
    def _update_active_signals(self, new_signals: List[TradingSignal]):
        """更新活跃信号列表"""
        current_time = datetime.now()
        
        # 移除过期信号（超过1小时）
        self.active_signals = [
            s for s in self.active_signals 
            if (current_time - s.timestamp).total_seconds() < 3600
        ]
        
        # 添加新信号
        for signal in new_signals:
            # 检查是否已存在相似信号
            similar_exists = any(
                abs(s.entry_price - signal.entry_price) / signal.entry_price < 0.01
                and s.signal_type == signal.signal_type
                for s in self.active_signals
            )
            
            if not similar_exists:
                self.active_signals.append(signal)
        
        # 按置信度排序
        self.active_signals.sort(key=lambda x: x.confidence * x.trigger_probability, reverse=True)
        
        # 保持最多10个信号
        self.active_signals = self.active_signals[:10]
    
    def _check_signals(self):
        """检查信号触发"""
        if not self.active_signals or self.position_count >= self.p.max_positions:
            return
        
        current_price = self.data.close[0]
        cash = self.broker.getcash()
        
        for signal in self.active_signals[:]:
            # 检查置信度和概率阈值
            if (signal.confidence < self.p.min_confidence or 
                signal.trigger_probability < self.p.min_probability):
                continue
            
            # 检查触发条件
            triggered = False
            if signal.signal_type == 'BUY':
                triggered = current_price >= signal.entry_price
            else:
                triggered = current_price <= signal.entry_price
            
            if triggered:
                # 计算仓位大小
                position_value = cash * self.p.position_size_pct
                position_size = position_value / current_price
                
                if position_size > 0:
                    # 执行交易
                    if signal.signal_type == 'BUY':
                        order = self.buy(size=position_size)
                    else:
                        order = self.sell(size=position_size)
                    
                    if order:
                        # 记录交易
                        self.profit_calculator.execute_signal(signal, current_price, position_size)
                        self.position_count += 1
                        
                        # 移除已执行的信号
                        self.active_signals.remove(signal)
                        
                        self.logger.info(f"执行信号: {signal.signal_type} @ {current_price:.2f}")
                        break
    
    def _update_positions(self):
        """更新持仓状态"""
        if not hasattr(self, 'profit_calculator'):
            return
        
        current_price = self.data.close[0]
        current_prices = {'BTC/USDT': current_price}  # 可扩展为多币种
        
        # 更新盈亏状态
        updates = self.profit_calculator.update_positions(current_prices)
        
        for update in updates:
            if update['action'] in ['stop_loss', 'take_profit']:
                # 平仓
                if self.position.size > 0:
                    self.close()
                elif self.position.size < 0:
                    self.close()
                
                self.position_count = max(0, self.position_count - 1)
                
                self.logger.info(f"平仓: {update['action']}, PnL: {update['pnl']:.2f}")
    
    def _log_status(self):
        """记录策略状态"""
        if len(self.price_data) % 50 == 0:  # 每50个K线记录一次
            current_price = self.data.close[0]
            cash = self.broker.getcash()
            total_value = self.position.size * current_price + cash
            
            # 获取表现摘要
            performance = self.profit_calculator.get_performance_summary()
            
            self.logger.info(
                f"策略状态 - 价格: {current_price:.2f}, "
                f"持仓: {self.position.size:.6f}, "
                f"现金: {cash:.2f}, "
                f"总值: {total_value:.2f}, "
                f"活跃信号: {len(self.active_signals)}, "
                f"关键位: {len(self.levels)}, "
                f"总PnL: {performance.get('total_pnl', 0):.2f}"
            )
    
    def get_analysis_report(self) -> Dict[str, Any]:
        """获取分析报告"""
        current_price = self.data.close[0] if hasattr(self, 'data') else 0
        
        # 支撑阻力位信息
        levels_info = []
        for level in self.levels[:10]:  # 前10个最重要的位
            levels_info.append({
                'price': level.price,
                'type': level.level_type,
                'strength': level.strength,
                'confidence': level.confidence,
                'breakout_probability': level.breakout_probability,
                'distance_pct': abs(level.price - current_price) / current_price * 100
            })
        
        # 活跃信号信息
        signals_info = []
        for signal in self.active_signals[:5]:  # 前5个信号
            signals_info.append({
                'type': signal.signal_type,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'confidence': signal.confidence,
                'trigger_probability': signal.trigger_probability,
                'risk_reward_ratio': signal.risk_reward_ratio,
                'reasoning': signal.reasoning
            })
        
        # 交易表现
        performance = self.profit_calculator.get_performance_summary()
        
        return {
            'current_price': current_price,
            'levels': levels_info,
            'active_signals': signals_info,
            'performance': performance,
            'strategy_status': {
                'position_count': self.position_count,
                'max_positions': self.p.max_positions,
                'data_points': len(self.price_data),
                'last_update': self.last_update
            }
        }
    
    def predict_next_signal(self):
        """预测下一个信号"""
        if not self.active_signals:
            return None, None
        
        # 返回最高优先级的信号
        best_signal = self.active_signals[0]
        return best_signal.signal_type, best_signal.entry_price


class SupportResistanceBacktestStrategy(bt.Strategy):
    """
    支撑阻力位回测策略（Backtrader版本）
    """
    
    params = (
        ('lookback_period', 100),
        ('min_confidence', 0.5),
        ('min_probability', 0.6),
        ('risk_reward_ratio', 2.0),
        ('position_size_pct', 0.1),
    )
    
    def __init__(self):
        self.logger = get_logger('sr_backtest')
        
        # 初始化分析器
        self.analyzer = TechnicalAnalyzer(
            lookback_period=self.p.lookback_period
        )
        
        self.signal_generator = SignalGenerator(
            risk_reward_ratio=self.p.risk_reward_ratio
        )
        
        # 数据缓存
        self.price_data = []
        self.levels = []
        self.last_analysis = 0
        
    def next(self):
        """回测主逻辑"""
        # 收集数据
        current_bar = {
            'datetime': self.datas[0].datetime.datetime(0),
            'open': self.data.open[0],
            'high': self.data.high[0],
            'low': self.data.low[0],
            'close': self.data.close[0],
            'volume': self.data.volume[0]
        }
        self.price_data.append(current_bar)
        
        # 定期分析
        if len(self.price_data) >= self.p.lookback_period and len(self.price_data) % 20 == 0:
            self._perform_analysis()
        
        # 检查交易机会
        self._check_trading_opportunities()
    
    def _perform_analysis(self):
        """执行技术分析"""
        try:
            df = pd.DataFrame(self.price_data[-self.p.lookback_period:])
            df.set_index('datetime', inplace=True)
            
            # 识别支撑阻力位
            self.levels = self.analyzer.identify_support_resistance(df)
            
            self.logger.info(f"识别到 {len(self.levels)} 个关键位")
            
        except Exception as e:
            self.logger.error(f"技术分析失败: {e}")
    
    def _check_trading_opportunities(self):
        """检查交易机会"""
        if not self.levels or self.position:
            return
        
        current_price = self.data.close[0]
        
        # 寻找交易机会
        for level in self.levels:
            if (level.confidence < self.p.min_confidence or 
                level.breakout_probability < self.p.min_probability):
                continue
            
            distance = abs(level.price - current_price) / current_price
            
            # 突破交易
            if distance < 0.005:  # 0.5%以内
                if level.level_type == 'resistance' and current_price > level.price:
                    # 突破阻力位，买入
                    size = self._calculate_position_size()
                    if size > 0:
                        self.buy(size=size)
                        self.logger.info(f"突破买入 @ {current_price:.2f}")
                        break
                
                elif level.level_type == 'support' and current_price < level.price:
                    # 跌破支撑位，卖出
                    size = self._calculate_position_size()
                    if size > 0:
                        self.sell(size=size)
                        self.logger.info(f"跌破卖出 @ {current_price:.2f}")
                        break
    
    def _calculate_position_size(self):
        """计算仓位大小"""
        cash = self.broker.getcash()
        current_price = self.data.close[0]
        
        position_value = cash * self.p.position_size_pct
        return position_value / current_price
    
    def notify_order(self, order):
        """订单通知"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.logger.info(f"买入成交: {order.executed.price:.2f}")
            else:
                self.logger.info(f"卖出成交: {order.executed.price:.2f}")