# -*- coding: utf-8 -*-
"""
K线数据ORM服务
提供K线数据管理功能 - 基于SQLAlchemy ORM
支持按时间框架分组的数据库表管理
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import desc, and_, asc, func, distinct

from services.orm.base_orm_service import BaseORMService
from data.models.market_data import KlineData1m, KlineData5m, KlineData15m, KlineData1h, KlineData4h, KlineData1d
from utils.time.timestamp_utils import TimestampConverter

class KlineDataServiceORM(BaseORMService):
    """K线数据ORM服务"""

    def __init__(self, use_timeframe_tables: bool = True):
        """
        初始化K线数据服务

        Args:
            use_timeframe_tables: 是否使用按时间框架分组的数据库表
        """
        # 使用默认模型，具体模型会根据时间框架动态选择
        super().__init__('kline_data_service_orm', KlineData1m)
        self.use_timeframe_tables = use_timeframe_tables

        # 数据保留策略
        self.retention_policy = {
            '1m': 180,   # 6个月
            '5m': 365,   # 1年
            '15m': 730,  # 2年
            '1h': 1095,  # 3年
            '4h': 1460,  # 4年（可按需调整）
            '1d': 1825   # 5年
        }

    def get_model_class(self, timeframe: str):
        """根据时间框架获取对应的模型类"""
        timeframe_models = {
            '1m': KlineData1m,
            '5m': KlineData5m,
            '15m': KlineData15m,
            '1h': KlineData1h,
            '4h': KlineData4h,
            '1d': KlineData1d
        }
        
        if timeframe in timeframe_models:
            return timeframe_models[timeframe]
        else:
            raise ValueError("不支持的时间框架: {}，支持的时间框架: {}".format(timeframe, list(timeframe_models.keys())))

    def save_kline_data(self, symbol: str, timeframe: str, data: pd.DataFrame, source: str = "binance") -> bool:
        """
        保存K线数据到数据库（使用统一的时间戳处理）

        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            data: K线数据DataFrame
            source: 数据来源

        Returns:
            bool: 保存是否成功
        """
        try:
            if data.empty:
                self.logger.warning("DataFrame为空，跳过保存")
                return True

            # 动态设置模型类
            self.model_class = self.get_model_class(timeframe)

            # 先标记现有数据为无效
            invalidate_conditions = {
                "symbol": symbol,
                "source": source,
                "is_valid": True
            }
            
            if not self.use_timeframe_tables:
                invalidate_conditions["timeframe"] = timeframe

            self.mark_invalid_by_conditions(invalidate_conditions)

            # 准备批量插入的数据
            records_to_insert = []
            for index, row in data.iterrows():
                # 从datetime列获取时间戳，而不是从索引
                if 'datetime' in row and pd.notna(row['datetime']):
                    if hasattr(row['datetime'], 'strftime'):
                        timestamp_str = row['datetime'].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        timestamp_str = str(row['datetime'])
                elif hasattr(index, 'strftime'):
                    # 备选方案：从索引获取
                    timestamp_str = index.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp_str = str(index)

                record_data = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": timestamp_str,
                    "open_price": float(row.get("open", 0)),
                    "high_price": float(row.get("high", 0)),
                    "low_price": float(row.get("low", 0)),
                    "close_price": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)),
                    "source": source,
                    "is_valid": True
                }

                # 只有当模型支持时，才添加期货指标字段
                if hasattr(self.get_model_class(timeframe), 'open_interest'):
                    record_data["open_interest"] = float(row.get("open_interest", 0)) if row.get("open_interest") is not None else None
                if hasattr(self.get_model_class(timeframe), 'funding_rate'):
                    record_data["funding_rate"] = float(row.get("funding_rate", 0)) if row.get("funding_rate") is not None else None
                records_to_insert.append(record_data)

            # 使用统一的批量 upsert
            unique_fields = ["symbol", "timeframe", "timestamp", "source"]
            success = self.batch_upsert(records_to_insert, unique_fields)

            if success:
                self.logger.info("K线数据保存到{}: {} {} {} 条记录".format(self.model_class.__tablename__, symbol, timeframe, len(data)))
            
            return success

        except Exception as e:
            self.logger.error("保存K线数据失败: {}".format(e))
            return False

    def load_kline_data(self, symbol: str, start_time: str, end_time: str, limit: int = 500,
                        timeframe: str = None, source: str = None, only_valid: bool = False) -> pd.DataFrame:
        """
        从数据库加载K线数据

        Args:
            symbol: 交易对符号
            start_time: 开始时间
            end_time: 结束时间
            limit: 记录数量限制
            timeframe: 时间框架
            source: 数据来源
            only_valid: 是否只获取有效记录

        Returns:
            pd.DataFrame: K线数据DataFrame
        """
        try:
            if not timeframe:
                raise ValueError("使用按时间框架分组的表时必须指定 timeframe 参数")

            model_class = self.get_model_class(timeframe)

            with self.get_db_session(auto_commit=False) as session:
                # 构建查询
                query = session.query(model_class).filter(
                    and_(
                        model_class.symbol == symbol,
                        model_class.timestamp >= start_time,
                        model_class.timestamp <= end_time
                    )
                )

                # 注意：对于按时间框架分组的表（KlineData5m等），
                # 表中每条记录的timeframe字段值应该等于表名对应的timeframe
                # 这里不需要再次过滤timeframe，因为表本身就是按timeframe分组的
                # if timeframe:
                #     query = query.filter(model_class.timeframe == timeframe)

                if source:
                    query = query.filter(model_class.source == source)

                if only_valid:
                    query = query.filter(model_class.is_valid.is_(True))

                records = query.order_by(asc(model_class.timestamp)).limit(limit).all()

                if not records:
                    return pd.DataFrame()

                data = []
                for record in records:
                    data.append({
                        "timestamp": record.timestamp,
                        "open": record.open_price,
                        "high": record.high_price,
                        "low": record.low_price,
                        "close": record.close_price,
                        "volume": record.volume,
                        "open_interest": getattr(record, 'open_interest', None),
                        "funding_rate": getattr(record, 'funding_rate', None),
                        "timeframe": record.timeframe,
                        "source": record.source,
                        "is_valid": record.is_valid,
                        "created_at": record.created_at,
                        "updated_at": record.updated_at
                    })

                df = pd.DataFrame(data)
                df.set_index("timestamp", inplace=True)
                return df

        except Exception as e:
            self.logger.error("从数据库加载K线数据失败: {}".format(e))
            return pd.DataFrame()

    def get_kline_data_summary(self, timeframe: str = None, only_valid: bool = True) -> Dict[str, Any]:
        """
        获取K线数据统计信息

        Args:
            timeframe: 时间框架
            only_valid: 是否只统计有效记录

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            if not timeframe:
                raise ValueError("使用按时间框架分组的表时必须指定 timeframe 参数")

            model_class = self.get_model_class(timeframe)

            with self.get_db_session(auto_commit=False) as session:
                query = session.query(model_class)

                if timeframe:
                    query = query.filter(model_class.timeframe == timeframe)

                if only_valid:
                    query = query.filter(model_class.is_valid.is_(True))

                # 获取总记录数
                total_records = query.count()

                # 获取交易对数量
                symbol_count = query.with_entities(model_class.symbol).distinct().count()

                # 获取时间框架数量
                timeframe_count = query.with_entities(model_class.timeframe).distinct().count()

                # 获取最新数据时间
                latest_time = query.with_entities(func.max(model_class.timestamp)).scalar()

                # 获取最新创建时间
                latest_created = query.with_entities(func.max(model_class.created_at)).scalar()

                return {
                    "table_name": model_class.__tablename__,
                    "timeframe": timeframe,
                    "total_records": total_records,
                    "symbol_count": symbol_count,
                    "timeframe_count": timeframe_count,
                    "latest_time": latest_time,
                    "latest_created": latest_created,
                    "only_valid": only_valid
                }

        except Exception as e:
            self.logger.error("获取K线数据统计信息失败: {}".format(e))
            return {}

    def get_available_symbols(self, timeframe: str = None, only_valid: bool = True) -> List[str]:
        """
        获取可用交易对列表

        Args:
            timeframe: 时间框架
            only_valid: 是否只获取有效记录的交易对

        Returns:
            List[str]: 交易对列表
        """
        try:
            if not timeframe:
                raise ValueError("使用按时间框架分组的表时必须指定 timeframe 参数")

            model_class = self.get_model_class(timeframe)

            with self.get_db_session(auto_commit=False) as session:
                query = session.query(distinct(model_class.symbol))

                if timeframe:
                    query = query.filter(model_class.timeframe == timeframe)

                if only_valid:
                    query = query.filter(model_class.is_valid.is_(True))

                symbols = [row[0] for row in query.order_by(model_class.symbol).all()]
                return symbols

        except Exception as e:
            self.logger.error("获取可用交易对列表失败: {}".format(e))
            return []

    def get_available_timeframes(self, only_valid: bool = True) -> List[str]:
        """
        获取可用时间框架列表

        Args:
            only_valid: 是否只获取有效记录的时间框架

        Returns:
            List[str]: 时间框架列表
        """
        return ['1m', '5m', '15m', '1h', '1d']

    def get_latest_kline_data(self, symbol: str, timeframe: str = None, source: str = None) -> Optional[Dict[str, Any]]:
        """
        获取最新的K线数据

        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            source: 数据来源

        Returns:
            Optional[Dict[str, Any]]: 最新K线数据或None
        """
        try:
            if not timeframe:
                raise ValueError("使用按时间框架分组的表时必须指定 timeframe 参数")

            model_class = self.get_model_class(timeframe)

            with self.get_db_session(auto_commit=False) as session:
                query = session.query(model_class).filter(
                    and_(
                        model_class.symbol == symbol,
                        model_class.is_valid == True
                    )
                )

                if timeframe:
                    query = query.filter(model_class.timeframe == timeframe)

                if source:
                    query = query.filter(model_class.source == source)

                record = query.order_by(desc(model_class.timestamp)).first()

                if record:
                    return {
                        "timestamp": record.timestamp,
                        "open": record.open_price,
                        "high": record.high_price,
                        "low": record.low_price,
                        "close": record.close_price,
                        "volume": record.volume,
                        "open_interest": record.open_interest,
                        "funding_rate": record.funding_rate,
                        "timeframe": record.timeframe,
                        "source": record.source,
                        "created_at": record.created_at,
                        "updated_at": record.updated_at
                    }
                return None

        except Exception as e:
            self.logger.error("获取最新K线数据失败: {}".format(e))
            return None

    def cleanup_expired_data(self, timeframe: str = None) -> bool:
        """
        清理过期数据

        Args:
            timeframe: 时间框架

        Returns:
            bool: 清理是否成功
        """
        try:
            if self.use_timeframe_tables and not timeframe:
                raise ValueError("使用按时间框架分组的表时必须指定 timeframe 参数")

            model_class = self.get_model_class(timeframe) if self.use_timeframe_tables else KlineData
            retention_days = self.retention_policy.get(timeframe, 180) if timeframe else 180

            # 动态设置模型类
            self.model_class = model_class
            
            cutoff_time = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # 使用统一的标记无效方法
            with self.get_db_session() as session:
                # 标记过期数据
                updated_count = session.query(model_class).filter(
                    and_(
                        model_class.timestamp < cutoff_time,
                        model_class.is_valid.is_(True)
                    )
                ).update({
                    "is_valid": False
                    # updated_at 会自动更新
                })

                self.logger.info("清理 {} 过期数据: {} 条".format(model_class.__tablename__, updated_count))
                return True

        except Exception as e:
            self.logger.error("清理过期数据失败: {}".format(e))
            return False

    def get_kline_statistics(self, symbol: str, timeframe: str, days: int = 30,
                             source: str = None) -> Dict[str, Any]:
        """
        获取K线统计信息

        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            days: 统计天数
            source: 数据来源

        Returns:
            Dict[str, Any]: K线统计信息
        """
        try:
            model_class = self.get_model_class(timeframe) if self.use_timeframe_tables else KlineData

            with self.get_db_session(auto_commit=False) as session:
                cutoff_date = datetime.now() - timedelta(days=days)
                cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

                query = session.query(
                    func.max(model_class.high_price).label('max_high'),
                    func.min(model_class.low_price).label('min_low'),
                    func.avg(model_class.close_price).label('avg_close'),
                    func.sum(model_class.volume).label('total_volume'),
                    func.count(model_class.id).label('record_count')
                ).filter(
                    and_(
                        model_class.symbol == symbol,
                        model_class.timeframe == timeframe,
                        model_class.timestamp >= cutoff_date_str,
                        model_class.is_valid == True
                    )
                )

                if source:
                    query = query.filter(model_class.source == source)

                result = query.first()

                if result:
                    return {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "days": days,
                        "max_high": float(result.max_high) if result.max_high else 0,
                        "min_low": float(result.min_low) if result.min_low else 0,
                        "avg_close": float(result.avg_close) if result.avg_close else 0,
                        "total_volume": float(result.total_volume) if result.total_volume else 0,
                        "record_count": result.record_count or 0,
                        "source": source
                    }
                else:
                    return {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "days": days,
                        "max_high": 0,
                        "min_low": 0,
                        "avg_close": 0,
                        "total_volume": 0,
                        "record_count": 0,
                        "source": source
                    }

        except Exception as e:
            self.logger.error("获取K线统计信息失败: {}".format(e))
            return {}

# =========================
# 任务执行
# =========================

    async def _execute_sync(self):
        """
        执行K线数据同步任务
        """
        try:
            self.logger.info("开始执行K线数据同步任务")

            # 这里可以添加具体的同步逻辑
            # 例如从外部API获取K线数据保存到数据库
            # 或者处理其他数据同步任务
            self.logger.info("K线数据同步任务执行完成")

        except Exception as e:
            self.logger.error("K线数据同步任务执行失败: {}".format(e))
            raise

    def get_task_config(self) -> Dict[str, Any]:
        """
        获取K线数据同步任务配置
        """
        return {
            "task_id": "kline_data_sync",
            "func_name": "sync_kline_data",
            "trigger_type": "interval",
            "trigger_args": {
                "minutes": 5  # 每5分钟执行一次
            },
            "max_instances": 1,
            "coalesce": True,
            "misfire_grace_time": 60,
            "enabled": True,
            "description": "K线数据同步任务"
        }

# 全局服务实例
_kline_data_service_orm: Optional[KlineDataServiceORM] = None

def get_kline_data_service_orm(use_timeframe_tables: bool = False) -> KlineDataServiceORM:
    """获取K线数据服务实例（单例模式）"""
    global _kline_data_service_orm
    if _kline_data_service_orm is None or _kline_data_service_orm.use_timeframe_tables != use_timeframe_tables:
        _kline_data_service_orm = KlineDataServiceORM(use_timeframe_tables)
    return _kline_data_service_orm

