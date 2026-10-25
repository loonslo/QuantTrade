# -*- coding: utf-8 -*-
"""
统一回测服务
处理回测相关的业务逻辑，包括回测执行、结果管理和统计分析
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import asyncio

from services.base.base_service import BaseService, ServiceMixin
from services.base.interfaces.services import IBacktestService
from utils.validation.exceptions import ValidationException
from core.backtrader_runner import run_backtrader_backtest

class BacktestValidationError(ValidationException):
    """回测验证错误"""

    def __init__(self, message: str, backtest_id: str = None, details: dict = None):
        self.backtest_id = backtest_id
        super().__init__(message, details=details)

class BacktestService(BaseService, ServiceMixin, IBacktestService):
    """
    统一回测服务

    功能：
    - 回测执行和管理
    - 回测结果存储和检索
    - 回测历史管理
    - 回测统计分析
    """

    def __init__(self, **kwargs):
        super().__init__(service_name="backtest", **kwargs)

        # 回测结果存储（生产环境应使用数据库）
        self._backtest_results: Dict[str, Dict[str, Any]] = {}
        self._backtest_queue: List[Dict[str, Any]] = []
        self._running_backtests: Dict[str, Dict[str, Any]] = {}

        # 回测配置
        self.max_concurrent_backtests = self.get_config("backtest.max_concurrent", 3)
        self.default_initial_cash = self.get_config("backtest.default_initial_cash", 100000.0)

    async def _on_initialize(self) -> None:
        """初始化钩子"""
        self.logger.info("初始化回测服务")

        # 启动回测队列处理器
        asyncio.create_task(self._process_backtest_queue())

        self.logger.info("回测服务初始化完成")

    # 实现IBacktestService接口

    async def run_backtest(self,
                          strategy_name: str,
                          symbol: str,
                          timeframe: str,
                          start_date: datetime,
                          end_date: datetime,
                          initial_cash: float,
                          params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行回测

        Args:
            strategy_name: 策略名称
            symbol: 交易对
            timeframe: 时间周期
            start_date: 开始日期
            end_date: 结束日期
            initial_cash: 初始资金
            params: 策略参数

        Returns:
            回测结果
        """
        try:
            # 验证回测参数
            await self._validate_backtest_params(
                strategy_name, symbol, timeframe, start_date, end_date, initial_cash, params
            )

            # 生成回测ID
            backtest_id = str(uuid.uuid4())

            # 创建回测任务
            backtest_task = {
                "id": backtest_id,
                "strategy_name": strategy_name,
                "symbol": symbol,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "initial_cash": initial_cash,
                "params": params,
                "status": "queued",
                "created_at": datetime.now(),
                "progress": 0
            }

            # 添加到队列
            self._backtest_queue.append(backtest_task)

            self.logger.info(f"回测任务已加入队列: {backtest_id}")

            return {
                "backtest_id": backtest_id,
                "status": "queued",
                "message": "回测任务已加入队列",
                "estimated_start_time": datetime.now() + timedelta(seconds=30)
            }

        except Exception as e:
            self.logger.error(f"创建回测任务失败: {e}")
            raise BacktestValidationError(f"创建回测任务失败: {e}")

    async def get_backtest_result(self, backtest_id: str) -> Dict[str, Any]:
        """
        获取回测结果

        Args:
            backtest_id: 回测ID

        Returns:
            回测结果
        """
        try:
            if not backtest_id:
                raise BacktestValidationError("回测ID不能为空", backtest_id)

            # 检查运行中的回测
            if backtest_id in self._running_backtests:
                running_backtest = self._running_backtests[backtest_id]
                return {
                    "backtest_id": backtest_id,
                    "status": "running",
                    "progress": running_backtest.get("progress", 0),
                    "message": "回测正在运行中",
                    "started_at": running_backtest.get("started_at")
                }

            # 检查队列中的回测
            queued_backtest = next((bt for bt in self._backtest_queue if bt["id"] == backtest_id), None)
            if queued_backtest:
                return {
                    "backtest_id": backtest_id,
                    "status": "queued",
                    "message": "回测在队列中等待",
                    "created_at": queued_backtest.get("created_at")
                }

            # 检查已完成的结果
            if backtest_id in self._backtest_results:
                result = self._backtest_results[backtest_id]
                return {
                    "backtest_id": backtest_id,
                    "status": "completed",
                    "result": result,
                    "message": "回测已完成"
                }

            raise BacktestValidationError(f"回测结果不存在: {backtest_id}", backtest_id)

        except BacktestValidationError:
            raise
        except Exception as e:
            self.logger.error(f"获取回测结果失败 {backtest_id}: {e}")
            raise BacktestValidationError(f"获取回测结果失败: {e}", backtest_id)

    async def list_backtest_history(self,
                                   page: int = 1,
                                   page_size: int = 10,
                                   filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取回测历史列表

        Args:
            page: 页码
            page_size: 每页大小
            filters: 过滤条件

        Returns:
            回测历史列表
        """
        try:
            # 验证分页参数
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 10

            # 获取所有结果
            all_results = list(self._backtest_results.values())

            # 应用过滤条件
            if filters:
                all_results = self._apply_filters(all_results, filters)

            # 排序（按创建时间倒序）
            all_results.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

            # 分页
            total = len(all_results)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            page_results = all_results[start_index:end_index]

            # 构建历史列表
            history = []
            for result in page_results:
                history.append({
                    "backtest_id": result["id"],
                    "strategy_name": result["strategy_name"],
                    "symbol": result["symbol"],
                    "timeframe": result["timeframe"],
                    "start_date": result["start_date"],
                    "end_date": result["end_date"],
                    "initial_cash": result["initial_cash"],
                    "final_cash": result.get("final_cash", result["initial_cash"]),
                    "total_return": result.get("total_return", 0.0),
                    "status": result.get("status", "completed"),
                    "created_at": result.get("created_at"),
                    "completed_at": result.get("completed_at")
                })

            return {
                "history": history,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size,
                    "has_next": end_index < total,
                    "has_prev": page > 1
                },
                "message": "获取回测历史成功"
            }

        except Exception as e:
            self.logger.error(f"获取回测历史失败: {e}")
            raise BacktestValidationError(f"获取回测历史失败: {e}")

    async def cancel_backtest(self, backtest_id: str) -> Dict[str, Any]:
        """
        取消回测

        Args:
            backtest_id: 回测ID

        Returns:
            取消结果
        """
        try:
            if not backtest_id:
                raise BacktestValidationError("回测ID不能为空", backtest_id)

            # 检查运行中的回测
            if backtest_id in self._running_backtests:
                del self._running_backtests[backtest_id]
                self.logger.info(f"取消运行中的回测: {backtest_id}")
                return {
                    "backtest_id": backtest_id,
                    "status": "cancelled",
                    "message": "回测已取消"
                }

            # 检查队列中的回测
            for i, backtest in enumerate(self._backtest_queue):
                if backtest["id"] == backtest_id:
                    del self._backtest_queue[i]
                    self.logger.info(f"取消队列中的回测: {backtest_id}")
                    return {
                        "backtest_id": backtest_id,
                        "status": "cancelled",
                        "message": "回测已取消"
                    }

            raise BacktestValidationError(f"回测不存在或已完成: {backtest_id}", backtest_id)

        except BacktestValidationError:
            raise
        except Exception as e:
            self.logger.error(f"取消回测失败 {backtest_id}: {e}")
            raise BacktestValidationError(f"取消回测失败: {e}", backtest_id)

    async def get_backtest_statistics(self) -> Dict[str, Any]:
        """
        获取回测统计信息

        Returns:
            回测统计信息
        """
        try:
            results = list(self._backtest_results.values())

            if not results:
                return {
                    "total_backtests": 0,
                    "successful_backtests": 0,
                    "average_return": 0.0,
                    "best_strategy": None,
                    "most_used_symbol": None,
                    "message": "暂无回测数据"
                }

            # 统计信息
            total_backtests = len(results)
            successful_backtests = len([r for r in results if r.get("total_return", 0) > 0])

            # 平均收益率
            returns = [r.get("total_return", 0) for r in results]
            average_return = sum(returns) / len(returns) if returns else 0.0

            # 最佳策略
            best_result = max(results, key=lambda x: x.get("total_return", 0))
            best_strategy = best_result.get("strategy_name")

            # 最常用交易对
            symbols = [r.get("symbol") for r in results]
            symbol_counts = {}
            for symbol in symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            most_used_symbol = max(symbol_counts.items(), key=lambda x: x[1])[0] if symbol_counts else None

            # 策略分布
            strategies = [r.get("strategy_name") for r in results]
            strategy_counts = {}
            for strategy in strategies:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

            return {
                "total_backtests": total_backtests,
                "successful_backtests": successful_backtests,
                "success_rate": (successful_backtests / total_backtests * 100) if total_backtests > 0 else 0,
                "average_return": round(average_return, 2),
                "best_return": round(best_result.get("total_return", 0), 2),
                "best_strategy": best_strategy,
                "most_used_symbol": most_used_symbol,
                "strategy_distribution": strategy_counts,
                "symbol_distribution": symbol_counts,
                "queue_size": len(self._backtest_queue),
                "running_count": len(self._running_backtests),
                "message": "获取回测统计成功"
            }

        except Exception as e:
            self.logger.error(f"获取回测统计失败: {e}")
            raise BacktestValidationError(f"获取回测统计失败: {e}")

    # 业务方法

    async def _validate_backtest_params(self,
                                       strategy_name: str,
                                       symbol: str,
                                       timeframe: str,
                                       start_date: datetime,
                                       end_date: datetime,
                                       initial_cash: float,
                                       params: Dict[str, Any]) -> None:
        """验证回测参数"""
        # 验证策略名称
        if not strategy_name:
            raise BacktestValidationError("策略名称不能为空")

        # 验证交易对
        if not symbol:
            raise BacktestValidationError("交易对不能为空")

        # 验证时间周期
        valid_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        if timeframe not in valid_timeframes:
            raise BacktestValidationError(f"无效的时间周期: {timeframe}")

        # 验证日期范围
        if start_date >= end_date:
            raise BacktestValidationError("开始日期必须早于结束日期")

        # 验证日期不能太久远
        max_history = datetime.now() - timedelta(days=365 * 5)  # 5年
        if start_date < max_history:
            raise BacktestValidationError("开始日期不能超过5年前")

        # 验证初始资金
        if initial_cash <= 0:
            raise BacktestValidationError("初始资金必须大于0")

        if initial_cash < 100:
            raise BacktestValidationError("初始资金不能少于100")

    async def _process_backtest_queue(self) -> None:
        """处理回测队列"""
        while True:
            try:
                # 检查是否有可运行的回测
                if (len(self._running_backtests) < self.max_concurrent_backtests and
                    self._backtest_queue):

                    # 获取队列中的第一个回测
                    backtest_task = self._backtest_queue.pop(0)

                    # 启动回测
                    asyncio.create_task(self._execute_backtest(backtest_task))

                # 等待一段时间再检查
                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"处理回测队列失败: {e}")
                await asyncio.sleep(5)

    async def _execute_backtest(self, backtest_task: Dict[str, Any]) -> None:
        """执行回测"""
        backtest_id = backtest_task["id"]

        try:
            # 标记为运行中
            self._running_backtests[backtest_id] = {
                **backtest_task,
                "status": "running",
                "started_at": datetime.now(),
                "progress": 0
            }

            self.logger.info(f"开始执行回测: {backtest_id}")

            # 模拟回测执行过程
            await self._simulate_backtest_execution(backtest_task)

            # 生成回测结果
            result = await self._generate_backtest_result(backtest_task)

            # 保存结果
            self._backtest_results[backtest_id] = result

            # 从运行中移除
            if backtest_id in self._running_backtests:
                del self._running_backtests[backtest_id]

            self.logger.info(f"回测执行完成: {backtest_id}")

        except Exception as e:
            self.logger.error(f"回测执行失败 {backtest_id}: {e}")

            # 保存失败结果
            self._backtest_results[backtest_id] = {
                **backtest_task,
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now()
            }

            # 从运行中移除
            if backtest_id in self._running_backtests:
                del self._running_backtests[backtest_id]

    async def _simulate_backtest_execution(self, backtest_task: Dict[str, Any]) -> None:
        """模拟回测执行过程"""
        backtest_id = backtest_task["id"]

        # 模拟执行步骤
        steps = [
            ("初始化回测环境", 10),
            ("加载历史数据", 30),
            ("执行策略逻辑", 40),
            ("计算性能指标", 15),
            ("生成报告", 5)
        ]

        total_progress = 0
        for step_name, step_duration in steps:
            self.logger.debug(f"回测 {backtest_id}: {step_name}")

            # 更新进度
            if backtest_id in self._running_backtests:
                self._running_backtests[backtest_id]["progress"] = total_progress

            # 模拟执行时间
            await asyncio.sleep(step_duration / 100)  # 加速模拟

            total_progress += step_duration

        # 完成
        if backtest_id in self._running_backtests:
            self._running_backtests[backtest_id]["progress"] = 100

    async def _generate_backtest_result(self, backtest_task: Dict[str, Any]) -> Dict[str, Any]:
        """生成回测结果 - 使用真实Backtrader引擎"""
        try:
            # 调用真实的回测引擎
            result = run_backtrader_backtest(
                strategy_name=backtest_task["strategy_name"],
                position_type='all_in',
                symbol=backtest_task["symbol"],
                timeframe=backtest_task["timeframe"],
                start_cash=backtest_task["initial_cash"],
                commission=0.001  # 默认手续费率
            )

            perf = result.get('performance', {})

            return {
                **backtest_task,
                "status": "completed",
                "performance": {
                    'initial_cash': result.get('initial_cash', backtest_task["initial_cash"]),
                    'final_cash': result.get('final_cash', backtest_task["initial_cash"]),
                    'total_return': perf.get('net_return', 0) * 100,  # 转换为百分比
                    'sharpe_ratio': perf.get('sharpe_ratio', 0),
                    'max_drawdown': perf.get('max_drawdown', 0),
                    'win_rate': perf.get('win_rate', 0) * 100 if perf.get('win_rate', 0) <= 1 else perf.get('win_rate', 0),
                    'total_trades': perf.get('total_trades', 0),
                    'profit_factor': perf.get('profit_factor', 0),
                },
                "trades": result.get('trades', []),
                "equity_curve": result.get('equity_curve', []),
                "completed_at": datetime.now()
            }

        except Exception as e:
            self.logger.error(f"真实回测执行失败: {e}")
            # 如果真实回测失败，返回错误信息
            return {
                **backtest_task,
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now()
            }

    def _apply_filters(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用过滤条件"""
        filtered_results = results

        # 按策略名称过滤
        if "strategy_name" in filters:
            strategy_name = filters["strategy_name"]
            filtered_results = [r for r in filtered_results if r.get("strategy_name") == strategy_name]

        # 按交易对过滤
        if "symbol" in filters:
            symbol = filters["symbol"]
            filtered_results = [r for r in filtered_results if r.get("symbol") == symbol]

        # 按时间范围过滤
        if "start_date" in filters:
            start_date = filters["start_date"]
            filtered_results = [r for r in filtered_results if r.get("created_at", datetime.min) >= start_date]

        if "end_date" in filters:
            end_date = filters["end_date"]
            filtered_results = [r for r in filtered_results if r.get("created_at", datetime.max) <= end_date]

        return filtered_results

    async def _on_cleanup(self) -> None:
        """清理钩子"""
        self.logger.info("清理回测服务资源")

        # 清理数据
        self._backtest_results.clear()
        self._backtest_queue.clear()
        self._running_backtests.clear()