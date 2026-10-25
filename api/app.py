"""
优化后的FastAPI应用
采用分层架构设计，统一使用路由和服务层
"""

from fastapi import FastAPI
# WebSocket功能已屏蔽
# from fastapi import WebSocket
import uvicorn
import signal
import sys
import os
from contextlib import asynccontextmanager

from utils.core.logger_manager import get_logger
from utils.core.config_manager import ConfigManager
# 临时注释掉调度器导入以解决循环导入问题
# from services.infrastructure.scheduler import get_scheduler_service
from data.config.database_initializer import DatabaseInitializer
# 导入整合后的路由
from api.routes import api_router

# 导入新的中间件和异常处理
from api.middleware import setup_all_middleware
from api.api_exceptions import register_exception_handlers


class QuantTradeAPI:
    """量化交易API应用"""

    def __init__(self, *, initialize_database: bool = True, enable_scheduler: bool = False):
        self.logger = get_logger("api.app")
        self.config_manager = ConfigManager()
        self.scheduler_service = None
        self.initialize_database = initialize_database
        self.enable_scheduler = enable_scheduler
        self.app = self._create_app()
        self._setup_middleware()
        self._setup_routes()
        self._setup_exception_handlers()

    def _create_app(self) -> FastAPI:
        """创建FastAPI应用"""
        @asynccontextmanager
        async def lifespan(app):
            if self.initialize_database:
                self._init_database_tables()
            if self.enable_scheduler:
                self._start_scheduler_service()
            try:
                yield
            finally:
                self._stop_scheduler_service()

        return FastAPI(
            title="QuantTrade API",
            description="提供量化交易系统的REST API接口",
            version="2.0.0",
            lifespan=lifespan,
            docs_url="/docs",
            redoc_url="/redoc"
        )

    def _setup_middleware(self):
        """设置中间件"""
        # 使用新的统一中间件设置
        setup_all_middleware(self.app, enable_rate_limiting=True)

    def _setup_routes(self):
        """设置路由"""
        # 注册API路由 - 只保留数据同步相关路由
        self.app.include_router(api_router)

        @self.app.get('/health', tags=['健康检查'])
        def health():
            return {'success': True, 'service': 'QuantTrade', 'version': '2.0.0'}

        # 配置静态文件服务 - 用于提供币种图标访问
        from fastapi.staticfiles import StaticFiles
        from pathlib import Path

        # 使用绝对路径确保正确映射
        # 获取当前文件所在目录
        current_dir = Path(__file__).parent.parent
        assets_dir = current_dir / "assets"
        self.logger.info(f"静态文件目录: {assets_dir} (存在: {assets_dir.exists()})")

        if assets_dir.exists():
            self.app.mount(
                "/static",
                StaticFiles(directory=str(assets_dir)),
                name="static"
            )
            self.logger.info(f"✅ 静态文件服务已配置: /static -> {assets_dir}")
        else:
            self.logger.warning("⚠️ assets 目录不存在，无法配置静态文件服务")

    def _setup_exception_handlers(self):
        """设置异常处理器"""
        # 注册新的异常处理器
        register_exception_handlers(self.app)

    def _init_support_resistance_system(self):
        """初始化支撑阻力位分析系统"""
        try:
            self.logger.info("初始化支撑阻力位分析系统...")
            
            # 1. 初始化数据库表
            self._init_database_tables()
            
            # 2. 启动定时任务服务
            self._start_scheduler_service()
            
            self.logger.info("支撑阻力位分析系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 支撑阻力位系统初始化失败: {e}")
            # 不抛出异常，允许API服务器继续启动
    
    def _init_database_tables(self):
        """初始化数据库表"""
        try:
            self.logger.info("📊 检查并创建支撑阻力位数据表...")
            
            # 创建数据库初始化器
            initializer = DatabaseInitializer()
            initializer.init_all_tables()
            
            # 导入模型以确保表被创建
            # 注意：SupportResistanceLevel 已合并到 crypto_technical_analysis 表中
            # 已移除对 CryptoTechnicalAnalysis 的依赖
            
            self.logger.info("✅ 支撑阻力位数据表检查完成")
            
        except Exception as e:
            self.logger.error(f"❌ 数据表初始化失败: {e}")
            raise
    
    def _start_scheduler_service(self):
        """启动定时任务服务"""
        try:
            self.logger.info("⏰ 启动调度器服务...")

            # 使用懒加载避免循环导入问题
            from services.infrastructure.scheduler import get_scheduler_service

            self.scheduler_service = get_scheduler_service()
            if not self.scheduler_service.start():
                raise Exception("调度器启动失败")

            self.logger.info("✅ 调度器服务启动成功")

            # 获取任务状态
            status = self.scheduler_service.get_scheduler_status()
            self.logger.info(f"📊 调度器状态: {status}")

        except ImportError as e:
            self.logger.warning(f"⚠️ 调度器服务导入失败: {e}")
        except Exception as e:
            self.logger.warning(f"⚠️ 调度器服务启动失败: {e}")
            # 不抛出异常，允许API服务器继续运行

    def _stop_scheduler_service(self):
        """停止定时任务服务"""
        try:
            if self.scheduler_service:
                self.logger.info("⏰ 停止定时任务服务...")
                self.scheduler_service.stop()
                self.logger.info("✅ 定时任务服务已停止")
        except Exception as e:
            self.logger.error(f"❌ 停止定时任务服务失败: {e}")

    def run(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """运行应用"""
        try:
            self.logger.info(f"🚀 启动量化交易系统API服务器: {host}:{port}")
            self.logger.info("📊 数据同步系统已集成")
            self.logger.info("📍 API文档: http://localhost:8000/docs")
            self.logger.info("🔧 数据同步接口: http://localhost:8000/api/data-sync")
            
            
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                reload=reload,
                log_level="info",
                access_log=True
            )
        except KeyboardInterrupt:
            self.logger.info("🛑 收到停止信号")
            self._stop_scheduler_service()
            self.logger.info("✅ 服务器已停止")
        except Exception as e:
            self.logger.error(f"❌ 服务器启动失败: {e}")
            self._stop_scheduler_service()
            sys.exit(1)


def create_app(*, initialize_database: bool = True, enable_scheduler: bool | None = None) -> FastAPI:
    """创建应用实例（用于uvicorn）"""
    if enable_scheduler is None:
        enable_scheduler = os.getenv('QUANTTRADE_ENABLE_SCHEDULER', '').lower() in {'1', 'true'}
    api = QuantTradeAPI(initialize_database=initialize_database, enable_scheduler=enable_scheduler)
    return api.app


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """启动服务器"""
    api = QuantTradeAPI()
    api.run(host, port, reload)


if __name__ == "__main__":
    # 信号处理
    def signal_handler(sig, frame):
        """信号处理器"""
        print("\n🛑 正在关闭服务器...")
        sys.exit(0)


    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 启动量化交易系统API服务器...")
    print("📍 服务器地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔄 按 Ctrl+C 停止服务器")
    print("-" * 50)

    run_server()
