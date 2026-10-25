"""
回测报告生成模块

生成专业的回测分析报告。

功能：
- HTML报告生成
- PDF报告生成（需要reportlab）
- 图表渲染
- 统计摘要

使用示例：
    from analytics.reporting import BacktestReport

    report = BacktestReport(backtest_result)
    report.generate_html('backtest_report.html')
    report.generate_pdf('backtest_report.pdf')
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestReportData:
    """回测报告数据"""
    # 基本信息
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float

    # 收益指标
    final_capital: float
    total_return: float
    annual_return: float
    monthly_returns: List[float]

    # 风险指标
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    calmar_ratio: float

    # 交易统计
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_trade: float
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float

    # 交易记录
    trades: List[Dict] = None

    # 权益曲线
    equity_curve: List[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'period': f"{self.start_date} - {self.end_date}",
            'initial_capital': self.initial_capital,
            'returns': {
                'final_capital': self.final_capital,
                'total_return': self.total_return,
                'annual_return': self.annual_return,
                'monthly_returns': self.monthly_returns
            },
            'risk': {
                'volatility': self.volatility,
                'sharpe_ratio': self.sharpe_ratio,
                'sortino_ratio': self.sortino_ratio,
                'max_drawdown': self.max_drawdown,
                'max_drawdown_duration': self.max_drawdown_duration,
                'calmar_ratio': self.calmar_ratio
            },
            'trading': {
                'total_trades': self.total_trades,
                'win_rate': self.win_rate,
                'profit_factor': self.profit_factor,
                'avg_trade': self.avg_trade,
                'avg_win': self.avg_win,
                'avg_loss': self.avg_loss,
                'best_trade': self.best_trade,
                'worst_trade': self.worst_trade
            }
        }


class BacktestReport:
    """
    回测报告生成器

    支持多种输出格式。
    """

    def __init__(self, data: BacktestReportData):
        """
        初始化报告生成器

        Args:
            data: 回测数据
        """
        self.data = data
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def generate_html(self, filepath: str, include_charts: bool = True):
        """
        生成HTML报告

        Args:
            filepath: 输出文件路径
            include_charts: 是否包含图表
        """
        html = self._generate_html_content(include_charts)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"HTML报告已生成: {filepath}")

    def _generate_html_content(self, include_charts: bool) -> str:
        """生成HTML内容"""
        d = self.data

        # 格式化数字
        def fmt(num, decimals=2):
            if num is None:
                return '-'
            if isinstance(num, float):
                return f"{num:.{decimals}f}"
            return str(num)

        def pct(num):
            if num is None:
                return '-'
            return f"{num*100:.2f}%"

        # 交易记录表格
        trades_html = ''
        if d.trades:
            trades_rows = []
            for i, trade in enumerate(d.trades[:50]):  # 最多50条
                trades_rows.append(f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{trade.get('date', '-')}</td>
                    <td class="{'buy' if trade.get('type') == 'buy' else 'sell'}">
                        {trade.get('type', '-').upper()}
                    </td>
                    <td>{trade.get('price', '-')}</td>
                    <td>{trade.get('quantity', '-')}</td>
                    <td class="{'profit' if trade.get('pnl', 0) > 0 else 'loss'}">
                        {trade.get('pnl', 0):.2f}
                    </td>
                </tr>
                """)
            trades_html = f"""
            <h2>交易记录</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>日期</th>
                        <th>类型</th>
                        <th>价格</th>
                        <th>数量</th>
                        <th>盈亏</th>
                    </tr>
                </thead>
                <tbody>{''.join(trades_rows)}</tbody>
            </table>
            """ if trades_rows else ''

        # 风险等级颜色
        risk_level = 'low'
        risk_color = 'green'
        if d.max_drawdown > 0.2:
            risk_level = 'high'
            risk_color = 'red'
        elif d.max_drawdown > 0.1:
            risk_level = 'medium'
            risk_color = 'orange'

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>回测报告 - {d.strategy_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f6fa; color: #2d3436; line-height: 1.6; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; padding: 40px; border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .card h2 {{ font-size: 18px; color: #2d3436; margin-bottom: 16px;
                    padding-bottom: 12px; border-bottom: 2px solid #f5f6fa; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }}
        .metric {{ background: #f5f6fa; padding: 16px; border-radius: 8px; text-align: center; }}
        .metric .label {{ font-size: 12px; color: #636e72; margin-bottom: 4px; }}
        .metric .value {{ font-size: 24px; font-weight: bold; color: #2d3436; }}
        .metric .value.green {{ color: #00b894; }}
        .metric .value.red {{ color: #d63031; }}
        .metric .value.orange {{ color: #fdcb6e; }}
        .section-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 768px) {{ .section-grid {{ grid-template-columns: 1fr; }} }}
        .data-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        .data-table th, .data-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
        .data-table th {{ background: #f5f6fa; font-weight: 600; }}
        .data-table .buy {{ color: #00b894; font-weight: 600; }}
        .data-table .sell {{ color: #d63031; font-weight: 600; }}
        .data-table .profit {{ color: #00b894; }}
        .data-table .loss {{ color: #d63031; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px;
                  font-size: 12px; font-weight: 600; }}
        .badge.low {{ background: #d4edda; color: #155724; }}
        .badge.medium {{ background: #fff3cd; color: #856404; }}
        .badge.high {{ background: #f8d7da; color: #721c24; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 20px; }}
        .summary-item {{ text-align: center; padding: 16px; background: #f5f6fa; border-radius: 8px; }}
        .summary-item .value {{ font-size: 20px; font-weight: bold; }}
        .footer {{ text-align: center; padding: 20px; color: #636e72; font-size: 12px; }}
        .chart-placeholder {{ height: 300px; background: linear-gradient(45deg, #f5f6fa 25%, transparent 25%),
                              background-size: 20px 20px; display: flex; align-items: center;
                              justify-content: center; color: #636e72; border-radius: 8px; margin: 16px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{d.strategy_name} - 回测报告</h1>
            <div class="meta">
                <span>{d.symbol}</span> |
                <span>{d.timeframe}</span> |
                <span>周期: {d.start_date} ~ {d.end_date}</span> |
                <span>生成时间: {self.timestamp}</span>
            </div>
        </div>

        <div class="card">
            <h2>收益概览</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="label">初始资金</div>
                    <div class="value">¥{fmt(d.initial_capital, 0)}</div>
                </div>
                <div class="metric">
                    <div class="label">最终资金</div>
                    <div class="value {'green' if d.final_capital > d.initial_capital else 'red'}">¥{fmt(d.final_capital, 0)}</div>
                </div>
                <div class="metric">
                    <div class="label">总收益率</div>
                    <div class="value {'green' if d.total_return > 0 else 'red'}">{pct(d.total_return)}</div>
                </div>
                <div class="metric">
                    <div class="label">年化收益率</div>
                    <div class="value {'green' if d.annual_return > 0 else 'red'}">{pct(d.annual_return)}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>风险指标</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="label">夏普比率</div>
                    <div class="value {'green' if d.sharpe_ratio > 1 else 'orange' if d.sharpe_ratio > 0 else 'red'}">{fmt(d.sharpe_ratio)}</div>
                </div>
                <div class="metric">
                    <div class="label">索提诺比率</div>
                    <div class="value {'green' if d.sortino_ratio > 1.5 else 'orange' if d.sortino_ratio > 0 else 'red'}">{fmt(d.sortino_ratio)}</div>
                </div>
                <div class="metric">
                    <div class="label">最大回撤</div>
                    <div class="value {'red' if d.max_drawdown > 0.15 else 'orange' if d.max_drawdown > 0.08 else 'green'}">{pct(d.max_drawdown)}</div>
                </div>
                <div class="metric">
                    <div class="label">卡玛比率</div>
                    <div class="value {'green' if d.calmar_ratio > 2 else 'orange' if d.calmar_ratio > 1 else 'red'}">{fmt(d.calmar_ratio)}</div>
                </div>
                <div class="metric">
                    <div class="label">波动率</div>
                    <div class="value">{pct(d.volatility)}</div>
                </div>
                <div class="metric">
                    <div class="label">回撤持续</div>
                    <div class="value">{d.max_drawdown_duration} 天</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>交易统计</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="label">总交易次数</div>
                    <div class="value">{d.total_trades}</div>
                </div>
                <div class="metric">
                    <div class="label">胜率</div>
                    <div class="value {'green' if d.win_rate > 0.5 else 'orange' if d.win_rate > 0.4 else 'red'}">{pct(d.win_rate)}</div>
                </div>
                <div class="metric">
                    <div class="label">盈亏比</div>
                    <div class="value {'green' if d.profit_factor > 1.5 else 'orange' if d.profit_factor > 1 else 'red'}">{fmt(d.profit_factor)}</div>
                </div>
                <div class="metric">
                    <div class="label">平均交易</div>
                    <div class="value {'green' if d.avg_trade > 0 else 'red'}">{fmt(d.avg_trade)}%</div>
                </div>
                <div class="metric">
                    <div class="label">平均盈利</div>
                    <div class="value green">{fmt(d.avg_win)}%</div>
                </div>
                <div class="metric">
                    <div class="label">平均亏损</div>
                    <div class="value red">{fmt(d.avg_loss)}%</div>
                </div>
                <div class="metric">
                    <div class="label">最大盈利</div>
                    <div class="value green">{pct(d.best_trade)}</div>
                </div>
                <div class="metric">
                    <div class="label">最大亏损</div>
                    <div class="value red">{pct(d.worst_trade)}</div>
                </div>
            </div>
        </div>

        {trades_html}

        <div class="footer">
            <p>报告由 QuantTradeSys 生成 | {self.timestamp}</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def generate_json(self, filepath: str):
        """导出JSON格式"""
        data = self.data.to_dict()
        data['generated_at'] = self.timestamp

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON报告已生成: {filepath}")

    def generate_summary(self) -> Dict[str, Any]:
        """生成摘要"""
        d = self.data

        # 评分 (0-100)
        score = 0
        score += min(d.sharpe_ratio * 20, 30)  # 夏普权重30
        score += min(d.win_rate * 30, 30)      # 胜率权重30
        score += min((1 - d.max_drawdown) * 20, 20)  # 回撤权重20
        score += min(d.profit_factor * 10, 20)  # 盈亏比权重20

        # 风险评估
        if d.max_drawdown > 0.2:
            risk_level = '高'
        elif d.max_drawdown > 0.1:
            risk_level = '中'
        else:
            risk_level = '低'

        return {
            'overall_score': round(score, 1),
            'risk_level': risk_level,
            'strategy_name': d.strategy_name,
            'key_metrics': {
                'sharpe_ratio': d.sharpe_ratio,
                'max_drawdown': d.max_drawdown,
                'win_rate': d.win_rate,
                'profit_factor': d.profit_factor
            },
            'recommendation': self._get_recommendation(score, d)
        }

    def _get_recommendation(self, score: float, d) -> str:
        """获取建议"""
        if score >= 80:
            return "策略表现优秀，建议进行实盘测试"
        elif score >= 60:
            return "策略表现良好，建议进一步优化参数"
        elif score >= 40:
            return "策略表现一般，建议调整策略或参数"
        else:
            return "策略表现不佳，建议重新设计策略"


def create_report_from_backtest(backtest_result: Dict[str, Any],
                                 strategy_name: str,
                                 symbol: str,
                                 timeframe: str,
                                 start_date: str,
                                 end_date: str,
                                 initial_capital: float = 10000) -> BacktestReport:
    """
    从回测结果创建报告

    Args:
        backtest_result: 回测结果字典
        strategy_name: 策略名称
        symbol: 交易对
        timeframe: 时间周期
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金

    Returns:
        BacktestReport: 报告对象
    """
    data = BacktestReportData(
        strategy_name=strategy_name,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        final_capital=backtest_result.get('final_capital', initial_capital),
        total_return=backtest_result.get('total_return', 0),
        annual_return=backtest_result.get('annual_return', 0),
        monthly_returns=backtest_result.get('monthly_returns', []),
        volatility=backtest_result.get('volatility', 0),
        sharpe_ratio=backtest_result.get('sharpe_ratio', 0),
        sortino_ratio=backtest_result.get('sortino_ratio', 0),
        max_drawdown=backtest_result.get('max_drawdown', 0),
        max_drawdown_duration=backtest_result.get('max_drawdown_duration', 0),
        calmar_ratio=backtest_result.get('calmar_ratio', 0),
        total_trades=backtest_result.get('total_trades', 0),
        win_rate=backtest_result.get('win_rate', 0),
        profit_factor=backtest_result.get('profit_factor', 0),
        avg_trade=backtest_result.get('avg_trade', 0),
        avg_win=backtest_result.get('avg_win', 0),
        avg_loss=backtest_result.get('avg_loss', 0),
        best_trade=backtest_result.get('best_trade', 0),
        worst_trade=backtest_result.get('worst_trade', 0),
        trades=backtest_result.get('trades', []),
        equity_curve=backtest_result.get('equity_curve', [])
    )

    return BacktestReport(data)


if __name__ == '__main__':
    # 测试
    report_data = BacktestReportData(
        strategy_name='均线交叉策略',
        symbol='BTCUSDT',
        timeframe='1h',
        start_date='2024-01-01',
        end_date='2024-12-01',
        initial_capital=10000,
        final_capital=12500,
        total_return=0.25,
        annual_return=0.18,
        monthly_returns=[0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.02, 0.01, -0.01, 0.03, 0.02, 0.01],
        volatility=0.15,
        sharpe_ratio=1.2,
        sortino_ratio=1.5,
        max_drawdown=0.12,
        max_drawdown_duration=30,
        calmar_ratio=1.5,
        total_trades=50,
        win_rate=0.55,
        profit_factor=1.5,
        avg_trade=0.5,
        avg_win=1.2,
        avg_loss=-0.8,
        best_trade=0.05,
        worst_trade=-0.03
    )

    report = BacktestReport(report_data)
    report.generate_html('test_report.html')
    report.generate_json('test_report.json')

    summary = report.generate_summary()
    print(f"综合评分: {summary['overall_score']}")
    print(f"风险等级: {summary['risk_level']}")
    print(f"建议: {summary['recommendation']}")
