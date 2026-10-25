"""
任务工具函数
提供任务执行、错误处理、日志记录等通用功能
"""

import asyncio
import functools
from typing import Callable, Any, Dict, Optional
from datetime import datetime
from utils.core.logger_manager import get_logger


def task_wrapper(func: Callable) -> Callable:
    """
    任务装饰器
    提供统一的错误处理、日志记录和性能监控
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        task_name = func.__name__
        logger = get_logger(f"scheduler.{task_name}")
        
        start_time = datetime.now()
        logger.info(f"开始执行任务: {task_name}")
        
        try:
            # 执行任务
            result = await func(*args, **kwargs)
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"任务执行成功: {task_name}, 耗时: {execution_time:.2f}秒")
            
            return result
            
        except Exception as e:
            # 记录错误信息
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"任务执行失败: {task_name}, 耗时: {execution_time:.2f}秒, 错误: {str(e)}")
            
            # 重新抛出异常，让上层处理
            raise
    
    return wrapper


def sync_task_wrapper(func: Callable) -> Callable:
    """
    同步任务装饰器
    将同步函数包装为异步函数
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 在线程池中执行同步函数
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    
    return wrapper


class TaskMetrics:
    """任务执行指标统计"""
    
    def __init__(self):
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = None
        self.last_success_time = None
        self.last_failure_time = None
    
    def record_execution(self, success: bool, execution_time: float):
        """记录任务执行结果"""
        self.execution_count += 1
        self.total_execution_time += execution_time
        self.last_execution_time = datetime.now()
        
        if success:
            self.success_count += 1
            self.last_success_time = datetime.now()
        else:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    def get_average_execution_time(self) -> float:
        """获取平均执行时间"""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.get_success_rate(),
            "average_execution_time": self.get_average_execution_time(),
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


# 全局任务指标存储
task_metrics: Dict[str, TaskMetrics] = {}


def get_task_metrics(task_name: str) -> TaskMetrics:
    """获取任务指标"""
    if task_name not in task_metrics:
        task_metrics[task_name] = TaskMetrics()
    return task_metrics[task_name]


def record_task_execution(task_name: str, success: bool, execution_time: float):
    """记录任务执行指标"""
    metrics = get_task_metrics(task_name)
    metrics.record_execution(success, execution_time)


def get_all_task_metrics() -> Dict[str, Dict[str, Any]]:
    """获取所有任务指标"""
    return {name: metrics.to_dict() for name, metrics in task_metrics.items()}


def create_task_response(
    task_id: str,
    status: str,
    message: str = "任务处理中",
    data: Any = None,
    progress: Optional[float] = None
) -> Dict[str, Any]:
    """
    创建任务响应
    
    Args:
        task_id: 任务ID
        status: 任务状态 (pending, running, completed, failed)
        message: 响应消息
        data: 任务数据
        progress: 任务进度 (0-100)
        
    Returns:
        任务响应字典
    """
    response = {
        "task_id": task_id,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if progress is not None:
        response["progress"] = progress
    
    return response


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息，如果任务不存在则返回None
    """
    # 这里应该从任务存储中获取任务状态
    # 目前返回基于任务指标的状态
    if task_id in task_metrics:
        metrics = task_metrics[task_id]
        return {
            "task_id": task_id,
            "status": "completed" if metrics.success_count > 0 else "failed",
            "execution_count": metrics.execution_count,
            "success_count": metrics.success_count,
            "failure_count": metrics.failure_count,
            "success_rate": metrics.get_success_rate(),
            "average_execution_time": metrics.get_average_execution_time(),
            "last_execution_time": metrics.last_execution_time.isoformat() if metrics.last_execution_time else None,
            "last_success_time": metrics.last_success_time.isoformat() if metrics.last_success_time else None,
            "last_failure_time": metrics.last_failure_time.isoformat() if metrics.last_failure_time else None
        }
    
    return None


def format_task_result(
    task_id: str,
    result: Any,
    success: bool = True,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    格式化任务结果
    
    Args:
        task_id: 任务ID
        result: 任务执行结果
        success: 是否成功
        error_message: 错误消息
        
    Returns:
        格式化的任务结果
    """
    response = {
        "task_id": task_id,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if success:
        response["data"] = result
        response["message"] = "任务执行成功"
    else:
        response["error"] = error_message or "任务执行失败"
        if result is not None:
            response["data"] = result
    
    return response


def handle_task_error(
    task_id: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    处理任务错误
    
    Args:
        task_id: 任务ID
        error: 异常对象
        context: 错误上下文信息
        
    Returns:
        错误响应字典
    """
    logger = get_logger(f"task_error.{task_id}")
    
    # 记录错误日志
    error_msg = f"任务 {task_id} 执行失败: {str(error)}"
    if context:
        error_msg += f", 上下文: {context}"
    
    logger.error(error_msg, exc_info=True)
    
    # 返回错误响应
    response = {
        "task_id": task_id,
        "success": False,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {}
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return response