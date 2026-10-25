"""
调度器管理器
管理任务的基本功能：列表、执行、记录
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict, deque

from utils.core.logger_manager import get_logger
from config.python_config.scheduler_config import SchedulerConfig, TaskConfig
from services.data_sync import DataSyncService
from services.data_sync.tasks.kline_data_sync import get_kline_data_sync_service
from services.data_sync.tasks.futures_data_sync_v2 import get_futures_data_sync_service_v2
from services.data_sync.tasks.us_market_sync import get_us_market_sync_service
from services.data_sync.tasks.qdii_fund_sync import get_qdii_fund_sync_service


class SchedulerManager:
    """调度器管理器"""
    
    def __init__(self):
        self.logger = get_logger("scheduler_manager")
        self.data_sync_service = DataSyncService()
        self._task_functions: Dict[str, callable] = {}
        
        # 任务执行历史记录（内存缓存，用于快速访问）
        self._task_execution_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # 初始化任务函数映射
        self._init_task_functions()
    
    def _init_task_functions(self):
        """初始化任务函数映射 - 更新为ORM服务结构"""
        kline_sync_service = get_kline_data_sync_service()
        futures_sync_service = get_futures_data_sync_service_v2()
        us_market_sync_service = get_us_market_sync_service()
        qdii_fund_sync_service = get_qdii_fund_sync_service()
        
        # 创建同步包装器函数，将异步函数转换为同步函数
        def sync_wrapper(async_func):
            """将异步函数包装为同步函数，供APScheduler调用"""
            def wrapper(*args, **kwargs):
                import asyncio
                import threading
                
                # 在线程池中运行时，总是创建新的事件循环
                def run_in_thread():
                    try:
                        # 创建新的事件循环
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(async_func(*args, **kwargs))
                            return result
                        finally:
                            loop.close()
                    except Exception as e:
                        raise e
                
                # 检查是否在主线程中
                if threading.current_thread() is threading.main_thread():
                    try:
                        # 尝试获取当前事件循环
                        loop = asyncio.get_running_loop()
                        # 如果有运行中的事件循环，在新线程中运行
                        result = None
                        exception = None
                        
                        def thread_target():
                            nonlocal result, exception
                            try:
                                result = run_in_thread()
                            except Exception as e:
                                exception = e
                        
                        thread = threading.Thread(target=thread_target)
                        thread.start()
                        thread.join()
                        
                        if exception:
                            raise exception
                        return result
                    except RuntimeError:
                        # 没有运行中的事件循环，直接运行
                        return run_in_thread()
                else:
                    # 在子线程中，直接创建新的事件循环
                    return run_in_thread()
            return wrapper
        
        # 默认交易对列表（热门币种）
        default_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
                          "SOLUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT"]

        self._task_functions = {
            # 数据同步服务任务 - 使用同步包装器
            "sync_popular_coins_data": sync_wrapper(self.data_sync_service.sync_top_symbols),
            "sync_market_overview_data": sync_wrapper(self.data_sync_service.sync_market_overview),
            # K线数据同步任务 - 使用新的KlineDataSyncService
            "sync_kline_1m_data": sync_wrapper(lambda: kline_sync_service.manual_sync_kline_data("1m", None, 1)),
            "sync_kline_3m_data": sync_wrapper(lambda: kline_sync_service.manual_sync_kline_data("3m", None, 1)),
            "sync_kline_5m_data": sync_wrapper(lambda: kline_sync_service.manual_sync_kline_data("5m", None, 1)),
            "sync_kline_15m_data": sync_wrapper(lambda: kline_sync_service.manual_sync_kline_data("15m", None, 1)),
            "sync_kline_1h_data": sync_wrapper(lambda: kline_sync_service.manual_sync_kline_data("1h", None, 1)),
            "sync_kline_4h_data": sync_wrapper(lambda: kline_sync_service.manual_sync_kline_data("4h", None, 1)),
            "sync_kline_1d_data": sync_wrapper(lambda: kline_sync_service.manual_sync_kline_data("1d", None, 1)),
            "database_maintenance": sync_wrapper(self.data_sync_service.database_maintenance),
            "data_cleanup": sync_wrapper(self.data_sync_service.cleanup_old_cache),

            # 期货数据同步任务（方案3：统一表结构）
            "sync_futures_data_v2": sync_wrapper(lambda: futures_sync_service.sync_futures_data()),

            # 美国市场数据同步任务
            "sync_us_market_data": sync_wrapper(us_market_sync_service.sync_us_market_data),

            # QDII基金数据同步任务
            "sync_all_qdii_funds": sync_wrapper(qdii_fund_sync_service.sync_all_qdii_funds),

            # K线数据同步服务任务（保持向后兼容）
            "sync_minute_kline_data": sync_wrapper(kline_sync_service.sync_minute_kline_data),
            "sync_daily_kline_data": sync_wrapper(kline_sync_service.sync_daily_kline_data),
            # 维护任务不需要，移除
        }
    
    def get_task_function(self, task_id: str) -> Optional[callable]:
        """获取任务函数"""
        return self._task_functions.get(task_id)
    
    def get_all_task_functions(self) -> Dict[str, callable]:
        """获取所有任务函数"""
        return self._task_functions.copy()
    
    def get_task_config(self, task_id: str) -> Optional[TaskConfig]:
        """获取任务配置"""
        return SchedulerConfig.get_task_by_id(task_id)
    
    def get_all_task_configs(self) -> Dict[str, TaskConfig]:
        """获取所有任务配置"""
        return SchedulerConfig.get_all_tasks()
    
    def validate_task(self, task_id: str) -> bool:
        """验证任务是否存在且有效"""
        task_config = self.get_task_config(task_id)
        if not task_config:
            return False
        
        task_function = self.get_task_function(task_id)
        if not task_function:
            return False
        
        return task_config.enabled
    
    async def execute_task_manually(self, task_id: str, **kwargs) -> bool:
        """手动执行任务"""
        try:
            if not self.validate_task(task_id):
                self.logger.error(f"任务验证失败: {task_id}")
                return False
            
            task_function = self.get_task_function(task_id)
            if not task_function:
                self.logger.error(f"任务函数不存在: {task_id}")
                return False
            
            self.logger.info(f"开始手动执行任务: {task_id}")
            result = await task_function(**kwargs)
            self.logger.info(f"任务手动执行完成: {task_id}, 结果: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"任务手动执行失败: {task_id}, 错误: {e}")
            return False
    
    def record_task_execution(self, task_id: str, success: bool, execution_time: float, 
                            error: Optional[str] = None, result: Any = None, 
                            execution_type: str = "manual", retry_count: int = 0):
        """记录任务执行结果"""
        try:
            # 获取任务配置
            task_config = self.get_task_config(task_id)
            task_name = task_config.func_name if task_config else task_id
            
            # 内存缓存（用于快速访问，不存储结果内容）
            execution_record = {
                "task_id": task_id,
                "task_name": task_name,
                "success": success,
                "execution_time": execution_time,
                "error": error,
                "result_type": type(result).__name__ if result is not None else None,
                "result_size": len(str(result)) if result is not None else 0,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "execution_type": execution_type,
                "retry_count": retry_count
            }
            
            # 添加到执行历史
            self._task_execution_history[task_id].append(execution_record)
            
            if success:
                self.logger.info(f"任务执行成功记录: {task_id}, 耗时: {execution_time:.2f}秒")
            else:
                self.logger.warning(f"任务执行失败记录: {task_id}, 错误: {error}")
                
        except Exception as e:
            self.logger.error(f"记录任务执行结果失败: {e}")
    
    def get_task_execution_history(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务执行历史"""
        try:
            # 从内存缓存获取历史记录
            history = list(self._task_execution_history[task_id])
            # 返回最新的记录，限制数量
            return history[-limit:] if history else []
        except Exception as e:
            self.logger.error(f"获取任务执行历史失败: {e}")
            return []
    
    def get_orm_service_status(self) -> Dict[str, Any]:
        """获取ORM服务状态概览"""
        try:
            from data.orm_services import get_kline_data_service
            
            # 获取K线数据服务
            kline_service = get_kline_data_service()
            
            # 获取系统健康状态（简化版本）
            health_data = {
                "status": "healthy",
                "services": {
                    "kline_service": "active",
                    "database": "connected"
                }
            }
            
            # 获取任务执行统计
            task_stats = {}
            for task_id in self._task_functions.keys():
                history = self.get_task_execution_history(task_id, 5)
                if history:
                    recent_success = sum(1 for h in history if h.get('success', False))
                    total_recent = len(history)
                    task_stats[task_id] = {
                        "recent_success_rate": recent_success / total_recent if total_recent > 0 else 0,
                        "last_execution": history[-1].get('timestamp') if history else None,
                        "last_success": history[-1].get('success', False) if history else False
                    }
            
            return {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "orm_services_health": health_data,
                "task_execution_stats": task_stats,
                "total_tasks": len(self._task_functions),
                "active_tasks": len([t for t in task_stats.values() if t.get('last_success', False)])
            }
            
        except Exception as e:
            self.logger.error(f"获取ORM服务状态失败: {e}")
            return {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "error": str(e),
                "orm_services_health": {},
                "task_execution_stats": {},
                "total_tasks": 0,
                "active_tasks": 0
            }

    def _sync_coin_list_from_coingecko(self) -> bool:
        """
        从CoinGecko同步币种列表到系统配置

        注意：此任务已不再使用，币种列表改为手动管理
        如需同步，请直接调用 /api/config/coin-list/sync 接口
        """
        try:
            from services.orm.coin_sync_service import get_coin_sync_service

            sync_service = get_coin_sync_service()

            # 同步20个主流币种
            success = sync_service.sync_from_coingecko(limit=20)

            if success:
                self.logger.info("✅ 币种列表同步成功（从CoinGecko）")
            else:
                self.logger.error("❌ 币种列表同步失败")

            return success

        except Exception as e:
            self.logger.error(f"币种列表同步异常: {e}")
            return False


# 全局调度器管理器实例
_scheduler_manager: Optional[SchedulerManager] = None


def get_scheduler_manager() -> SchedulerManager:
    """获取调度器管理器实例（单例模式）"""
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager


