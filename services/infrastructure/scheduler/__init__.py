# -*- coding: utf-8 -*-
# Scheduler Services
"""
调度服务模块
提供任务调度和定时任务管理功
"""

from .scheduler_service import SchedulerService

# 全局调度器服务实例
_scheduler_service = None

def get_scheduler_service() -> SchedulerService:
    """获取调度器服务实例"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service

__all__ = [
    "SchedulerService",
    "get_scheduler_service"
]
