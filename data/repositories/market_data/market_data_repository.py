"""
市场数据仓储
处理市场数据的存储和查询
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy import and_, desc, asc, func

from ..repository_base import BaseRepository
from data.models.market_data import FearGreedIndex, MarketOverview
from data.models.market_data import KlineData1m, KlineData1h, KlineData1d, CryptoMarketRankings
from utils.validation.exceptions import DataException
from data.database.session_manager import get_session_manager, get_logger


class FearGreedRepository(BaseRepository):
    """恐惧贪婪指数仓储"""
    
    def __init__(self):
        super().__init__(FearGreedIndex, "FearGreedRepository")
    
    async def get_latest(self) -> Optional[FearGreedIndex]:
        """获取最新的恐惧贪婪指数"""
        try:
            with self.get_session() as session:
                return session.query(FearGreedIndex).filter(
                    FearGreedIndex.is_valid == True
                ).order_by(desc(FearGreedIndex.data_timestamp)).first()
        except Exception as e:
            self.logger.error(f"获取最新恐惧贪婪指数失败: {str(e)}")
            raise DataException(f"获取最新恐惧贪婪指数失败: {str(e)}")
    
    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[FearGreedIndex]:
        """根据日期范围获取恐惧贪婪指数"""
        try:
            with self.get_session() as session:
                return session.query(FearGreedIndex).filter(
                    and_(
                        FearGreedIndex.data_timestamp >= start_date,
                        FearGreedIndex.data_timestamp <= end_date,
                        FearGreedIndex.is_valid == True
                    )
                ).order_by(FearGreedIndex.data_timestamp).all()
        except Exception as e:
            self.logger.error(f"根据日期范围获取恐惧贪婪指数失败: {str(e)}")
            raise DataException(f"根据日期范围获取恐惧贪婪指数失败: {str(e)}")
    
    async def get_by_value_range(self, min_value: int, max_value: int) -> List[FearGreedIndex]:
        """根据数值范围获取恐惧贪婪指数"""
        try:
            with self.get_session() as session:
                return session.query(FearGreedIndex).filter(
                    and_(
                        FearGreedIndex.value >= min_value,
                        FearGreedIndex.value <= max_value,
                        FearGreedIndex.is_valid == True
                    )
                ).order_by(desc(FearGreedIndex.data_timestamp)).all()
        except Exception as e:
            self.logger.error(f"根据数值范围获取恐惧贪婪指数失败: {str(e)}")
            raise DataException(f"根据数值范围获取恐惧贪婪指数失败: {str(e)}")


class CoinDetailsRepository(BaseRepository):
    """币种详情仓储"""
    
    def __init__(self):
        super().__init__(CoinDetails, "CoinDetailsRepository")
    
    async def get_by_symbol(self, symbol: str) -> Optional[CoinDetails]:
        """根据交易对获取最新币种详情"""
        try:
            with self.get_session() as session:
                return session.query(CoinDetails).filter(
                    and_(
                        CoinDetails.symbol == symbol.upper(),
                        CoinDetails.is_valid == True
                    )
                ).order_by(desc(CoinDetails.data_timestamp)).first()
        except Exception as e:
            self.logger.error(f"根据交易对获取币种详情失败: {symbol}, {str(e)}")
            raise DataException(f"根据交易对获取币种详情失败: {str(e)}")
    
    async def get_by_symbols(self, symbols: List[str]) -> List[CoinDetails]:
        """根据交易对列表获取币种详情"""
        try:
            with self.get_session() as session:
                symbols_upper = [s.upper() for s in symbols]
                return session.query(CoinDetails).filter(
                    and_(
                        CoinDetails.symbol.in_(symbols_upper),
                        CoinDetails.is_valid == True
                    )
                ).order_by(CoinDetails.symbol, desc(CoinDetails.data_timestamp)).all()
        except Exception as e:
            self.logger.error(f"根据交易对列表获取币种详情失败: {str(e)}")
            raise DataException(f"根据交易对列表获取币种详情失败: {str(e)}")
    
    async def get_by_trend(self, trend: str) -> List[CoinDetails]:
        """根据趋势获取币种详情"""
        try:
            with self.get_session() as session:
                return session.query(CoinDetails).filter(
                    and_(
                        CoinDetails.trend == trend,
                        CoinDetails.is_valid == True
                    )
                ).order_by(desc(CoinDetails.data_timestamp)).all()
        except Exception as e:
            self.logger.error(f"根据趋势获取币种详情失败: {trend}, {str(e)}")
            raise DataException(f"根据趋势获取币种详情失败: {str(e)}")
    
    async def get_top_performers(self, limit: int = 10, by_change: bool = True) -> List[CoinDetails]:
        """获取表现最佳的币种"""
        try:
            with self.get_session() as session:
                query = session.query(CoinDetails).filter(
                    CoinDetails.is_valid == True
                )
                
                if by_change:
                    query = query.order_by(desc(CoinDetails.change_24h))
                else:
                    query = query.order_by(desc(CoinDetails.price))
                
                return query.limit(limit).all()
        except Exception as e:
            self.logger.error(f"获取表现最佳币种失败: {str(e)}")
            raise DataException(f"获取表现最佳币种失败: {str(e)}")


class MarketOverviewRepository(BaseRepository):
    """市场概览仓储"""
    
    def __init__(self):
        super().__init__(MarketOverview, "MarketOverviewRepository")
    
    async def get_latest(self) -> Optional[MarketOverview]:
        """获取最新市场概览"""
        try:
            with self.get_session() as session:
                return session.query(MarketOverview).filter(
                    MarketOverview.is_valid == True
                ).order_by(desc(MarketOverview.data_timestamp)).first()
        except Exception as e:
            self.logger.error(f"获取最新市场概览失败: {str(e)}")
            raise DataException(f"获取最新市场概览失败: {str(e)}")
    
    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[MarketOverview]:
        """根据日期范围获取市场概览"""
        try:
            with self.get_session() as session:
                return session.query(MarketOverview).filter(
                    and_(
                        MarketOverview.data_timestamp >= start_date,
                        MarketOverview.data_timestamp <= end_date,
                        MarketOverview.is_valid == True
                    )
                ).order_by(MarketOverview.data_timestamp).all()
        except Exception as e:
            self.logger.error(f"根据日期范围获取市场概览失败: {str(e)}")
            raise DataException(f"根据日期范围获取市场概览失败: {str(e)}")
    
    async def get_by_trend(self, trend: str) -> List[MarketOverview]:
        """根据市场趋势获取概览"""
        try:
            with self.get_session() as session:
                return session.query(MarketOverview).filter(
                    and_(
                        MarketOverview.market_trend == trend,
                        MarketOverview.is_valid == True
                    )
                ).order_by(desc(MarketOverview.data_timestamp)).all()
        except Exception as e:
            self.logger.error(f"根据市场趋势获取概览失败: {trend}, {str(e)}")
            raise DataException(f"根据市场趋势获取概览失败: {str(e)}")


class KlineDataRepository:
    """K线数据仓储"""
    
    def __init__(self):
        # 不指定特定模型类，因为我们处理多个K线模型
        self.logger = get_logger("KlineDataRepository")
        self.session_manager = get_session_manager()
    
    def get_session(self):
        """获取数据库会话"""
        return self.session_manager.get_session()
    
    def _get_model_class(self, timeframe: str):
        """根据时间周期获取对应的模型类"""
        if timeframe == '1m':
            return KlineData1m
        elif timeframe == '1h':
            return KlineData1h
        elif timeframe == '1d':
            return KlineData1d
        else:
            raise ValueError(f"不支持的时间周期: {timeframe}")
    
    async def get_kline_data(self, 
                           symbol: str, 
                           timeframe: str,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           limit: Optional[int] = None) -> List[Union[KlineData1m, KlineData1h, KlineData1d]]:
        """获取K线数据"""
        try:
            model_class = self._get_model_class(timeframe)
            
            with self.get_session() as session:
                query = session.query(model_class).filter(
                    and_(
                        model_class.symbol == symbol.upper(),
                        model_class.is_valid == True
                    )
                )
                
                # 时间范围过滤
                if start_time:
                    if isinstance(start_time, str):
                        start_time_str = start_time
                    else:
                        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
                    query = query.filter(model_class.timestamp >= start_time_str)
                if end_time:
                    if isinstance(end_time, str):
                        end_time_str = end_time
                    else:
                        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
                    query = query.filter(model_class.timestamp <= end_time_str)
                
                # 排序
                query = query.order_by(model_class.timestamp)
                
                # 限制数量
                if limit:
                    query = query.limit(limit)
                
                return query.all()
                
        except Exception as e:
            self.logger.error(f"获取K线数据失败: {symbol} {timeframe}, {str(e)}")
            raise DataException(f"获取K线数据失败: {str(e)}")
    
    async def save_kline_data(self, 
                            symbol: str, 
                            timeframe: str,
                            kline_data: List[Dict[str, Any]]) -> int:
        """保存K线数据"""
        try:
            model_class = self._get_model_class(timeframe)
            
            with self.get_session() as session:
                saved_count = 0
                
                for data in kline_data:
                    # 检查是否已存在
                    existing = session.query(model_class).filter(
                        and_(
                            model_class.symbol == symbol.upper(),
                            model_class.timestamp == data['timestamp']
                        )
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        for key, value in data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        existing.updated_at = datetime.now()
                    else:
                        # 创建新记录
                        kline = model_class(
                            symbol=symbol.upper(),
                            **data
                        )
                        session.add(kline)
                    
                    saved_count += 1
                
                session.commit()
                
                self.logger.info(f"保存K线数据成功: {symbol} {timeframe}, 数量: {saved_count}")
                
                return saved_count
                
        except Exception as e:
            self.logger.error(f"保存K线数据失败: {symbol} {timeframe}, {str(e)}")
            raise DataException(f"保存K线数据失败: {str(e)}")
    
    async def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[str]:
        """获取最新的时间戳"""
        try:
            model_class = self._get_model_class(timeframe)
            
            with self.get_session() as session:
                result = session.query(func.max(model_class.timestamp)).filter(
                    and_(
                        model_class.symbol == symbol.upper(),
                        model_class.is_valid == True
                    )
                ).scalar()
                
                return result
                
        except Exception as e:
            self.logger.error(f"获取最新时间戳失败: {symbol} {timeframe}, {str(e)}")
            raise DataException(f"获取最新时间戳失败: {str(e)}")
    
    async def get_ohlcv_data(self, 
                            symbol: str, 
                            timeframe: str,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None,
                            limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取OHLCV数据（兼容市场分析服务）
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            start_time: 开始时间
            end_time: 结束时间
            limit: 数据条数限制
            
        Returns:
            List[Dict[str, Any]]: OHLCV数据列表
        """
        try:
            # 调用现有的get_kline_data方法
            kline_data = await self.get_kline_data(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            # 转换为标准OHLCV格式
            ohlcv_data = []
            for item in kline_data:
                if hasattr(item, '__dict__'):
                    # 转换为标准OHLCV格式
                    item_dict = {
                        'timestamp': item.timestamp,
                        'open': item.open_price,
                        'high': item.high_price,
                        'low': item.low_price,
                        'close': item.close_price,
                        'volume': item.volume,
                        'symbol': item.symbol,
                        'timeframe': item.timeframe
                    }
                    ohlcv_data.append(item_dict)
                else:
                    ohlcv_data.append(item)
            
            return ohlcv_data
                
        except Exception as e:
            self.logger.error(f"获取OHLCV数据失败: {symbol} {timeframe}, {str(e)}")
            raise DataException(f"获取OHLCV数据失败: {str(e)}")


class CryptoMarketRankingsRepository(BaseRepository):
    """热门币种仓储"""
    
    def __init__(self):
        super().__init__(CryptoMarketRankings, "CryptoMarketRankingsRepository")
    
    async def get_by_quote_asset(self, quote_asset: str, limit: int = 50) -> List[CryptoMarketRankings]:
        """根据计价货币获取热门币种"""
        try:
            with self.get_session() as session:
                return session.query(CryptoMarketRankings).filter(
                    and_(
                        CryptoMarketRankings.quote_asset == quote_asset.upper(),
                        CryptoMarketRankings.is_valid == True
                    )
                ).order_by(CryptoMarketRankings.rank).limit(limit).all()
        except Exception as e:
            self.logger.error(f"根据计价货币获取热门币种失败: {quote_asset}, {str(e)}")
            raise DataException(f"根据计价货币获取热门币种失败: {str(e)}")
    
    async def get_top_gainers(self, quote_asset: str = None, limit: int = 10) -> List[CryptoMarketRankings]:
        """获取涨幅最大的币种"""
        try:
            with self.get_session() as session:
                query = session.query(CryptoMarketRankings).filter(
                    CryptoMarketRankings.is_valid == True
                )
                
                if quote_asset:
                    query = query.filter(CryptoMarketRankings.quote_asset == quote_asset.upper())
                
                return query.order_by(desc(CryptoMarketRankings.change_24h)).limit(limit).all()
        except Exception as e:
            self.logger.error(f"获取涨幅最大币种失败: {str(e)}")
            raise DataException(f"获取涨幅最大币种失败: {str(e)}")
    
    async def get_top_losers(self, quote_asset: str = None, limit: int = 10) -> List[CryptoMarketRankings]:
        """获取跌幅最大的币种"""
        try:
            with self.get_session() as session:
                query = session.query(CryptoMarketRankings).filter(
                    CryptoMarketRankings.is_valid == True
                )
                
                if quote_asset:
                    query = query.filter(CryptoMarketRankings.quote_asset == quote_asset.upper())
                
                return query.order_by(asc(CryptoMarketRankings.change_24h)).limit(limit).all()
        except Exception as e:
            self.logger.error(f"获取跌幅最大币种失败: {str(e)}")
            raise DataException(f"获取跌幅最大币种失败: {str(e)}")
    
    async def get_by_volume_range(self, 
                                min_volume: float, 
                                max_volume: float = None,
                                quote_asset: str = None) -> List[CryptoMarketRankings]:
        """根据成交量范围获取币种"""
        try:
            with self.get_session() as session:
                query = session.query(CryptoMarketRankings).filter(
                    and_(
                        CryptoMarketRankings.volume_24h >= min_volume,
                        CryptoMarketRankings.is_valid == True
                    )
                )
                
                if max_volume:
                    query = query.filter(CryptoMarketRankings.volume_24h <= max_volume)
                
                if quote_asset:
                    query = query.filter(CryptoMarketRankings.quote_asset == quote_asset.upper())
                
                return query.order_by(desc(CryptoMarketRankings.volume_24h)).all()
        except Exception as e:
            self.logger.error(f"根据成交量范围获取币种失败: {str(e)}")
            raise DataException(f"根据成交量范围获取币种失败: {str(e)}")


# 统一的市场数据仓储工厂
class MarketDataRepositoryFactory:
    """市场数据仓储工厂"""
    
    _repositories = {}
    
    @classmethod
    def get_fear_greed_repository(cls) -> FearGreedRepository:
        """获取恐惧贪婪指数仓储"""
        if 'fear_greed' not in cls._repositories:
            cls._repositories['fear_greed'] = FearGreedRepository()
        return cls._repositories['fear_greed']
    
    @classmethod
    def get_coin_details_repository(cls) -> CoinDetailsRepository:
        """获取币种详情仓储"""
        if 'coin_details' not in cls._repositories:
            try:
                cls._repositories['coin_details'] = CoinDetailsRepository()
                print(f"CoinDetailsRepository created successfully: {cls._repositories['coin_details']}")
            except Exception as e:
                print(f"Failed to create CoinDetailsRepository: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return None
        return cls._repositories['coin_details']
    
    @classmethod
    def get_market_overview_repository(cls) -> MarketOverviewRepository:
        """获取市场概览仓储"""
        if 'market_overview' not in cls._repositories:
            cls._repositories['market_overview'] = MarketOverviewRepository()
        return cls._repositories['market_overview']
    
    @classmethod
    def get_kline_data_repository(cls) -> KlineDataRepository:
        """获取K线数据仓储"""
        if 'kline_data' not in cls._repositories:
            try:
                cls._repositories['kline_data'] = KlineDataRepository()
                print(f"KlineDataRepository created successfully: {cls._repositories['kline_data']}")
            except Exception as e:
                print(f"Failed to create KlineDataRepository: {e}")
                return None
        return cls._repositories['kline_data']
    
    @classmethod
    def get_popular_coins_repository(cls) -> CryptoMarketRankingsRepository:
        """获取热门币种仓储"""
        if 'popular_coins' not in cls._repositories:
            cls._repositories['popular_coins'] = CryptoMarketRankingsRepository()
        return cls._repositories['popular_coins']