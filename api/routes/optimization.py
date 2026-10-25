"""
优化和对比API接口

提供回测参数优化和策略对比的API。

Endpoints:
- POST /api/optimize/grid-search     网格搜索优化
- POST /api/optimize/genetic         遗传算法优化
- POST /api/optimize/random          随机搜索优化
- POST /api/backtest/compare         策略对比
- POST /api/backtest/report          生成报告
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 请求模型 ============

class GridSearchRequest(BaseModel):
    """网格搜索请求"""
    strategy: str = Field(..., description="策略名称")
    symbol: str = Field(..., description="交易对")
    timeframe: str = Field(default="1h", description="时间周期")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    initial_capital: float = Field(default=10000, description="初始资金")
    param_grid: Dict[str, List[Any]] = Field(..., description="参数网格")
    metric: str = Field(default="sharpe_ratio", description="优化指标")
    commission: float = Field(default=0.001, description="手续费率")


class GeneticOptimizeRequest(BaseModel):
    """遗传算法优化请求"""
    strategy: str = Field(..., description="策略名称")
    symbol: str = Field(..., description="交易对")
    timeframe: str = Field(default="1h", description="时间周期")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    initial_capital: float = Field(default=10000, description="初始资金")
    param_bounds: Dict[str, List[float]] = Field(..., description="参数边界")
    population_size: int = Field(default=50, description="种群大小")
    generations: int = Field(default=30, description="迭代代数")
    mutation_rate: float = Field(default=0.1, description="变异率")
    metric: str = Field(default="sharpe_ratio", description="优化指标")
    commission: float = Field(default=0.001, description="手续费率")


class CompareRequest(BaseModel):
    """策略对比请求"""
    symbol: str = Field(..., description="交易对")
    timeframe: str = Field(default="1h", description="时间周期")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    initial_capital: float = Field(default=10000, description="初始资金")
    strategies: List[Dict[str, Any]] = Field(..., description="策略列表")
    commission: float = Field(default=0.001, description="手续费率")


class ReportRequest(BaseModel):
    """报告生成请求"""
    backtest_result: Dict[str, Any] = Field(..., description="回测结果")
    strategy_name: str = Field(..., description="策略名称")
    symbol: str = Field(..., description="交易对")
    timeframe: str = Field(..., description="时间周期")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    initial_capital: float = Field(default=10000, description="初始资金")
    format: str = Field(default="html", description="报告格式")


# ============ API 端点 ============

@router.post("/optimize/grid-search")
async def grid_search_optimize(request: GridSearchRequest):
    """
    网格搜索优化

    穷举所有参数组合，找到最优参数。
    适合参数空间较小的情况。
    """
    try:
        from analytics.optimization import GridSearchOptimizer
        from core.backtrader_runner import run_backtrader_backtest

        # 获取数据时间范围
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d')

        # 定义真实的回测函数
        def run_backtest(**params):
            try:
                result = run_backtrader_backtest(
                    strategy_name=request.strategy,
                    position_type='all_in',
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    start_cash=request.initial_capital,
                    commission=request.commission
                )
                # 返回优化指标分数
                metric_value = result.get('performance', {}).get(request.metric, 0)
                return metric_value
            except Exception as e:
                logger.warning(f"回测执行失败: {e}")
                return 0.0

        optimizer = GridSearchOptimizer(
            backtest_func=run_backtest,
            param_grid=request.param_grid,
            metric=request.metric
        )

        result = optimizer.optimize()

        return {
            "success": True,
            "message": "网格搜索完成",
            "data": {
                "best_params": result.best_params,
                "best_score": result.best_score,
                "total_evaluations": result.total_evaluations,
                "elapsed_time": result.elapsed_time,
                "top_5_results": sorted(
                    result.all_results,
                    key=lambda x: x.get('score', 0),
                    reverse=True
                )[:5]
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化失败: {str(e)}")


@router.post("/optimize/genetic")
async def genetic_optimize(request: GeneticOptimizeRequest):
    """
    遗传算法优化

    使用遗传算法智能搜索最优参数。
    适合复杂连续参数空间。
    """
    try:
        from analytics.optimization import GeneticAlgorithmOptimizer
        from core.backtrader_runner import run_backtrader_backtest

        # 定义真实的回测函数
        def run_backtest(**params):
            try:
                result = run_backtrader_backtest(
                    strategy_name=request.strategy,
                    position_type='all_in',
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    start_cash=request.initial_capital,
                    commission=request.commission
                )
                return result.get('performance', {}).get(request.metric, 0)
            except Exception as e:
                logger.warning(f"回测执行失败: {e}")
                return 0.0

        param_types = {}
        for key, bounds in request.param_bounds.items():
            if all(isinstance(b, int) for b in bounds):
                param_types[key] = int
            else:
                param_types[key] = float

        optimizer = GeneticAlgorithmOptimizer(
            backtest_func=run_backtest,
            param_bounds={k: (v[0], v[1]) for k, v in request.param_bounds.items()},
            param_types=param_types,
            population_size=request.population_size,
            n_generations=request.generations,
            mutation_rate=request.mutation_rate,
            metric=request.metric
        )

        result = optimizer.optimize()

        return {
            "success": True,
            "message": "遗传算法优化完成",
            "data": {
                "best_params": result.best_params,
                "best_score": result.best_score,
                "total_evaluations": result.total_evaluations,
                "elapsed_time": result.elapsed_time,
                "generations": request.generations,
                "population_size": request.population_size
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化失败: {str(e)}")


@router.post("/optimize/random")
async def random_search_optimize(request: GeneticOptimizeRequest):
    """
    随机搜索优化

    随机采样参数组合。
    适合参数空间大、计算资源有限的情况。
    """
    try:
        from analytics.optimization import RandomSearchOptimizer
        from core.backtrader_runner import run_backtrader_backtest

        # 定义真实的回测函数
        def run_backtest(**params):
            try:
                result = run_backtrader_backtest(
                    strategy_name=request.strategy,
                    position_type='all_in',
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    start_cash=request.initial_capital,
                    commission=request.commission
                )
                return result.get('performance', {}).get(request.metric, 0)
            except Exception as e:
                logger.warning(f"回测执行失败: {e}")
                return 0.0

        param_distributions = {}
        for key, bounds in request.param_bounds.items():
            param_type = int if all(isinstance(b, int) for b in bounds) else float
            param_distributions[key] = (bounds[0], bounds[1], param_type)

        optimizer = RandomSearchOptimizer(
            backtest_func=run_backtest,
            param_distributions=param_distributions,
            n_iterations=request.population_size,
            metric=request.metric
        )

        result = optimizer.optimize()

        return {
            "success": True,
            "message": "随机搜索优化完成",
            "data": {
                "best_params": result.best_params,
                "best_score": result.best_score,
                "total_evaluations": result.total_evaluations,
                "elapsed_time": result.elapsed_time,
                "iterations": request.population_size
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化失败: {str(e)}")


@router.post("/backtest/compare")
async def compare_strategies(request: CompareRequest):
    """
    策略对比

    对比多个策略的回测结果。
    """
    try:
        from analytics.comparison import StrategyComparer
        from core.backtrader_runner import run_backtrader_backtest

        comparer = StrategyComparer()

        for strategy in request.strategies:
            strategy_name = strategy.get('name', 'unknown')
            try:
                result = run_backtrader_backtest(
                    strategy_name=strategy_name,
                    position_type='all_in',
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    start_cash=request.initial_capital,
                    commission=request.commission
                )
                perf = result.get('performance', {})
                comparer.add_result_from_dict(
                    name=strategy_name,
                    data={
                        'total_return': perf.get('net_return', 0),
                        'sharpe_ratio': perf.get('sharpe_ratio', 0),
                        'max_drawdown': perf.get('max_drawdown', 0),
                        'win_rate': perf.get('win_rate', 0),
                        'total_trades': perf.get('total_trades', 0),
                        'profit_factor': perf.get('profit_factor', 0),
                    },
                    params=strategy.get('params', {})
                )
            except Exception as e:
                logger.warning(f"策略 {strategy_name} 回测失败: {e}")
                comparer.add_result_from_dict(
                    name=strategy_name,
                    data={
                        'total_return': 0,
                        'sharpe_ratio': 0,
                        'max_drawdown': 0,
                        'win_rate': 0,
                        'total_trades': 0,
                        'profit_factor': 0,
                    },
                    params=strategy.get('params', {})
                )

        result = comparer.compare()
        comparer.print_report()

        return {
            "success": True,
            "message": "策略对比完成",
            "data": {
                "total_strategies": result['total_strategies'],
                "best_strategy": result['best_strategy'],
                "rankings": result['rankings'],
                "scores": result['scores'],
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比失败: {str(e)}")


@router.post("/backtest/report")
async def generate_report(request: ReportRequest):
    """
    生成回测报告

    生成HTML或JSON格式的回测报告。
    """
    try:
        from analytics.reporting import create_report_from_backtest

        report = create_report_from_backtest(
            backtest_result=request.backtest_result,
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital
        )

        if request.format == 'html':
            filename = f"report_{request.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report.generate_html(filename)
            return {
                "success": True,
                "message": f"HTML报告已生成: {filename}",
                "data": {"file": filename},
                "summary": report.generate_summary()
            }
        elif request.format == 'json':
            filename = f"report_{request.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report.generate_json(filename)
            return {
                "success": True,
                "message": f"JSON报告已生成: {filename}",
                "data": {"file": filename},
                "summary": report.generate_summary()
            }
        else:
            raise ValueError(f"不支持的格式: {request.format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.get("/optimize/status")
async def get_optimize_status():
    """获取优化模块状态"""
    return {
        "status": "ready",
        "available_optimizers": ["grid-search", "genetic", "random"],
        "available_metrics": [
            "sharpe_ratio",
            "total_return",
            "max_drawdown",
            "sortino_ratio",
            "calmar_ratio"
        ],
        "timestamp": datetime.now().isoformat()
    }

