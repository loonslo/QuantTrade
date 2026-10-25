"""
API工具模块
提供API响应、任务处理等API相关工具
"""

from .responses import (
    create_success_response,
    create_error_response,
    create_paginated_response,
    create_no_content_response,
    create_created_response,
    create_validation_error_response,
    create_not_found_response,
    create_unauthorized_response,
    create_forbidden_response,
    create_rate_limit_response
)

from .task_utils import (
    task_wrapper,
    sync_task_wrapper,
    TaskMetrics,
    get_task_metrics,
    record_task_execution,
    get_all_task_metrics,
    create_task_response,
    get_task_status,
    format_task_result,
    handle_task_error
)

__all__ = [
    # 响应工具
    'create_success_response',
    'create_error_response', 
    'create_paginated_response',
    'create_no_content_response',
    'create_created_response',
    'create_validation_error_response',
    'create_not_found_response',
    'create_unauthorized_response',
    'create_forbidden_response',
    'create_rate_limit_response',
    
    # 任务工具
    'task_wrapper',
    'sync_task_wrapper',
    'TaskMetrics',
    'get_task_metrics',
    'record_task_execution',
    'get_all_task_metrics',
    'create_task_response',
    'get_task_status',
    'format_task_result',
    'handle_task_error'
]
