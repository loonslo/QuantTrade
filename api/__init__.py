"""
API模块初始化
"""

# 延迟导入避免循环依赖
def create_app():
    """创建FastAPI应用"""
    from .app import create_app as _create_app
    return _create_app()

__all__ = ["create_app"]
