"""
策略和交易记录仓储
处理策略数据和交易记录的存储和查询
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Session

from ..repository_base import BaseRepository
from data.models.strategy.trade_records_model import TradeRecords
from utils.validation.exceptions import DataException


class TradeRecordsRepository(BaseRepository):
    """交易记录仓储"""
    
    def __init__(self):
        super().__init__(TradeRecords, "TradeRecordsRepository")
    
    async def get_by_symbol(self, symbol: str, limit: int = None) -> List[TradeRecords]:
        """根据交易对获取交易记录"""
        try:
            with self.get_session() as session:
                query = session.query(TradeRecords).filter(
                    and_(
                        TradeRecords.symbol == symbol.upper(),
                        TradeRecords.is_valid == True
                    )
                ).order_by(desc(TradeRecords.trade_datetime))
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"根据交易对获取交易记录失败: {symbol}, {str(e)}")
            raise DataException(f"根据交易对获取交易记录失败: {str(e)}")
    
    async def get_by_strategy(self, strategy_name: str, limit: int = None) -> List[TradeRecords]:
        """根据策略名称获取交易记录"""
        try:
            with self.get_session() as session:
                query = session.query(TradeRecords).filter(
                    and_(
                        TradeRecords.strategy_name == strategy_name,
                        TradeRecords.is_valid == True
                    )
                ).order_by(desc(TradeRecords.trade_datetime))
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"根据策略获取交易记录失败: {strategy_name}, {str(e)}")
            raise DataException(f"根据策略获取交易记录失败: {str(e)}")
    
    async def get_by_date_range(self, 
                              start_date: datetime, 
                              end_date: datetime,
                              symbol: str = None,
                              strategy_name: str = None) -> List[TradeRecords]:
        """根据日期范围获取交易记录"""
        try:
            with self.get_session() as session:
                query = session.query(TradeRecords).filter(
                    and_(
                        TradeRecords.trade_datetime >= start_date,
                        TradeRecords.trade_datetime <= end_date,
                        TradeRecords.is_valid == True
                    )
                )
                
                if symbol:
                    query = query.filter(TradeRecords.symbol == symbol.upper())
                
                if strategy_name:
                    query = query.filter(TradeRecords.strategy_name == strategy_name)
                
                return query.order_by(TradeRecords.trade_datetime).all()
        except Exception as e:
            self.logger.error(f"根据日期范围获取交易记录失败: {str(e)}")
            raise DataException(f"根据日期范围获取交易记录失败: {str(e)}")
    
    async def get_by_side(self, side: str, symbol: str = None, limit: int = None) -> List[TradeRecords]:
        """根据交易方向获取交易记录"""
        try:
            with self.get_session() as session:
                query = session.query(TradeRecords).filter(
                    and_(
                        TradeRecords.side == side.lower(),
                        TradeRecords.is_valid == True
                    )
                )
                
                if symbol:
                    query = query.filter(TradeRecords.symbol == symbol.upper())
                
                query = query.order_by(desc(TradeRecords.trade_datetime))
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"根据交易方向获取交易记录失败: {side}, {str(e)}")
            raise DataException(f"根据交易方向获取交易记录失败: {str(e)}")
    
    async def get_by_position_id(self, position_id: str) -> List[TradeRecords]:
        """根据持仓ID获取交易记录"""
        try:
            with self.get_session() as session:
                return session.query(TradeRecords).filter(
                    and_(
                        TradeRecords.position_id == position_id,
                        TradeRecords.is_valid == True
                    )
                ).order_by(TradeRecords.trade_datetime).all()
        except Exception as e:
            self.logger.error(f"根据持仓ID获取交易记录失败: {position_id}, {str(e)}")
            raise DataException(f"根据持仓ID获取交易记录失败: {str(e)}")
    
    async def get_profitable_trades(self, 
                                  symbol: str = None, 
                                  strategy_name: str = None,
                                  limit: int = None) -> List[TradeRecords]:
        """获取盈利的交易记录"""
        try:
            with self.get_session() as session:
                query = session.query(TradeRecords).filter(
                    and_(
                        TradeRecords.pnl > 0,
                        TradeRecords.is_valid == True
                    )
                )
                
                if symbol:
                    query = query.filter(TradeRecords.symbol == symbol.upper())
                
                if strategy_name:
                    query = query.filter(TradeRecords.strategy_name == strategy_name)
                
                query = query.order_by(desc(TradeRecords.pnl))
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"获取盈利交易记录失败: {str(e)}")
            raise DataException(f"获取盈利交易记录失败: {str(e)}")
    
    async def get_losing_trades(self, 
                              symbol: str = None, 
                              strategy_name: str = None,
                              limit: int = None) -> List[TradeRecords]:
        """获取亏损的交易记录"""
        try:
            with self.get_session() as session:
                query = session.query(TradeRecords).filter(
                    and_(
                        TradeRecords.pnl < 0,
                        TradeRecords.is_valid == True
                    )
                )
                
                if symbol:
                    query = query.filter(TradeRecords.symbol == symbol.upper())
                
                if strategy_name:
                    query = query.filter(TradeRecords.strategy_name == strategy_name)
                
                query = query.order_by(asc(TradeRecords.pnl))
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"获取亏损交易记录失败: {str(e)}")
            raise DataException(f"获取亏损交易记录失败: {str(e)}")
    
    async def get_trade_statistics(self, 
                                 symbol: str = None, 
                                 strategy_name: str = None,
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """获取交易统计信息"""
        try:
            with self.get_session() as session:
                query = session.query(TradeRecords).filter(
                    TradeRecords.is_valid == True
                )
                
                # 应用过滤条件
                if symbol:
                    query = query.filter(TradeRecords.symbol == symbol.upper())
                
                if strategy_name:
                    query = query.filter(TradeRecords.strategy_name == strategy_name)
                
                if start_date:
                    query = query.filter(TradeRecords.trade_datetime >= start_date)
                
                if end_date:
                    query = query.filter(TradeRecords.trade_datetime <= end_date)
                
                # 获取所有交易记录
                trades = query.all()
                
                if not trades:
                    return {
                        'total_trades': 0,
                        'buy_trades': 0,
                        'sell_trades': 0,
                        'total_volume': 0,
                        'total_commission': 0,
                        'total_pnl': 0,
                        'profitable_trades': 0,
                        'losing_trades': 0,
                        'win_rate': 0,
                        'avg_profit': 0,
                        'avg_loss': 0,
                        'profit_factor': 0,
                        'max_profit': 0,
                        'max_loss': 0
                    }
                
                # 计算统计信息
                total_trades = len(trades)
                buy_trades = len([t for t in trades if t.side == 'buy'])
                sell_trades = len([t for t in trades if t.side == 'sell'])
                
                total_volume = sum(t.quantity for t in trades)
                total_commission = sum(t.commission for t in trades)
                
                # PnL统计
                pnl_trades = [t for t in trades if t.pnl is not None]
                total_pnl = sum(t.pnl for t in pnl_trades)
                
                profitable_trades = [t for t in pnl_trades if t.pnl > 0]
                losing_trades = [t for t in pnl_trades if t.pnl < 0]
                
                profitable_count = len(profitable_trades)
                losing_count = len(losing_trades)
                
                win_rate = (profitable_count / len(pnl_trades) * 100) if pnl_trades else 0
                
                total_profit = sum(t.pnl for t in profitable_trades)
                total_loss = abs(sum(t.pnl for t in losing_trades))
                
                avg_profit = (total_profit / profitable_count) if profitable_count > 0 else 0
                avg_loss = (total_loss / losing_count) if losing_count > 0 else 0
                
                profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')
                
                max_profit = max((t.pnl for t in profitable_trades), default=0)
                max_loss = min((t.pnl for t in losing_trades), default=0)
                
                return {
                    'total_trades': total_trades,
                    'buy_trades': buy_trades,
                    'sell_trades': sell_trades,
                    'total_volume': total_volume,
                    'total_commission': total_commission,
                    'total_pnl': total_pnl,
                    'profitable_trades': profitable_count,
                    'losing_trades': losing_count,
                    'win_rate': round(win_rate, 2),
                    'avg_profit': round(avg_profit, 4),
                    'avg_loss': round(avg_loss, 4),
                    'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else None,
                    'max_profit': round(max_profit, 4),
                    'max_loss': round(max_loss, 4)
                }
                
        except Exception as e:
            self.logger.error(f"获取交易统计信息失败: {str(e)}")
            raise DataException(f"获取交易统计信息失败: {str(e)}")
    
    async def get_daily_pnl(self, 
                          symbol: str = None, 
                          strategy_name: str = None,
                          days: int = 30) -> List[Dict[str, Any]]:
        """获取每日盈亏统计"""
        try:
            with self.get_session() as session:
                # 计算开始日期
                start_date = datetime.now() - timedelta(days=days)
                
                query = session.query(
                    func.date(TradeRecords.trade_datetime).label('date'),
                    func.sum(TradeRecords.pnl).label('daily_pnl'),
                    func.count(TradeRecords.id).label('trade_count')
                ).filter(
                    and_(
                        TradeRecords.trade_datetime >= start_date,
                        TradeRecords.pnl.isnot(None),
                        TradeRecords.is_valid == True
                    )
                )
                
                if symbol:
                    query = query.filter(TradeRecords.symbol == symbol.upper())
                
                if strategy_name:
                    query = query.filter(TradeRecords.strategy_name == strategy_name)
                
                results = query.group_by(
                    func.date(TradeRecords.trade_datetime)
                ).order_by(
                    func.date(TradeRecords.trade_datetime)
                ).all()
                
                return [
                    {
                        'date': result.date.isoformat(),
                        'daily_pnl': float(result.daily_pnl or 0),
                        'trade_count': result.trade_count
                    }
                    for result in results
                ]
                
        except Exception as e:
            self.logger.error(f"获取每日盈亏统计失败: {str(e)}")
            raise DataException(f"获取每日盈亏统计失败: {str(e)}")
    
    async def get_symbol_performance(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取交易对表现统计"""
        try:
            with self.get_session() as session:
                results = session.query(
                    TradeRecords.symbol,
                    func.count(TradeRecords.id).label('trade_count'),
                    func.sum(TradeRecords.pnl).label('total_pnl'),
                    func.sum(TradeRecords.quantity).label('total_volume'),
                    func.sum(TradeRecords.commission).label('total_commission')
                ).filter(
                    and_(
                        TradeRecords.pnl.isnot(None),
                        TradeRecords.is_valid == True
                    )
                ).group_by(
                    TradeRecords.symbol
                ).order_by(
                    desc(func.sum(TradeRecords.pnl))
                ).limit(limit).all()
                
                return [
                    {
                        'symbol': result.symbol,
                        'trade_count': result.trade_count,
                        'total_pnl': float(result.total_pnl or 0),
                        'total_volume': float(result.total_volume or 0),
                        'total_commission': float(result.total_commission or 0)
                    }
                    for result in results
                ]
                
        except Exception as e:
            self.logger.error(f"获取交易对表现统计失败: {str(e)}")
            raise DataException(f"获取交易对表现统计失败: {str(e)}")
    
    async def get_strategy_performance(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取策略表现统计"""
        try:
            with self.get_session() as session:
                results = session.query(
                    TradeRecords.strategy_name,
                    func.count(TradeRecords.id).label('trade_count'),
                    func.sum(TradeRecords.pnl).label('total_pnl'),
                    func.sum(TradeRecords.quantity).label('total_volume'),
                    func.sum(TradeRecords.commission).label('total_commission')
                ).filter(
                    and_(
                        TradeRecords.strategy_name != '',
                        TradeRecords.pnl.isnot(None),
                        TradeRecords.is_valid == True
                    )
                ).group_by(
                    TradeRecords.strategy_name
                ).order_by(
                    desc(func.sum(TradeRecords.pnl))
                ).limit(limit).all()
                
                return [
                    {
                        'strategy_name': result.strategy_name,
                        'trade_count': result.trade_count,
                        'total_pnl': float(result.total_pnl or 0),
                        'total_volume': float(result.total_volume or 0),
                        'total_commission': float(result.total_commission or 0)
                    }
                    for result in results
                ]
                
        except Exception as e:
            self.logger.error(f"获取策略表现统计失败: {str(e)}")
            raise DataException(f"获取策略表现统计失败: {str(e)}")
    
    async def cleanup_old_trades(self, days_to_keep: int = 365) -> int:
        """清理旧的交易记录"""
        try:
            with self.get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                deleted_count = session.query(TradeRecords).filter(
                    TradeRecords.trade_datetime < cutoff_date
                ).delete()
                
                session.commit()
                
                self.logger.info(f"清理旧交易记录完成，删除 {deleted_count} 条记录")
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"清理旧交易记录失败: {str(e)}")
            raise DataException(f"清理旧交易记录失败: {str(e)}")


# 策略仓储工厂
class StrategyRepositoryFactory:
    """策略仓储工厂"""
    
    _repositories = {}
    
    @classmethod
    def get_trade_records_repository(cls) -> TradeRecordsRepository:
        """获取交易记录仓储"""
        if 'trade_records' not in cls._repositories:
            cls._repositories['trade_records'] = TradeRecordsRepository()
        return cls._repositories['trade_records']