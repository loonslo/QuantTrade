# -*- coding: utf-8 -*-
"""
美国市场数据ORM服务
处理纳斯达克、标普500指数和美元人民币汇率数据
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc, and_

from services.orm.base_orm_service import BaseORMService
from data.models.market_data.us_market_model import USMarketIndex, ExchangeRate
from utils.time.timestamp_utils import TimestampConverter


class USMarketServiceORM(BaseORMService):
    """美国市场指数ORM服务"""

    def __init__(self):
        super().__init__('us_market_service_orm', USMarketIndex)

    async def _execute_sync(self):
        """执行同步任务"""
        self.logger.info("美国市场指数同步任务执行")
        pass

    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置"""
        return {
            "task_name": "us_market_sync",
            "description": "美国市场指数数据同步",
            "enabled": True
        }

    def save_index_data(self, index_data: Dict[str, Any]) -> bool:
        """
        保存指数数据到数据库

        Args:
            index_data: 指数数据字典

        Returns:
            bool: 保存是否成功
        """
        try:
            symbol = index_data.get('symbol')
            if not symbol:
                self.logger.error("指数代码不能为空")
                return False

            # 先标记该指数的现有数据为无效
            self.mark_invalid_by_conditions({"symbol": symbol, "is_valid": True})

            # 准备记录数据
            current_time = TimestampConverter.get_current_datetime_for_db()
            data_timestamp = index_data.get('timestamp', current_time)
            
            record_data = {
                "symbol": symbol,
                "name": index_data.get("name", ""),
                "price": index_data.get("price", 0),
                "change": index_data.get("change", 0),
                "change_percent": index_data.get("change_percent", 0),
                "open_price": index_data.get("open"),
                "high_price": index_data.get("high"),
                "low_price": index_data.get("low"),
                "volume": index_data.get("volume", 0),
                "data_timestamp": data_timestamp,
                "is_valid": True,
                "source": index_data.get("source", "yahoo_finance")
            }

            # 创建记录
            result = self.create_model_record(record_data)

            if result:
                self.logger.info(f"{symbol} 指数数据保存成功: {record_data['price']}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"保存指数数据失败: {e}")
            return False

    def get_latest_index(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新的指数数据

        Args:
            symbol: 指数代码

        Returns:
            指数数据字典或None
        """
        try:
            records = self.get_model_records_by_conditions(
                conditions={"symbol": symbol, "is_valid": True},
                limit=1,
                order_by="data_timestamp"
            )

            if records:
                record = records[0]
                return {
                    "symbol": record.symbol,
                    "name": record.name,
                    "price": record.price,
                    "change": record.change,
                    "change_percent": record.change_percent,
                    "open": record.open_price,
                    "high": record.high_price,
                    "low": record.low_price,
                    "volume": record.volume,
                    "timestamp": record.data_timestamp,
                    "source": record.source
                }

            return None

        except Exception as e:
            self.logger.error(f"获取最新指数数据失败: {e}")
            return None

    def get_all_latest_indices(self) -> List[Dict[str, Any]]:
        """获取所有最新的指数数据"""
        results = []
        for symbol in ['NASDAQ', 'SP500']:
            data = self.get_latest_index(symbol)
            if data:
                results.append(data)
        return results


class ExchangeRateServiceORM(BaseORMService):
    """汇率数据ORM服务"""

    def __init__(self):
        super().__init__('exchange_rate_service_orm', ExchangeRate)

    async def _execute_sync(self):
        """执行同步任务"""
        self.logger.info("汇率数据同步任务执行")
        pass

    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置"""
        return {
            "task_name": "exchange_rate_sync",
            "description": "汇率数据同步",
            "enabled": True
        }

    def save_rate_data(self, rate_data: Dict[str, Any]) -> bool:
        """
        保存汇率数据到数据库

        Args:
            rate_data: 汇率数据字典

        Returns:
            bool: 保存是否成功
        """
        try:
            symbol = rate_data.get('symbol')
            if not symbol:
                self.logger.error("汇率代码不能为空")
                return False

            # 先标记该汇率的现有数据为无效
            self.mark_invalid_by_conditions({"symbol": symbol, "is_valid": True})

            # 准备记录数据
            current_time = TimestampConverter.get_current_datetime_for_db()
            data_timestamp = rate_data.get('timestamp', current_time)
            
            record_data = {
                "symbol": symbol,
                "name": rate_data.get("name", ""),
                "rate": rate_data.get("rate", 0),
                "change": rate_data.get("change", 0),
                "change_percent": rate_data.get("change_percent", 0),
                "open_rate": rate_data.get("open"),
                "high_rate": rate_data.get("high"),
                "low_rate": rate_data.get("low"),
                "data_timestamp": data_timestamp,
                "is_valid": True,
                "source": rate_data.get("source", "yahoo_finance")
            }

            # 创建记录
            result = self.create_model_record(record_data)

            if result:
                self.logger.info(f"{symbol} 汇率数据保存成功: {record_data['rate']}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"保存汇率数据失败: {e}")
            return False

    def get_latest_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新的汇率数据

        Args:
            symbol: 汇率代码

        Returns:
            汇率数据字典或None
        """
        try:
            records = self.get_model_records_by_conditions(
                conditions={"symbol": symbol, "is_valid": True},
                limit=1,
                order_by="data_timestamp"
            )

            if records:
                record = records[0]
                return {
                    "symbol": record.symbol,
                    "name": record.name,
                    "rate": record.rate,
                    "change": record.change,
                    "change_percent": record.change_percent,
                    "open": record.open_rate,
                    "high": record.high_rate,
                    "low": record.low_rate,
                    "timestamp": record.data_timestamp,
                    "source": record.source
                }

            return None

        except Exception as e:
            self.logger.error(f"获取最新汇率数据失败: {e}")
            return None


# 单例模式
_us_market_service_instance = None
_exchange_rate_service_instance = None


def get_us_market_service_orm() -> USMarketServiceORM:
    """获取美国市场服务单例"""
    global _us_market_service_instance
    if _us_market_service_instance is None:
        _us_market_service_instance = USMarketServiceORM()
    return _us_market_service_instance


def get_exchange_rate_service_orm() -> ExchangeRateServiceORM:
    """获取汇率服务单例"""
    global _exchange_rate_service_instance
    if _exchange_rate_service_instance is None:
        _exchange_rate_service_instance = ExchangeRateServiceORM()
    return _exchange_rate_service_instance
