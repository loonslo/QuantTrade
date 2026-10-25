# -*- coding: utf-8 -*-
"""
DataSyncService 最小子类示例

用法：复制此模板到你的服务模块，修改类名与实现细节。
"""

from typing import Dict, Any

from services.data_sync.base_service import DataSyncService


class ExampleDataSyncService(DataSyncService):
    """示例：实现一个最小的数据同步服务"""

    def __init__(self, service_name: str = "example_data_sync"):
        super().__init__(service_name)

    async def _execute_sync(self):
        # 1) 拉取外部数据
        # 2) 清洗/转换
        # 3) 通过 ORM 写入数据库
        # 更新统计字段以便监控与结果输出
        self.records_processed += 0
        self.records_inserted += 0
        self.records_updated += 0

    def get_task_config(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "batch_size": self.batch_size,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "enabled": True,
        }


