# -*- coding: utf-8 -*-
"""
K线数据同步服务
提供K线数据同步功能
"""

from typing import Optional, List, Dict, Tuple
from datetime import datetime
import asyncio
import pandas as pd

from utils.core.logger_manager import get_logger
from api.utils.task_utils import task_wrapper, record_task_execution
from utils.core.singleton import get_binance_provider
from data.orm_services import get_kline_data_service
from services.data_sync.constants import (
    DEFAULT_SYMBOLS, SUPPORTED_TIMEFRAMES, TIMEFRAME_LIMITS, 
    MAX_MANUAL_LIMITS, FUTURES_INDICATOR_TIMEFRAMES, DATA_SOURCE_BINANCE
)

class KlineDataSyncService:
    """K线数据同步服务"""
    
    # 使用统一的常量定义
    DEFAULT_SYMBOLS = DEFAULT_SYMBOLS
    TIMEFRAME_LIMITS = TIMEFRAME_LIMITS
    MAX_MANUAL_LIMITS = MAX_MANUAL_LIMITS
    FUTURES_INDICATOR_TIMEFRAMES = FUTURES_INDICATOR_TIMEFRAMES

    def __init__(self):
        self.logger = get_logger('kline_data_sync_service')
        # 使用现货API获取K线数据（不获取期货指标）
        self.provider = get_binance_provider(enable_futures=False)
        self.futures_enabled = False
        self.logger.info("K线数据同步服务已使用现货模式")

    async def _sync_timeframe_data(self, timeframe: str, symbols: Optional[List[str]] = None, 
                                   task_name: str = None, limit: Optional[int] = None) -> bool:
        """
        通用的时间框架数据同步方法
        
        Args:
            timeframe: 时间框架 (1m, 1d, etc.)
            symbols: 交易对列表
            task_name: 任务名称，用于记录执行
            limit: 数据条数限制，None时使用默认值
            
        Returns:
            bool: 是否有成功同步的数据
        """
        start_time = datetime.now()
        
        try:
            # 使用默认交易对
            if not symbols:
                symbols = self.DEFAULT_SYMBOLS.copy()

            # 使用分表数据库模块
            kline_service = get_kline_data_service(use_timeframe_tables=True)
            success_count = 0
            total_count = len(symbols)
            
            # 获取该时间框架的数据量限制
            if limit is None:
                limit = self.TIMEFRAME_LIMITS.get(timeframe, 1)
            else:
                # 验证手动设置的limit不超过最大限制
                max_limit = MAX_MANUAL_LIMITS.get(timeframe, 1000)
                if limit > max_limit:
                    self.logger.warning(f"请求的数据条数 {limit} 超过最大限制 {max_limit}，将使用最大限制")
                    limit = max_limit

            for symbol in symbols:
                try:
                    # 在线程池中调用provider获取数据
                    kline_data = await asyncio.to_thread(
                        self.provider.get_ohlcv,
                        symbol,
                        timeframe,
                        limit=limit
                    )

                    if not kline_data.empty:
                        # 为短时间框架添加合约指标
                        if timeframe in self.FUTURES_INDICATOR_TIMEFRAMES:
                            kline_data = await self._add_futures_indicators(symbol, kline_data, timeframe)
                        
                        # 保存到对应时间框架的数据表
                        if kline_service.save_kline_data(symbol, timeframe, kline_data, "binance"):
                            success_count += 1
                            self.logger.info(f"同步 {symbol} {timeframe} K线数据成功 {len(kline_data)} 条")
                        else:
                            self.logger.warning(f"保存 {symbol} {timeframe} K线数据到数据库失败")
                    else:
                        self.logger.warning(f"获取 {symbol} {timeframe} K线数据为空")

                except Exception as e:
                    self.logger.warning(f"同步 {symbol} {timeframe} K线数据失败: {e}")
                    continue

            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 记录任务执行
            if task_name:
                record_task_execution(task_name, True, execution_time)

            self.logger.info(f"{timeframe} K线数据同步完成 {success_count}/{total_count} 成功")
            return success_count > 0

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 记录任务执行失败
            if task_name:
                record_task_execution(task_name, False, execution_time)
                
            self.logger.error(f"{timeframe} K线数据同步失败: {e}")
            raise

    @task_wrapper
    async def sync_minute_kline_data(self, symbols: Optional[List[str]] = None) -> bool:
        """同步1分钟K线数据（包含合约指标）"""
        return await self._sync_timeframe_data("1m", symbols, "sync_minute_kline_data")

    @task_wrapper
    async def sync_daily_kline_data(self, symbols: Optional[List[str]] = None) -> bool:
        """同步1天K线数据"""
        return await self._sync_timeframe_data("1d", symbols, "sync_daily_kline_data")

    # 手动同步方法 - 支持自定义数据条数
    @task_wrapper
    async def manual_sync_kline_data(self, timeframe: str, symbols: Optional[List[str]] = None, 
                                   limit: int = 100) -> bool:
        """
        手动同步K线数据 - 支持自定义数据条数
        
        Args:
            timeframe: 时间框架 (1m, 3m, 5m, 15m, 1h, 1d)
            symbols: 交易对列表
            limit: 数据条数限制
            
        Returns:
            bool: 是否有成功同步的数据
        """
        if timeframe not in self.TIMEFRAME_LIMITS:
            self.logger.error(f"不支持的时间框架: {timeframe}")
            return False
        
        if limit <= 0:
            self.logger.error(f"数据条数必须大于0: {limit}")
            return False
        
        self.logger.info(f"开始手动同步 {timeframe} K线数据，条数限制: {limit}")
        return await self._sync_timeframe_data(timeframe, symbols, f"manual_sync_{timeframe}_kline_data", limit)

    @task_wrapper
    async def manual_sync_minute_kline_data(self, symbols: Optional[List[str]] = None, limit: int = 100) -> bool:
        """手动同步1分钟K线数据"""
        return await self.manual_sync_kline_data("1m", symbols, limit)

    @task_wrapper
    async def manual_sync_daily_kline_data(self, symbols: Optional[List[str]] = None, limit: int = 100) -> bool:
        """手动同步1天K线数据"""
        return await self.manual_sync_kline_data("1d", symbols, limit)

    @task_wrapper
    async def manual_sync_all_timeframes_kline_data(self, symbols: Optional[List[str]] = None, 
                                                  limit: int = 100) -> bool:
        """
        手动同步所有时间框架的K线数据
        
        Args:
            symbols: 交易对列表
            limit: 每个时间框架的数据条数限制
            
        Returns:
            bool: 是否有成功同步的数据
        """
        start_time = datetime.now()
        
        try:
            # 使用默认交易对
            if not symbols:
                symbols = self.DEFAULT_SYMBOLS.copy()
            
            # 支持的时间框架
            timeframes = SUPPORTED_TIMEFRAMES
            total_success = 0
            total_count = len(symbols) * len(timeframes)
            
            for timeframe in timeframes:
                self.logger.info(f"开始手动同步 {timeframe} 时间框架数据，条数限制: {limit}")
                
                # 使用通用同步方法，但不记录单独的任务执行
                success = await self._sync_timeframe_data(timeframe, symbols, task_name=None, limit=limit)
                if success:
                    # 计算成功的数量（简化处理，假设全部成功）
                    total_success += len(symbols)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("manual_sync_all_timeframes_kline_data", True, execution_time)
            
            self.logger.info(f"所有时间框架K线数据手动同步完成 {total_success}/{total_count} 成功")
            return total_success > 0
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("manual_sync_all_timeframes_kline_data", False, execution_time)
            self.logger.error(f"所有时间框架K线数据手动同步失败: {e}")
            raise

    def get_supported_timeframes(self) -> List[str]:
        """获取支持的时间框架列表"""
        return SUPPORTED_TIMEFRAMES.copy()

    def get_max_limits(self) -> Dict[str, int]:
        """获取各时间框架的最大数据条数限制"""
        return MAX_MANUAL_LIMITS.copy()

    def get_default_limits(self) -> Dict[str, int]:
        """获取各时间框架的默认数据条数限制"""
        return TIMEFRAME_LIMITS.copy()

    def validate_timeframe(self, timeframe: str) -> bool:
        """验证时间框架是否支持"""
        return timeframe in TIMEFRAME_LIMITS

    def validate_limit(self, timeframe: str, limit: int) -> Tuple[bool, str]:
        """
        验证数据条数限制是否有效
        
        Returns:
            tuple: (是否有效, 错误信息)
        """
        if limit <= 0:
            return False, "数据条数必须大于0"
        
        max_limit = MAX_MANUAL_LIMITS.get(timeframe, 1000)
        if limit > max_limit:
            return False, f"数据条数不能超过最大限制 {max_limit}"
        
        return True, ""

    async def _add_futures_indicators(self, symbol: str, kline_data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        为K线数据添加合约指标（持仓量和资金费率）
        
        注意：如果DataFrame中已经包含open_interest和funding_rate字段，则跳过重复获取
        
        Args:
            symbol: 交易对符号
            kline_data: K线数据DataFrame
            
        Returns:
            pd.DataFrame: 包含合约指标的K线数据
        """
        try:
            # 检查是否已经包含合约指标字段；若存在但为常量（快照），仍将尝试历史替换
            if 'open_interest' in kline_data.columns and 'funding_rate' in kline_data.columns:
                oi_unique = kline_data['open_interest'].nunique(dropna=True)
                fr_unique = kline_data['funding_rate'].nunique(dropna=True)
                if oi_unique > 1 or fr_unique > 1:
                    self.logger.debug(f"{symbol} 合约指标已为时序数据，跳过历史合并")
                    return kline_data
                else:
                    self.logger.debug(f"{symbol} 合约指标为快照或缺失，执行历史合并替换")
            
            # 只有在期货功能启用时才获取合约指标
            if not self.futures_enabled:
                kline_data['open_interest'] = None
                kline_data['funding_rate'] = None
                self.logger.debug(f"{symbol} 期货功能未启用，跳过合约指标")
                return kline_data
            
            # 优先尝试获取按时间的历史序列并与K线按timestamp合并
            def _fmt_ts(idx_val) -> str:
                try:
                    return pd.Timestamp(idx_val).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    return str(idx_val)

            # 规范化K线时间戳列
            kline_df = kline_data.copy()
            if 'timestamp' not in kline_df.columns:
                kline_df['timestamp'] = [ _fmt_ts(i) for i in kline_df.index ]

            # 映射时间框架到频率，直接使用本批次的时间框架确定频率
            tf_to_freq = { '1m':'1T', '3m':'3T', '5m':'5T', '15m':'15T', '1h':'1H', '4h':'4H', '1d':'1D' }
            # 直接使用传入的 timeframe
            local_tf = timeframe
            freq = tf_to_freq.get(local_tf, None)

            try:
                # 历史序列：可能返回DataFrame或list，尽量限定窗口以减少数据量
                # 计算K线窗口
                try:
                    k_start = pd.to_datetime(kline_df['timestamp'].iloc[0])
                    k_end = pd.to_datetime(kline_df['timestamp'].iloc[-1])
                except Exception:
                    k_start = None
                    k_end = None

                # 为历史查询增加时间缓冲，避免窗口过小导致无返回
                if k_start is not None and k_end is not None:
                    pad_hours_map = {'1m': 24, '3m': 36, '5m': 48, '15m': 72, '1h': 168, '4h': 336, '1d': 720}
                    pad_hours = pad_hours_map.get(local_tf, 72)
                    k_start_q = k_start - pd.Timedelta(hours=pad_hours)
                    k_end_q = k_end + pd.Timedelta(hours=pad_hours)
                else:
                    k_start_q = k_start
                    k_end_q = k_end

                # 历史序列：可能返回DataFrame或list
                oi_hist = None
                fr_hist = None
                if hasattr(self.provider, 'get_open_interest_history'):
                    try:
                        if k_start_q is not None and k_end_q is not None:
                            # 尝试多签名：带时间窗/带timeframe
                            try:
                                oi_hist = await asyncio.to_thread(self.provider.get_open_interest_history, symbol, k_start_q, k_end_q, local_tf)
                            except Exception:
                                try:
                                    oi_hist = await asyncio.to_thread(self.provider.get_open_interest_history, symbol, k_start_q, k_end_q)
                                except Exception:
                                    oi_hist = await asyncio.to_thread(self.provider.get_open_interest_history, symbol)
                        else:
                            oi_hist = await asyncio.to_thread(self.provider.get_open_interest_history, symbol)
                    except Exception as _:
                        oi_hist = None
                if hasattr(self.provider, 'get_funding_rate_history'):
                    try:
                        if k_start_q is not None and k_end_q is not None:
                            try:
                                fr_hist = await asyncio.to_thread(self.provider.get_funding_rate_history, symbol, k_start_q, k_end_q, local_tf)
                            except Exception:
                                try:
                                    fr_hist = await asyncio.to_thread(self.provider.get_funding_rate_history, symbol, k_start_q, k_end_q)
                                except Exception:
                                    fr_hist = await asyncio.to_thread(self.provider.get_funding_rate_history, symbol)
                        else:
                            fr_hist = await asyncio.to_thread(self.provider.get_funding_rate_history, symbol)
                    except Exception as _:
                        fr_hist = None

                def _hist_to_df(hist, value_key_candidates: List[str]) -> pd.DataFrame:
                    if hist is None:
                        return pd.DataFrame(columns=['timestamp','value'])
                    if isinstance(hist, pd.DataFrame):
                        dfh = hist.copy()
                    else:
                        dfh = pd.DataFrame(hist)
                    # 识别时间与取值列
                    ts_col = 'timestamp' if 'timestamp' in dfh.columns else 'time'
                    val_col = None
                    for k in value_key_candidates:
                        if k in dfh.columns:
                            val_col = k
                            break
                    if ts_col not in dfh.columns or val_col is None:
                        return pd.DataFrame(columns=['timestamp','value'])
                    dfh = dfh[[ts_col, val_col]].rename(columns={ts_col:'timestamp', val_col:'value'})
                    # 统一时间戳格式
                    dfh['timestamp'] = dfh['timestamp'].apply(_fmt_ts)
                    # 去重并按时间排序
                    dfh = dfh.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                    return dfh

                oi_df = _hist_to_df(oi_hist, ['openInterest','openInterestAmount','sumOpenInterest','value'])
                fr_df = _hist_to_df(fr_hist, ['fundingRate','lastFundingRate','value'])

                # 若有频率信息，进行重采样到指定频率并对齐K线时间戳
                def _align_to_kline(ts_df: pd.DataFrame, k_ts: pd.Series, method: str = 'ffill') -> pd.Series:
                    if ts_df is None or ts_df.empty:
                        return pd.Series([None]*len(k_ts), index=k_ts.index)
                    s = ts_df.set_index(pd.to_datetime(ts_df['timestamp']))['value']
                    if freq:
                        try:
                            # 先按目标频率重采样取区间“最后值”，再进行前向填充，避免长周期被早期快照覆盖
                            s = s.resample(freq).last().ffill()
                        except Exception:
                            s = s.sort_index().ffill()
                    # 目标索引
                    k_idx = pd.to_datetime(k_ts)
                    aligned = s.reindex(k_idx, method=method)
                    # 返回按字符串时间戳序列
                    aligned.index = k_ts.index
                    return aligned

                k_ts = kline_df['timestamp']
                oi_aligned = _align_to_kline(oi_df, k_ts)
                fr_aligned = _align_to_kline(fr_df, k_ts)

                # 仅在对应历史存在时覆盖该字段，避免把快照覆盖为None
                has_oi_hist = (oi_df is not None and not oi_df.empty)
                has_fr_hist = (fr_df is not None and not fr_df.empty)
                if has_oi_hist or has_fr_hist:
                    self.logger.info(f"{symbol} 历史合约指标对齐完成: timeframe={local_tf}, 窗口=[{k_start_q}, {k_end_q}], OI点数={len(oi_df) if oi_df is not None else 0}, FR点数={len(fr_df) if fr_df is not None else 0}")
                    if has_oi_hist:
                        kline_df['open_interest'] = oi_aligned
                    if has_fr_hist:
                        kline_df['funding_rate'] = fr_aligned
                    return kline_df
            except Exception as e:
                self.logger.info(f"{symbol} 历史合约指标合并失败，回退到快照: {e}")

            # 回退：使用当前快照（整列相同，作为保底）
            open_interest_data = await asyncio.to_thread(self.provider.get_open_interest, symbol)
            funding_rate_data = await asyncio.to_thread(self.provider.get_funding_rate, symbol)

            open_interest_value = None
            if open_interest_data:
                if 'openInterest' in open_interest_data:
                    open_interest_value = float(open_interest_data['openInterest'])
                elif 'openInterestAmount' in open_interest_data:
                    open_interest_value = float(open_interest_data['openInterestAmount'])
                elif 'sumOpenInterest' in open_interest_data:
                    open_interest_value = float(open_interest_data['sumOpenInterest'])

            funding_rate_value = None
            if funding_rate_data:
                if 'fundingRate' in funding_rate_data:
                    funding_rate_value = float(funding_rate_data['fundingRate'])
                elif 'lastFundingRate' in funding_rate_data:
                    funding_rate_value = float(funding_rate_data['lastFundingRate'])

            kline_data['open_interest'] = open_interest_value
            kline_data['funding_rate'] = funding_rate_value
            return kline_data
            
        except Exception as e:
            self.logger.warning(f"获取 {symbol} 合约指标失败: {e}")
            # 如果获取合约指标失败，添加空值
            kline_data['open_interest'] = None
            kline_data['funding_rate'] = None
            return kline_data

    @task_wrapper
    async def sync_all_timeframes_kline_data(self, symbols: Optional[List[str]] = None) -> bool:
        """同步所有时间框架的K线数据"""
        start_time = datetime.now()
        
        try:
            # 使用默认交易对
            if not symbols:
                symbols = self.DEFAULT_SYMBOLS.copy()
            
            # 支持的时间框架
            timeframes = SUPPORTED_TIMEFRAMES
            total_success = 0
            total_count = len(symbols) * len(timeframes)
            
            for timeframe in timeframes:
                self.logger.info(f"开始同步 {timeframe} 时间框架数据")
                
                # 使用通用同步方法，但不记录单独的任务执行（避免重复记录）
                success = await self._sync_timeframe_data(timeframe, symbols, task_name=None)
                if success:
                    # 计算成功的数量（简化处理，假设全部成功）
                    total_success += len(symbols)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_all_timeframes_kline_data", True, execution_time)
            
            self.logger.info(f"所有时间框架K线数据同步完成 {total_success}/{total_count} 成功")
            return total_success > 0
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_all_timeframes_kline_data", False, execution_time)
            self.logger.error(f"所有时间框架K线数据同步失败: {e}")
            raise

# 单例模式
_kline_data_sync_service: Optional[KlineDataSyncService] = None

def get_kline_data_sync_service() -> KlineDataSyncService:
    """获取K线数据同步服务单例实例"""
    global _kline_data_sync_service
    if _kline_data_sync_service is None:
        _kline_data_sync_service = KlineDataSyncService()
    return _kline_data_sync_service