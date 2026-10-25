# -*- coding: utf-8 -*-
"""
币圈原生技术指标计算模块
包含Supertrend、Heikin-Ashi、PSAR、VWAP、Funding Rate、OI等指标
以及链上情绪指标和短打模板策略
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional



class CryptoIndicators:
    """币圈原生指标计算器"""

    @staticmethod
    def calculate_supertrend(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                           period: int = 10, multiplier: float = 2.0) -> Dict:
        """
        计算Supertrend指标（动态止损/开多空）

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: ATR周期，默认10
            multiplier: ATR乘数，1h用2.0，4h用3.0

        Returns:
            Dict: 包含supertrend值和趋势方向
        """
        # 计算ATR
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = pd.Series(true_range).rolling(window=period).mean().values

        # 计算HL2 (价格中位数)
        hl2 = (high + low) / 2

        # 计算上轨和下轨
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)

        supertrend = np.zeros_like(close)
        direction = np.zeros_like(close)

        for i in range(1, len(close)):
            # 上轨计算
            if upper_band[i] < upper_band[i-1] or close[i-1] > upper_band[i-1]:
                upper_band[i] = upper_band[i]
            else:
                upper_band[i] = upper_band[i-1]

            # 下轨计算
            if lower_band[i] > lower_band[i-1] or close[i-1] < lower_band[i-1]:
                lower_band[i] = lower_band[i]
            else:
                lower_band[i] = lower_band[i-1]

            # Supertrend计算
            if supertrend[i-1] == upper_band[i-1] and close[i] <= upper_band[i]:
                supertrend[i] = upper_band[i]
                direction[i] = -1  # 看跌
            elif supertrend[i-1] == upper_band[i-1] and close[i] > upper_band[i]:
                supertrend[i] = lower_band[i]
                direction[i] = 1  # 看涨
            elif supertrend[i-1] == lower_band[i] and close[i] >= lower_band[i]:
                supertrend[i] = lower_band[i]
                direction[i] = 1  # 看涨
            elif supertrend[i-1] == lower_band[i] and close[i] < lower_band[i]:
                supertrend[i] = upper_band[i]
                direction[i] = -1  # 看跌
            else:
                supertrend[i] = supertrend[i-1]
                direction[i] = direction[i-1]

        return {
            'supertrend': supertrend,
            'direction': direction,
            'atr': atr,
            'upper_band': upper_band,
            'lower_band': lower_band
        }

    @staticmethod
    def calculate_heikin_ashi(open_price: np.ndarray, high: np.ndarray,
                            low: np.ndarray, close: np.ndarray,
                            volume: Optional[np.ndarray] = None) -> Dict:
        """
        计算Heikin-Ashi平滑K线（过滤噪音）

        Args:
            open_price: 开盘价序列
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            volume: 可选的成交量序列

        Returns:
            Dict: 包含Heikin-Ashi K线数据
        """
        ha_open = np.zeros_like(close)
        ha_high = np.zeros_like(close)
        ha_low = np.zeros_like(close)
        ha_close = np.zeros_like(close)
        ha_volume = np.zeros_like(close) if volume is not None else None

        # 第一个K线的HA_open等于第一个K线的open
        ha_open[0] = open_price[0]

        for i in range(len(close)):
            # HA_close = (Open + High + Low + Close) / 4
            ha_close[i] = (open_price[i] + high[i] + low[i] + close[i]) / 4

            if i == 0:
                ha_open[i] = open_price[i]
            else:
                # HA_open = (前一个HA_open + 前一个HA_close) / 2
                ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2

            # HA_high = max(High, HA_open, HA_close)
            ha_high[i] = max(high[i], ha_open[i], ha_close[i])

            # HA_low = min(Low, HA_open, HA_close)
            ha_low[i] = min(low[i], ha_open[i], ha_close[i])

            if volume is not None:
                ha_volume[i] = volume[i]

        return {
            'ha_open': ha_open,
            'ha_high': ha_high,
            'ha_low': ha_low,
            'ha_close': ha_close,
            'ha_volume': ha_volume
        }

    @staticmethod
    def calculate_psar(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                      af_start: float = 0.008, af_max: float = 0.08) -> Dict:
        """
        计算PSAR指标（币圈优化版）

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            af_start: 初始加速因子，币圈常用0.008（原版0.02）
            af_max: 最大加速因子，币圈常用0.08（原版0.2）

        Returns:
            Dict: 包含PSAR值和趋势方向
        """
        length = len(close)
        psar = np.zeros(length)
        ep = np.zeros(length)  # 极值点
        af = np.zeros(length)  # 加速因子
        trend = np.zeros(length)  # 趋势方向，1为看涨，-1为看跌

        # 初始化
        psar[0] = low[0]
        ep[0] = high[0]
        af[0] = af_start
        trend[0] = 1

        for i in range(1, length):
            # 计算PSAR
            psar[i] = psar[i-1] + af[i-1] * (ep[i-1] - psar[i-1])

            # 趋势翻转检查
            if trend[i-1] == 1:  # 看涨趋势
                if low[i] <= psar[i]:
                    trend[i] = -1
                    psar[i] = ep[i-1]
                    af[i] = af_start
                    ep[i] = low[i]
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af[i] = min(af[i-1] + af_start, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
            else:  # 看跌趋势
                if high[i] >= psar[i]:
                    trend[i] = 1
                    psar[i] = ep[i-1]
                    af[i] = af_start
                    ep[i] = high[i]
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af[i] = min(af[i-1] + af_start, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]

        return {
            'psar': psar,
            'trend': trend,
            'ep': ep,
            'af': af
        }

    @staticmethod
    def calculate_vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                      volume: np.ndarray, reset_period: str = '1d') -> Dict:
        """
        计算VWAP（日内公平价）

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            volume: 成交量序列
            reset_period: 重置周期，'1d'为日线VWAP

        Returns:
            Dict: 包含VWAP值和标准差
        """
        # 计算典型价格
        typical_price = (high + low + close) / 3

        # 计算VWAP
        vwap = np.zeros_like(close)
        cum_volume = np.cumsum(volume)
        cum_pv = np.cumsum(typical_price * volume)

        for i in range(len(close)):
            if cum_volume[i] > 0:
                vwap[i] = cum_pv[i] / cum_volume[i]

        # 计算标准差（用于确定高价区和低价区）
        std_dev = np.zeros_like(close)
        for i in range(len(close)):
            if i >= 20:  # 使用20期计算标准差
                std_dev[i] = np.std(typical_price[i-20:i])
            else:
                std_dev[i] = np.std(typical_price[:i+1])

        return {
            'vwap': vwap,
            'upper_band': vwap + (2 * std_dev),
            'lower_band': vwap - (2 * std_dev),
            'std_dev': std_dev
        }

    @staticmethod
    def calculate_stoch_rsi(close: np.ndarray, period: int = 14, smooth_k: int = 3,
                          smooth_d: int = 3, overbought: int = 80,
                          oversold: int = 20) -> Dict:
        """
        计算StochRSI指标（比裸RSI早1根K）

        Args:
            close: 收盘价序列
            period: RSI周期，默认14
            smooth_k: %K平滑周期，默认3
            smooth_d: %D平滑周期，默认3
            overbought: 超买线，默认80
            oversold: 超卖线，默认20

        Returns:
            Dict: 包含StochRSI值和信号
        """
        # 计算RSI
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.mean(gain[:period])
        avg_loss = np.mean(loss[:period])

        rsi = np.zeros(len(close))
        for i in range(len(close)):
            if i >= period:
                avg_gain = ((avg_gain * (period-1)) + gain[i-1]) / period
                avg_loss = ((avg_loss * (period-1)) + loss[i-1]) / period

            rs = avg_gain / (avg_loss + 1e-10)
            rsi[i] = 100 - (100 / (1 + rs))

        # 计算StochRSI
        stoch_rsi = np.zeros_like(close)
        for i in range(len(close)):
            if i >= period:
                rsi_min = np.min(rsi[i-period:i+1])
                rsi_max = np.max(rsi[i-period:i+1])
                if rsi_max - rsi_min > 0:
                    stoch_rsi[i] = (rsi[i] - rsi_min) / (rsi_max - rsi_min) * 100
                else:
                    stoch_rsi[i] = 50

        # 平滑处理
        k_line = pd.Series(stoch_rsi).rolling(window=smooth_k).mean().values
        d_line = pd.Series(k_line).rolling(window=smooth_d).mean().values

        return {
            'stoch_rsi': stoch_rsi,
            'k_line': k_line,
            'd_line': d_line,
            'signal': np.where((k_line[:-1] < overbought) & (k_line[:-1] > oversold), 'neutral',
                         np.where((k_line[:-1] < oversold), 'oversold',
                             np.where((k_line[:-1] > overbought), 'overbought', 'neutral'))),
            'overbought': overbought,
            'oversold': oversold
        }

    @staticmethod
    def calculate_vw_macd(close: np.ndarray, volume: np.ndarray, fast: int = 8,
                         slow: int = 21, signal: int = 5) -> Dict:
        """
        计算VW-MACD（成交量加权MACD）

        Args:
            close: 收盘价序列
            volume: 成交量序列
            fast: 快线周期，默认8
            slow: 慢线周期，默认21
            signal: 信号线周期，默认5

        Returns:
            Dict: 包含VW-MACD值
        """
        # 计算成交量加权的EMA
        def vw_ema(prices, volumes, period):
            alpha = 2 / (period + 1)
            vw_ema = np.zeros_like(prices)
            pv_sum = prices[0] * volumes[0]
            vol_sum = volumes[0]
            vw_ema[0] = prices[0]

            for i in range(1, len(prices)):
                pv_sum = alpha * (prices[i] * volumes[i]) + (1 - alpha) * pv_sum
                vol_sum = alpha * volumes[i] + (1 - alpha) * vol_sum
                vw_ema[i] = pv_sum / (vol_sum + 1e-10)

            return vw_ema

        fast_vwema = vw_ema(close, volume, fast)
        slow_vwema = vw_ema(close, volume, slow)

        # 计算VW-MACD线
        vw_macd_line = fast_vwema - slow_vwema

        # 计算信号线
        signal_line = pd.Series(vw_macd_line).rolling(window=signal).mean().values

        # 计算柱状图
        histogram = vw_macd_line - signal_line

        return {
            'vw_macd': vw_macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def calculate_ema_ribbon(close: np.ndarray) -> Dict:
        """
        计算EMA Ribbon（指数均线带）

        Args:
            close: 收盘价序列

        Returns:
            Dict: 包含多条EMA线
        """
        periods = [8, 13, 21, 34, 55, 89]
        ema_values = {}

        for period in periods:
            alpha = 2 / (period + 1)
            ema = [close[0]]
            for price in close[1:]:
                ema.append(alpha * price + (1 - alpha) * ema[-1])
            ema_values[f'ema{period}'] = np.array(ema)

        # 判断多空排列
        ribbon_trend = np.zeros(len(close))
        for i in range(len(close)):
            ema_list = [ema_values[f'ema{p}'][i] for p in periods]
            if ema_list == sorted(ema_list):
                ribbon_trend[i] = 1  # 多头排列
            elif ema_list == sorted(ema_list, reverse=True):
                ribbon_trend[i] = -1  # 空头排列
            else:
                ribbon_trend[i] = 0  # 混乱

        return {
            **ema_values,
            'ribbon_trend': ribbon_trend
        }

    @staticmethod
    def analyze_short_template(open_price: np.ndarray, high: np.ndarray, low: np.ndarray,
                              close: np.ndarray, volume: np.ndarray) -> Dict:
        """
        币圈短打模板分析（1小时为例）

        进场逻辑：
        ① EMA Ribbon多头排列 + Supertrend多头
        ② StochRSI金叉出超卖区
        ③ 交易所净流入负值（提币）
        ④ Funding负值或低于-0.05%
        → 满足4中3即可做多；反向则做空

        Args:
            open_price: 开盘价序列
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            volume: 成交量序列

        Returns:
            Dict: 包含信号分析和交易建议
        """
        # 计算所有指标
        supertrend_result = CryptoIndicators.calculate_supertrend(high, low, close, 10, 2.0)
        stoch_rsi_result = CryptoIndicators.calculate_stoch_rsi(close)
        ema_ribbon_result = CryptoIndicators.calculate_ema_ribbon(close)

        latest_idx = -1
        signals = {
            'ema_ribbon_bullish': False,
            'supertrend_bullish': False,
            'stoch_rsi_bullish': False,
            'netflow_bullish': False,
            'funding_bullish': False
        }

        # 信号1: EMA Ribbon多头排列
        if ema_ribbon_result['ribbon_trend'][latest_idx] == 1:
            signals['ema_ribbon_bullish'] = True

        # 信号2: Supertrend看涨
        if supertrend_result['direction'][latest_idx] == 1:
            signals['supertrend_bullish'] = True

        # 信号3: StochRSI金叉（K线上穿D线且从超卖区）
        if (stoch_rsi_result['k_line'][latest_idx-1] <= stoch_rsi_result['oversold'] and
            stoch_rsi_result['k_line'][latest_idx] > stoch_rsi_result['d_line'][latest_idx]):
            signals['stoch_rsi_bullish'] = True

        # 信号4-5: 需要外部数据（暂时设为True以便测试）
        # 实际项目中应从交易所API获取
        signals['netflow_bullish'] = True  # 净流入负值（提币）
        signals['funding_bullish'] = True  # Funding负值

        # 计算综合信号
        bullish_signals = sum(signals.values())
        bearish_signals = 6 - bullish_signals  # 总信号数减去看涨信号数

        # 交易建议
        if bullish_signals >= 3:
            recommendation = 'STRONG_BUY'
        elif bullish_signals >= 2:
            recommendation = 'BUY'
        elif bearish_signals >= 3:
            recommendation = 'STRONG_SELL'
        elif bearish_signals >= 2:
            recommendation = 'SELL'
        else:
            recommendation = 'HOLD'

        return {
            'signals': signals,
            'bullish_count': bullish_signals,
            'bearish_count': bearish_signals,
            'recommendation': recommendation,
            'supertrend': {
                'value': supertrend_result['supertrend'][latest_idx],
                'direction': 'bullish' if supertrend_result['direction'][latest_idx] == 1 else 'bearish'
            },
            'stoch_rsi': {
                'k': round(stoch_rsi_result['k_line'][latest_idx], 2),
                'd': round(stoch_rsi_result['d_line'][latest_idx], 2)
            },
            'ema_ribbon_trend': 'bullish' if ema_ribbon_result['ribbon_trend'][latest_idx] == 1 else
                               'bearish' if ema_ribbon_result['ribbon_trend'][latest_idx] == -1 else 'neutral'
        }


# 链上情绪指标计算
class OnChainIndicators:
    """链上情绪指标计算器"""

    @staticmethod
    def analyze_exchange_netflow(netflow_data: List[Dict]) -> Dict:
        """
        分析交易所净流入

        Args:
            netflow_data: 净流入数据 [{'timestamp': ..., 'netflow': ...}, ...]

        Returns:
            Dict: 净流入分析和预警
        """
        if not netflow_data:
            return {'alert': 'neutral', 'interpretation': '无数据'}

        latest = netflow_data[-1]['netflow']
        avg_24h = np.mean([d['netflow'] for d in netflow_data[-24:]]) if len(netflow_data) >= 24 else latest

        alert = 'neutral'
        interpretation = ''

        if latest > 5000:  # 大额流入（单位：BTC）
            alert = 'bearish'
            interpretation = f'交易所净流入{latest:.0f} BTC，大额流入→砸盘预警'
        elif latest < -1000:  # 提币
            alert = 'bullish'
            interpretation = f'交易所净流出{abs(latest):.0f} BTC，提币出所→上涨信号'
        else:
            interpretation = f'交易所净流入{latest:.0f} BTC，正常范围'

        return {
            'current_netflow': latest,
            'avg_24h': avg_24h,
            'alert': alert,
            'interpretation': interpretation,
            'trend': 'increasing' if latest > avg_24h else 'decreasing'
        }

    @staticmethod
    def calculate_asopr(sopr_data: List[Dict]) -> Dict:
        """
        计算aSOPR（调整后已实现盈亏比）

        Args:
            sopr_data: SOPR数据 [{'timestamp': ..., 'sopr': ...}, ...]

        Returns:
            Dict: aSOPR分析和阈值
        """
        if not sopr_data:
            return {'alert': 'neutral', 'interpretation': '无数据'}

        latest = sopr_data[-1]['sopr']

        alert = 'neutral'
        interpretation = ''

        if latest > 1.05:
            alert = 'bearish'
            interpretation = f'aSOPR为{latest:.2f}，短线过热'
        elif latest < 0.97:
            alert = 'bullish'
            interpretation = f'aSOPR为{latest:.2f}，过热杀空'
        else:
            interpretation = f'aSOPR为{latest:.2f}，正常范围'

        return {
            'current_sopr': latest,
            'alert': alert,
            'interpretation': interpretation,
            'threshold_overbought': 1.05,
            'threshold_oversold': 0.97
        }

    @staticmethod
    def calculate_leverage_ratio(oi_data: List[Dict], exchange_balance: List[Dict]) -> Dict:
        """
        计算估算杠杆比率

        Args:
            oi_data: 未平仓量数据
            exchange_balance: 交易所余额数据

        Returns:
            Dict: 杠杆比率分析
        """
        if not oi_data or not exchange_balance:
            return {'alert': 'neutral', 'interpretation': '数据不足'}

        latest_oi = oi_data[-1]['oi']
        latest_balance = exchange_balance[-1]['balance']

        leverage_ratio = latest_oi / latest_balance if latest_balance > 0 else 0

        alert = 'neutral'
        interpretation = ''

        if leverage_ratio > 3.0:
            alert = 'danger'
            interpretation = f'杠杆比率{leverage_ratio:.2f}创新高，杠杆炸弹风险'
        elif leverage_ratio > 2.0:
            alert = 'warning'
            interpretation = f'杠杆比率{leverage_ratio:.2f}较高，注意风险'
        else:
            interpretation = f'杠杆比率{leverage_ratio:.2f}正常'

        return {
            'leverage_ratio': leverage_ratio,
            'alert': alert,
            'interpretation': interpretation,
            'warning_level': 2.0,
            'danger_level': 3.0
        }


# 期货市场指标
class FuturesIndicators:
    """期货市场指标计算器"""

    @staticmethod
    def analyze_funding_rate(funding_rates: List[Dict]) -> Dict:
        """
        分析资金费率

        Args:
            funding_rates: 资金费率历史数据 [{'timestamp': ..., 'rate': ...}, ...]

        Returns:
            Dict: 资金费率分析
        """
        if not funding_rates:
            return {'alert': 'neutral', 'interpretation': '无数据'}

        latest_rate = funding_rates[-1]['rate']
        avg_rate = np.mean([abs(d['rate']) for d in funding_rates[-8:]])  # 8小时平均

        alert = 'neutral'
        interpretation = ''

        if latest_rate > 0.002:  # 0.2%/8h
            alert = 'bearish'
            interpretation = f'资金费率{latest_rate*100:.2f}%/8h，极端高位警惕多头熄火'
        elif latest_rate < -0.002:  # -0.2%/8h
            alert = 'bullish'
            interpretation = f'资金费率{latest_rate*100:.2f}%/8h，空头陷阱机会'
        elif latest_rate > avg_rate * 1.5:
            alert = 'caution'
            interpretation = f'资金费率{latest_rate*100:.2f}%/8h，高于均值，注意风险'
        else:
            interpretation = f'资金费率{latest_rate*100:.2f}%/8h，正常范围'

        return {
            'current_rate': latest_rate,
            'rate_percentage': latest_rate * 100,
            'avg_rate': avg_rate * 100,
            'alert': alert,
            'interpretation': interpretation,
            'next_funding_time': funding_rates[-1]['next_time'] if 'next_time' in funding_rates[-1] else None
        }

    @staticmethod
    def analyze_open_interest(oi_data: List[Dict], price_data: List[float]) -> Dict:
        """
        分析未平仓量（OI）

        Args:
            oi_data: 未平仓量历史数据
            price_data: 对应的价格数据

        Returns:
            Dict: OI分析
        """
        if not oi_data or not price_data:
            return {'interpretation': '数据不足'}

        latest_oi = oi_data[-1]['oi']
        prev_oi = oi_data[-2]['oi'] if len(oi_data) > 1 else latest_oi
        latest_price = price_data[-1]
        prev_price = price_data[-2] if len(price_data) > 1 else latest_price

        oi_change = (latest_oi - prev_oi) / prev_oi * 100 if prev_oi > 0 else 0
        price_change = (latest_price - prev_price) / prev_price * 100 if prev_price > 0 else 0

        # 量价背离分析
        if oi_change > 0 and price_change > 0:
            interpretation = '价格↑+OI↑=健康多头'
            signal = 'bullish'
        elif oi_change > 0 and price_change < 0:
            interpretation = '价格↓+OI↑=空头减仓反弹'
            signal = 'bullish'
        elif oi_change < 0 and price_change > 0:
            interpretation = '价格↑+OI↓=多头减仓离场'
            signal = 'bearish'
        else:
            interpretation = '价格↓+OI↓=健康空头'
            signal = 'bearish'

        return {
            'current_oi': latest_oi,
            'oi_change': oi_change,
            'price_change': price_change,
            'signal': signal,
            'interpretation': interpretation
        }
