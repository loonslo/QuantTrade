"""
数据库配置管理
支持多种数据库类型和配置
"""

import os
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from .sql_logging_config import enable_sql_logging_for_engine


class DatabaseConfig:
    """数据库配置管理"""
    
    # 支持的数据库类型
    SUPPORTED_DATABASES = {
        'sqlite': 'sqlite:///{db_path}',
        'postgresql': 'postgresql://{user}:{password}@{host}:{port}/{database}',
        'mysql': 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
        'mongodb': 'mongodb://{host}:{port}/{database}'
    }
    
    def __init__(self):
        # 从环境变量或配置文件读取数据库配置
        self.db_type = os.getenv('DB_TYPE', 'sqlite')
        self.db_path = os.getenv('DB_PATH', 'quant_trading.db')
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'quant_trading')
        self.db_user = os.getenv('DB_USER', '')
        self.db_password = os.getenv('DB_PASSWORD', '')
        
        # 连接池配置
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '20'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '30'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        
        # 初始化引擎和会话工厂
        self._engine: Optional[Engine] = None
        self._SessionLocal: Optional[sessionmaker] = None
        
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        if self.db_type == 'sqlite':
            return self.SUPPORTED_DATABASES['sqlite'].format(db_path=self.db_path)
        elif self.db_type == 'postgresql':
            return self.SUPPORTED_DATABASES['postgresql'].format(
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name
            )
        elif self.db_type == 'mysql':
            return self.SUPPORTED_DATABASES['mysql'].format(
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name
            )
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")
    
    def create_engine(self) -> Engine:
        """创建数据库引擎"""
        if self._engine is None:
            database_url = self.get_database_url()
            
            # 根据数据库类型配置引擎参数
            if self.db_type == 'sqlite':
                self._engine = create_engine(
                    database_url,
                    echo=False,  # 禁用SQLAlchemy默认日志，使用自定义日志
                    connect_args={"check_same_thread": False}
                )
            else:
                self._engine = create_engine(
                    database_url,
                    echo=False,  # 禁用SQLAlchemy默认日志，使用自定义日志
                    poolclass=QueuePool,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    pool_pre_ping=True
                )
            
            # 启用高级SQL日志功能（统一日志格式）
            enable_sql_logging_for_engine(self._engine)
        
        return self._engine
    
    def get_session_factory(self) -> sessionmaker:
        """获取会话工厂"""
        if self._SessionLocal is None:
            engine = self.create_engine()
            self._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
        
        return self._SessionLocal
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        SessionLocal = self.get_session_factory()
        return SessionLocal()
    
    def close_engine(self):
        """关闭数据库引擎"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._SessionLocal = None
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"数据库连接测试失败: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """获取数据库信息"""
        return {
            "type": self.db_type,
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "connected": self.test_connection()
        }


# 全局数据库配置实例
_database_config: Optional[DatabaseConfig] = None


def get_database_config() -> DatabaseConfig:
    """获取数据库配置实例（单例模式）"""
    global _database_config
    if _database_config is None:
        _database_config = DatabaseConfig()
    return _database_config


def get_database_session() -> Session:
    """获取数据库会话（依赖注入）"""
    config = get_database_config()
    return config.get_session()


def close_database():
    """关闭数据库连接"""
    global _database_config
    if _database_config:
        _database_config.close_engine()
        _database_config = None


# 导入数据库初始化器
from .database_initializer import DatabaseInitializer
