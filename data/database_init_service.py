"""
数据库初始化服务
统一管理所有数据库表的创建和初始化
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import inspect

from utils.core.logger_manager import get_logger
from data.config.database_config import get_database_config
from data.models.base.base_model import BaseModel as MarketDataBase
from data.models.base.base_model import Base as KlineDataBase


# 移除对已删除文件的依赖，直接使用SQLAlchemy


class DatabaseInitService:
    """数据库初始化服务"""
    
    def __init__(self):
        self.logger = get_logger('database_init_service')
        self.db_config = get_database_config()
        self.engine = None
        self.session_factory = None
        
    def _get_engine(self):
        """获取数据库引擎"""
        if self.engine is None:
            self.engine = self.db_config.create_engine()
        return self.engine
    
    def _get_session_factory(self):
        """获取会话工厂"""
        if self.session_factory is None:
            self.session_factory = self.db_config.get_session_factory()
        return self.session_factory

    def _list_declared_tables(self) -> set:
        """从已注册的 SQLAlchemy Base 动态收集应存在的表名"""
        tables = set()
        for base in (MarketDataBase, KlineDataBase):
            try:
                tables.update(base.metadata.tables.keys())
            except Exception:
                # 保守处理，单个 Base 获取失败不影响其他 Base
                continue
        return tables
    
    def init_all_tables(self) -> bool:
        """初始化所有数据库表（使用SQLAlchemy ORM）"""
        try:
            self.logger.info("🔄 开始初始化数据库表...")
            
            # 使用SQLAlchemy ORM创建所有模型表
            success = self._create_sqlalchemy_tables()
            
            if success:
                self.logger.info("✅ 所有数据库表初始化完成")
                return True
            else:
                self.logger.error("❌ 数据库表初始化失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 数据库表初始化失败: {e}")
            return False
    
    def _create_sqlalchemy_tables(self) -> bool:
        """使用SQLAlchemy创建模型表"""
        try:
            engine = self._get_engine()
            
            # 创建所有SQLAlchemy模型表
            MarketDataBase.metadata.create_all(bind=engine)
            KlineDataBase.metadata.create_all(bind=engine)
            
            self.logger.info("✅ SQLAlchemy模型表创建完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ SQLAlchemy表创建失败: {e}")
            return False
    
    # 已移除原生SQL表创建方法，完全使用SQLAlchemy ORM
    
    def check_tables_exist(self) -> Dict[str, bool]:
        """检查所有表是否存在（基于模型元数据动态收集）"""
        try:
            engine = self._get_engine()
            inspector = inspect(engine)
            
            # 获取实际存在的表名
            existing_tables = set(inspector.get_table_names())

            # 动态收集应存在的表名（与模型保持一致，避免硬编码漂移）
            required_tables = self._list_declared_tables()
            
            # 检查每个表是否存在
            table_status = {}
            for table in required_tables:
                table_status[table] = table in existing_tables
            
            return table_status
            
        except Exception as e:
            self.logger.error(f"❌ 检查表存在性失败: {e}")
            return {}
    
    def get_missing_tables(self) -> List[str]:
        """获取缺失的表列表"""
        table_status = self.check_tables_exist()
        return [table for table, exists in table_status.items() if not exists]
    
    def get_table_info(self) -> Dict[str, Any]:
        """获取数据库表信息"""
        try:
            engine = self._get_engine()
            inspector = inspect(engine)
            
            tables = inspector.get_table_names()
            table_info = {}
            
            for table in tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                
                table_info[table] = {
                    'columns': len(columns),
                    'column_names': [col['name'] for col in columns],
                    'indexes': len(indexes),
                    'index_names': [idx['name'] for idx in indexes if idx['name']]
                }
            
            return table_info
            
        except Exception as e:
            self.logger.error(f"❌ 获取表信息失败: {e}")
            return {}
    
    def verify_database_integrity(self) -> bool:
        """验证数据库完整性"""
        try:
            # 检查关键表是否存在
            missing_tables = self.get_missing_tables()
            
            if missing_tables:
                self.logger.warning(f"⚠️  发现缺失的表: {missing_tables}")
                return False
            
            # 检查表结构
            table_info = self.get_table_info()
            if not table_info:
                self.logger.error("❌ 无法获取表信息")
                return False
            
            self.logger.info(f"✅ 数据库完整性验证通过，共 {len(table_info)} 个表")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 数据库完整性验证失败: {e}")
            return False
    
    def create_missing_tables(self) -> bool:
        """只创建缺失的表"""
        try:
            missing_tables = self.get_missing_tables()
            
            if not missing_tables:
                self.logger.info("✅ 所有表已存在，无需创建")
                return True
            
            self.logger.info(f"🔄 发现 {len(missing_tables)} 个缺失的表，开始创建...")
            
            # 重新初始化所有表（CREATE TABLE IF NOT EXISTS 会跳过已存在的表）
            return self.init_all_tables()
            
        except Exception as e:
            self.logger.error(f"❌ 创建缺失表失败: {e}")
            return False
    
    def get_database_status(self) -> Dict[str, Any]:
        """获取数据库状态信息"""
        try:
            table_status = self.check_tables_exist()
            table_info = self.get_table_info()
            missing_tables = self.get_missing_tables()
            
            return {
                'total_tables': len(table_status),
                'existing_tables': len([t for t, exists in table_status.items() if exists]),
                'missing_tables': len(missing_tables),
                'missing_table_names': missing_tables,
                'table_details': table_info,
                'database_path': self.db_config.db_path,
                'database_type': self.db_config.db_type
            }
            
        except Exception as e:
            self.logger.error(f"❌ 获取数据库状态失败: {e}")
            return {}


# 全局服务实例
_database_init_service: Optional[DatabaseInitService] = None


def get_database_init_service() -> DatabaseInitService:
    """获取数据库初始化服务实例（单例模式）"""
    global _database_init_service
    if _database_init_service is None:
        _database_init_service = DatabaseInitService()
    return _database_init_service


def init_database_tables() -> bool:
    """便捷函数：初始化数据库表"""
    service = get_database_init_service()
    return service.init_all_tables()


def check_and_create_tables() -> bool:
    """便捷函数：检查并创建缺失的表"""
    service = get_database_init_service()
    return service.create_missing_tables()


if __name__ == "__main__":
    # 直接运行此脚本时初始化数据库
    print("🚀 数据库表初始化服务")
    print("=" * 40)
    
    service = get_database_init_service()
    
    # 显示当前状态
    status = service.get_database_status()
    print(f"📊 数据库状态:")
    print(f"   - 数据库类型: {status.get('database_type', 'unknown')}")
    print(f"   - 数据库路径: {status.get('database_path', 'unknown')}")
    print(f"   - 总表数: {status.get('total_tables', 0)}")
    print(f"   - 已存在: {status.get('existing_tables', 0)}")
    print(f"   - 缺失: {status.get('missing_tables', 0)}")
    
    if status.get('missing_tables', 0) > 0:
        print(f"   - 缺失的表: {', '.join(status.get('missing_table_names', []))}")
    
    print("\n🔄 开始初始化...")
    success = service.init_all_tables()
    
    if success:
        print("✅ 数据库表初始化成功")
        
        # 显示表详情
        table_info = service.get_table_info()
        print(f"\n📋 表详情:")
        for table, info in table_info.items():
            print(f"  {table}: {info['columns']} 列, {info['indexes']} 个索引")
    else:
        print("❌ 数据库表初始化失败")
