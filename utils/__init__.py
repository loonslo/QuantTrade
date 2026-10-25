"""
统一工具模块
提供项目中所有工具类的统一入口
"""

# 核心工具
from .core import (
    ConfigManager,
    config_manager,
    LoggerManager,
    logger_manager,
    get_logger,
    SingletonManager,
    singleton_manager
)

# API工具
from .api import (
    create_success_response,
    create_error_response,
    create_paginated_response,
    create_no_content_response,
    create_created_response,
    create_validation_error_response,
    create_not_found_response,
    create_unauthorized_response,
    create_forbidden_response,
    create_rate_limit_response,
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

# 验证工具
# from .validation import *  # 避免循环导入

# 时间工具
# from .time import *  # 避免循环导入

# 助手工具
from .helpers.constants import ConfigConstants

# 服务工具
from .services import (
    ServiceConfigManager,
    get_config_manager,
    LLMConfigManager,
    llm_config_manager
)

__all__ = [
    # 核心工具
    'ConfigManager',
    'config_manager',
    'LoggerManager', 
    'logger_manager',
    'get_logger',
    'SingletonManager',
    'singleton_manager',
    
    # API工具
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
    'task_wrapper',
    'sync_task_wrapper',
    'TaskMetrics',
    'get_task_metrics',
    'record_task_execution',
    'get_all_task_metrics',
    'create_task_response',
    'get_task_status',
    'format_task_result',
    # 助手工具
    'ConfigConstants',
    
    # 服务工具
    'ServiceConfigManager',
    'get_config_manager',
    'LLMConfigManager',
    'llm_config_manager'
]