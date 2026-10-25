"""
SQLite存储实现
使用SQLAlchemy ORM，支持多种数据库类型
"""

import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from utils.core.logger_manager import get_logger
from data.config.database_config import get_database_config
from data.config.database_initializer import DatabaseInitializer
from data.models.strategy.trade_records_model import TradeRecordModel


class SQLiteStorage:
    """SQLite存储类"""
    
    def __init__(self, db_path: str = "quant_trading.db"):
        self.db_path = db_path
        self.logger = get_logger('sqlite_storage')
        
        # 获取数据库配置
        self.db_config = get_database_config()
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            # 使用DatabaseInitializer创建表结构
            initializer = DatabaseInitializer(self.db_path)
            initializer.init_all_tables()
            self.logger.info("数据库初始化完成")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取SQLAlchemy会话（向后兼容）"""
        return self.db_config.get_session()
    
    def get_native_connection(self) -> sqlite3.Connection:
        """获取原生SQLite连接（仅用于性能优化的批量操作）"""
        return sqlite3.connect(self.db_path)
    
    # ==================== 交易记录操作 ====================
    def save_trade_record(self, record: TradeRecordModel) -> bool:
        """保存交易记录"""
        try:
            with self.get_session() as session:
                session.add(record)
                session.commit()
                self.logger.info(f"交易记录保存成功: {record.id}")
                return True
        except Exception as e:
            self.logger.error(f"保存交易记录失败: {e}")
            return False
    
    def get_trade_records(self, limit: int = 100, offset: int = 0) -> List[TradeRecordModel]:
        """获取交易记录列表"""
        try:
            with self.get_session() as session:
                records = session.query(TradeRecordModel).order_by(
                    desc(TradeRecordModel.timestamp)
                ).offset(offset).limit(limit).all()
                return records
        except Exception as e:
            self.logger.error(f"获取交易记录失败: {e}")
            return []
    
    def get_trade_record_by_id(self, record_id: int) -> Optional[TradeRecordModel]:
        """根据ID获取交易记录"""
        try:
            with self.get_session() as session:
                record = session.query(TradeRecordModel).filter(
                    TradeRecordModel.id == record_id
                ).first()
                return record
        except Exception as e:
            self.logger.error(f"根据ID获取交易记录失败: {e}")
            return None
    
    def update_trade_record(self, record_id: int, updates: Dict[str, Any]) -> bool:
        """更新交易记录"""
        try:
            with self.get_session() as session:
                record = session.query(TradeRecordModel).filter(
                    TradeRecordModel.id == record_id
                ).first()
                
                if record:
                    for key, value in updates.items():
                        if hasattr(record, key):
                            setattr(record, key, value)
                    
                    record.updated_at = datetime.now()
                    session.commit()
                    self.logger.info(f"交易记录更新成功: {record_id}")
                    return True
                else:
                    self.logger.warning(f"交易记录不存在: {record_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"更新交易记录失败: {e}")
            return False
    
    def delete_trade_record(self, record_id: int) -> bool:
        """删除交易记录"""
        try:
            with self.get_session() as session:
                record = session.query(TradeRecordModel).filter(
                    TradeRecordModel.id == record_id
                ).first()
                
                if record:
                    session.delete(record)
                    session.commit()
                    self.logger.info(f"交易记录删除成功: {record_id}")
                    return True
                else:
                    self.logger.warning(f"交易记录不存在: {record_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"删除交易记录失败: {e}")
            return False
    
    def search_trade_records(self, filters: Dict[str, Any], 
                           limit: int = 100, offset: int = 0) -> List[TradeRecordModel]:
        """搜索交易记录"""
        try:
            with self.get_session() as session:
                query = session.query(TradeRecordModel)
                
                # 应用过滤条件
                for key, value in filters.items():
                    if hasattr(TradeRecordModel, key) and value is not None:
                        if isinstance(value, str):
                            query = query.filter(getattr(TradeRecordModel, key).like(f"%{value}%"))
                        else:
                            query = query.filter(getattr(TradeRecordModel, key) == value)
                
                records = query.order_by(desc(TradeRecordModel.timestamp)).offset(offset).limit(limit).all()
                return records
                
        except Exception as e:
            self.logger.error(f"搜索交易记录失败: {e}")
            return []
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """获取交易统计信息"""
        try:
            with self.get_session() as session:
                # 总记录数
                total_count = session.query(TradeRecordModel).count()
                
                # 成功交易数
                success_count = session.query(TradeRecordModel).filter(
                    TradeRecordModel.status == "success"
                ).count()
                
                # 失败交易数
                failed_count = session.query(TradeRecordModel).filter(
                    TradeRecordModel.status == "failed"
                ).count()
                
                # 总交易金额
                total_amount = session.query(func.sum(TradeRecordModel.amount)).filter(
                    TradeRecordModel.status == "success"
                ).scalar() or 0
                
                return {
                    "total_count": total_count,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
                    "total_amount": total_amount
                }
                
        except Exception as e:
            self.logger.error(f"获取交易统计失败: {e}")
            return {}
    
    # ==================== 市场数据操作 ====================
    def save_market_data(self, df, symbol: str, overwrite: bool = False) -> bool:
        """
        保存市场数据到数据库
        
        Args:
            df: 包含OHLCV数据的DataFrame，索引为时间
            symbol: 交易对名称
            overwrite: 是否覆盖已存在的数据，默认False（跳过）
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 检查DataFrame是否为空（兼容pandas DataFrame和普通字典）
            if hasattr(df, 'empty') and df.empty:
                self.logger.warning(f"DataFrame为空，跳过保存: {symbol}")
                return False
            
            # 使用原生SQLite连接进行批量插入
            conn = self.get_native_connection()
            cursor = conn.cursor()
            
            # 准备数据：将DataFrame转换为数据库记录
            data_to_insert = []
            from api import BaseModelWithDateTime
            current_time = BaseModelWithDateTime.format_datetime_for_db()
            
            for dt, row in df.iterrows():
                # 将时间戳转换为字符串格式
                if hasattr(dt, 'strftime'):
                    dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    dt_str = str(dt)
                
                data_to_insert.append((
                    symbol,
                    '1m',  # timeframe
                    dt_str,  # timestamp
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume']),
                    'binance',  # source
                    1,  # is_valid
                    current_time,  # created_at
                    current_time   # updated_at
                ))
            
            if overwrite:
                # 使用REPLACE来处理重复数据（覆盖模式）
                cursor.executemany('''
                    INSERT OR REPLACE INTO kline_data 
                    (symbol, timeframe, timestamp, open_price, high_price, low_price, close_price, volume, source, is_valid, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data_to_insert)
                self.logger.info(f"✅ 已覆盖保存 {len(data_to_insert)} 条 {symbol} 数据到数据库")
            else:
                # 使用INSERT OR IGNORE来跳过重复数据（跳过模式）
                cursor.executemany('''
                    INSERT OR IGNORE INTO kline_data 
                    (symbol, timeframe, timestamp, open_price, high_price, low_price, close_price, volume, source, is_valid, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data_to_insert)
                
                # 检查实际插入的数据条数
                inserted_count = cursor.rowcount
                self.logger.info(f"✅ 已保存 {inserted_count} 条 {symbol} 数据到数据库（跳过 {len(data_to_insert) - inserted_count} 条重复数据）")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"保存市场数据失败: {e}")
            return False
    
    def load_market_data(self, symbol: str, start_time: Optional[str] = None, 
                        end_time: Optional[str] = None, limit: Optional[int] = None) -> Any:
        """
        从数据库加载市场数据
        
        Args:
            symbol: 交易对名称
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 限制返回条数（可选）
            
        Returns:
            pandas.DataFrame: 包含OHLCV数据的DataFrame
        """
        try:
            # 延迟导入pandas，只在需要时导入
            import pandas as pd
            
            conn = self.get_native_connection()
            
            # 构建查询条件
            query = "SELECT timestamp, open_price, high_price, low_price, close_price, volume FROM kline_data WHERE symbol = ?"
            params = [symbol]
            
            # 添加时间范围条件
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp"
            
            # 添加数量限制
            if limit:
                query += f" LIMIT {limit}"
            
            # 执行查询
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # 处理查询结果
            if not df.empty:
                # 转换时间戳为datetime索引
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                # 重命名列以匹配标准OHLCV格式
                df.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high', 
                    'low_price': 'low',
                    'close_price': 'close'
                }, inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"加载市场数据失败: {e}")
            # 返回空的DataFrame，但避免直接导入pandas
            try:
                import pandas as pd
                return pd.DataFrame()
            except ImportError:
                # 如果pandas不可用，返回空字典
                return {}
    
    def get_market_data_summary(self) -> Dict[str, Any]:
        """获取市场数据统计信息"""
        try:
            conn = self.get_native_connection()
            cursor = conn.cursor()
            
            # 获取总数据条数
            cursor.execute("SELECT COUNT(*) FROM market_data")
            total_count = cursor.fetchone()[0]
            
            # 获取交易对数量
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM market_data")
            symbol_count = cursor.fetchone()[0]
            
            # 获取时间范围
            cursor.execute("SELECT MIN(datetime), MAX(datetime) FROM market_data")
            time_range = cursor.fetchone()
            
            # 获取各交易对的数据量
            cursor.execute("SELECT symbol, COUNT(*) FROM market_data GROUP BY symbol ORDER BY COUNT(*) DESC")
            symbols = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_records': total_count,
                'symbol_count': symbol_count,
                'start_time': time_range[0] if time_range[0] else None,
                'end_time': time_range[1] if time_range[1] else None,
                'symbols': [{'symbol': s[0], 'count': s[1]} for s in symbols]
            }
            
        except Exception as e:
            self.logger.error(f"获取市场数据统计失败: {e}")
            return {}
    
    def close(self):
        """关闭数据库连接"""
        self.db_config.close_engine() 