"""
回测仓储
处理回测结果的存储和查询
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index, and_, desc, func
from sqlalchemy.orm import Session
import json

from ..repository_base import BaseRepository
from data.models.base.base_model import BaseModel
from utils.validation.exceptions import DataException


class BacktestResult(BaseModel):
    """回测结果模型"""
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    backtest_id = Column(String(50), nullable=False, unique=True, comment='回测ID')
    strategy_name = Column(String(100), nullable=False, index=True, comment='策略名称')
    symbol = Column(String(20), nullable=False, index=True, comment='交易对')
    timeframe = Column(String(10), nullable=False, comment='时间周期')
    start_date = Column(DateTime, nullable=False, comment='开始日期')
    end_date = Column(DateTime, nullable=False, comment='结束日期')
    initial_cash = Column(Float, nullable=False, comment='初始资金')
    final_cash = Column(Float, nullable=False, comment='最终资金')
    total_return = Column(Float, nullable=False, index=True, comment='总收益率')
    total_trades = Column(Integer, comment='总交易次数')
    win_rate = Column(Float, comment='胜率')
    profit_factor = Column(Float, comment='盈亏比')
    sharpe_ratio = Column(Float, comment='夏普比率')
    max_drawdown = Column(Float, comment='最大回撤')
    avg_holding_period = Column(Float, comment='平均持仓时间（小时）')
    strategy_params = Column(Text, comment='策略参数JSON')
    performance_metrics = Column(Text, comment='性能指标JSON')
    trades_data = Column(Text, comment='交易记录JSON')
    execution_time = Column(Float, comment='执行时间(秒)')
    status = Column(String(20), default='completed', comment='状态')
    error_message = Column(Text, comment='错误信息')
    
    def __init__(self, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'backtest_engine'
        super().__init__(**kwargs)
    
    __table_args__ = (
        Index('idx_backtest_strategy', 'strategy_name'),
        Index('idx_backtest_symbol', 'symbol'),
        Index('idx_backtest_return', 'total_return'),
        Index('idx_backtest_date_range', 'start_date', 'end_date'),
        {'comment': '回测结果表'}
    )
    
    def set_strategy_params(self, params: Dict[str, Any]):
        """设置策略参数"""
        self.strategy_params = json.dumps(params, ensure_ascii=False)
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        if self.strategy_params:
            try:
                return json.loads(self.strategy_params)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_performance_metrics(self, metrics: Dict[str, Any]):
        """设置性能指标"""
        self.performance_metrics = json.dumps(metrics, ensure_ascii=False)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if self.performance_metrics:
            try:
                return json.loads(self.performance_metrics)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_trades_data(self, trades: List[Dict[str, Any]]):
        """设置交易记录"""
        self.trades_data = json.dumps(trades, ensure_ascii=False)
    
    def get_trades_data(self) -> List[Dict[str, Any]]:
        """获取交易记录"""
        if self.trades_data:
            try:
                return json.loads(self.trades_data)
            except json.JSONDecodeError:
                return []
        return []


class StrategyConfig(BaseModel):
    """策略配置模型"""
    __tablename__ = 'strategy_configs'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    strategy_name = Column(String(100), nullable=False, unique=True, comment='策略名称')
    display_name = Column(String(200), nullable=False, comment='显示名称')
    description = Column(Text, comment='策略描述')
    category = Column(String(50), index=True, comment='策略分类')
    risk_level = Column(String(20), index=True, comment='风险等级')
    parameters = Column(Text, comment='参数定义JSON')
    default_params = Column(Text, comment='默认参数JSON')
    is_active = Column(Boolean, default=True, index=True, comment='是否激活')
    version = Column(String(20), default='1.0.0', comment='版本号')
    author = Column(String(100), comment='作者')
    
    def __init__(self, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'strategy_manager'
        super().__init__(**kwargs)
    
    __table_args__ = (
        Index('idx_strategy_category', 'category'),
        Index('idx_strategy_risk_level', 'risk_level'),
        Index('idx_strategy_active', 'is_active'),
        {'comment': '策略配置表'}
    )
    
    def set_parameters(self, params: Dict[str, Any]):
        """设置参数定义"""
        self.parameters = json.dumps(params, ensure_ascii=False)
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义"""
        if self.parameters:
            try:
                return json.loads(self.parameters)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_default_params(self, params: Dict[str, Any]):
        """设置默认参数"""
        self.default_params = json.dumps(params, ensure_ascii=False)
    
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认参数"""
        if self.default_params:
            try:
                return json.loads(self.default_params)
            except json.JSONDecodeError:
                return {}
        return {}


class BacktestRepository(BaseRepository):
    """回测结果仓储"""
    
    def __init__(self):
        super().__init__(BacktestResult, "BacktestRepository")
    
    async def save_backtest_result(self, backtest_data: Dict[str, Any]) -> BacktestResult:
        """保存回测结果"""
        try:
            # 创建回测结果实例
            backtest = BacktestResult(
                backtest_id=backtest_data['backtest_id'],
                strategy_name=backtest_data['strategy_name'],
                symbol=backtest_data['symbol'],
                timeframe=backtest_data['timeframe'],
                start_date=backtest_data['start_date'],
                end_date=backtest_data['end_date'],
                initial_cash=backtest_data['initial_cash'],
                final_cash=backtest_data.get('final_cash', 0),
                total_return=backtest_data.get('total_return', 0),
                execution_time=backtest_data.get('execution_time', 0),
                status=backtest_data.get('status', 'completed'),
                error_message=backtest_data.get('error_message')
            )
            
            # 设置JSON数据
            if 'strategy_params' in backtest_data:
                backtest.set_strategy_params(backtest_data['strategy_params'])
            
            if 'performance_metrics' in backtest_data:
                backtest.set_performance_metrics(backtest_data['performance_metrics'])
            
            if 'trades_data' in backtest_data:
                backtest.set_trades_data(backtest_data['trades_data'])
            
            return await self.create(backtest)
            
        except Exception as e:
            self.logger.error(f"保存回测结果失败: {str(e)}")
            raise DataException(f"保存回测结果失败: {str(e)}")
    
    async def get_by_backtest_id(self, backtest_id: str) -> Optional[BacktestResult]:
        """根据回测ID获取结果"""
        try:
            with self.get_session() as session:
                return session.query(BacktestResult).filter(
                    and_(
                        BacktestResult.backtest_id == backtest_id,
                        BacktestResult.is_valid == True
                    )
                ).first()
        except Exception as e:
            self.logger.error(f"根据回测ID获取结果失败: {backtest_id}, {str(e)}")
            raise DataException(f"根据回测ID获取结果失败: {str(e)}")
    
    async def get_by_strategy(self, 
                            strategy_name: str, 
                            limit: int = None) -> List[BacktestResult]:
        """根据策略名称获取回测结果"""
        try:
            with self.get_session() as session:
                query = session.query(BacktestResult).filter(
                    and_(
                        BacktestResult.strategy_name == strategy_name,
                        BacktestResult.is_valid == True
                    )
                ).order_by(desc(BacktestResult.created_at))
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"根据策略获取回测结果失败: {strategy_name}, {str(e)}")
            raise DataException(f"根据策略获取回测结果失败: {str(e)}")
    
    async def get_by_symbol(self, 
                          symbol: str, 
                          limit: int = None) -> List[BacktestResult]:
        """根据交易对获取回测结果"""
        try:
            with self.get_session() as session:
                query = session.query(BacktestResult).filter(
                    and_(
                        BacktestResult.symbol == symbol.upper(),
                        BacktestResult.is_valid == True
                    )
                ).order_by(desc(BacktestResult.total_return))
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"根据交易对获取回测结果失败: {symbol}, {str(e)}")
            raise DataException(f"根据交易对获取回测结果失败: {str(e)}")
    
    async def get_best_performing(self, limit: int = 10) -> List[BacktestResult]:
        """获取表现最佳的回测结果"""
        try:
            with self.get_session() as session:
                return session.query(BacktestResult).filter(
                    and_(
                        BacktestResult.status == 'completed',
                        BacktestResult.is_valid == True
                    )
                ).order_by(desc(BacktestResult.total_return)).limit(limit).all()
        except Exception as e:
            self.logger.error(f"获取表现最佳回测结果失败: {str(e)}")
            raise DataException(f"获取表现最佳回测结果失败: {str(e)}")
    
    async def get_backtest_statistics(self) -> Dict[str, Any]:
        """获取回测统计信息"""
        try:
            with self.get_session() as session:
                # 总体统计
                total_stats = session.query(
                    func.count(BacktestResult.id).label('total_backtests'),
                    func.count().filter(BacktestResult.total_return > 0).label('profitable_backtests'),
                    func.avg(BacktestResult.total_return).label('avg_return'),
                    func.max(BacktestResult.total_return).label('max_return'),
                    func.min(BacktestResult.total_return).label('min_return'),
                    func.avg(BacktestResult.execution_time).label('avg_execution_time')
                ).filter(
                    and_(
                        BacktestResult.status == 'completed',
                        BacktestResult.is_valid == True
                    )
                ).first()
                
                # 按策略统计
                strategy_stats = session.query(
                    BacktestResult.strategy_name,
                    func.count(BacktestResult.id).label('backtest_count'),
                    func.avg(BacktestResult.total_return).label('avg_return'),
                    func.max(BacktestResult.total_return).label('max_return')
                ).filter(
                    and_(
                        BacktestResult.status == 'completed',
                        BacktestResult.is_valid == True
                    )
                ).group_by(BacktestResult.strategy_name).order_by(
                    desc(func.avg(BacktestResult.total_return))
                ).all()
                
                # 计算成功率
                success_rate = 0
                if total_stats.total_backtests > 0:
                    success_rate = (total_stats.profitable_backtests / total_stats.total_backtests) * 100
                
                return {
                    'total_backtests': total_stats.total_backtests or 0,
                    'profitable_backtests': total_stats.profitable_backtests or 0,
                    'success_rate': round(success_rate, 2),
                    'avg_return': round(total_stats.avg_return or 0, 4),
                    'max_return': round(total_stats.max_return or 0, 4),
                    'min_return': round(total_stats.min_return or 0, 4),
                    'avg_execution_time': round(total_stats.avg_execution_time or 0, 2),
                    'strategy_performance': [
                        {
                            'strategy_name': row.strategy_name,
                            'backtest_count': row.backtest_count,
                            'avg_return': round(row.avg_return, 4),
                            'max_return': round(row.max_return, 4)
                        }
                        for row in strategy_stats
                    ]
                }
                
        except Exception as e:
            self.logger.error(f"获取回测统计信息失败: {str(e)}")
            raise DataException(f"获取回测统计信息失败: {str(e)}")
    
    async def cleanup_old_backtests(self, days_to_keep: int = 90) -> int:
        """清理旧的回测结果"""
        try:
            with self.get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                deleted_count = session.query(BacktestResult).filter(
                    BacktestResult.created_at < cutoff_date
                ).delete()
                
                session.commit()
                
                self.logger.info(f"清理旧回测结果完成，删除 {deleted_count} 条记录")
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"清理旧回测结果失败: {str(e)}")
            raise DataException(f"清理旧回测结果失败: {str(e)}")


class StrategyConfigRepository(BaseRepository[StrategyConfig]):
    """策略配置仓储"""
    
    def __init__(self):
        super().__init__(StrategyConfig, "StrategyConfigRepository")
    
    async def get_by_strategy_name(self, strategy_name: str) -> Optional[StrategyConfig]:
        """根据策略名称获取配置"""
        try:
            with self.get_session() as session:
                return session.query(StrategyConfig).filter(
                    and_(
                        StrategyConfig.strategy_name == strategy_name,
                        StrategyConfig.is_active == True,
                        StrategyConfig.is_valid == True
                    )
                ).first()
        except Exception as e:
            self.logger.error(f"根据策略名称获取配置失败: {strategy_name}, {str(e)}")
            raise DataException(f"根据策略名称获取配置失败: {str(e)}")
    
    async def get_by_category(self, category: str) -> List[StrategyConfig]:
        """根据分类获取策略配置"""
        try:
            with self.get_session() as session:
                return session.query(StrategyConfig).filter(
                    and_(
                        StrategyConfig.category == category,
                        StrategyConfig.is_active == True,
                        StrategyConfig.is_valid == True
                    )
                ).order_by(StrategyConfig.strategy_name).all()
        except Exception as e:
            self.logger.error(f"根据分类获取策略配置失败: {category}, {str(e)}")
            raise DataException(f"根据分类获取策略配置失败: {str(e)}")
    
    async def get_by_risk_level(self, risk_level: str) -> List[StrategyConfig]:
        """根据风险等级获取策略配置"""
        try:
            with self.get_session() as session:
                return session.query(StrategyConfig).filter(
                    and_(
                        StrategyConfig.risk_level == risk_level,
                        StrategyConfig.is_active == True,
                        StrategyConfig.is_valid == True
                    )
                ).order_by(StrategyConfig.strategy_name).all()
        except Exception as e:
            self.logger.error(f"根据风险等级获取策略配置失败: {risk_level}, {str(e)}")
            raise DataException(f"根据风险等级获取策略配置失败: {str(e)}")
    
    async def search_strategies(self, keyword: str) -> List[StrategyConfig]:
        """搜索策略配置"""
        try:
            with self.get_session() as session:
                return session.query(StrategyConfig).filter(
                    and_(
                        or_(
                            StrategyConfig.strategy_name.contains(keyword),
                            StrategyConfig.display_name.contains(keyword),
                            StrategyConfig.description.contains(keyword)
                        ),
                        StrategyConfig.is_active == True,
                        StrategyConfig.is_valid == True
                    )
                ).order_by(StrategyConfig.strategy_name).all()
        except Exception as e:
            self.logger.error(f"搜索策略配置失败: {keyword}, {str(e)}")
            raise DataException(f"搜索策略配置失败: {str(e)}")
    
    async def deactivate_strategy(self, strategy_name: str) -> bool:
        """停用策略（软删除）"""
        try:
            with self.get_session() as session:
                strategy = session.query(StrategyConfig).filter(
                    StrategyConfig.strategy_name == strategy_name
                ).first()
                
                if not strategy:
                    return False
                
                strategy.is_active = False
                strategy.updated_at = datetime.now()
                
                session.commit()
                
                self.logger.info(f"停用策略成功: {strategy_name}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"停用策略失败: {strategy_name}, {str(e)}")
            raise DataException(f"停用策略失败: {str(e)}")


# 回测仓储工厂
class BacktestRepositoryFactory:
    """回测仓储工厂"""
    
    _repositories = {}
    
    @classmethod
    def get_backtest_repository(cls) -> BacktestRepository:
        """获取回测结果仓储"""
        if 'backtest' not in cls._repositories:
            cls._repositories['backtest'] = BacktestRepository()
        return cls._repositories['backtest']
    
    @classmethod
    def get_strategy_config_repository(cls) -> StrategyConfigRepository:
        """获取策略配置仓储"""
        if 'strategy_config' not in cls._repositories:
            cls._repositories['strategy_config'] = StrategyConfigRepository()
        return cls._repositories['strategy_config']