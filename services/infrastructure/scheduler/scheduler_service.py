# -*- coding: utf-8 -*-
"""
定时任务调度器核心服务
基于APScheduler实现的任务调度系统
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.pool import ThreadPoolExecutor
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    BackgroundScheduler = None
    CronTrigger = None
    IntervalTrigger = None
    DateTrigger = None
    MemoryJobStore = None
    ThreadPoolExecutor = None

from utils.core.logger_manager import get_logger
from config.python_config.scheduler_config import SchedulerConfig, TaskConfig

# 使用懒加载避免循环导入问题
_scheduler_manager = None

def _get_scheduler_manager():
    """懒加载获取调度器管理器"""
    global _scheduler_manager
    if _scheduler_manager is None:
        from api.core.scheduler_manager import get_scheduler_manager
        _scheduler_manager = get_scheduler_manager()
    return _scheduler_manager

class SchedulerService:
    """定时任务调度器服务"""

    def __init__(self):
        self.logger = get_logger("scheduler_service")
        self._scheduler_manager = None  # 延迟初始化

        if not APSCHEDULER_AVAILABLE:
            self.logger.error("APScheduler未安装，定时任务功能不可用")
            self.scheduler = None
            return

        # 配置调度器
        self._configure_scheduler()
        self._is_running = False

    def _get_scheduler_manager(self):
        """获取调度器管理器（懒加载）"""
        if self._scheduler_manager is None:
            from api.core.scheduler_manager import get_scheduler_manager
            self._scheduler_manager = get_scheduler_manager()
        return self._scheduler_manager

    def _configure_scheduler(self):
        """配置调度器"""
        try:
            # 配置执行器
            executors = {
                'default': ThreadPoolExecutor(max_workers=10)
            }

            # 配置任务存储
            jobstores = {
                'default': MemoryJobStore()
            }

            # 创建调度器
            self.scheduler = BackgroundScheduler(
                executors=executors,
                jobstores=jobstores,
                timezone='Asia/Shanghai'
            )

            # 配置调度器选项
            self.scheduler.configure(
                job_defaults={
                    'coalesce': True,
                    'max_instances': 1,
                    'misfire_grace_time': 60
                }
            )

            self.logger.info("调度器配置完成")

        except Exception as e:
            self.logger.error(f"调度器配置失败: {e}")
            self.scheduler = None

    def start(self) -> bool:
        """启动调度器"""
        if not self.scheduler:
            self.logger.error("调度器未配置，无法启动")
            return False

        try:
            if not self._is_running:
                self.scheduler.start()
                self._is_running = True
                self.logger.info("调度器启动成功")

                # 初始化所有任务
                self._initialize_all_jobs()

            return True

        except Exception as e:
            self.logger.error(f"调度器启动失败: {e}")
            return False

    def stop(self) -> bool:
        """停止调度器"""
        if not self.scheduler:
            return False

        try:
            if self._is_running:
                self.scheduler.shutdown(wait=True)
                self._is_running = False
                self.logger.info("调度器已停止")
            return True

        except Exception as e:
            self.logger.error(f"调度器停止失败: {e}")
            return False

    def is_running(self) -> bool:
        """检查调度器是否运行中"""
        return self._is_running and self.scheduler and self.scheduler.running

    def _initialize_all_jobs(self):
        """初始化所有定时任务"""
        try:
            # 获取所有任务配置
            all_tasks = SchedulerConfig.get_all_tasks()

            for task_name, task_config in all_tasks.items():
                if task_config.enabled:
                    self._add_job(task_config)

            self.logger.info(f"成功初始化{len(all_tasks)} 个定时任务")

        except Exception as e:
            self.logger.error(f"初始化定时任务失败: {e}")

    def _add_job(self, task_config: TaskConfig) -> bool:
        """添加定时任务"""
        try:
            if not self.scheduler:
                return False

            # 获取任务函数：使用task_id 作为键与 SchedulerManager 保持一致
            task_function = self._get_scheduler_manager().get_task_function(task_config.task_id)
            if not task_function:
                self.logger.error(f"任务函数不存在: {task_config.task_id}")
                return False

            # 创建触发器
            trigger = self._create_trigger(task_config)
            if not trigger:
                self.logger.error(f"创建触发器失败: {task_config.task_id}")
                return False

            # 添加任务
            self.scheduler.add_job(
                func=task_function,
                trigger=trigger,
                id=task_config.task_id,
                name=task_config.task_id,
                max_instances=task_config.max_instances,
                coalesce=task_config.coalesce,
                misfire_grace_time=task_config.misfire_grace_time,
                replace_existing=True
            )

            self.logger.info(f"成功添加定时任务: {task_config.task_id}")
            return True

        except Exception as e:
            self.logger.error(f"添加定时任务失败: {task_config.task_id}, 错误: {e}")
            return False

    def _create_trigger(self, task_config: TaskConfig):
        """创建触发器"""
        try:
            trigger_type = task_config.trigger_type
            trigger_args = task_config.trigger_args

            if trigger_type == "cron":
                return CronTrigger(**trigger_args)
            elif trigger_type == "interval":
                return IntervalTrigger(**trigger_args)
            elif trigger_type == "date":
                return DateTrigger(**trigger_args)
            else:
                self.logger.error(f"不支持的触发器类型: {trigger_type}")
                return None

        except Exception as e:
            self.logger.error(f"创建触发器失败: {e}")
            return None

    def add_job(self, task_config: TaskConfig) -> bool:
        """动态添加任务"""
        return self._add_job(task_config)

    def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        try:
            if self.scheduler and self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                self.logger.info(f"成功移除任务: {job_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"移除任务失败: {job_id}, 错误: {e}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        try:
            if self.scheduler and self.scheduler.get_job(job_id):
                self.scheduler.pause_job(job_id)
                self.logger.info(f"成功暂停任务: {job_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"暂停任务失败: {job_id}, 错误: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        try:
            if self.scheduler and self.scheduler.get_job(job_id):
                self.scheduler.resume_job(job_id)
                self.logger.info(f"成功恢复任务: {job_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"恢复任务失败: {job_id}, 错误: {e}")
            return False

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        try:
            if not self.scheduler:
                return None

            job = self.scheduler.get_job(job_id)
            if not job:
                return None

            return {
                "id": job.id,
                "name": job.name,
                "func": job.func_ref,
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "active": not job.pending
            }

        except Exception as e:
            self.logger.error(f"获取任务信息失败: {job_id}, 错误: {e}")
            return None

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """获取所有任务信息"""
        try:
            if not self.scheduler:
                return []

            jobs = []
            for job in self.scheduler.get_jobs():
                job_info = {
                    "id": job.id,
                    "name": job.name,
                    "func": job.func_ref,
                    "trigger": str(job.trigger),
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "active": not job.pending
                }
                jobs.append(job_info)

            return jobs

        except Exception as e:
            self.logger.error(f"获取所有任务信息失败: {e}")
            return []

    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        if not self.scheduler:
            return {"error": "调度器未配置"}

        try:
            return {
                "running": self.is_running(),
                "job_count": len(self.scheduler.get_jobs())
            }

        except Exception as e:
            self.logger.error(f"获取调度器状态失败: {e}")
            return {"error": str(e)}

    def trigger_job(self, job_id: str) -> bool:
        """手动触发任务"""
        try:
            if not self.scheduler:
                return False

            job = self.scheduler.get_job(job_id)
            if not job:
                self.logger.error(f"任务不存在: {job_id}")
                return False

            # 手动执行任务
            self.scheduler.trigger_job(job_id)
            self.logger.info(f"成功触发任务: {job_id}")
            return True

        except Exception as e:
            self.logger.error(f"触发任务失败: {job_id}, 错误: {e}")
            return False

    def execute_task_manually(self, task_id: str) -> Dict[str, Any]:
        """手动执行任务（绕过调度器）"""
        try:
            self.logger.info(f"开始手动执行任务: {task_id}")

            # 获取任务函数
            task_function = self._get_scheduler_manager().get_task_function(task_id)
            if not task_function:
                error_msg = f"任务函数不存在: {task_id}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": error_msg,
                    "execution_time": None
                }

            # 记录执行开始时间
            start_time = datetime.now()

            try:
                # 执行任务（同步方式）
                # 注意：由于我们在scheduler_manager中已经包装了异步函数，
                # 这里的task_function应该都是同步函数
                result = task_function()

                # 记录执行结束时间
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()

                self.logger.info(f"任务执行成功: {task_id}, 耗时: {execution_time:.2f}秒")

                # 记录执行历史
                self._get_scheduler_manager().record_task_execution(
                    task_id, True, execution_time, None, result, "manual", 0
                )

                return {
                    "success": True,
                    "task_id": task_id,
                    "result": result,
                    "execution_time": execution_time,
                    "message": "任务执行成功"
                }

            except Exception as e:
                # 记录执行结束时间
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()

                error_msg = f"任务执行失败: {str(e)}"
                self.logger.error(f"{error_msg}, 耗时: {execution_time:.2f}秒")

                # 记录执行历史
                self._get_scheduler_manager().record_task_execution(
                    task_id, False, execution_time, str(e), None, "manual", 0
                )

                return {
                    "success": False,
                    "task_id": task_id,
                    "error": error_msg,
                    "execution_time": execution_time
                }

        except Exception as e:
            error_msg = f"手动执行任务失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "task_id": task_id,
                "error": error_msg,
                "execution_time": None
            }

    def get_task_execution_history(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务执行历史"""
        try:
            return self._get_scheduler_manager().get_task_execution_history(task_id, limit)
        except Exception as e:
            self.logger.error(f"获取任务执行历史失败: {e}")
            return []

# 全局调度器服务实例在 __init__.py 中管理