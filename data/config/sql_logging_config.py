# -*- coding: utf-8 -*-
"""
SQL日志配置
提供灵活的SQL查询日志配置选项
"""

import logging
import os
from typing import Optional
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

class SQLLoggingConfig:
    """SQL日志配置管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger('sqlalchemy.engine')
        self.logger.setLevel(logging.INFO)
        
        # 从环境变量读取配置
        self.enable_sql_logging = os.getenv('ENABLE_SQL_LOGGING', 'true').lower() == 'true'
        self.sql_log_level = os.getenv('SQL_LOG_LEVEL', 'INFO').upper()
        self.log_sql_params = os.getenv('LOG_SQL_PARAMS', 'true').lower() == 'true'
        self.log_sql_timing = os.getenv('LOG_SQL_TIMING', 'true').lower() == 'true'
        
        # 配置日志格式
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志格式"""
        if not self.enable_sql_logging:
            return
            
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.sql_log_level))
        
        # 设置日志格式
        if self.log_sql_timing:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [SQL] %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [SQL] %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        
        # 添加处理器（避免重复）
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.propagate = False
            # 设置日志级别，避免重复记录
            self.logger.setLevel(getattr(logging, self.sql_log_level))
    
    def enable_engine_logging(self, engine: Engine):
        """为数据库引擎启用SQL日志"""
        if not self.enable_sql_logging:
            return
            
        # 监听SQL语句执行
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """SQL执行前的事件处理"""
            if self.log_sql_params and parameters:
                self.logger.info(f"执行SQL: {statement}")
                self.logger.info(f"参数: {parameters}")
            else:
                self.logger.info(f"执行SQL: {statement}")
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """SQL执行后的事件处理"""
            if self.log_sql_timing:
                # 这里可以添加执行时间统计
                pass
    
    def enable_pool_logging(self, engine: Engine):
        """为连接池启用日志"""
        if not self.enable_sql_logging:
            return
            
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """连接建立时的日志"""
            self.logger.debug("数据库连接已建立")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """从连接池获取连接时的日志"""
            self.logger.debug("从连接池获取连接")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接归还到连接池时的日志"""
            self.logger.debug("连接已归还到连接池")
    
    def get_logging_config(self) -> dict:
        """获取当前日志配置"""
        return {
            "enable_sql_logging": self.enable_sql_logging,
            "sql_log_level": self.sql_log_level,
            "log_sql_params": self.log_sql_params,
            "log_sql_timing": self.log_sql_timing
        }

# 全局SQL日志配置实例
_sql_logging_config: Optional[SQLLoggingConfig] = None

def get_sql_logging_config() -> SQLLoggingConfig:
    """获取SQL日志配置实例（单例模式）"""
    global _sql_logging_config
    if _sql_logging_config is None:
        _sql_logging_config = SQLLoggingConfig()
    return _sql_logging_config

def enable_sql_logging_for_engine(engine: Engine):
    """为数据库引擎启用SQL日志"""
    config = get_sql_logging_config()
    config.enable_engine_logging(engine)
    config.enable_pool_logging(engine)
