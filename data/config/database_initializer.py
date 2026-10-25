"""
数据库初始化器
负责创建和管理数据库表结构
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from utils.core.logger_manager import get_logger
from data.config.database_config import get_database_config


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, db_path: str = "quant_trading.db"):
        self.logger = get_logger('db_initializer')
        self.db_path = db_path
        self.db_config = get_database_config()
    
    def init_all_tables(self):
        """初始化所有数据表"""
        try:
            self.logger.info("开始初始化数据库表...")
            
            # 使用SQLAlchemy模型创建所有表
            self._create_tables_with_sqlalchemy()
            
            self.logger.info("✅ 数据库表初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 数据库表初始化失败: {e}")
            raise
    
    def _create_tables_with_sqlalchemy(self):
        """使用SQLAlchemy模型创建所有表"""
        try:
            engine = self.db_config.create_engine()
            
            # 导入所有SQLAlchemy模型（统一Base，导入data.models会注册全部模型）
            from data.models import Base as ModelsBase
            
            # 先删除可能冲突的索引
            self._cleanup_conflicting_indexes(engine)
            
            # 创建所有模型表（统一一次性创建）
            ModelsBase.metadata.create_all(bind=engine)
            
            self.logger.info("✅ SQLAlchemy模型表创建完成")
            
        except Exception as e:
            self.logger.error(f"❌ SQLAlchemy表创建失败: {e}")
            raise
    
    def _cleanup_conflicting_indexes(self, engine):
        """清理可能冲突的索引"""
        try:
            # 可能冲突的索引名称
            conflicting_indexes = [
                'idx_symbol_latest',
                'idx_symbol_timeframe', 
                'idx_analysis_time',
                'idx_confidence',
                'idx_created_at'
            ]
            
            with engine.connect() as conn:
                for index_name in conflicting_indexes:
                    try:
                        conn.execute(text(f"DROP INDEX IF EXISTS {index_name};"))
                        self.logger.info(f"清理索引: {index_name}")
                    except Exception as e:
                        self.logger.debug(f"清理索引 {index_name} 时出错: {e}")
                
                conn.commit()
                
        except Exception as e:
            self.logger.warning(f"清理冲突索引时出错: {e}")
    
    def check_tables_exist(self) -> dict:
        """检查表是否存在"""
        try:
            engine = self.db_config.create_engine()
            
            tables_to_check = [
                # K线数据表
                'kline_data_1m',
                'kline_data_3m', 
                'kline_data_5m',
                'kline_data_15m',
                'kline_data_1h',
                'kline_data_4h',
                'kline_data_1d',
                
                # 市场数据表
                'crypto_market_rankings',
                'market_overview',
                
                # 技术指标表
                'technical_indicators',
                
                # 交易记录表
                'trade_records',
                
                # 注意：以下表已删除或合并
                # 'support_resistance_levels',
                # 'trading_signals',
                # 'analysis_history',
                # 'fear_greed_index',
                # 'coin_details',
                # 'market_data'
            ]
            
            existing_tables = []
            missing_tables = []
            
            with engine.connect() as conn:
                for table in tables_to_check:
                    try:
                        conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1;"))
                        existing_tables.append(table)
                    except Exception:
                        missing_tables.append(table)
            
            return {
                'existing_tables': existing_tables,
                'missing_tables': missing_tables,
                'total_tables': len(tables_to_check),
                'existing_count': len(existing_tables),
                'missing_count': len(missing_tables)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 检查表存在性失败: {e}")
            return {}
    
    def drop_all_tables(self):
        """删除所有表（谨慎使用）"""
        try:
            engine = self.db_config.create_engine()
            
            # 获取所有表名（与check_tables_exist保持一致）
            tables = [
                # K线数据表
                'kline_data_1m',
                'kline_data_3m', 
                'kline_data_5m',
                'kline_data_15m',
                'kline_data_1h',
                'kline_data_4h',
                'kline_data_1d',
                
                # 市场数据表
                'crypto_market_rankings',
                'market_overview',
                
                # 技术指标表
                'technical_indicators',
                
                # 交易记录表
                'trade_records',
            ]
            
            with engine.connect() as conn:
                for table in tables:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table};"))
                        self.logger.info(f"删除表: {table}")
                    except Exception as e:
                        self.logger.warning(f"删除表 {table} 失败: {e}")
                
                conn.commit()
            
            self.logger.info("✅ 所有表删除完成")
            
        except Exception as e:
            self.logger.error(f"❌ 删除表失败: {e}")
            raise


# 获取数据库初始化器实例
def get_database_initializer(db_path: str = "quant_trading.db") -> DatabaseInitializer:
    """获取数据库初始化器实例"""
    return DatabaseInitializer(db_path)