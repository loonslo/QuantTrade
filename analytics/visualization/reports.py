"""
报告生成器
生成各种分析报告
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json
import html

from utils.core.logger_manager import get_logger
from utils.validation.exceptions import AnalysisException
from ..performance.unified_metrics import PerformanceMetrics
from ..performance.risk_metrics import RiskMetrics


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.logger = get_logger('report_generator')
        
    def generate_performance_report(self, 
                                   metrics: PerformanceMetrics,
                                   title: str = "策略性能报告",
                                   output_path: Optional[str] = None) -> str:
        """
        生成性能报告
        
        Args:
            metrics: 性能指标
            title: 报告标题
            output_path: 输出路径
            
        Returns:
            str: HTML报告内容
        """
        try:
            self.logger.info("开始生成性能报告")
            
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .positive {{
            color: #27ae60;
        }}
        .negative {{
            color: #e74c3c;
        }}
        .neutral {{
            color: #f39c12;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value {'positive' if metrics.total_return > 0 else 'negative'}">
                    {metrics.total_return:.2f}%
                </div>
                <div class="metric-label">总收益率</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {'positive' if metrics.sharpe_ratio > 1 else 'negative' if metrics.sharpe_ratio < 0 else 'neutral'}">
                    {metrics.sharpe_ratio:.3f}
                </div>
                <div class="metric-label">夏普比率</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value negative">
                    {metrics.max_drawdown:.2f}%
                </div>
                <div class="metric-label">最大回撤</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {'positive' if metrics.win_rate > 50 else 'negative'}">
                    {metrics.win_rate:.1f}%
                </div>
                <div class="metric-label">胜率</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value neutral">
                    {metrics.total_trades}
                </div>
                <div class="metric-label">总交易次数</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {'positive' if metrics.profit_factor > 1 else 'negative'}">
                    {metrics.profit_factor:.2f}
                </div>
                <div class="metric-label">盈利因子</div>
            </div>
        </div>
        
        <h2>详细指标</h2>
        <table>
            <tr>
                <th>指标名称</th>
                <th>数值</th>
                <th>说明</th>
            </tr>
            <tr>
                <td>年化收益率</td>
                <td>{metrics.annual_return:.2f}%</td>
                <td>按年计算的收益率</td>
            </tr>
            <tr>
                <td>波动率</td>
                <td>{metrics.volatility:.2f}%</td>
                <td>收益率的年化标准差</td>
            </tr>
            <tr>
                <td>信息比率</td>
                <td>{metrics.information_ratio:.3f}</td>
                <td>超额收益与跟踪误差的比值</td>
            </tr>
            <tr>
                <td>卡尔玛比率</td>
                <td>{metrics.calmar_ratio:.3f}</td>
                <td>年化收益率与最大回撤的比值</td>
            </tr>
            <tr>
                <td>索提诺比率</td>
                <td>{metrics.sortino_ratio:.3f}</td>
                <td>下行风险调整后的收益</td>
            </tr>
            <tr>
                <td>平均盈利</td>
                <td>{metrics.avg_win:.2f}</td>
                <td>平均盈利交易的收益</td>
            </tr>
            <tr>
                <td>平均亏损</td>
                <td>{metrics.avg_loss:.2f}</td>
                <td>平均亏损交易的损失</td>
            </tr>
            <tr>
                <td>最大连续盈利</td>
                <td>{metrics.max_consecutive_wins}</td>
                <td>最大连续盈利次数</td>
            </tr>
            <tr>
                <td>最大连续亏损</td>
                <td>{metrics.max_consecutive_losses}</td>
                <td>最大连续亏损次数</td>
            </tr>
        </table>
        
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>数据来源: 量化交易系统</p>
        </div>
    </div>
</body>
</html>
"""
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.info(f"性能报告已保存到 {output_path}")
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"生成性能报告失败: {e}")
            raise AnalysisException(f"生成性能报告失败: {e}")
    
    def generate_risk_report(self, 
                            risk_metrics: RiskMetrics,
                            title: str = "风险分析报告",
                            output_path: Optional[str] = None) -> str:
        """
        生成风险报告
        
        Args:
            risk_metrics: 风险指标
            title: 报告标题
            output_path: 输出路径
            
        Returns:
            str: HTML报告内容
        """
        try:
            self.logger.info("开始生成风险报告")
            
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #e74c3c;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .risk-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .risk-card {{
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .risk-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .risk-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .high-risk {{
            color: #e74c3c;
        }}
        .medium-risk {{
            color: #f39c12;
        }}
        .low-risk {{
            color: #27ae60;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #e74c3c;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="risk-grid">
            <div class="risk-card">
                <div class="risk-value {'high-risk' if risk_metrics.volatility > 30 else 'medium-risk' if risk_metrics.volatility > 15 else 'low-risk'}">
                    {risk_metrics.volatility:.2f}%
                </div>
                <div class="risk-label">波动率</div>
            </div>
            
            <div class="risk-card">
                <div class="risk-value high-risk">
                    {risk_metrics.var_95:.2f}%
                </div>
                <div class="risk-label">95% VaR</div>
            </div>
            
            <div class="risk-card">
                <div class="risk-value high-risk">
                    {risk_metrics.var_99:.2f}%
                </div>
                <div class="risk-label">99% VaR</div>
            </div>
            
            <div class="risk-card">
                <div class="risk-value {'high-risk' if risk_metrics.beta > 1.5 else 'medium-risk' if risk_metrics.beta > 0.5 else 'low-risk'}">
                    {risk_metrics.beta:.3f}
                </div>
                <div class="risk-label">贝塔系数</div>
            </div>
            
            <div class="risk-card">
                <div class="risk-value {'high-risk' if abs(risk_metrics.skewness) > 1 else 'medium-risk' if abs(risk_metrics.skewness) > 0.5 else 'low-risk'}">
                    {risk_metrics.skewness:.3f}
                </div>
                <div class="risk-label">偏度</div>
            </div>
            
            <div class="risk-card">
                <div class="risk-value {'high-risk' if risk_metrics.kurtosis > 3 else 'medium-risk' if risk_metrics.kurtosis > 1 else 'low-risk'}">
                    {risk_metrics.kurtosis:.3f}
                </div>
                <div class="risk-label">峰度</div>
            </div>
        </div>
        
        <h2>风险指标详情</h2>
        <table>
            <tr>
                <th>指标名称</th>
                <th>数值</th>
                <th>风险等级</th>
                <th>说明</th>
            </tr>
            <tr>
                <td>波动率</td>
                <td>{risk_metrics.volatility:.2f}%</td>
                <td>{'高风险' if risk_metrics.volatility > 30 else '中风险' if risk_metrics.volatility > 15 else '低风险'}</td>
                <td>价格波动的年化标准差</td>
            </tr>
            <tr>
                <td>95% VaR</td>
                <td>{risk_metrics.var_95:.2f}%</td>
                <td>高风险</td>
                <td>95%置信度下的最大损失</td>
            </tr>
            <tr>
                <td>99% VaR</td>
                <td>{risk_metrics.var_99:.2f}%</td>
                <td>高风险</td>
                <td>99%置信度下的最大损失</td>
            </tr>
            <tr>
                <td>95% CVaR</td>
                <td>{risk_metrics.cvar_95:.2f}%</td>
                <td>高风险</td>
                <td>95%置信度下的条件风险价值</td>
            </tr>
            <tr>
                <td>99% CVaR</td>
                <td>{risk_metrics.cvar_99:.2f}%</td>
                <td>高风险</td>
                <td>99%置信度下的条件风险价值</td>
            </tr>
            <tr>
                <td>下行偏差</td>
                <td>{risk_metrics.downside_deviation:.2f}%</td>
                <td>{'高风险' if risk_metrics.downside_deviation > 20 else '中风险' if risk_metrics.downside_deviation > 10 else '低风险'}</td>
                <td>下行波动的标准差</td>
            </tr>
            <tr>
                <td>贝塔系数</td>
                <td>{risk_metrics.beta:.3f}</td>
                <td>{'高风险' if risk_metrics.beta > 1.5 else '中风险' if risk_metrics.beta > 0.5 else '低风险'}</td>
                <td>相对于基准的系统性风险</td>
            </tr>
            <tr>
                <td>相关系数</td>
                <td>{risk_metrics.correlation:.3f}</td>
                <td>{'高风险' if abs(risk_metrics.correlation) > 0.7 else '中风险' if abs(risk_metrics.correlation) > 0.3 else '低风险'}</td>
                <td>与基准的相关性</td>
            </tr>
            <tr>
                <td>溃疡指数</td>
                <td>{risk_metrics.ulcer_index:.3f}</td>
                <td>{'高风险' if risk_metrics.ulcer_index > 0.1 else '中风险' if risk_metrics.ulcer_index > 0.05 else '低风险'}</td>
                <td>回撤的平方根平均值</td>
            </tr>
            <tr>
                <td>收益痛苦比</td>
                <td>{risk_metrics.gain_to_pain_ratio:.3f}</td>
                <td>{'低风险' if risk_metrics.gain_to_pain_ratio > 1 else '中风险' if risk_metrics.gain_to_pain_ratio > 0.5 else '高风险'}</td>
                <td>平均收益与平均损失的比值</td>
            </tr>
        </table>
        
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>数据来源: 量化交易系统</p>
        </div>
    </div>
</body>
</html>
"""
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.info(f"风险报告已保存到 {output_path}")
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"生成风险报告失败: {e}")
            raise AnalysisException(f"生成风险报告失败: {e}")
    
    def generate_comprehensive_report(self, 
                                    performance_metrics: PerformanceMetrics,
                                    risk_metrics: RiskMetrics,
                                    trades: List[Dict] = None,
                                    title: str = "综合分析报告",
                                    output_path: Optional[str] = None) -> str:
        """
        生成综合分析报告
        
        Args:
            performance_metrics: 性能指标
            risk_metrics: 风险指标
            trades: 交易记录
            title: 报告标题
            output_path: 输出路径
            
        Returns:
            str: HTML报告内容
        """
        try:
            self.logger.info("开始生成综合分析报告")
            
            # 生成性能报告和风险报告
            perf_report = self.generate_performance_report(performance_metrics, "性能分析")
            risk_report = self.generate_risk_report(risk_metrics, "风险分析")
            
            # 合并报告
            comprehensive_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }}
        .section h2 {{
            color: #34495e;
            margin-top: 0;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-value {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .summary-label {{
            font-size: 0.8em;
            opacity: 0.9;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="section">
            <h2>执行摘要</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-value">{performance_metrics.total_return:.2f}%</div>
                    <div class="summary-label">总收益率</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{performance_metrics.sharpe_ratio:.3f}</div>
                    <div class="summary-label">夏普比率</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{performance_metrics.max_drawdown:.2f}%</div>
                    <div class="summary-label">最大回撤</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{risk_metrics.volatility:.2f}%</div>
                    <div class="summary-label">波动率</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{performance_metrics.win_rate:.1f}%</div>
                    <div class="summary-label">胜率</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{performance_metrics.total_trades}</div>
                    <div class="summary-label">交易次数</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>性能分析</h2>
            {perf_report.split('<div class="metrics-grid">')[1].split('</div>')[0] if '<div class="metrics-grid">' in perf_report else '<p>性能数据不可用</p>'}
        </div>
        
        <div class="section">
            <h2>风险分析</h2>
            {risk_report.split('<div class="risk-grid">')[1].split('</div>')[0] if '<div class="risk-grid">' in risk_report else '<p>风险数据不可用</p>'}
        </div>
        
        {f'''
        <div class="section">
            <h2>交易统计</h2>
            <p>总交易次数: {len(trades) if trades else 0}</p>
            <p>盈利交易: {len([t for t in trades if t.get('pnl', 0) > 0]) if trades else 0}</p>
            <p>亏损交易: {len([t for t in trades if t.get('pnl', 0) < 0]) if trades else 0}</p>
        </div>
        ''' if trades else ''}
        
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>数据来源: 量化交易系统</p>
        </div>
    </div>
</body>
</html>
"""
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(comprehensive_html)
                self.logger.info(f"综合分析报告已保存到 {output_path}")
            
            return comprehensive_html
            
        except Exception as e:
            self.logger.error(f"生成综合分析报告失败: {e}")
            raise AnalysisException(f"生成综合分析报告失败: {e}")


def generate_report(metrics: Dict[str, Any], 
                   report_type: str = "performance",
                   output_path: Optional[str] = None) -> str:
    """
    便捷函数：生成报告
    
    Args:
        metrics: 指标数据
        report_type: 报告类型
        output_path: 输出路径
        
    Returns:
        str: HTML报告内容
    """
    generator = ReportGenerator()
    
    if report_type == "performance":
        return generator.generate_performance_report(metrics, output_path=output_path)
    elif report_type == "risk":
        return generator.generate_risk_report(metrics, output_path=output_path)
    else:
        raise ValueError(f"不支持的报告类型: {report_type}")