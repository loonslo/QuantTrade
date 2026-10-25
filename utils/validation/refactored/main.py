# -*- coding: utf-8 -*-
"""
量化交易系统 - 验证器模块（主入口）
========================================

这是重构后的主入口文件，整合所有验证功能。

重构说明:
- 原始文件: utils/validation/validators.py (695行)
- 拆分后: 6个功能模块，平均每个 < 150行
- 职责分离: 每个模块专注特定验证类型
- 易于维护: 修改不影响其他模块

作者：量化交易团队
版本：1.1.0
"""

# 导入所有核心类型
from .core_types import ValidationResult

# 导入所有验证器
from .data_validation import DataValidator, validate_symbol, validate_timeframe, validate_amount
from .strategy_validation import StrategyValidator
from .risk_validation import RiskValidator
from .universal_validation import UniversalValidator
from .data_quality import DataQualityChecker

# 向后兼容：保持原有导入方式
__all__ = [
    'ValidationResult',
    'DataValidator',
    'validate_symbol',
    'validate_timeframe',
    'validate_amount',
    'StrategyValidator',
    'RiskValidator',
    'UniversalValidator',
    'DataQualityChecker',
]

# 便捷访问方式
data_validator = DataValidator()
strategy_validator = StrategyValidator()
risk_validator = RiskValidator()
universal_validator = UniversalValidator()
data_quality_checker = DataQualityChecker()
