"""
定时任务调度器配置
集中管理所有定时任务的配置信息
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TaskConfig:
    """任务配置类"""
    task_id: str
    func_name: str
    trigger_type: str  # cron, interval, date
    trigger_args: Dict[str, Any]
    max_instances: int = 1
    coalesce: bool = True
    misfire_grace_time: int = 60
    enabled: bool = True
    description: str = ""  # 任务描述


class SchedulerConfig:
    """调度器配置管理"""
    
    # 数据同步任务配置 - 更新为ORM服务结构
    DATA_SYNC_TASKS = {
        
        # 热门币种同步 - 使用ORM服务
        "popular_coins_data_sync": TaskConfig(
            task_id="sync_popular_coins_data",
            func_name="sync_top_symbols",
            trigger_type="interval", 
            trigger_args={"minutes": 10},  # 每10分钟同步一次
            max_instances=1,
            misfire_grace_time=120,
            description="同步热门交易对数据到popular_coins表"
        ),
        
        
        # 市场概览同步 - 使用ORM服务
        "market_overview_data_sync": TaskConfig(
            task_id="sync_market_overview_data",
            func_name="sync_market_overview",
            trigger_type="interval",
            trigger_args={"minutes": 5},  # 每5分钟同步一次
            max_instances=1,
            misfire_grace_time=60,
            description="同步市场概览数据到market_overview表"
        ),
        
        # 1分钟K线数据同步 - 使用ORM拆分表
        "kline_1m_data_sync": TaskConfig(
            task_id="sync_kline_1m_data",
            func_name="sync_market_data_1m",
            trigger_type="interval",
            trigger_args={"minutes": 3},  # 每3分钟同步一次
            max_instances=1,
            misfire_grace_time=120,
            description="同步1分钟K线数据到kline_1m拆分表"
        ),
        
        # 3分钟K线数据同步
        "kline_3m_data_sync": TaskConfig(
            task_id="sync_kline_3m_data",
            func_name="sync_market_data_3m",
            trigger_type="interval",
            trigger_args={"minutes": 5},  # 每5分钟同步一次
            max_instances=1,
            misfire_grace_time=120,
            description="同步3分钟K线数据到kline_3m拆分表"
        ),
        
        # 5分钟K线数据同步
        "kline_5m_data_sync": TaskConfig(
            task_id="sync_kline_5m_data",
            func_name="sync_market_data_5m",
            trigger_type="interval",
            trigger_args={"minutes": 8},  # 每8分钟同步一次
            max_instances=1,
            misfire_grace_time=120,
            description="同步5分钟K线数据到kline_5m拆分表"
        ),
        
        # 15分钟K线数据同步
        "kline_15m_data_sync": TaskConfig(
            task_id="sync_kline_15m_data",
            func_name="sync_market_data_15m",
            trigger_type="interval",
            trigger_args={"minutes": 20},  # 每20分钟同步一次
            max_instances=1,
            misfire_grace_time=180,
            description="同步15分钟K线数据到kline_15m拆分表"
        ),
        
        # 1小时K线数据同步
        "kline_1h_data_sync": TaskConfig(
            task_id="sync_kline_1h_data",
            func_name="sync_market_data_1h",
            trigger_type="interval",
            trigger_args={"minutes": 65},  # 每65分钟同步一次
            max_instances=1,
            misfire_grace_time=300,
            description="同步1小时K线数据到kline_1h拆分表"
        ),
        
        # 4小时K线数据同步
        "kline_4h_data_sync": TaskConfig(
            task_id="sync_kline_4h_data",
            func_name="sync_market_data_4h",
            trigger_type="interval",
            trigger_args={"hours": 4, "minutes": 10},  # 每4小时10分钟同步一次
            max_instances=1,
            misfire_grace_time=600,
            description="同步4小时K线数据到kline_4h拆分表"
        ),
        
        # 1天K线数据同步 - 使用ORM拆分表
        "kline_1d_data_sync": TaskConfig(
            task_id="sync_kline_1d_data",
            func_name="sync_market_data_1d",
            trigger_type="cron",
            trigger_args={"hour": 1, "minute": 0},  # 每天凌晨1点同步一次
            max_instances=1,
            misfire_grace_time=300,
            description="同步1天K线数据到kline_1d拆分表"
        ),
        
        # 数据库维护任务
        "database_maintenance": TaskConfig(
            task_id="database_maintenance",
            func_name="database_maintenance",
            trigger_type="cron",
            trigger_args={"hour": 2, "minute": 0},  # 每天凌晨2点执行
            max_instances=1,
            misfire_grace_time=300,
            description="数据库维护任务（VACUUM、ANALYZE等）"
        ),
        
        # 过期数据清理任务
        "data_cleanup": TaskConfig(
            task_id="data_cleanup",
            func_name="cleanup_old_cache",
            trigger_type="cron",
            trigger_args={"hour": 3, "minute": 0},  # 每天凌晨3点执行
            max_instances=1,
            misfire_grace_time=300,
            description="清理数据库中的过期数据"
        ),

        # 支撑阻力位同步任务（暂时禁用，等待实现）
        "support_resistance_4h_sync": TaskConfig(
            task_id="sync_support_resistance_4h",
            func_name="sync_support_resistance_4h",
            trigger_type="interval",
            trigger_args={"hours": 4},
            max_instances=1,
            misfire_grace_time=600,
            enabled=False,  # 暂时禁用
            description="同步4小时支撑阻力位数据（未实现）"
        ),

        "support_resistance_1d_sync": TaskConfig(
            task_id="sync_support_resistance_1d",
            func_name="sync_support_resistance_1d",
            trigger_type="cron",
            trigger_args={"hour": 1, "minute": 30},
            max_instances=1,
            misfire_grace_time=600,
            enabled=False,  # 暂时禁用
            description="同步日线支撑阻力位数据（未实现）"
        ),

        # 交易信号同步任务（暂时禁用，等待实现）
        "trading_signals_15m_sync": TaskConfig(
            task_id="sync_trading_signals_15m",
            func_name="sync_trading_signals_15m",
            trigger_type="interval",
            trigger_args={"minutes": 15},
            max_instances=1,
            misfire_grace_time=300,
            enabled=False,  # 暂时禁用
            description="同步15分钟交易信号数据（未实现）"
        ),

        "trading_signals_4h_sync": TaskConfig(
            task_id="sync_trading_signals_4h",
            func_name="sync_trading_signals_4h",
            trigger_type="interval",
            trigger_args={"hours": 4},
            max_instances=1,
            misfire_grace_time=600,
            enabled=False,  # 暂时禁用
            description="同步4小时交易信号数据（未实现）"
        ),

        "trading_signals_1d_sync": TaskConfig(
            task_id="sync_trading_signals_1d",
            func_name="sync_trading_signals_1d",
            trigger_type="cron",
            trigger_args={"hour": 2, "minute": 0},
            max_instances=1,
            misfire_grace_time=600,
            enabled=False,  # 暂时禁用
            description="同步日线交易信号数据（未实现）"
        ),

        # 期货数据同步任务（方案3：统一表结构）
        "futures_data_v2_sync": TaskConfig(
            task_id="sync_futures_data_v2",
            func_name="sync_futures_data_v2",
            trigger_type="interval",
            trigger_args={"minutes": 5},  # 每5分钟同步一次
            max_instances=1,
            misfire_grace_time=120,
            description="同步期货数据到统一表结构（持仓量和资金费率）"
        ),

        # 美国市场数据同步任务
        "us_market_data_sync": TaskConfig(
            task_id="sync_us_market_data",
            func_name="sync_us_market_data",
            trigger_type="cron",
            trigger_args={"hour": 22, "minute": 30},  # 每天22:30同步（美股收盘后）
            max_instances=1,
            misfire_grace_time=300,
            description="同步美国市场数据（纳斯达克、标普500、美元人民币汇率）"
        ),

        # QDII基金数据同步任务
        "qdii_fund_data_sync": TaskConfig(
            task_id="sync_all_qdii_funds",
            func_name="sync_all_qdii_funds",
            trigger_type="cron",
            trigger_args={"hour": 15, "minute": 30},  # 每天15:30同步（A股收盘后）
            max_instances=1,
            misfire_grace_time=300,
            description="同步QDII基金数据（纳斯达克和标普相关）"
        ),
    }
    
    # 系统维护任务配置
    SYSTEM_TASKS = {}
    
    @classmethod
    def get_all_tasks(cls) -> Dict[str, TaskConfig]:
        """获取所有任务配置"""
        return {**cls.DATA_SYNC_TASKS, **cls.SYSTEM_TASKS}
    
    @classmethod
    def get_data_sync_tasks(cls) -> Dict[str, TaskConfig]:
        """获取数据同步任务配置"""
        return cls.DATA_SYNC_TASKS
    
    @classmethod
    def get_system_tasks(cls) -> Dict[str, TaskConfig]:
        """获取系统维护任务配置"""
        return cls.SYSTEM_TASKS
    
    @classmethod
    def get_task_by_id(cls, task_id: str) -> TaskConfig:
        """根据任务ID获取配置"""
        all_tasks = cls.get_all_tasks()
        # 通过task_id字段查找，而不是通过字典的键
        for task_config in all_tasks.values():
            if task_config.task_id == task_id:
                return task_config
        return None
