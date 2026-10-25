"""
通用Pydantic模式定义
定义基础模型和通用字段
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BaseModelWithDateTime(BaseModel):
    """带时间戳的基础模型"""
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = Field(False, description="请求失败")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_details: Optional[dict] = Field(None, description="错误详情")


class PaginationParams(BaseModel):
    """分页参数模型"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(20, ge=1, le=100, description="每页大小，最大100")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginationResponse(BaseModel):
    """分页响应模型"""
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    total: int = Field(..., description="总记录数")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    
    @classmethod
    def create(cls, page: int, size: int, total: int) -> "PaginationResponse":
        """创建分页响应"""
        pages = (total + size - 1) // size
        return cls(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
