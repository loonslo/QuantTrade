"""
量化交易系统 - 验证器模块（重构后）
========================================

重构说明:
- 原始文件: utils/validation/validators.py (695行)
- 拆分后: 多个独立模块，平均每个 < 200行
- 职责分离: 每个模块专注特定验证类型
- 易于维护: 修改不影响其他模块

作者：量化交易团队
版本：1.1.0
"""

import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from ..core.logger_manager import get_logger


# 类 UniversalValidator 未找到

