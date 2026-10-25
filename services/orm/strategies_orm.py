# -*- coding: utf-8 -*-
"""
策略 ORM 服务
管理策略的配置信息、元数据和版本
"""

from typing import Dict, Any, Optional, List
import json

from services.orm.base_orm_service import BaseORMService
from data.models.market_data.strategies_model import Strategy


class StrategiesServiceORM(BaseORMService):
    """策略 ORM 服务"""

    def __init__(self):
        super().__init__('strategies_service_orm', Strategy)

    def get_strategy_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """根据策略ID获取策略"""
        with self.get_db_session(auto_commit=False) as session:
            return session.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()

    def get_active_strategies(self, source: Optional[str] = None,
                             category: Optional[str] = None) -> List[Strategy]:
        """获取激活的策略"""
        with self.get_db_session(auto_commit=False) as session:
            query = session.query(Strategy).filter(Strategy.is_active == True)

            if source:
                query = query.filter(Strategy.strategy_source == source)
            if category:
                query = query.filter(Strategy.strategy_category == category)

            return query.order_by(Strategy.created_at.desc()).all()

    def create_strategy(self, strategy_data: Dict[str, Any]) -> Optional[Strategy]:
        """创建策略"""
        try:
            # 检查策略ID是否已存在
            existing = self.get_strategy_by_id(strategy_data['strategy_id'])
            if existing:
                self.logger.error(f"策略ID已存在: {strategy_data['strategy_id']}")
                return None

            # 创建策略
            strategy = Strategy(**strategy_data)

            with self.get_db_session(auto_commit=True) as session:
                session.add(strategy)
                session.flush()

            self.logger.info(f"成功创建策略: {strategy.strategy_name}")
            return strategy

        except Exception as e:
            self.logger.error(f"创建策略失败: {e}", exc_info=True)
            return None

    def update_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]) -> Optional[Strategy]:
        """更新策略"""
        try:
            with self.get_db_session(auto_commit=True) as session:
                strategy = session.query(Strategy).filter(
                    Strategy.strategy_id == strategy_id
                ).first()

                if not strategy:
                    self.logger.error(f"策略不存在: {strategy_id}")
                    return None

                # 更新字段
                for key, value in strategy_data.items():
                    if hasattr(strategy, key):
                        setattr(strategy, key, value)

                strategy.updated_at = func.now()

                self.logger.info(f"成功更新策略: {strategy_id}")
                return strategy

        except Exception as e:
            self.logger.error(f"更新策略失败: {e}", exc_info=True)
            return None

    def delete_strategy(self, strategy_id: str) -> bool:
        """删除策略（软删除，设置is_active=False）"""
        try:
            with self.get_db_session(auto_commit=True) as session:
                strategy = session.query(Strategy).filter(
                    Strategy.strategy_id == strategy_id
                ).first()

                if not strategy:
                    self.logger.error(f"策略不存在: {strategy_id}")
                    return False

                strategy.is_active = False
                strategy.updated_at = func.now()

                self.logger.info(f"成功删除策略: {strategy_id}")
                return True

        except Exception as e:
            self.logger.error(f"删除策略失败: {e}", exc_info=True)
            return False

    def get_strategies_by_source(self, source: str) -> List[Strategy]:
        """根据来源获取策略"""
        with self.get_db_session(auto_commit=False) as session:
            return session.query(Strategy).filter(
                Strategy.strategy_source == source,
                Strategy.is_active == True
            ).order_by(Strategy.created_at.desc()).all()

    def get_strategies_by_category(self, category: str) -> List[Strategy]:
        """根据分类获取策略"""
        with self.get_db_session(auto_commit=False) as session:
            return session.query(Strategy).filter(
                Strategy.strategy_category == category,
                Strategy.is_active == True
            ).order_by(Strategy.created_at.desc()).all()

    def get_default_strategies(self) -> List[Strategy]:
        """获取默认策略"""
        with self.get_db_session(auto_commit=False) as session:
            return session.query(Strategy).filter(
                Strategy.is_default == True,
                Strategy.is_active == True
            ).order_by(Strategy.created_at.desc()).all()

    def update_performance_metrics(self, strategy_id: str, metrics: Dict[str, Any]) -> bool:
        """更新策略性能指标"""
        try:
            with self.get_db_session(auto_commit=True) as session:
                strategy = session.query(Strategy).filter(
                    Strategy.strategy_id == strategy_id
                ).first()

                if not strategy:
                    self.logger.error(f"策略不存在: {strategy_id}")
                    return False

                # 更新性能指标
                strategy.update_performance_metrics(**metrics)

                self.logger.info(f"成功更新策略性能指标: {strategy_id}")
                return True

        except Exception as e:
            self.logger.error(f"更新策略性能指标失败: {e}", exc_info=True)
            return False

    def get_strategies_performance_stats(self) -> Dict[str, Any]:
        """获取策略性能统计"""
        with self.get_db_session(auto_commit=False) as session:
            from sqlalchemy import func, case

            # 按来源统计
            source_stats = session.query(
                Strategy.strategy_source,
                func.count(Strategy.id).label('count'),
                func.avg(Strategy.success_rate).label('avg_success_rate'),
                func.avg(Strategy.avg_confidence).label('avg_confidence')
            ).filter(
                Strategy.is_active == True
            ).group_by(Strategy.strategy_source).all()

            # 按分类统计
            category_stats = session.query(
                Strategy.strategy_category,
                func.count(Strategy.id).label('count'),
                func.avg(Strategy.success_rate).label('avg_success_rate'),
                func.avg(Strategy.avg_confidence).label('avg_confidence')
            ).filter(
                Strategy.is_active == True
            ).group_by(Strategy.strategy_category).all()

            # 总策略数
            total_strategies = session.query(Strategy).filter(
                Strategy.is_active == True
            ).count()

            return {
                'total_strategies': total_strategies,
                'by_source': [
                    {
                        'source': stat.strategy_source,
                        'count': stat.count,
                        'avg_success_rate': float(stat.avg_success_rate) if stat.avg_success_rate else None,
                        'avg_confidence': float(stat.avg_confidence) if stat.avg_confidence else None
                    }
                    for stat in source_stats
                ],
                'by_category': [
                    {
                        'category': stat.strategy_category,
                        'count': stat.count,
                        'avg_success_rate': float(stat.avg_success_rate) if stat.avg_success_rate else None,
                        'avg_confidence': float(stat.avg_confidence) if stat.avg_confidence else None
                    }
                    for stat in category_stats
                ]
            }

    async def _execute_sync(self):
        return None

    def get_task_config(self) -> Dict[str, Any]:
        return {
            'task_name': 'strategies_sync',
            'enabled': True,
        }


# 全局实例
_strategies_service_orm: Optional[StrategiesServiceORM] = None


def get_strategies_service_orm() -> StrategiesServiceORM:
    global _strategies_service_orm
    if _strategies_service_orm is None:
        _strategies_service_orm = StrategiesServiceORM()
    return _strategies_service_orm
