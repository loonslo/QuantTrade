# -*- coding: utf-8 -*-
"""
数据同步API请求模型
定义数据同步相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Any


class TechnicalIndicatorRecord(BaseModel):
    """单条技术指标记录。至少包含 timestamp，其它指标字段允许扩展。"""
    timestamp: str = Field(..., description="时间戳，格式如 YYYY-mm-dd HH:MM:SS")

    class Config:
        extra = 'allow'
