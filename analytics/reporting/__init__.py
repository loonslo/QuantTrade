"""
回测报告生成模块

生成专业的回测分析报告。

功能：
- HTML报告生成
- JSON数据导出
- 统计摘要
- 风险评估

使用示例：
    from analytics.reporting import BacktestReport, create_report_from_backtest

    # 方式1：直接创建报告
    report = BacktestReport(report_data)
    report.generate_html('report.html')
    report.generate_json('report.json')

    # 方式2：从回测结果创建
    report = create_report_from_backtest(
        backtest_result, '均线策略', 'BTCUSDT', '1h',
        '2024-01-01', '2024-12-01', 10000
    )
    report.generate_html('report.html')
"""

from .report_generator import (
    BacktestReport,
    BacktestReportData,
    create_report_from_backtest
)

__all__ = [
    'BacktestReport',
    'BacktestReportData',
    'create_report_from_backtest',
]
