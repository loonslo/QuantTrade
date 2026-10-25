"""
策略参数优化模块

提供多种参数优化算法：
1. 网格搜索 (Grid Search) - 穷举所有参数组合
2. 遗传算法 (Genetic Algorithm) - 智能搜索最优参数
3. 随机搜索 (Random Search) - 随机采样参数组合

使用示例：
    from analytics.optimization.optimizer import GridSearchOptimizer, GeneticAlgorithmOptimizer

    # 网格搜索
    optimizer = GridSearchOptimizer(backtest_func, param_grid)
    results = optimizer.optimize(data, metric='sharpe_ratio')

    # 遗传算法
    optimizer = GeneticAlgorithmOptimizer(backtest_func, param_bounds)
    best_params = optimizer.optimize(data, generations=50)
"""

from typing import Dict, Any, List, Callable, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """优化结果"""
    best_params: Dict[str, Any]
    best_score: float
    all_results: List[Dict[str, Any]]
    total_evaluations: int
    elapsed_time: float
    metric_name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'total_evaluations': self.total_evaluations,
            'elapsed_time': self.elapsed_time,
            'metric_name': self.metric_name,
            'top_results': sorted(
                self.all_results,
                key=lambda x: x['score'],
                reverse=True
            )[:5]
        }


class BaseOptimizer(ABC):
    """优化器基类"""

    def __init__(self, backtest_func: Callable,
                 metric: str = 'sharpe_ratio',
                 maximize: bool = True,
                 n_jobs: int = 1):
        """
        初始化优化器

        Args:
            backtest_func: 回测函数，接受参数返回性能指标
            metric: 优化指标 (sharpe_ratio, total_return, max_drawdown)
            maximize: 是否最大化指标
            n_jobs: 并行任务数
        """
        self.backtest_func = backtest_func
        self.metric = metric
        self.maximize = maximize
        self.n_jobs = n_jobs

    @abstractmethod
    def generate_params(self) -> List[Dict[str, Any]]:
        """生成参数组合"""
        pass

    def _evaluate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个参数组合"""
        try:
            score = self.backtest_func(**params)
            return {
                'params': params,
                'score': score,
                'success': True
            }
        except Exception as e:
            logger.error(f"回测失败: {e}, 参数: {params}")
            return {
                'params': params,
                'score': float('-inf') if self.maximize else float('inf'),
                'success': False,
                'error': str(e)
            }

    def optimize(self, **kwargs) -> OptimizationResult:
        """
        执行优化

        Returns:
            OptimizationResult: 优化结果
        """
        import time
        start_time = time.time()

        # 生成参数
        param_list = self.generate_params()
        logger.info(f"开始优化，共 {len(param_list)} 个参数组合")

        # 评估所有组合
        all_results = []
        if self.n_jobs > 1:
            with ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = [executor.submit(self._evaluate, params) for params in param_list]
                for future in as_completed(futures):
                    all_results.append(future.result())
        else:
            for params in param_list:
                result = self._evaluate(params)
                all_results.append(result)

        # 过滤成功的结果
        successful_results = [r for r in all_results if r['success']]
        if not successful_results:
            logger.warning("所有回测都失败了")

        # 找到最优参数
        if self.maximize:
            best_result = max(all_results, key=lambda x: x['score'])
        else:
            best_result = min(all_results, key=lambda x: x['score'])

        elapsed_time = time.time() - start_time

        return OptimizationResult(
            best_params=best_result['params'],
            best_score=best_result['score'],
            all_results=all_results,
            total_evaluations=len(param_list),
            elapsed_time=elapsed_time,
            metric_name=self.metric
        )


class GridSearchOptimizer(BaseOptimizer):
    """
    网格搜索优化器

    穷举所有参数组合，适合参数空间较小的情况。
    """

    def __init__(self, backtest_func: Callable,
                 param_grid: Dict[str, List[Any]],
                 metric: str = 'sharpe_ratio',
                 maximize: bool = True,
                 n_jobs: int = 1):
        """
        初始化网格搜索优化器

        Args:
            backtest_func: 回测函数
            param_grid: 参数网格，示例:
                {
                    'short_window': [5, 10, 20],
                    'long_window': [20, 50, 100],
                    'threshold': [0.01, 0.02, 0.03]
                }
            metric: 优化指标
            maximize: 是否最大化
            n_jobs: 并行数
        """
        super().__init__(backtest_func, metric, maximize, n_jobs)
        self.param_grid = param_grid

    def generate_params(self) -> List[Dict[str, Any]]:
        """生成所有参数组合"""
        from itertools import product

        # 生成所有组合
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())

        param_list = []
        for combination in product(*values):
            param_dict = {}
            for key, value in zip(keys, combination):
                param_dict[key] = value
            param_list.append(param_dict)

        logger.info(f"生成 {len(param_list)} 个参数组合")
        return param_list


class RandomSearchOptimizer(BaseOptimizer):
    """
    随机搜索优化器

    随机采样参数组合，适合参数空间大、计算资源有限的情况。
    研究表明随机搜索通常比网格搜索更高效。
    """

    def __init__(self, backtest_func: Callable,
                 param_distributions: Dict[str, Tuple[Any, Any, int]],
                 n_iterations: int = 100,
                 metric: str = 'sharpe_ratio',
                 maximize: bool = True,
                 n_jobs: int = 1):
        """
        初始化随机搜索优化器

        Args:
            backtest_func: 回测函数
            param_distributions: 参数分布，示例:
                {
                    'short_window': (5, 50, int),  # min, max, type
                    'long_window': (20, 200, int),
                    'threshold': (0.001, 0.1, float)
                }
            n_iterations: 采样次数
            metric: 优化指标
            maximize: 是否最大化
            n_jobs: 并行数
        """
        super().__init__(backtest_func, metric, maximize, n_jobs)
        self.param_distributions = param_distributions
        self.n_iterations = n_iterations

    def _sample_value(self, dist: Tuple) -> Any:
        """采样单个值"""
        min_val, max_val, type_ = dist
        if type_ == int:
            return random.randint(int(min_val), int(max_val))
        elif type_ == float:
            return random.uniform(min_val, max_val)
        else:
            return type_(random.uniform(min_val, max_val))

    def generate_params(self) -> List[Dict[str, Any]]:
        """生成随机参数组合"""
        param_list = []
        for _ in range(self.n_iterations):
            param_dict = {}
            for key, dist in self.param_distributions.items():
                param_dict[key] = self._sample_value(dist)
            param_list.append(param_dict)
        return param_list


class GeneticAlgorithmOptimizer(BaseOptimizer):
    """
    遗传算法优化器

    模拟生物进化过程，通过选择、交叉、变异来搜索最优参数。
    适合复杂参数空间。
    """

    def __init__(self, backtest_func: Callable,
                 param_bounds: Dict[str, Tuple[Any, Any]],
                 param_types: Dict[str, type] = None,
                 population_size: int = 50,
                 n_generations: int = 30,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 elitism: int = 2,
                 metric: str = 'sharpe_ratio',
                 maximize: bool = True,
                 n_jobs: int = 1):
        """
        初始化遗传算法优化器

        Args:
            backtest_func: 回测函数
            param_bounds: 参数边界，示例:
                {
                    'short_window': (5, 50),
                    'long_window': (20, 200),
                    'threshold': (0.001, 0.1)
                }
            param_types: 参数类型
            population_size: 种群大小
            n_generations: 迭代代数
            mutation_rate: 变异率
            crossover_rate: 交叉率
            elitism: 精英保留数
            metric: 优化指标
            maximize: 是否最大化
            n_jobs: 并行数
        """
        super().__init__(backtest_func, metric, maximize, n_jobs)
        self.param_bounds = param_bounds
        self.param_types = param_types or {k: float for k in param_bounds}
        self.population_size = population_size
        self.n_generations = n_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism = elitism

    def _random_params(self) -> Dict[str, Any]:
        """生成随机参数"""
        params = {}
        for key, (min_val, max_val) in self.param_bounds.items():
            param_type = self.param_types.get(key, float)
            if param_type == int:
                params[key] = random.randint(int(min_val), int(max_val))
            else:
                params[key] = random.uniform(min_val, max_val)
        return params

    def _crossover(self, parent1: Dict[str, Any],
                   parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """交叉操作"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        child1, child2 = {}, {}
        for key in parent1.keys():
            if random.random() < 0.5:
                child1[key] = parent1[key]
                child2[key] = parent2[key]
            else:
                child1[key] = parent2[key]
                child2[key] = parent1[key]
        return child1, child2

    def _mutate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """变异操作"""
        for key, (min_val, max_val) in self.param_bounds.items():
            if random.random() < self.mutation_rate:
                param_type = self.param_types.get(key, float)
                if param_type == int:
                    # 整数扰动
                    delta = random.randint(-5, 5)
                    params[key] = max(min_val, min(max_val, params[key] + delta))
                else:
                    # 浮点数扰动
                    delta = random.uniform(-0.05, 0.05) * (max_val - min_val)
                    params[key] = max(min_val, min(max_val, params[key] + delta))
        return params

    def _evaluate_population(self, population: List[Dict[str, Any]]) -> List[Tuple]:
        """评估种群"""
        if self.n_jobs > 1:
            with ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = [executor.submit(self._evaluate, ind) for ind in population]
                results = [f.result() for f in as_completed(futures)]
        else:
            results = [self._evaluate(ind) for ind in population]

        # 返回 (个体, 适应度) 元组
        scored = [(ind, r['score']) for ind, r in zip(population, results)]
        return scored

    def optimize(self, **kwargs) -> OptimizationResult:
        """
        执行遗传算法优化

        Returns:
            OptimizationResult: 优化结果
        """
        import time
        start_time = time.time()

        # 初始化种群
        population = [self._random_params() for _ in range(self.population_size)]
        all_results = []

        logger.info(f"开始遗传算法优化，种群大小: {self.population_size}, 代数: {self.n_generations}")

        for generation in range(self.n_generations):
            # 评估种群
            scored_pop = self._evaluate_population(population)

            # 记录最优结果
            best_ind = max(scored_pop, key=lambda x: x[1])
            all_results.append({
                'generation': generation,
                'best_score': best_ind[1],
                'best_params': best_ind[0].copy()
            })
            logger.info(f"第 {generation+1} 代，最优分数: {best_ind[1]:.4f}")

            # 选择 - 轮盘赌
            total_fitness = sum(s for _, s in scored_pop)
            if total_fitness == 0:
                selected = [ind for ind, _ in random.sample(scored_pop, k=self.population_size)]
            else:
                selected = []
                for _ in range(self.population_size):
                    r = random.uniform(0, total_fitness)
                    cumsum = 0
                    for ind, score in scored_pop:
                        cumsum += score
                        if cumsum >= r:
                            selected.append(ind.copy())
                            break
                    if not selected:
                        selected.append(scored_pop[0][0].copy())

            # 生成新一代
            new_population = []

            # 精英保留
            sorted_pop = sorted(scored_pop, key=lambda x: x[1], reverse=self.maximize)
            for i in range(self.elitism):
                new_population.append(sorted_pop[i][0].copy())

            # 交叉和变异
            while len(new_population) < self.population_size:
                parent1, parent2 = random.sample(selected, 2)
                child1, child2 = self._crossover(parent1, parent2)
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                new_population.extend([child1, child2])

            population = new_population[:self.population_size]

        # 最终评估
        final_scored = self._evaluate_population(population)
        best_ind, best_score = max(final_scored, key=lambda x: x[1]) if self.maximize else \
            min(final_scored, key=lambda x: x[1])

        elapsed_time = time.time() - start_time

        return OptimizationResult(
            best_params=best_ind,
            best_score=best_score,
            all_results=all_results,
            total_evaluations=self.population_size * self.n_generations,
            elapsed_time=elapsed_time,
            metric_name=self.metric
        )


class BayesianOptimizer:
    """
    贝叶斯优化器

    使用高斯过程模型预测参数性能，适合计算昂贵的评估。
    注意：需要安装 scikit-learn
    """

    def __init__(self, backtest_func: Callable,
                 param_bounds: Dict[str, Tuple[float, float]],
                 n_iterations: int = 30,
                 metric: str = 'sharpe_ratio',
                 maximize: bool = True):
        """
        初始化贝叶斯优化器

        Args:
            backtest_func: 回测函数
            param_bounds: 参数边界
            n_iterations: 迭代次数
            metric: 优化指标
            maximize: 是否最大化
        """
        try:
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import Matern
        except ImportError:
            logger.error("请安装 scikit-learn: pip install scikit-learn")
            raise

        self.backtest_func = backtest_func
        self.param_bounds = param_bounds
        self.n_iterations = n_iterations
        self.metric = metric
        self.maximize = maximize

        # 参数归一化
        self.param_names = list(param_bounds.keys())
        self.bounds = np.array([param_bounds[k] for k in self.param_names])

        # 初始化高斯过程
        kernel = Matern(nu=2.5)
        self.gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-6)

        self.X_observed = []
        self.y_observed = []

    def _normalize_params(self, params: Dict[str, float]) -> np.ndarray:
        """归一化参数到 [0, 1]"""
        values = [params[k] for k in self.param_names]
        normalized = []
        for v, (low, high) in zip(values, self.bounds):
            normalized.append((v - low) / (high - low))
        return np.array(normalized)

    def _denormalize_params(self, x: np.ndarray) -> Dict[str, float]:
        """反归一化"""
        denormalized = {}
        for i, key in enumerate(self.param_names):
            low, high = self.bounds[i]
            denormalized[key] = low + x[i] * (high - low)
        return denormalized

    def _acquisition_function(self, x: np.ndarray) -> np.ndarray:
        """获取函数 (Expected Improvement)"""
        if not self.X_observed:
            return np.random.rand(len(x))

        mu, sigma = self.gp.predict(x, return_std=True)

        if self.maximize:
            best_y = max(self.y_observed)
        else:
            best_y = min(self.y_observed)

        # Expected Improvement
        with np.errstate(divide='ignore'):
            Z = (mu - best_y) / sigma
            ei = (mu - best_y) * norm.cdf(Z) + sigma * norm.pdf(Z)
            ei[sigma == 0.0] = 0.0

        return -ei  # 最小化获取函数

    def optimize(self, **kwargs) -> OptimizationResult:
        """
        执行贝叶斯优化

        Returns:
            OptimizationResult: 优化结果
        """
        import time
        from scipy.stats import norm

        start_time = time.time()

        logger.info(f"开始贝叶斯优化，迭代次数: {self.n_iterations}")

        # 初始随机采样
        n_init = min(5, self.n_iterations)
        for _ in range(n_init):
            x = np.random.rand(len(self.param_names))
            params = self._denormalize_params(x)
            score = self._evaluate(params)['score']
            self.X_observed.append(x)
            self.y_observed.append(score)

        # 迭代优化
        for i in range(self.n_iterations - n_init):
            # 拟合高斯过程
            self.gp.fit(np.array(self.X_observed), np.array(self.y_observed))

            # 采样下一个点
            x_candidates = np.random.rand(1000, len(self.param_names))
            acq_values = self._acquisition_function(x_candidates)
            best_idx = np.argmin(acq_values)
            x_next = x_candidates[best_idx]

            # 评估
            params = self._denormalize_params(x_next)
            score = self._evaluate(params)['score']

            self.X_observed.append(x_next)
            self.y_observed.append(score)

            logger.info(f"迭代 {i+1}/{self.n_iterations - n_init}, 分数: {score:.4f}")

        # 找到最优
        if self.maximize:
            best_idx = np.argmax(self.y_observed)
        else:
            best_idx = np.argmin(self.y_observed)

        best_params = self._denormalize_params(self.X_observed[best_idx])
        best_score = self.y_observed[best_idx]

        elapsed_time = time.time() - start_time

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=[{
                'params': self._denormalize_params(x),
                'score': y
            } for x, y in zip(self.X_observed, self.y_observed)],
            total_evaluations=len(self.X_observed),
            elapsed_time=elapsed_time,
            metric_name=self.metric
        )


def objective_function_example(strategy: str, **params) -> float:
    """
    回测目标函数示例

    Args:
        strategy: 策略名称
        **params: 策略参数

    Returns:
        float: 优化指标分数
    """
    # 这里应该调用实际的回测引擎
    # 示例返回随机分数
    import random
    return random.uniform(0.5, 2.0)
