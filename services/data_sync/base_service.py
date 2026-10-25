# -*- coding: utf-8 -*-
"""
数据同步服务基类
提供组合式的数据同步服务功能
"""

from typing import Dict, Any, List, Optional, Union, Type, TypeVar
from datetime import datetime
from abc import ABC, abstractmethod
from contextlib import contextmanager

from utils.core.logger_manager import get_logger
from utils.helpers.constants import ConfigConstants
from data.types import ServiceResponse
from data.database.session_manager import get_session_manager, ORMBaseService
from .sync_manager import BaseSyncTask, SyncTaskResult, SyncTaskStatus

# 泛型类型变量
ModelType = TypeVar('ModelType')

class DataSyncService(ORMBaseService, BaseSyncTask):
    """
    数据同步服务基类

    职责：
    - 提供同步任务的执行框架（生命周期、统计、重试、批处理等）
    - 组合 ORM 能力（通过继承 ORMBaseService）与任务调度能力（BaseSyncTask）
    - 由具体业务子类实现数据抓取/转换/入库逻辑

    子类需要实现：
    - _execute_sync: 具体同步逻辑
    - get_task_config: 返回任务配置

    常用属性：
    - service_name: 服务名称
    - records_processed/updated/inserted/deleted: 统计字段
    - batch_size/max_retries/retry_delay: 批量与重试配置
    """

    def __init__(self, service_name: str):
        ORMBaseService.__init__(self, service_name)
        BaseSyncTask.__init__(self, service_name)

        # 统计组
        self.records_processed = 0
        self.records_updated = 0
        self.records_inserted = 0
        self.records_deleted = 0
        self.batch_size = 1000
        self.max_retries = 3
        self.retry_delay = 5

    def _model_to_dict(self, model_instance) -> Dict[str, Any]:
        """
        将SQLAlchemy模型实例转换为字典

        Args:
            model_instance: SQLAlchemy模型实例

        Returns:
            Dict[str, Any]: 模型实例数据
        """
        if model_instance is None:
            return {}

        result = {}
        for column in model_instance.__table__.columns:
            value = getattr(model_instance, column.name)
            # 处理datetime类型
            if isinstance(value, datetime):
                result[column.name] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                result[column.name] = value
        return result

    def _models_to_dicts(self, model_instances: List) -> List[Dict[str, Any]]:
        """
        将SQLAlchemy模型实例列表转换为字典列表

        Args:
            model_instances: SQLAlchemy模型实例列表

        Returns:
            List[Dict[str, Any]]: 模型实例数据列表
        """
        return [self._model_to_dict(instance) for instance in model_instances]

    def _build_response(self,
                        data: Union[List[dict], dict, None] = None,
                        count: int = 0,
                        message: str = "操作成功",
                        success: bool = True) -> ServiceResponse:
        """
        构建服务响应

        Args:
            data: 响应数据
            count: 数据数量
            message: 响应消息
            success: 是否成功

        Returns:
            ServiceResponse: 标准化的服务响应对象
        """
        return ServiceResponse(
            success=success,
            data=data,
            count=count,
            message=message
        )

    def _build_error_response(self,
                              error_message: str,
                              error_code: Optional[str] = None) -> ServiceResponse:
        """
        构建错误响应

        Args:
            error_message: 错误消息
            error_code: 错误代码

        Returns:
            ServiceResponse: 错误响应
        """
        return ServiceResponse(
            success=False,
            data=None,
            count=0,
            message="{}错误: {}".format(self.service_name, error_message)
        )

    def _format_datetime(self, dt: Union[datetime, str, None]) -> str:
        """
        格式化时间值

        Args:
            dt: 时间对象或字符串

        Returns:
            str: 格式化后的时间字符串
        """
        if dt is None:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d %H:%M:%S')

        if isinstance(dt, str):
            try:
                # 尝试解析ISO格式
                parsed_dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return parsed_dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                # 解析失败时返回原字符串
                return dt

        return str(dt)

    def _validate_required_fields(self,
                                  data: Dict[str, Any],
                                  required_fields: List[str]) -> bool:
        """
        验证必填字段

        Args:
            data: 待验证数据
            required_fields: 必填字段列表

        Returns:
            bool: 验证是否通过
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            self.logger.error("缺少必填字段: {}".format(missing_fields))
            return False
        return True

    def _validate_data_types(self,
                              data: Dict[str, Any],
                              field_types: Dict[str, type]) -> bool:
        """
        验证数据类型

        Args:
            data: 待验证数据
            field_types: 字段类型映射

        Returns:
            bool: 验证是否通过
        """
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                self.logger.error("字段 {} 类型错误，期望{}，实际{}".format(field, expected_type, type(data[field])))
                return False
        return True

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理数据中的None值和空字符串

        Args:
            data: 原始数据

        Returns:
            Dict[str, Any]: 清理后的数据
        """
        return {k: v for k, v in data.items() if v is not None and v != ""}

    def _format_price(self, price: Union[float, int, str]) -> float:
        """
        格式化价格数据

        Args:
            price: 价格值

        Returns:
            float: 格式化后的价格
        """
        try:
            return float(price)
        except (ValueError, TypeError):
            self.logger.warning("无效价格值: {}".format(price))
            return 0.0

    def _format_percentage(self, percentage: Union[float, int, str]) -> float:
        """
        格式化百分比数据

        Args:
            percentage: 百分比值

        Returns:
            float: 格式化后的百分比
        """
        try:
            value = float(percentage)
            # 如果值大于1，认为是百分比值，需要除以100
            if abs(value) > 1:
                value = value / 100
            return value
        except (ValueError, TypeError):
            self.logger.warning("无效百分比值: {}".format(percentage))
            return 0.0

    def _get_current_timestamp(self) -> datetime:
        """
        获取当前时间戳

        Returns:
            datetime: 当前时间
        """
        from utils.time.timestamp_utils import TimestampConverter
        return TimestampConverter.get_current_datetime_for_db()

    def _is_data_fresh(self,
                        last_updated: Union[datetime, str],
                        max_age_seconds: int = ConfigConstants.CACHE_TIMEOUT) -> bool:
        """
        检查数据是否新鲜

        Args:
            last_updated: 最后更新时间
            max_age_seconds: 最大年龄秒数

        Returns:
            bool: 数据是否新鲜
        """
        if isinstance(last_updated, str):
            try:
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            except ValueError:
                return False

        age_seconds = (datetime.now() - last_updated).total_seconds()
        return age_seconds <= max_age_seconds

    async def execute(self) -> SyncTaskResult:
        """
        执行同步任务的核心逻辑
        """
        self.start_time = datetime.now()
        self.status = SyncTaskStatus.RUNNING

        # 重置统计
        self.records_processed = 0
        self.records_updated = 0
        self.records_inserted = 0
        self.records_deleted = 0

        try:
            # 执行具体的同步逻辑
            await self._execute_sync()

            self.end_time = datetime.now()
            self.status = SyncTaskStatus.COMPLETED

            return self._create_result(
                status=SyncTaskStatus.COMPLETED,
                records_processed=self.records_processed,
                records_updated=self.records_updated,
                records_inserted=self.records_inserted
            )

        except Exception as e:
            error_msg = "同步任务执行失败: {}".format(str(e))
            self.logger.error(error_msg)

            self.end_time = datetime.now()
            self.status = SyncTaskStatus.FAILED
            self.error_message = error_msg

            return self._create_result(
                status=SyncTaskStatus.FAILED,
                error_message=error_msg
            )

    @abstractmethod
    async def _execute_sync(self):
        """
        执行具体的同步逻辑 - 子类必须实现
        """
        pass

    @abstractmethod
    def get_task_config(self) -> Dict[str, Any]:
        """
        获取任务配置 - 子类必须实现
        """
        pass

    def _batch_process(self, items: List[Any], process_func, batch_size: Optional[int] = None) -> int:
        """
        批量处理数据

        Args:
            items: 待处理数据列表
            process_func: 处理函数
            batch_size: 批次大小

        Returns:
            int: 处理记录数量
        """
        if not items:
            return 0

        batch_size = batch_size or self.batch_size
        processed_count = 0

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                result = process_func(batch)
                processed_count += len(batch)
                self.logger.debug("批量处理完成: {} 个记录".format(len(batch)))
            except Exception as e:
                self.logger.error("批量处理失败: {}".format(e))
                # 如果遇到错误，继续处理下一批
                raise

        return processed_count

    def _retry_on_failure(self, func, *args, **kwargs):
        """
        失败时重试

        Args:
            func: 要执行的函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        import time

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    self.logger.warning("第 {} 次失败，{}秒后重试: {}".format(attempt + 1, self.retry_delay, e))
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error("重试 {} 次后仍然失败: {}".format(self.max_retries, e))

        raise last_exception

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计

        Returns:
            Dict[str, Any]: 性能统计
        """
        execution_time = None
        if self.start_time and self.end_time:
            execution_time = (self.end_time - self.start_time).total_seconds()

        return {
            'service_name': self.service_name,
            'status': self.status.value if self.status else 'unknown',
            'records_processed': self.records_processed,
            'records_updated': self.records_updated,
            'records_inserted': self.records_inserted,
            'records_deleted': self.records_deleted,
            'execution_time': execution_time,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message
        }