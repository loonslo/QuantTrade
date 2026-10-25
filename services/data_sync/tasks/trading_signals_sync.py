# -*- coding: utf-8 -*-
"""
交易信号同步任务（完整版）
基于technical_indicators和support_resistance数据生成交易信号
"""
from typing import Optional, List, Type, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..base_service import DataSyncService
from utils.core.logger_manager import get_logger
from data.models.market_data.trading_signals_model import (
    TradingSignal15m,
    TradingSignal4h,
    TradingSignal1d
)
from data.models.market_data.indicators_model import (
    TechnicalIndicators15m,
    TechnicalIndicators4h,
    TechnicalIndicators1d
)
from data.models.market_data.support_resistance_model import (
    SupportResistance4h,
    SupportResistance1d
)
from services.orm.trading_signals_orm import get_trading_signals_service_orm
from services.orm.support_resistance_orm import get_support_resistance_service_orm
from services.strategy.strategy_manager import get_strategy_manager

class TradingSignalsSyncTask(DataSyncService):
    SUPPORTED_TIMEFRAMES = ["15m", "4h", "1d"]

    def __init__(self):
        super().__init__('trading_signals_sync')

    async def _execute_sync(self) -> bool:
        """
        执行同步任务的抽象方法实现
        
        Returns:
            bool: 同步是否成功
        """
        try:
            self.logger.info("开始执行交易信号同步任务")
            
            # 同步多个时间周期的信号
            timeframes = ["15m", "4h", "1d"]
            symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
            
            success_count = 0
            total_tasks = len(timeframes) * len(symbols)
            
            for timeframe in timeframes:
                for symbol in symbols:
                    ok = await self.compute_and_sync_trading_signals(timeframe, symbol)
                    if ok:
                        success_count += 1
            
            self.logger.info(f"交易信号同步完成: 成功 {success_count}/{total_tasks}")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"执行交易信号同步失败: {e}", exc_info=True)
            return False

    def get_task_config(self) -> Dict[str, Any]:
        """
        获取任务配置的抽象方法实现
        
        Returns:
            Dict[str, Any]: 任务配置信息
        """
        return {
            'task_name': 'trading_signals_sync',
            'description': '交易信号同步任务',
            'schedule_interval': 300,
            'max_retries': 3,
            'retry_delay': 60,
            'batch_size': 10,
            'enabled': True,
            'timeout': 600,
            'timeframes': self.SUPPORTED_TIMEFRAMES,
            'symbols': ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
        }

        self.logger = get_logger('trading_signals_sync')
        self.trading_signals_orm = get_trading_signals_service_orm()
        self.strategy_manager = get_strategy_manager()

    def _get_indicators_model_by_timeframe(self, timeframe: str) -> Optional[Type]:
        mapping = {
            "15m": TechnicalIndicators15m,
            "4h": TechnicalIndicators4h,
            "1d": TechnicalIndicators1d,
        }
        return mapping.get(timeframe)

    def _get_sr_model_by_timeframe(self, timeframe: str) -> Optional[Type]:
        mapping = {
            "4h": SupportResistance4h,
            "1d": SupportResistance1d,
        }
        return mapping.get(timeframe)

    def _get_trading_signal_model_by_timeframe(self, timeframe: str) -> Optional[Type]:
        mapping = {
            "15m": TradingSignal15m,
            "4h": TradingSignal4h,
            "1d": TradingSignal1d,
        }
        return mapping.get(timeframe)

    async def compute_and_sync_trading_signals(self, timeframe: str, symbol: str) -> bool:
        """计算并同步单个交易对的交易信号"""
        try:
            self.logger.info(f"开始计算交易信号: {symbol} {timeframe}")

            # 1. 获取technical_indicators数据（最近50条）
            indicators_data = self._get_technical_indicators_data(timeframe, symbol, limit=50)
            if not indicators_data or len(indicators_data) < 20:
                self.logger.warning(f"技术指标数据不足: {symbol} {timeframe}, 数量: {len(indicators_data) if indicators_data else 0}")
                return False

            # 2. 获取支撑阻力位数据
            sr_timeframe = "4h" if timeframe in ["15m", "4h"] else "1d"
            sr_data = self._get_support_resistance_data(sr_timeframe, symbol)
            if not sr_data:
                self.logger.warning(f"支撑阻力位数据不存在: {symbol} {sr_timeframe}")

            # 3. 获取最新K线数据（最近20条）
            kline_data = self._get_kline_data(timeframe, symbol, limit=20)
            if not kline_data or len(kline_data) < 10:
                self.logger.warning(f"K线数据不足: {symbol} {timeframe}, 数量: {len(kline_data) if kline_data else 0}")
                return False

            # 4. 生成交易信号
            signals = []
            signals.extend(self._generate_rsi_signals(indicators_data, kline_data, sr_data, symbol, timeframe))
            signals.extend(self._generate_macd_signals(indicators_data, kline_data, symbol, timeframe))
            signals.extend(self._generate_trend_reversal_signals(indicators_data, kline_data, symbol, timeframe))
            signals.extend(self._generate_breakout_signals(indicators_data, kline_data, sr_data, symbol, timeframe))

            # 5. 去重（基于相同时间、相同策略的信号）
            signals = self._deduplicate_signals(signals)

            # 6. 保存信号
            if signals:
                ok = self.trading_signals_orm.save_signals(timeframe, signals)
                if ok:
                    self.logger.info(f"成功保存交易信号: {symbol} {timeframe}, 数量: {len(signals)}")
                    return True
                else:
                    self.logger.error(f"保存交易信号失败: {symbol} {timeframe}")
                    return False
            else:
                self.logger.info(f"无新交易信号: {symbol} {timeframe}")
                return True

        except Exception as e:
            self.logger.error(f"计算交易信号失败: {symbol} {timeframe}, 错误: {e}", exc_info=True)
            return False

    def _get_technical_indicators_data(self, timeframe: str, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取技术指标数据"""
        try:
            model_class = self._get_indicators_model_by_timeframe(timeframe)
            if not model_class:
                return []

            with self.get_db_session(auto_commit=False) as session:
                results = session.query(model_class).filter(
                    model_class.symbol == symbol,
                    model_class.is_valid == True
                ).order_by(model_class.timestamp.desc()).limit(limit).all()

                data = []
                for row in reversed(results):
                    data.append(row.to_dict())

                return data
        except Exception as e:
            self.logger.error(f"获取技术指标数据失败: {e}")
            return []

    def _get_support_resistance_data(self, timeframe: str, symbol: str) -> List[Dict[str, Any]]:
        """获取支撑阻力位数据"""
        try:
            model_class = self._get_sr_model_by_timeframe(timeframe)
            if not model_class:
                return []

            with self.get_db_session(auto_commit=False) as session:
                results = session.query(model_class).filter(
                    model_class.symbol == symbol
                ).order_by(model_class.strength_score.desc()).limit(20).all()

                data = []
                for row in results:
                    data.append({
                        'symbol': row.symbol,
                        'timeframe': row.timeframe,
                        'price_level': row.price_level,
                        'level_type': row.level_type,
                        'strength_score': row.strength_score,
                        'touch_count': row.touch_count,
                        'bounce_count': row.bounce_count,
                        'volume_at_level': row.volume_at_level,
                        'distance_from_current_pct': row.distance_from_current_pct
                    })

                return data
        except Exception as e:
            self.logger.error(f"获取支撑阻力位数据失败: {e}")
            return []

    def _get_kline_data(self, timeframe: str, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            # 获取对应的K线表名
            table_name = f"kline_data_{timeframe}"

            with self.get_db_session(auto_commit=False) as session:
                # 使用原生SQL查询
                query = f"""
                    SELECT symbol, timeframe, open_time, close_time, open, high, low, close, volume
                    FROM {table_name}
                    WHERE symbol = :symbol
                    ORDER BY close_time DESC
                    LIMIT :limit
                """
                result = session.execute(query, {"symbol": symbol, "limit": limit})

                data = []
                for row in reversed(result.fetchall()):
                    data.append({
                        'symbol': row[0],
                        'timeframe': row[1],
                        'open_time': row[2],
                        'close_time': row[3],
                        'open': float(row[4]),
                        'high': float(row[5]),
                        'low': float(row[6]),
                        'close': float(row[7]),
                        'volume': float(row[8])
                    })

                return data
        except Exception as e:
            self.logger.error(f"获取K线数据失败: {e}")
            return []

    def _get_strategy_config(self, strategy_id: str) -> Dict[str, Any]:
        """从策略表获取策略配置"""
        config = self.strategy_manager.get_strategy_config_for_signal(strategy_id)
        if config:
            self.logger.debug(f"从策略表获取配置: {strategy_id}")
            return config
        else:
            self.logger.warning(f"策略表未找到配置，使用默认值: {strategy_id}")
            # 返回默认配置
            if strategy_id == 'rsi_tech_v1':
                return {
                    'strategy_id': 'rsi_tech_v1',
                    'parameters': {
                        'rsi_period': 14,
                        'oversold_threshold': 30,
                        'overbought_threshold': 70,
                        'support_tolerance_pct': 2.0,
                        'resistance_tolerance_pct': 2.0
                    }
                }
            elif strategy_id == 'macd_tech_v1':
                return {
                    'strategy_id': 'macd_tech_v1',
                    'parameters': {
                        'fast_period': 12,
                        'slow_period': 26,
                        'signal_period': 9,
                        'trend_verification': True
                    }
                }
            elif strategy_id == 'trend_tech_v1':
                return {
                    'strategy_id': 'trend_tech_v1',
                    'parameters': {
                        'trend_lookback': 5,
                        'min_trend_strength': 0.5,
                        'confirmation_required': True
                    }
                }
            elif strategy_id == 'breakout_tech_v1':
                return {
                    'strategy_id': 'breakout_tech_v1',
                    'parameters': {
                        'breakout_threshold_pct': 1.0,
                        'volume_confirmation': True,
                        'volume_threshold': 1.2,
                        'min_strength_score': 60
                    }
                }
            else:
                return {
                    'strategy_id': strategy_id,
                    'parameters': {}
                }

    def _generate_rsi_signals(self, indicators_data: List[Dict], kline_data: List[Dict],
                             sr_data: List[Dict], symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """生成RSI交易信号"""
        signals = []

        if len(indicators_data) < 2:
            return signals

        # 获取策略配置
        strategy_config = self._get_strategy_config('rsi_tech_v1')
        params = strategy_config.get('parameters', {})
        oversold_threshold = params.get('oversold_threshold', 30)
        overbought_threshold = params.get('overbought_threshold', 70)
        support_tolerance = params.get('support_tolerance_pct', 2.0)
        resistance_tolerance = params.get('resistance_tolerance_pct', 2.0)

        current = indicators_data[-1]
        previous = indicators_data[-2]

        current_price = kline_data[-1]['close'] if kline_data else current.get('close', 0)
        current_rsi = current.get('rsi14')
        prev_rsi = previous.get('rsi14')

        if current_rsi is None or prev_rsi is None:
            return signals

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # RSI超卖反弹信号（买入）
        if prev_rsi < oversold_threshold and current_rsi >= oversold_threshold:
            # 检查是否接近支撑位
            support_level = self._find_nearest_level(sr_data, current_price, 'support', tolerance_pct=support_tolerance)

            confidence = min(1.0, (50 - prev_rsi) / 20 * 0.6 + (current_rsi - oversold_threshold) / 20 * 0.4)
            if support_level:
                confidence += 0.2  # 支撑位加分

            stop_loss = support_level['price_level'] * 0.98 if support_level else current_price * 0.95
            take_profit = [current_price * 1.03, current_price * 1.05]

            # 将策略配置转换为JSON字符串
            import json
            strategy_config_json = json.dumps(strategy_config)

            signals.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'signal_time': current_time,
                'signal_type': 'buy',
                'strategy_name': 'rsi_oversold_bounce',
                'strategy_source': 'system',
                'strategy_category': 'technical',
                'strategy_version': '1.0',
                'strategy_id': 'rsi_tech_v1',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': str(take_profit),
                'confidence_score': min(1.0, confidence),
                'trend_direction': current.get('trend_direction', 'neutral'),
                'market_volatility': current.get('volatility_7d', 0) or 0.1,
                'strategy_params': json.dumps(params),
                'strategy_config': strategy_config_json
            })

        # RSI超买回落信号（卖出）
        elif prev_rsi > 70 and current_rsi <= 70:
            # 检查是否接近阻力位
            resistance_level = self._find_nearest_level(sr_data, current_price, 'resistance', tolerance_pct=2.0)

            confidence = min(1.0, (prev_rsi - 50) / 20 * 0.6 + (70 - current_rsi) / 20 * 0.4)
            if resistance_level:
                confidence += 0.2  # 阻力位加分

            stop_loss = resistance_level['price_level'] * 1.02 if resistance_level else current_price * 1.05
            take_profit = [current_price * 0.97, current_price * 0.95]

            signals.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'signal_time': current_time,
                'signal_type': 'sell',
                'strategy_name': 'rsi_overbought_decline',
                'strategy_source': 'system',
                'strategy_category': 'technical',
                'strategy_version': '1.0',
                'strategy_id': 'rsi_tech_v1',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': str(take_profit),
                'confidence_score': min(1.0, confidence),
                'trend_direction': current.get('trend_direction', 'neutral'),
                'market_volatility': current.get('volatility_7d', 0) or 0.1
            })

        return signals

    def _generate_macd_signals(self, indicators_data: List[Dict], kline_data: List[Dict],
                              symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """生成MACD交易信号"""
        signals = []

        if len(indicators_data) < 2:
            return signals

        current = indicators_data[-1]
        previous = indicators_data[-2]

        current_price = kline_data[-1]['close'] if kline_data else current.get('close', 0)
        current_macd = current.get('macd_line')
        current_signal = current.get('macd_signal')
        prev_macd = previous.get('macd_line')
        prev_signal = previous.get('macd_signal')

        if current_macd is None or current_signal is None or prev_macd is None or prev_signal is None:
            return signals

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        trend = current.get('trend_direction', 'neutral')

        # MACD金叉（买入）
        if prev_macd <= prev_signal and current_macd > current_signal:
            confidence = min(1.0, (current_macd - current_signal) * 2 + 0.5)

            # 趋势方向验证
            if trend == 'up':
                confidence += 0.2
            elif trend == 'down':
                confidence -= 0.2

            stop_loss = current_price * 0.97
            take_profit = [current_price * 1.04, current_price * 1.07]

            signals.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'signal_time': current_time,
                'signal_type': 'buy',
                'strategy_name': 'macd_golden_cross',
                'strategy_source': 'system',
                'strategy_category': 'technical',
                'strategy_version': '1.0',
                'strategy_id': 'macd_tech_v1',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': str(take_profit),
                'confidence_score': min(1.0, max(0.3, confidence)),
                'trend_direction': trend,
                'market_volatility': current.get('volatility_7d', 0) or 0.1
            })

        # MACD死叉（卖出）
        elif prev_macd >= prev_signal and current_macd < current_signal:
            confidence = min(1.0, (prev_signal - prev_macd) * 2 + 0.5)

            # 趋势方向验证
            if trend == 'down':
                confidence += 0.2
            elif trend == 'up':
                confidence -= 0.2

            stop_loss = current_price * 1.03
            take_profit = [current_price * 0.96, current_price * 0.93]

            signals.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'signal_time': current_time,
                'signal_type': 'sell',
                'strategy_name': 'macd_death_cross',
                'strategy_source': 'system',
                'strategy_category': 'technical',
                'strategy_version': '1.0',
                'strategy_id': 'macd_tech_v1',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': str(take_profit),
                'confidence_score': min(1.0, max(0.3, confidence)),
                'trend_direction': trend,
                'market_volatility': current.get('volatility_7d', 0) or 0.1
            })

        return signals

    def _generate_trend_reversal_signals(self, indicators_data: List[Dict], kline_data: List[Dict],
                                         symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """生成趋势反转信号"""
        signals = []

        if len(indicators_data) < 5:
            return signals

        current = indicators_data[-1]
        previous = indicators_data[-4]  # 3根K线前的数据

        current_price = kline_data[-1]['close'] if kline_data else current.get('close', 0)
        current_trend = current.get('trend_direction')
        prev_trend = previous.get('trend_direction')

        if current_trend is None or prev_trend is None or current_trend == prev_trend:
            return signals

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 趋势反转确认
        trend_change_strength = abs(current.get('trend_strength_score', 0) - previous.get('trend_strength_score', 0))
        confidence = min(1.0, trend_change_strength / 50 + 0.5)

        if current_trend == 'up' and prev_trend in ['down', 'sideways']:
            # 牛市反转
            stop_loss = current_price * 0.95
            take_profit = [current_price * 1.05, current_price * 1.10]

            signals.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'signal_time': current_time,
                'signal_type': 'buy',
                'strategy_name': 'trend_reversal_bullish',
                'strategy_source': 'system',
                'strategy_category': 'technical',
                'strategy_version': '1.0',
                'strategy_id': 'trend_tech_v1',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': str(take_profit),
                'confidence_score': min(1.0, confidence),
                'trend_direction': current_trend,
                'market_volatility': current.get('volatility_7d', 0) or 0.1
            })

        elif current_trend == 'down' and prev_trend in ['up', 'sideways']:
            # 熊市反转
            stop_loss = current_price * 1.05
            take_profit = [current_price * 0.95, current_price * 0.90]

            signals.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'signal_time': current_time,
                'signal_type': 'sell',
                'strategy_name': 'trend_reversal_bearish',
                'strategy_source': 'system',
                'strategy_category': 'technical',
                'strategy_version': '1.0',
                'strategy_id': 'trend_tech_v1',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': str(take_profit),
                'confidence_score': min(1.0, confidence),
                'trend_direction': current_trend,
                'market_volatility': current.get('volatility_7d', 0) or 0.1
            })

        return signals

    def _generate_breakout_signals(self, indicators_data: List[Dict], kline_data: List[Dict],
                                   sr_data: List[Dict], symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """生成突破信号"""
        signals = []

        if not sr_data or len(kline_data) < 5:
            return signals

        current = indicators_data[-1]
        current_price = kline_data[-1]['close'] if kline_data else current.get('close', 0)
        prev_4_high = max([k['high'] for k in kline_data[-5:-1]])
        prev_4_low = min([k['low'] for k in kline_data[-5:-1]])

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 突破阻力位
        strong_resistances = [sr for sr in sr_data if sr['level_type'] == 'resistance' and sr['strength_score'] > 60]
        for resistance in strong_resistances[:3]:  # 取前3个最强阻力位
            if current_price > resistance['price_level'] * 1.01 and prev_4_high <= resistance['price_level']:
                # 成交量确认
                avg_volume = np.mean([k['volume'] for k in kline_data[-5:]])
                current_volume = kline_data[-1]['volume'] if kline_data else 0

                confidence = min(1.0, resistance['strength_score'] / 100 * 0.5)
                if current_volume > avg_volume * 1.2:
                    confidence += 0.3  # 成交量确认加分

                stop_loss = resistance['price_level'] * 0.99
                take_profit = [resistance['price_level'] * 1.03, resistance['price_level'] * 1.05]

                signals.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'signal_time': current_time,
                    'signal_type': 'buy',
                    'strategy_name': 'resistance_breakout',
                    'strategy_source': 'system',
                    'strategy_category': 'technical',
                    'strategy_version': '1.0',
                    'strategy_id': 'breakout_tech_v1',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': str(take_profit),
                    'confidence_score': min(1.0, confidence),
                    'trend_direction': current.get('trend_direction', 'neutral'),
                    'market_volatility': current.get('volatility_7d', 0) or 0.1
                })
                break  # 只取第一个符合条件的

        # 跌破支撑位
        strong_supports = [sr for sr in sr_data if sr['level_type'] == 'support' and sr['strength_score'] > 60]
        for support in strong_supports[:3]:  # 取前3个最强支撑位
            if current_price < support['price_level'] * 0.99 and prev_4_low >= support['price_level']:
                # 成交量确认
                avg_volume = np.mean([k['volume'] for k in kline_data[-5:]])
                current_volume = kline_data[-1]['volume'] if kline_data else 0

                confidence = min(1.0, support['strength_score'] / 100 * 0.5)
                if current_volume > avg_volume * 1.2:
                    confidence += 0.3  # 成交量确认加分

                stop_loss = support['price_level'] * 1.01
                take_profit = [support['price_level'] * 0.97, support['price_level'] * 0.95]

                signals.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'signal_time': current_time,
                    'signal_type': 'sell',
                    'strategy_name': 'support_breakdown',
                    'strategy_source': 'system',
                    'strategy_category': 'technical',
                    'strategy_version': '1.0',
                    'strategy_id': 'breakout_tech_v1',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': str(take_profit),
                    'confidence_score': min(1.0, confidence),
                    'trend_direction': current.get('trend_direction', 'neutral'),
                    'market_volatility': current.get('volatility_7d', 0) or 0.1
                })
                break  # 只取第一个符合条件的

        return signals

    def _find_nearest_level(self, sr_data: List[Dict], current_price: float,
                           level_type: str, tolerance_pct: float = 2.0) -> Optional[Dict]:
        """查找最近的支撑/阻力位"""
        if not sr_data:
            return None

        levels = [sr for sr in sr_data if sr['level_type'] == level_type]
        if not levels:
            return None

        # 按距离排序
        levels.sort(key=lambda x: abs(x['price_level'] - current_price) / current_price)

        # 找到在容差范围内的最近级别
        for level in levels:
            distance_pct = abs(level['price_level'] - current_price) / current_price * 100
            if distance_pct <= tolerance_pct:
                return level

        return None

    def _deduplicate_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重信号（基于相同时间、相同策略）"""
        if not signals:
            return []

        seen = set()
        unique_signals = []

        for signal in signals:
            key = (signal['signal_time'], signal['strategy_name'], signal['symbol'])
            if key not in seen:
                seen.add(key)
                unique_signals.append(signal)

        return unique_signals

    async def manual_sync_trading_signals(self, timeframe: str, symbols: Optional[List[str]] = None) -> bool:
        """手动触发交易信号同步（支持多交易对）"""
        try:
            if timeframe not in self.SUPPORTED_TIMEFRAMES:
                self.logger.error(f"不支持的时间周期: {timeframe}")
                return False

            # 默认交易对
            if symbols is None:
                symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
                          "SOLUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT"]

            self.logger.info(f"开始同步交易信号: timeframe={timeframe}, symbols={symbols}")

            success_count = 0
            for symbol in symbols:
                ok = await self.compute_and_sync_trading_signals(timeframe, symbol)
                if ok:
                    success_count += 1

            total = len(symbols)
            self.logger.info(f"交易信号同步完成: 成功 {success_count}/{total}")

            return success_count > 0

        except Exception as e:
            self.logger.error(f"同步交易信号失败: {e}", exc_info=True)
            return False

_ts_sync_task: Optional[TradingSignalsSyncTask] = None

def get_trading_signals_sync_task() -> TradingSignalsSyncTask:
    global _ts_sync_task
    if _ts_sync_task is None:
        _ts_sync_task = TradingSignalsSyncTask()
    return _ts_sync_task
