# -*- coding: utf-8 -*-
"""
市场概览ORM服务
处理市场概览数据和恐惧贪婪指数（已合并到MarketOverview表）
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc, and_

from services.orm.base_orm_service import BaseORMService
from data.models.market_data import MarketOverview
from utils.time.timestamp_utils import TimestampConverter


class MarketOverviewServiceORM(BaseORMService):
    """市场概览ORM服务"""

    def __init__(self):
        super().__init__('market_overview_service_orm', MarketOverview)

    async def _execute_sync(self):
        """执行同步任务（抽象方法实现）"""
        self.logger.info("MarketOverview同步任务执行")
        # 这里可以添加具体的同步逻辑
        pass

    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置（抽象方法实现）"""
        return {
            "task_name": "market_overview_sync",
            "description": "市场概览数据同步",
            "enabled": True
        }

    def save_market_overview(self, overview_data: Dict[str, Any]) -> bool:
        """
        保存市场概览数据到数据库（使用统一的时间戳处理）

        Args:
            overview_data: 市场概览数据字典

        Returns:
            bool: 保存是否成功
        """
        try:
            # 先标记现有数据为无效
            self.mark_invalid_by_conditions({"is_valid": True})

            # 准备记录数据
            current_time = TimestampConverter.get_current_datetime_for_db()
            record_data = {
                "total_market_cap": overview_data.get("total_market_cap", 0),
                "total_volume_24h": overview_data.get("total_volume_24h", 0),
                "market_trend": overview_data.get("market_trend", "neutral"),
                "risk_level": overview_data.get("risk_level", "medium"),
                "btc_dominance": overview_data.get("btc_dominance", 0),
                "eth_dominance": overview_data.get("eth_dominance", 0),
                "fear_greed_value": overview_data.get("fear_greed_value", 50),
                "fear_greed_classification": overview_data.get("fear_greed_classification", "Neutral"),
                "data_timestamp": current_time,
                "is_valid": True,
                "source": overview_data.get("source", "data_sync")
                # created_at 和 updated_at 会自动设置
            }

            # 使用统一的创建方法
            result = self.create_model_record(record_data)

            if result:
                self.logger.info(f"市场概览数据保存成功")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"保存市场概览数据失败: {e}")
            return False

    def save_fear_greed_index(self, fear_greed_data: Dict[str, Any]) -> bool:
        """
        保存恐惧贪婪指数数据（使用统一的时间戳处理）

        Args:
            fear_greed_data: 恐惧贪婪指数数据

        Returns:
            bool: 保存是否成功
        """
        try:
            # 获取最新的市场概览记录
            latest_records = self.get_model_records_by_conditions(
                conditions={"is_valid": True},
                limit=1,
                order_by="data_timestamp"  # 需要降序，这里简化处理
            )

            current_time = TimestampConverter.get_current_datetime_for_db()

            if latest_records:
                # 更新现有记录的恐惧贪婪指数
                latest_overview = latest_records[0]
                update_data = {
                    "fear_greed_value": fear_greed_data.get("value", 50),
                    "fear_greed_classification": fear_greed_data.get("classification", "Neutral")
                }
                
                success = self.update_model_record(latest_overview.id, update_data)
                if success:
                    self.logger.info(f"更新现有市场概览记录的恐惧贪婪指数")
                return success
            else:
                # 创建新的市场概览记录，只包含恐惧贪婪指数
                record_data = {
                    "total_market_cap": 0,
                    "total_volume_24h": 0,
                    "market_trend": "neutral",
                    "risk_level": "medium",
                    "btc_dominance": 0,
                    "eth_dominance": 0,
                    "fear_greed_value": fear_greed_data.get("value", 50),
                    "fear_greed_classification": fear_greed_data.get("classification", "Neutral"),
                    "data_timestamp": current_time,
                    "is_valid": True,
                    "source": fear_greed_data.get("source", "alternative.me")
                    # created_at 和 updated_at 会自动设置
                }
                
                result = self.create_model_record(record_data)
                if result:
                    self.logger.info(f"创建新的市场概览记录（仅恐惧贪婪指数）")
                    return True
                return False

        except Exception as e:
            self.logger.error(f"保存恐惧贪婪指数失败: {e}")
            return False

    def get_latest_market_overview(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的市场概览数据

        Returns:
            Optional[Dict[str, Any]]: 最新市场概览数据或None
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                record = session.query(MarketOverview).filter(
                    MarketOverview.is_valid.is_(True)
                ).order_by(desc(MarketOverview.data_timestamp)).first()

                if record:
                    return {
                        "total_market_cap": record.total_market_cap,
                        "total_volume_24h": record.total_volume_24h,
                        "market_trend": record.market_trend,
                        "risk_level": record.risk_level,
                        "btc_dominance": record.btc_dominance,
                        "eth_dominance": record.eth_dominance,
                        "fear_greed_value": record.fear_greed_value,
                        "fear_greed_classification": record.fear_greed_classification,
                        "data_timestamp": record.data_timestamp,
                        "source": record.source,
                        "created_at": record.created_at,
                        "updated_at": record.updated_at
                    }
                return None

        except Exception as e:
            self.logger.error(f"获取最新市场概览数据失败: {e}")
            return None

    def get_fear_greed_history(self, days: int = 30) -> list:
        """
        获取恐惧贪婪指数历史数据

        Args:
            days: 获取最近多少天的数据

        Returns:
            list: 历史数据列表
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                cutoff_date = datetime.now() - timedelta(days=days)

                records = session.query(MarketOverview).filter(
                    and_(
                        MarketOverview.is_valid.is_(True),
                        MarketOverview.data_timestamp >= cutoff_date,
                        MarketOverview.fear_greed_value.isnot(None)
                    )
                ).order_by(desc(MarketOverview.data_timestamp)).all()

                return [{
                    "value": record.fear_greed_value,
                    "classification": record.fear_greed_classification,
                    "timestamp": record.data_timestamp,
                    "source": record.source
                } for record in records]

        except Exception as e:
            self.logger.error(f"获取恐惧贪婪指数历史数据失败: {e}")
            return []


# 全局服务实例
_market_overview_service_orm: Optional[MarketOverviewServiceORM] = None


def get_market_overview_service_orm() -> MarketOverviewServiceORM:
    """获取市场概览服务实例（单例模式）"""
    global _market_overview_service_orm
    if _market_overview_service_orm is None:
        _market_overview_service_orm = MarketOverviewServiceORM()
    return _market_overview_service_orm