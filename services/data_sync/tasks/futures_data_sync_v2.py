# -*- coding: utf-8 -*-
"""
期货数据同步服务
直接同步到概览表，支持灵活存储和趋势分析
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import json
import os

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from utils.core.logger_manager import get_logger
from api.utils.task_utils import task_wrapper, record_task_execution
from utils.core.singleton import get_binance_provider
from data.database.session_manager import get_session_manager
from data.models.market_data.futures_data_model_v2 import CryptoFuturesOverview


class FuturesDataSyncServiceV2:
    """期货数据同步服务 - 直接同步到概览表"""

    # 同步配置
    SYNC_CONFIG = {
        # 支持的交易对
        'symbols': ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT", "SOLUSDT", "XRPUSDT"],

        # 数据获取配置
        'fetch_interval_minutes': 5,  # 每5分钟获取一次数据
        'data_retention_days': 30,  # 保留30天完整数据

        # 数据验证
        'validate_data': True,
        'max_oi_change_percent': 50,  # 持仓量变化超过50%认为异常
        # 注意：已移除资金费率变化验证，因为实际交易中会出现大幅变化

        # 多交易所支持
        'use_multi_exchange': False,

        # 资金费率结算时间（UTC）
        'funding_settlement_times': [0, 8, 16],  # 00:00, 08:00, 16:00
    }

    def __init__(self):
        self.logger = get_logger('futures_data_sync_v2')
        self.provider = get_binance_provider(enable_futures=True)
        self.session_manager = get_session_manager()
        self.universal_provider = None

        # 加载配置
        self._load_config()

        # 初始化多交易所数据提供者
        if self.SYNC_CONFIG.get('use_multi_exchange', False):
            try:
                # TODO: 重新实现多交易所数据提供者
                self.universal_provider = None
                self.logger.info("多交易所期货数据支持已禁用")
            except Exception as e:
                self.logger.warning(f"初始化多交易所数据提供者失败: {e}")
                self.universal_provider = None

        # 数据质量统计
        self.quality_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'data_validation_failures': 0,
            'retry_attempts': 0,
            'records_saved': 0,
            'data_sources': {},
            'overview_update_count': 0,
        }

    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = os.path.join('config', 'futures_sync_v2_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self.SYNC_CONFIG.update(user_config)
                    self.logger.info(f"已加载期货同步配置: {config_path}")
            else:
                self._create_default_config(config_path)
        except Exception as e:
            self.logger.warning(f"加载期货配置失败，使用默认配置: {e}")

    def _create_default_config(self, config_path: str):
        """创建默认配置文件"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.SYNC_CONFIG, f, indent=2, ensure_ascii=False)
            self.logger.info(f"已创建默认期货同步配置文件: {config_path}")
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")

    def _validate_futures_data(self, data: Dict[str, Any], symbol: str, last_record: Optional[CryptoFuturesOverview] = None) -> Tuple[bool, str]:
        """验证期货数据有效性

        Returns:
            (is_valid, reason)
        """
        if not data:
            return False, "数据为空"

        # 验证持仓量
        if 'open_interest' in data and data['open_interest'] is not None:
            oi = float(data['open_interest'])
            if oi < 0:
                return False, f"持仓量不能为负数: {oi}"

            # 验证变化幅度
            if last_record and last_record.latest_open_interest:
                change_percent = abs((oi - last_record.latest_open_interest) / last_record.latest_open_interest) * 100
                if change_percent > self.SYNC_CONFIG['max_oi_change_percent']:
                    return False, f"持仓量变化过大: {change_percent:.1f}%"

        # 验证资金费率
        if 'funding_rate' in data and data['funding_rate'] is not None:
            fr = float(data['funding_rate'])
            if abs(fr) > 1.0:  # 资金费率通常不超过1%
                return False, f"资金费率异常: {fr}"

            # 注释掉变化幅度验证，因为实际交易中资金费率可能出现大幅变化
            # 用户明确要求不要验证变化过大
            # if last_record and last_record.latest_funding_rate is not None:
            #     change_percent = abs((fr - last_record.latest_funding_rate) / last_record.latest_funding_rate * 100) if last_record.latest_funding_rate != 0 else 0
            #     if change_percent > self.SYNC_CONFIG['max_fr_change_percent']:
            #         return False, f"资金费率变化过大: {change_percent:.1f}%"

        return True, "数据有效"

    async def _get_futures_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取期货数据（多交易所容错）"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                self.quality_stats['total_requests'] += 1
                if attempt > 0:
                    self.quality_stats['retry_attempts'] += 1

                # 优先使用多交易所数据源
                if self.universal_provider:
                    try:
                        # TODO: 重新实现多交易所数据获取
                        pass
                    except Exception as e:
                        self.logger.warning(f"多交易所数据源失败 (尝试 {attempt + 1}): {e}")

                # 备用方案：使用Binance Provider
                data = await self._get_futures_data_legacy(symbol)
                if data:
                    return data

                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                self.logger.error(f"获取期货数据异常: {symbol}, 错误: {e}")

        self.quality_stats['failed_requests'] += 1
        return None

    async def _get_futures_data_legacy(self, symbol: str) -> Optional[Dict[str, Any]]:
        """使用Binance Provider获取期货数据"""
        try:
            # 并发获取持仓量和资金费率
            oi_task = asyncio.to_thread(self._get_open_interest_enhanced, symbol)
            fr_task = asyncio.to_thread(self._get_funding_rate_enhanced, symbol)

            oi_data, fr_data = await asyncio.gather(oi_task, fr_task, return_exceptions=True)

            # 处理持仓量
            open_interest = None
            oi_source = 'binance_legacy'
            oi_error = None

            if isinstance(oi_data, Exception):
                oi_error = str(oi_data)
                self.logger.error(f"获取持仓量异常: {symbol}, 错误: {oi_error}")
            elif isinstance(oi_data, dict):
                # 尝试从不同字段获取持仓量
                if 'openInterest' in oi_data:
                    open_interest = float(oi_data['openInterest'])
                    self.logger.debug(f"成功获取持仓量(字段openInterest): {symbol} = {open_interest}")
                elif 'openInterestAmount' in oi_data:
                    open_interest = float(oi_data['openInterestAmount'])
                    self.logger.debug(f"成功获取持仓量(字段openInterestAmount): {symbol} = {open_interest}")
                elif 'info' in oi_data and isinstance(oi_data['info'], dict):
                    # 数据可能在info字段内
                    info_data = oi_data['info']
                    if 'openInterest' in info_data:
                        open_interest = float(info_data['openInterest'])
                        self.logger.debug(f"成功获取持仓量(从info字段): {symbol} = {open_interest}")
                    else:
                        oi_error = f"info字段中缺少openInterest: {info_data}"
                        self.logger.warning(f"持仓量数据格式异常: {symbol}, 数据: {oi_data}")
                else:
                    oi_error = f"响应数据格式错误: {oi_data}"
                    self.logger.warning(f"持仓量数据缺少openInterest/openInterestAmount字段: {symbol}, 数据: {oi_data}")
            else:
                oi_error = f"响应类型错误: {type(oi_data)}"
                self.logger.warning(f"持仓量数据类型异常: {symbol}, 类型: {type(oi_data)}, 数据: {oi_data}")

            # 处理资金费率
            funding_rate = None
            fr_source = 'binance_legacy'
            fr_error = None

            if isinstance(fr_data, Exception):
                fr_error = str(fr_data)
                self.logger.error(f"获取资金费率异常: {symbol}, 错误: {fr_error}")
            elif isinstance(fr_data, dict):
                # 尝试从不同字段获取资金费率
                if 'fundingRate' in fr_data:
                    funding_rate = float(fr_data['fundingRate'])
                    self.logger.debug(f"成功获取资金费率(字段fundingRate): {symbol} = {funding_rate}")
                elif 'info' in fr_data and isinstance(fr_data['info'], dict):
                    # 数据可能在info字段内
                    info_data = fr_data['info']
                    if 'fundingRate' in info_data:
                        funding_rate = float(info_data['fundingRate'])
                        self.logger.debug(f"成功获取资金费率(从info字段): {symbol} = {funding_rate}")
                    else:
                        fr_error = f"info字段中缺少fundingRate: {info_data}"
                        self.logger.warning(f"资金费率数据格式异常: {symbol}, 数据: {fr_data}")
                else:
                    fr_error = f"响应数据格式错误: {fr_data}"
                    self.logger.warning(f"资金费率数据缺少fundingRate字段: {symbol}, 数据: {fr_data}")
            else:
                fr_error = f"响应类型错误: {type(fr_data)}"
                self.logger.warning(f"资金费率数据类型异常: {symbol}, 类型: {type(fr_data)}, 数据: {fr_data}")

            # 确保至少有一个数据获取成功
            if open_interest is None and funding_rate is None:
                self.logger.error(f"期货数据获取完全失败: {symbol}, 持仓量错误: {oi_error}, 资金费率错误: {fr_error}")
                return None

            result = {
                'symbol': symbol,
                'open_interest': open_interest,
                'funding_rate': funding_rate,
                'timestamp': datetime.now(),
                'funding_time': self._get_funding_time_str(),
                'next_funding_time': self._get_next_funding_time_str(),
                'data_sources': {
                    'open_interest_source': oi_source,
                    'funding_rate_source': fr_source
                },
                'errors': {
                    'open_interest_error': oi_error,
                    'funding_rate_error': fr_error
                }
            }

            # 记录数据源统计
            for source in [oi_source, fr_source]:
                if source not in self.quality_stats['data_sources']:
                    self.quality_stats['data_sources'][source] = 0
                self.quality_stats['data_sources'][source] += 1

            # 记录成功统计
            if open_interest is not None:
                self.quality_stats['successful_requests'] += 1
            if funding_rate is not None:
                self.quality_stats['successful_requests'] += 1

            self.logger.info(f"期货数据获取结果: {symbol}, 持仓量: {open_interest}, 资金费率: {funding_rate}")
            return result

        except Exception as e:
            self.logger.error(f"Binance Provider获取期货数据失败: {symbol}, 错误: {e}")
            return None

    def _get_open_interest_enhanced(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓量（增强版）"""
        try:
            if hasattr(self.provider, 'futures_exchange') and self.provider.futures_exchange:
                # 策略1: fetch_open_interest
                if self.provider.futures_exchange.has.get('fetchOpenInterest', False):
                    return self.provider.futures_exchange.fetch_open_interest(symbol)

                # 策略2: fetch_open_interest_history
                if self.provider.futures_exchange.has.get('fetchOpenInterestHistory', False):
                    history = self.provider.futures_exchange.fetch_open_interest_history(symbol, limit=1)
                    if history:
                        return history[0]

            # 策略3: provider方法
            return self.provider.get_open_interest(symbol)

        except Exception as e:
            self.logger.error(f"获取持仓量失败: {symbol}, 错误: {e}")
            return None

    def _get_funding_rate_enhanced(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取资金费率（增强版）"""
        try:
            if hasattr(self.provider, 'futures_exchange') and self.provider.futures_exchange:
                # 策略1: fetch_funding_rate
                if self.provider.futures_exchange.has.get('fetchFundingRate', False):
                    return self.provider.futures_exchange.fetch_funding_rate(symbol)

                # 策略2: fetch_funding_rate_history
                if self.provider.futures_exchange.has.get('fetchFundingRateHistory', False):
                    history = self.provider.futures_exchange.fetch_funding_rate_history(symbol, limit=1)
                    if history:
                        return history[0]

            # 策略3: provider方法
            return self.provider.get_funding_rate(symbol)

        except Exception as e:
            self.logger.error(f"获取资金费率失败: {symbol}, 错误: {e}")
            return None

    def _get_funding_time_str(self) -> str:
        """获取当前资金费率结算时间字符串"""
        now = datetime.utcnow()
        hour = now.hour
        if hour < 8:
            settlement_hour = 0
        elif hour < 16:
            settlement_hour = 8
        else:
            settlement_hour = 16

        settlement_time = now.replace(hour=settlement_hour, minute=0, second=0, microsecond=0)
        return settlement_time.strftime('%Y-%m-%d %H:%M:%S')

    def _get_next_funding_time_str(self) -> str:
        """获取下次资金费率结算时间字符串"""
        now = datetime.utcnow()
        hour = now.hour
        if hour < 8:
            next_hour = 8
        elif hour < 16:
            next_hour = 16
        else:
            next_hour = 0
            now += timedelta(days=1)

        next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        return next_time.strftime('%Y-%m-%d %H:%M:%S')

    async def _get_historical_data(self, session: Session, symbol: str, hours_ago: int) -> Optional[Dict[str, Any]]:
        """获取历史数据（用于趋势分析）"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_ago)
            historical_record = session.query(CryptoFuturesOverview)\
                .filter(CryptoFuturesOverview.symbol == symbol)\
                .filter(CryptoFuturesOverview.last_update <= cutoff_time)\
                .order_by(CryptoFuturesOverview.last_update.desc())\
                .first()

            if historical_record:
                return {
                    'open_interest': historical_record.latest_open_interest,
                    'funding_rate': historical_record.latest_funding_rate,
                    'update_time': historical_record.last_update
                }
            return None
        except Exception as e:
            self.logger.warning(f"获取历史数据失败: {symbol}, 错误: {e}")
            return None

    async def _update_overview_table(self, session: Session, symbol: str, futures_data: Dict[str, Any]) -> bool:
        """更新概览表"""
        try:
            # 获取现有记录
            overview = session.query(CryptoFuturesOverview)\
                .filter(CryptoFuturesOverview.symbol == symbol)\
                .first()

            if not overview:
                overview = CryptoFuturesOverview(symbol=symbol)

            # 计算24小时变化（使用最新数据）
            oi_change_24h = None
            oi_change_percent = None
            old_open_interest = overview.latest_open_interest
            new_open_interest = futures_data.get('open_interest')

            if old_open_interest and new_open_interest:
                oi_change_24h = new_open_interest - old_open_interest
                oi_change_percent = (oi_change_24h / old_open_interest) * 100

            fr_change_24h = None
            old_funding_rate = overview.latest_funding_rate
            new_funding_rate = futures_data.get('funding_rate')
            if old_funding_rate and new_funding_rate:
                fr_change_24h = new_funding_rate - old_funding_rate

            # 更新基础数据
            overview.latest_open_interest = new_open_interest
            overview.latest_funding_rate = new_funding_rate
            overview.next_funding_time = futures_data.get('next_funding_time')
            overview.oi_change_24h = oi_change_24h
            overview.oi_change_percent = oi_change_percent
            overview.fr_change_24h = fr_change_24h
            overview.last_update = datetime.now()
            overview.is_active = True

            # 记录写入日志
            self.logger.info(
                f"写入期货数据: {symbol}, "
                f"持仓量: {old_open_interest} -> {new_open_interest}, "
                f"资金费率: {old_funding_rate} -> {new_funding_rate}, "
                f"oi_change_24h: {oi_change_24h}, "
                f"fr_change_24h: {fr_change_24h}"
            )

            session.add(overview)
            self.quality_stats['overview_update_count'] += 1
            self.quality_stats['records_saved'] += 1

            self.logger.info(f"更新概览表成功: {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"更新概览表失败: {symbol}, 错误: {e}")
            session.rollback()
            return False

    @task_wrapper
    async def sync_futures_data(self, symbols: Optional[List[str]] = None, auto_sync: bool = True) -> bool:
        """同步期货数据

        Args:
            symbols: 交易对列表，为空时使用默认列表
            auto_sync: 是否为自动同步（自动同步时只保存最新数据）

        Returns:
            bool: 同步是否成功
        """
        try:
            start_time = datetime.now()

            # 获取要同步的交易对
            if not symbols:
                symbols = self.SYNC_CONFIG['symbols']

            self.logger.info(f"开始同步期货数据: {symbols}, auto_sync={auto_sync}")

            success_count = 0
            total_count = len(symbols)

            # 使用session确保事务性
            with self.session_manager.get_session() as session:
                for symbol in symbols:
                    try:
                        # 获取期货数据
                        futures_data = await self._get_futures_data(symbol)

                        if not futures_data:
                            self.logger.warning(f"未获取到期货数据: {symbol}")
                            continue

                        # 获取现有记录（用于数据验证）
                        last_record = session.query(CryptoFuturesOverview)\
                            .filter(CryptoFuturesOverview.symbol == symbol)\
                            .first()

                        # 验证数据
                        if self.SYNC_CONFIG['validate_data']:
                            is_valid, reason = self._validate_futures_data(futures_data, symbol, last_record)
                            if not is_valid:
                                self.quality_stats['data_validation_failures'] += 1
                                self.logger.warning(f"期货数据验证失败: {symbol} - {reason}")
                                continue

                        # 保存数据
                        saved = await self._update_overview_table(session, symbol, futures_data)
                        if saved:
                            session.commit()
                            success_count += 1
                        else:
                            session.rollback()

                    except Exception as e:
                        self.logger.error(f"同步期货数据失败: {symbol}, 错误: {e}")
                        continue

            # 记录执行结果
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self._log_quality_stats(duration)
            self._record_execution(success_count, total_count, duration)

            self.logger.info(f"期货数据同步完成: {success_count}/{total_count} 成功，耗时 {duration:.2f}秒")
            return success_count > 0

        except Exception as e:
            self.logger.error(f"期货数据同步任务失败: {e}")
            return False

    def _log_quality_stats(self, duration: float):
        """记录数据质量统计"""
        stats = self.quality_stats
        if stats['total_requests'] > 0:
            success_rate = (stats['successful_requests'] / stats['total_requests']) * 100
            data_sources_info = ", ".join([f"{k}: {v}" for k, v in stats['data_sources'].items()]) if stats['data_sources'] else "无"

            self.logger.info(
                f"数据质量统计 - 总请求: {stats['total_requests']}, "
                f"成功: {stats['successful_requests']}, "
                f"失败: {stats['failed_requests']}, "
                f"成功率: {success_rate:.1f}%, "
                f"重试次数: {stats['retry_attempts']}, "
                f"验证失败: {stats['data_validation_failures']}, "
                f"保存记录: {stats['records_saved']}, "
                f"概览更新: {stats['overview_update_count']}, "
                f"数据源: {data_sources_info}, "
                f"耗时: {duration:.2f}秒"
            )

        # 重置统计
        self.quality_stats = {k: 0 for k in self.quality_stats.keys()}
        self.quality_stats['data_sources'] = {}

    def _record_execution(self, success_count: int, total_count: int, duration: float):
        """记录任务执行"""
        try:
            record_task_execution(
                task_name="sync_futures_data_v2",
                success=success_count == total_count,
                execution_time=duration
            )
        except Exception as e:
            self.logger.warning(f"记录任务执行失败: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            test_symbol = "BTCUSDT"
            test_data = await self._get_futures_data(test_symbol)

            return {
                'status': 'healthy' if test_data else 'unhealthy',
                'test_symbol': test_symbol,
                'test_result': test_data is not None,
                'config': self.SYNC_CONFIG,
                'quality_stats': self.quality_stats,
                'multi_exchange_enabled': self.universal_provider is not None
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'config': self.SYNC_CONFIG,
                'quality_stats': self.quality_stats
            }

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.SYNC_CONFIG.copy()


# 全局服务实例
_futures_sync_service_v2: Optional[FuturesDataSyncServiceV2] = None


def get_futures_data_sync_service_v2() -> FuturesDataSyncServiceV2:
    """获取期货数据同步服务实例（单例模式）"""
    global _futures_sync_service_v2
    if _futures_sync_service_v2 is None:
        _futures_sync_service_v2 = FuturesDataSyncServiceV2()
    return _futures_sync_service_v2
