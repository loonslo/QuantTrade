"""
策略对比模块

支持多个策略的回测结果对比分析。

功能：
- 多策略对比
- 排名和评分
- 可视化对比
- 对比报告生成

使用示例：
    from analytics.comparison import StrategyComparer

    comparer = StrategyComparer()
    comparer.add_result('均线策略', ma_result)
    comparer.add_result('MACD策略', macd_result)
    report = comparer.compare()
    comparer.print_report()
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """策略回测结果"""
    name: str
    total_return: float          # 总收益率
    annual_return: float         # 年化收益率
    volatility: float            # 波动率
    sharpe_ratio: float          # 夏普比率
    sortino_ratio: float         # 索提诺比率
    max_drawdown: float          # 最大回撤
    max_drawdown_duration: int   # 最大回撤持续天数
    total_trades: int            # 总交易次数
    win_rate: float              # 胜率
    profit_factor: float         # 盈亏比
    avg_trade: float             # 平均每笔交易
    avg_win: float               # 平均盈利
    avg_loss: float              # 平均亏损
    best_trade: float            # 最大盈利
    worst_trade: float           # 最大亏损
    calmar_ratio: float          # 卡玛比率
    tail_ratio: float            # 尾端比率
    win_loss_ratio: float        # 盈亏比
    expectancy: float            # 期望收益
    execution_time: float = 0    # 执行时间
    params: Dict[str, Any] = field(default_factory=dict)  # 策略参数

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'returns': {
                'total_return': self.total_return,
                'annual_return': self.annual_return,
            },
            'risk': {
                'volatility': self.volatility,
                'sharpe_ratio': self.sharpe_ratio,
                'sortino_ratio': self.sortino_ratio,
                'max_drawdown': self.max_drawdown,
                'calmar_ratio': self.calmar_ratio,
            },
            'trading': {
                'total_trades': self.total_trades,
                'win_rate': self.win_rate,
                'profit_factor': self.profit_factor,
                'avg_trade': self.avg_trade,
            },
            'params': self.params
        }


class StrategyComparer:
    """
    策略对比器

    对比多个策略的回测结果，生成排名和报告。
    """

    def __init__(self):
        """初始化策略对比器"""
        self.results: Dict[str, StrategyResult] = {}
        self.metrics_config = self._default_metrics()

    def _default_metrics(self) -> Dict[str, Dict]:
        """默认指标配置"""
        return {
            'sharpe_ratio': {'weight': 0.25, 'higher_better': True, 'name': '夏普比率'},
            'total_return': {'weight': 0.20, 'higher_better': True, 'name': '总收益率'},
            'max_drawdown': {'weight': 0.15, 'higher_better': False, 'name': '最大回撤'},
            'win_rate': {'weight': 0.15, 'higher_better': True, 'name': '胜率'},
            'profit_factor': {'weight': 0.15, 'higher_better': True, 'name': '盈亏比'},
            'calmar_ratio': {'weight': 0.10, 'higher_better': True, 'name': '卡玛比率'},
        }

    def add_result(self, name: str, result: StrategyResult):
        """
        添加策略结果

        Args:
            name: 策略名称
            result: 回测结果
        """
        self.results[name] = result
        logger.info(f"添加策略结果: {name}")

    def add_result_from_dict(self, name: str, data: Dict[str, Any], params: Dict[str, Any] = None):
        """
        从字典添加策略结果

        Args:
            name: 策略名称
            data: 回测数据字典
            params: 策略参数
        """
        result = StrategyResult(
            name=name,
            total_return=data.get('total_return', 0),
            annual_return=data.get('annual_return', 0),
            volatility=data.get('volatility', 0),
            sharpe_ratio=data.get('sharpe_ratio', 0),
            sortino_ratio=data.get('sortino_ratio', 0),
            max_drawdown=data.get('max_drawdown', 0),
            max_drawdown_duration=data.get('max_drawdown_duration', 0),
            total_trades=data.get('total_trades', 0),
            win_rate=data.get('win_rate', 0),
            profit_factor=data.get('profit_factor', 0),
            avg_trade=data.get('avg_trade', 0),
            avg_win=data.get('avg_win', 0),
            avg_loss=data.get('avg_loss', 0),
            best_trade=data.get('best_trade', 0),
            worst_trade=data.get('worst_trade', 0),
            calmar_ratio=data.get('calmar_ratio', 0),
            tail_ratio=data.get('tail_ratio', 0),
            win_loss_ratio=data.get('win_loss_ratio', 0),
            expectancy=data.get('expectancy', 0),
            params=params or {}
        )
        self.add_result(name, result)

    def compare(self) -> Dict[str, Any]:
        """
        执行对比分析

        Returns:
            Dict: 对比结果
        """
        if not self.results:
            return {'error': '没有策略结果可供对比'}

        # 计算排名
        rankings = self._calculate_rankings()

        # 计算综合得分
        scores = self._calculate_composite_scores(rankings)

        # 找出最优策略
        best_strategy = max(scores.items(), key=lambda x: x[1]['composite_score'])

        return {
            'total_strategies': len(self.results),
            'rankings': rankings,
            'scores': scores,
            'best_strategy': {
                'name': best_strategy[0],
                'score': best_strategy[1]['composite_score']
            },
            'metrics_config': self.metrics_config,
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_rankings(self) -> Dict[str, Dict[str, int]]:
        """计算各指标排名"""
        rankings = {}

        for metric, config in self.metrics_config.items():
            values = [(name, getattr(result, metric)) for name, result in self.results.items()]

            # 按指标值排序
            if config['higher_better']:
                sorted_values = sorted(values, key=lambda x: x[1], reverse=True)
            else:
                sorted_values = sorted(values, key=lambda x: x[1])  # 回撤越小越好

            # 分配排名
            for rank, (name, _) in enumerate(sorted_values, 1):
                if name not in rankings:
                    rankings[name] = {}
                rankings[name][metric] = rank

        return rankings

    def _calculate_composite_scores(self, rankings: Dict[str, Dict]) -> Dict[str, Dict]:
        """计算综合得分"""
        scores = {}

        for name in self.results.keys():
            total_score = 0
            total_weight = 0

            for metric, config in self.metrics_config.items():
                weight = config['weight']
                rank = rankings[name].get(metric, len(self.results))
                total_weight += weight

                # 排名转换为分数 (第1名=100分，最后1名=1分)
                rank_score = 100 - (rank - 1) * (99 / max(len(self.results) - 1, 1))
                total_score += rank_score * weight

            composite_score = total_score / total_weight if total_weight > 0 else 0

            scores[name] = {
                'composite_score': composite_score,
                'rank_scores': rankings[name]
            }

        return scores

    def print_report(self, result: Dict[str, Any] = None):
        """打印对比报告"""
        if result is None:
            result = self.compare()

        if 'error' in result:
            print(f"错误: {result['error']}")
            return

        print("\n" + "=" * 80)
        print("策略对比报告")
        print("=" * 80)
        print(f"对比策略数量: {result['total_strategies']}")
        print(f"生成时间: {result['timestamp']}")
        print("-" * 80)

        # 排序输出
        sorted_scores = sorted(
            result['scores'].items(),
            key=lambda x: x[1]['composite_score'],
            reverse=True
        )

        print("\n【综合排名】")
        print(f"{'排名':<4} {'策略名称':<20} {'综合得分':<10} {'夏普比率':<10} {'收益率':<10} {'最大回撤':<10}")
        print("-" * 80)

        for rank, (name, score_info) in enumerate(sorted_scores, 1):
            result_item = self.results[name]
            print(f"{rank:<4} {name:<20} {score_info['composite_score']:.2f}    "
                  f"{result_item.sharpe_ratio:.3f}    "
                  f"{result_item.total_return*100:.2f}%   "
                  f"{result_item.max_drawdown*100:.2f}%")

        print("\n【最优策略】")
        best = result['best_strategy']
        print(f"  策略名称: {best['name']}")
        print(f"  综合得分: {best['score']:.2f}")

        best_result = self.results[best['name']]
        print(f"  年化收益率: {best_result.annual_return*100:.2f}%")
        print(f"  夏普比率: {best_result.sharpe_ratio:.3f}")
        print(f"  最大回撤: {best_result.max_drawdown*100:.2f}%")
        print(f"  胜率: {best_result.win_rate*100:.2f}%")

        print("\n【各指标排名】")
        print(f"{'策略名称':<20}", end='')
        for metric in self.metrics_config:
            short_names = {
                'sharpe_ratio': '夏普',
                'total_return': '收益',
                'max_drawdown': '回撤',
                'win_rate': '胜率',
                'profit_factor': '盈亏',
                'calmar_ratio': '卡玛'
            }
            print(f"{short_names.get(metric, metric):<6}", end='')
        print()
        print("-" * 60)

        for name, score_info in sorted_scores:
            print(f"{name:<20}", end='')
            for metric in self.metrics_config:
                rank = score_info['rank_scores'].get(metric, '-')
                print(f"{rank:<6}", end='')
            print()

        print("\n" + "=" * 80)

    def get_best_params(self) -> Dict[str, Any]:
        """获取最优策略参数"""
        result = self.compare()
        best_name = result['best_strategy']['name']
        return self.results[best_name].params

    def export_report(self, filepath: str, format: str = 'json'):
        """
        导出报告

        Args:
            filepath: 文件路径
            format: 格式 ('json', 'csv')
        """
        result = self.compare()

        if format == 'json':
            self._export_json(filepath, result)
        elif format == 'csv':
            self._export_csv(filepath, result)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def _export_json(self, filepath: str, result: Dict[str, Any]):
        """导出JSON格式"""
        export_data = {
            'report': result,
            'strategies': {
                name: r.to_dict()
                for name, r in self.results.items()
            }
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已导出: {filepath}")

    def _export_csv(self, filepath: str, result: Dict[str, Any]):
        """导出CSV格式"""
        import csv

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            # 表头
            headers = ['策略名称', '综合得分', '总收益率', '年化收益率',
                       '波动率', '夏普比率', '最大回撤', '交易次数', '胜率', '盈亏比']
            writer.writerow(headers)

            # 数据行
            sorted_scores = sorted(
                result['scores'].items(),
                key=lambda x: x[1]['composite_score'],
                reverse=True
            )

            for name, _ in sorted_scores:
                r = self.results[name]
                writer.writerow([
                    name,
                    _['composite_score'],
                    f"{r.total_return*100:.2f}%",
                    f"{r.annual_return*100:.2f}%",
                    f"{r.volatility*100:.2f}%",
                    f"{r.sharpe_ratio:.3f}",
                    f"{r.max_drawdown*100:.2f}%",
                    r.total_trades,
                    f"{r.win_rate*100:.2f}%",
                    f"{r.profit_factor:.2f}"
                ])

        logger.info(f"报告已导出: {filepath}")


def create_comparison_report(results: List[Dict[str, Any]],
                              strategy_names: List[str] = None) -> Dict[str, Any]:
    """
    快速创建对比报告

    Args:
        results: 回测结果列表
        strategy_names: 策略名称列表

    Returns:
        Dict: 对比结果
    """
    comparer = StrategyComparer()

    names = strategy_names or [f"策略{i+1}" for i in range(len(results))]

    for name, result in zip(names, results):
        comparer.add_result_from_dict(name, result)

    return comparer.compare()


if __name__ == '__main__':
    # 测试
    comparer = StrategyComparer()

    # 添加模拟数据
    comparer.add_result_from_dict('均线策略', {
        'total_return': 0.25,
        'annual_return': 0.18,
        'volatility': 0.15,
        'sharpe_ratio': 1.2,
        'sortino_ratio': 1.5,
        'max_drawdown': 0.12,
        'max_drawdown_duration': 30,
        'total_trades': 50,
        'win_rate': 0.55,
        'profit_factor': 1.5,
        'calmar_ratio': 1.5
    }, {'short_window': 5, 'long_window': 20})

    comparer.add_result_from_dict('MACD策略', {
        'total_return': 0.30,
        'annual_return': 0.22,
        'volatility': 0.18,
        'sharpe_ratio': 1.3,
        'sortino_ratio': 1.6,
        'max_drawdown': 0.15,
        'max_drawdown_duration': 40,
        'total_trades': 60,
        'win_rate': 0.52,
        'profit_factor': 1.4,
        'calmar_ratio': 1.47
    }, {'fast': 12, 'slow': 26})

    comparer.add_result_from_dict('RSI策略', {
        'total_return': 0.18,
        'annual_return': 0.14,
        'volatility': 0.12,
        'sharpe_ratio': 1.1,
        'sortino_ratio': 1.3,
        'max_drawdown': 0.08,
        'max_drawdown_duration': 20,
        'total_trades': 40,
        'win_rate': 0.60,
        'profit_factor': 1.8,
        'calmar_ratio': 1.75
    }, {'period': 14, 'overbought': 70, 'oversold': 30})

    # 生成报告
    result = comparer.compare()
    comparer.print_report()

    # 导出
    comparer.export_report('strategy_comparison.json', format='json')
    comparer.export_report('strategy_comparison.csv', format='csv')
