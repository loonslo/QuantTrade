# -*- coding: utf-8 -*-
"""
美股个股数据ORM服务
处理美股个股日K线数据的CRUD操作
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import and_, desc

from services.orm.base_orm_service import BaseORMService
from data.models.market_data.us_stocks_model import USStockDailyKline
from utils.time.timestamp_utils import TimestampConverter


class USStocksServiceORM(BaseORMService):
    """美股个股数据ORM服务"""

    def __init__(self):
        super().__init__('us_stocks_service_orm', USStockDailyKline)

    async def _execute_sync(self):
        """执行同步任务"""
        self.logger.info("美股个股数据同步任务执行")
        pass

    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置"""
        return {
            "task_name": "us_stocks_sync",
            "description": "美股个股日K线数据同步",
            "enabled": True
        }

    def save_daily_kline(self, symbol: str, kline_data: Dict[str, Any]) -> bool:
        """
        保存单条日K线数据
        
        Args:
            symbol: 股票代码
            kline_data: K线数据 {
                'timestamp': '2026-03-27',
                'open': 220.5,
                'high': 225.0,
                'low': 219.0,
                'close': 224.0,
                'volume': 50000000
            }
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 解析时间戳
            ts_str = kline_data.get('timestamp')
            if isinstance(ts_str, str):
                data_timestamp = datetime.strptime(ts_str, '%Y-%m-%d')
            else:
                data_timestamp = ts_str

            record_data = {
                "symbol": symbol.upper(),
                "timestamp": data_timestamp,
                "open_price": kline_data.get('open', 0),
                "high_price": kline_data.get('high', 0),
                "low_price": kline_data.get('low', 0),
                "close_price": kline_data.get('close', 0),
                "volume": kline_data.get('volume', 0),
                "is_valid": True,
                "source": 'yahoo_finance'
            }

            # 使用 upsert 逻辑：先尝试更新已有记录
            existing = self.get_model_records_by_conditions(
                conditions={
                    "symbol": symbol.upper(),
                    "timestamp": data_timestamp
                },
                limit=1
            )

            if existing:
                # 更新已有记录
                record = existing[0]
                record.open_price = record_data['open_price']
                record.high_price = record_data['high_price']
                record.low_price = record_data['low_price']
                record.close_price = record_data['close_price']
                record.volume = record_data['volume']
                record.is_valid = True
                record.updated_at = TimestampConverter.get_current_datetime_for_db()
                self.logger.debug(f"更新 {symbol} {ts_str} 已有记录")
                return True
            else:
                # 创建新记录
                result = self.create_model_record(record_data)
                if result:
                    self.logger.debug(f"新增 {symbol} {ts_str} K线数据")
                    return True
                return False

        except Exception as e:
            self.logger.error(f"保存 {symbol} K线数据失败: {e}")
            return False

    def save_batch_daily_kline(self, symbol: str, klines: List[Dict[str, Any]]) -> bool:
        """
        批量保存日K线数据
        
        Args:
            symbol: 股票代码
            klines: K线数据列表
            
        Returns:
            bool: 保存是否成功
        """
        if not klines:
            self.logger.warning(f"{symbol} 无K线数据需要保存")
            return True

        try:
            success_count = 0
            fail_count = 0

            for kline_data in klines:
                if self.save_daily_kline(symbol, kline_data):
                    success_count += 1
                else:
                    fail_count += 1

            self.logger.info(f"{symbol} 批量保存完成: 成功 {success_count}, 失败 {fail_count}")
            return fail_count == 0

        except Exception as e:
            self.logger.error(f"批量保存 {symbol} K线数据失败: {e}")
            return False

    def get_latest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新的K线数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            K线数据字典或None
        """
        try:
            records = self.get_model_records_by_conditions(
                conditions={
                    "symbol": symbol.upper(),
                    "is_valid": True
                },
                limit=1,
                order_by="timestamp"
            )

            if records:
                record = records[0]
                return {
                    "symbol": record.symbol,
                    "timestamp": record.timestamp.strftime('%Y-%m-%d') if record.timestamp else None,
                    "open": record.open_price,
                    "high": record.high_price,
                    "low": record.low_price,
                    "close": record.close_price,
                    "volume": record.volume,
                    "source": record.source
                }

            return None

        except Exception as e:
            self.logger.error(f"获取 {symbol} 最新K线失败: {e}")
            return None

    def get_klines(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        获取指定日期范围的K线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            K线数据列表
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')

            records = self.get_model_records_by_conditions(
                conditions={
                    "symbol": symbol.upper(),
                    "is_valid": True,
                    "timestamp": (start_dt, end_dt)
                },
                order_by="timestamp",
                limit=10000
            )

            results = []
            for record in records:
                results.append({
                    "symbol": record.symbol,
                    "timestamp": record.timestamp.strftime('%Y-%m-%d') if record.timestamp else None,
                    "open": record.open_price,
                    "high": record.high_price,
                    "low": record.low_price,
                    "close": record.close_price,
                    "volume": record.volume,
                    "source": record.source
                })

            return results

        except Exception as e:
            self.logger.error(f"获取 {symbol} K线数据失败: {e}")
            return []

    def get_count(self, symbol: str) -> int:
        """获取某股票的总数据条数"""
        try:
            records = self.get_model_records_by_conditions(
                conditions={"symbol": symbol.upper(), "is_valid": True}
            )
            return len(records) if records else 0
        except Exception as e:
            self.logger.error(f"获取 {symbol} 数据条数失败: {e}")
            return 0

    def get_date_range(self, symbol: str) -> tuple:
        """获取某股票的数据日期范围 (min_date, max_date)"""
        try:
            records = self.get_model_records_by_conditions(
                conditions={"symbol": symbol.upper(), "is_valid": True},
                order_by="timestamp",
                limit=100000
            )
            
            if not records:
                return (None, None)
            
            timestamps = [r.timestamp for r in records if r.timestamp]
            if not timestamps:
                return (None, None)
            
            return (
                min(timestamps).strftime('%Y-%m-%d'),
                max(timestamps).strftime('%Y-%m-%d')
            )
        except Exception as e:
            self.logger.error(f"获取 {symbol} 日期范围失败: {e}")
            return (None, None)


# 单例模式
_us_stocks_service_instance = None


def get_us_stocks_service() -> USStocksServiceORM:
    """获取美股数据服务单例"""
    global _us_stocks_service_instance
    if _us_stocks_service_instance is None:
        _us_stocks_service_instance = USStocksServiceORM()
    return _us_stocks_service_instance
