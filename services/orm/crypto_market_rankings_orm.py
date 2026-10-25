# -*- coding: utf-8 -*-
"""
加密货币市场排行ORM服务
提供加密货币市场排行数据管理功能 - 基于SQLAlchemy ORM
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import desc, and_, asc

from services.orm.base_orm_service import BaseORMService
from data.models.market_data import CryptoMarketRankings
from data.types import SymbolData
from utils.time.timestamp_utils import TimestampConverter

class CryptoMarketRankingsServiceORM(BaseORMService):
    """加密货币市场排行ORM服务"""

    def __init__(self):
        super().__init__('crypto_market_rankings_service_orm', CryptoMarketRankings)

    def save_market_rankings(self, symbols_data: List[Dict[str, Any]]) -> bool:
        """
        保存市场排行数据到数据库的ORM方法
        先将同源同 quote_asset 的历史记录设置为is_valid=False，
        然后插入新数据并设置is_valid=True

        Args:
            symbols_data: 市场排行数据列表

        Returns:
            bool: 保存是否成功
        """
        try:
            current_time = TimestampConverter.get_current_datetime_for_db()
            
            # 获取所有涉及的quote_asset
            quote_assets = list(set(symbol["quote_asset"] for symbol in symbols_data))
            
            for quote_asset in quote_assets:
                # 将该quote_asset的所有有效记录设置为无效
                self.mark_invalid_by_conditions({
                    "quote_asset": quote_asset,
                    "is_valid": True
                })

            # 准备记录数据
            records_data = []
            for rank, symbol_data in enumerate(symbols_data, 1):
                record_data = {
                    "symbol": symbol_data["symbol"],
                    "quote_asset": symbol_data["quote_asset"],
                    "price": symbol_data["price"],
                    "change_24h": symbol_data["change_24h"],
                    "change_amount": symbol_data["change_amount"],
                    "volume_24h": symbol_data["volume_24h"],
                    "market_cap": symbol_data["market_cap"],
                    "market_cap_rank": rank,
                    "data_timestamp": current_time,
                    "is_valid": True,
                    "source": symbol_data.get("source", "binance")
                }
                records_data.append(record_data)

            # 使用批量创建方法
            result = True
            for record_data in records_data:
                if not self.create_model_record(record_data):
                    result = False
                    break
            
            if result:
                self.logger.info("成功保存 {} 条市场排行数据".format(len(symbols_data)))
                return True
            else:
                return False

        except Exception as e:
            self.logger.error("保存市场排行数据失败: {}".format(e))
            return False



    def get_latest_rankings(self, quote_asset: str = "USDT", limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取最新的市场排行数据

        Args:
            quote_asset: 计价货币
            limit: 限制数量

        Returns:
            List[Dict[str, Any]]: 排行数据列表
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                records = session.query(CryptoMarketRankings).filter(
                    and_(
                        CryptoMarketRankings.quote_asset == quote_asset,
                        CryptoMarketRankings.is_valid.is_(True)
                    )
                ).order_by(asc(CryptoMarketRankings.market_cap_rank)).limit(limit).all()
                
                return [self._model_to_dict(record) for record in records]

        except Exception as e:
            self.logger.error("获取最新排行数据失败: {}".format(e))
            return []



    def get_rankings_by_change(self, quote_asset: str = "USDT", 
                              order: str = "desc", limit: int = 50) -> List[Dict[str, Any]]:
        """
        按涨跌幅获取排行数据

        Args:
            quote_asset: 计价货币
            order: 排序方式 'desc'(跌幅榜) 或 'asc'(涨幅榜)
            limit: 限制数量

        Returns:
            List[Dict[str, Any]]: 排行数据列表
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                query = session.query(CryptoMarketRankings).filter(
                    and_(
                        CryptoMarketRankings.quote_asset == quote_asset,
                        CryptoMarketRankings.is_valid.is_(True)
                    )
                )

                if order == "desc":
                    query = query.order_by(desc(CryptoMarketRankings.change_24h))
                else:
                    query = query.order_by(asc(CryptoMarketRankings.change_24h))

                records = query.limit(limit).all()
                return [self._model_to_dict(record) for record in records]

        except Exception as e:
            self.logger.error("按涨跌幅获取排行数据失败: {}".format(e))
            return []

    def get_rankings_summary(self, quote_asset: str = "USDT") -> Dict[str, Any]:
        """
        获取排行数据统计信息

        Args:
            quote_asset: 计价货币

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                # 获取总记录数
                total_count = session.query(CryptoMarketRankings).filter(
                    and_(
                        CryptoMarketRankings.quote_asset == quote_asset,
                        CryptoMarketRankings.is_valid.is_(True)
                    )
                ).count()

                # 获取最新更新时间
                latest_record = session.query(CryptoMarketRankings).filter(
                    and_(
                        CryptoMarketRankings.quote_asset == quote_asset,
                        CryptoMarketRankings.is_valid.is_(True)
                    )
                ).order_by(desc(CryptoMarketRankings.updated_at)).first()

                latest_updated_at = None
                if latest_record:
                    latest_updated_at = latest_record.updated_at.strftime('%Y-%m-%d %H:%M:%S')

                # 计算涨跌统计
                from sqlalchemy import func
                change_stats = session.query(
                    func.count().label('total'),
                    func.sum(func.case([(CryptoMarketRankings.change_24h > 0, 1)], else_=0)).label('gainers'),
                    func.sum(func.case([(CryptoMarketRankings.change_24h < 0, 1)], else_=0)).label('losers'),
                    func.avg(CryptoMarketRankings.change_24h).label('avg_change')
                ).filter(
                    and_(
                        CryptoMarketRankings.quote_asset == quote_asset,
                        CryptoMarketRankings.is_valid == True
                    )
                ).first()

                return {
                    "total_count": total_count,
                    "quote_asset": quote_asset,
                    "latest_updated_at": latest_updated_at,
                    "gainers_count": int(change_stats.gainers or 0),
                    "losers_count": int(change_stats.losers or 0),
                    "neutral_count": total_count - int(change_stats.gainers or 0) - int(change_stats.losers or 0),
                    "avg_change_24h": float(change_stats.avg_change or 0)
                }

        except Exception as e:
            self.logger.error("获取排行统计信息失败: {}".format(e))
            return {
                "total_count": 0,
                "quote_asset": quote_asset,
                "latest_updated_at": None,
                "gainers_count": 0,
                "losers_count": 0,
                "neutral_count": 0,
                "avg_change_24h": 0.0
            }





# 全局服务实例
_crypto_market_rankings_service_orm: Optional[CryptoMarketRankingsServiceORM] = None

def get_crypto_market_rankings_service_orm() -> CryptoMarketRankingsServiceORM:
    """获取市场排行服务实例（单例模式）"""
    global _crypto_market_rankings_service_orm
    if _crypto_market_rankings_service_orm is None:
        _crypto_market_rankings_service_orm = CryptoMarketRankingsServiceORM()
    return _crypto_market_rankings_service_orm

