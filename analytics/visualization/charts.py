"""
图表生成器
生成各种交易分析图表
"""

# 导入统一的matplotlib配置
from utils.helpers.matplotlib_config import configure_matplotlib, save_chart

# 配置matplotlib
configure_matplotlib()

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from utils.core.logger_manager import get_logger


class ChartGenerator:
    """图表生成器"""
    
    def __init__(self):
        """初始化图表生成器"""
        self.logger = get_logger('chart_generator')
        
    def plot_price_chart(self, 
                        data: pd.DataFrame, 
                        title: str = "价格图表",
                        save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制价格图表
        
        Args:
            data: OHLCV数据
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 绘制K线图
            if 'close' in data.columns:
                ax.plot(data.index, data['close'], label='收盘价', linewidth=1)
            
            if 'high' in data.columns and 'low' in data.columns:
                ax.fill_between(data.index, data['low'], data['high'], 
                              alpha=0.3, label='价格区间')
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('价格', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            if save_path:
                save_chart(fig, save_path)
                self.logger.info(f"价格图表已保存到 {save_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"绘制价格图表失败: {e}")
            raise
    
    def plot_volume_chart(self, 
                         data: pd.DataFrame, 
                         title: str = "成交量图表",
                         save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制成交量图表
        
        Args:
            data: OHLCV数据
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if 'volume' in data.columns:
                ax.bar(data.index, data['volume'], alpha=0.7, color='skyblue')
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('成交量', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            if save_path:
                save_chart(fig, save_path)
                self.logger.info(f"成交量图表已保存到 {save_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"绘制成交量图表失败: {e}")
            raise
    
    def plot_performance_chart(self, 
                              equity_curve: pd.Series,
                              title: str = "策略表现",
                              save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制策略表现图表
        
        Args:
            equity_curve: 权益曲线
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # 权益曲线
            ax1.plot(equity_curve.index, equity_curve.values, 
                    linewidth=2, color='blue', label='权益曲线')
            ax1.set_title(f"{title} - 权益曲线", fontsize=14, fontweight='bold')
            ax1.set_ylabel('权益', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 回撤曲线
            rolling_max = equity_curve.expanding().max()
            drawdown = (equity_curve - rolling_max) / rolling_max * 100
            
            ax2.fill_between(drawdown.index, drawdown.values, 0, 
                            alpha=0.7, color='red', label='回撤')
            ax2.set_title('回撤曲线', fontsize=14, fontweight='bold')
            ax2.set_xlabel('时间', fontsize=12)
            ax2.set_ylabel('回撤 (%)', fontsize=12)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                save_chart(fig, save_path)
                self.logger.info(f"策略表现图表已保存到 {save_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"绘制策略表现图表失败: {e}")
            raise
    
    def plot_trade_distribution(self, 
                               trades: List[Dict],
                               title: str = "交易分布",
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制交易分布图表
        
        Args:
            trades: 交易记录列表
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        try:
            if not trades:
                raise ValueError("没有交易数据")
            
            df = pd.DataFrame(trades)
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 盈亏分布
            if 'pnl' in df.columns:
                ax1.hist(df['pnl'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                ax1.set_title('盈亏分布', fontsize=12, fontweight='bold')
                ax1.set_xlabel('盈亏', fontsize=10)
                ax1.set_ylabel('频次', fontsize=10)
                ax1.grid(True, alpha=0.3)
            
            # 胜率饼图
            if 'pnl' in df.columns:
                wins = len(df[df['pnl'] > 0])
                losses = len(df[df['pnl'] < 0])
                draws = len(df[df['pnl'] == 0])
                
                sizes = [wins, losses, draws]
                labels = ['盈利', '亏损', '平局']
                colors = ['green', 'red', 'gray']
                
                ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax2.set_title('交易结果分布', fontsize=12, fontweight='bold')
            
            # 交易时间分布
            if 'timestamp' in df.columns:
                df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
                hourly_counts = df['hour'].value_counts().sort_index()
                ax3.bar(hourly_counts.index, hourly_counts.values, alpha=0.7, color='orange')
                ax3.set_title('交易时间分布', fontsize=12, fontweight='bold')
                ax3.set_xlabel('小时', fontsize=10)
                ax3.set_ylabel('交易次数', fontsize=10)
                ax3.grid(True, alpha=0.3)
            
            # 累计收益曲线
            if 'pnl' in df.columns:
                cumulative_pnl = df['pnl'].cumsum()
                ax4.plot(range(len(cumulative_pnl)), cumulative_pnl.values, 
                        linewidth=2, color='purple')
                ax4.set_title('累计收益曲线', fontsize=12, fontweight='bold')
                ax4.set_xlabel('交易次数', fontsize=10)
                ax4.set_ylabel('累计收益', fontsize=10)
                ax4.grid(True, alpha=0.3)
            
            plt.suptitle(title, fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            if save_path:
                save_chart(fig, save_path)
                self.logger.info(f"交易分布图表已保存到 {save_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"绘制交易分布图表失败: {e}")
            raise
    
    def plot_correlation_matrix(self, 
                               data: pd.DataFrame,
                               title: str = "相关性矩阵",
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制相关性矩阵热力图
        
        Args:
            data: 数据DataFrame
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        try:
            # 计算相关性矩阵
            correlation_matrix = data.corr()
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # 绘制热力图
            sns.heatmap(correlation_matrix, 
                       annot=True, 
                       cmap='coolwarm', 
                       center=0,
                       square=True,
                       ax=ax)
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            
            if save_path:
                save_chart(fig, save_path)
                self.logger.info(f"相关性矩阵图表已保存到 {save_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"绘制相关性矩阵失败: {e}")
            raise
    
    def plot_risk_metrics(self, 
                          metrics: Dict[str, float],
                          title: str = "风险指标",
                          save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制风险指标雷达图
        
        Args:
            metrics: 风险指标字典
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        try:
            # 选择要显示的指标
            display_metrics = {
                '夏普比率': metrics.get('sharpe_ratio', 0),
                '最大回撤': metrics.get('max_drawdown', 0),
                '胜率': metrics.get('win_rate', 0),
                '盈利因子': metrics.get('profit_factor', 0),
                '平均收益': metrics.get('avg_return', 0)
            }
            
            # 标准化数据（0-1范围）
            normalized_metrics = {}
            for key, value in display_metrics.items():
                if key == '最大回撤':
                    # 回撤越小越好，所以取反
                    normalized_metrics[key] = max(0, 1 - abs(value) / 100)
            else:
                    # 其他指标越大越好
                    normalized_metrics[key] = min(1, max(0, value / 10))
            
            # 创建雷达图
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            
            # 角度
            angles = np.linspace(0, 2 * np.pi, len(normalized_metrics), endpoint=False)
            values = list(normalized_metrics.values())
            
            # 闭合图形
            angles = np.concatenate((angles, [angles[0]]))
            values = np.concatenate((values, [values[0]]))
            
            # 绘制
            ax.plot(angles, values, 'o-', linewidth=2, color='blue')
            ax.fill(angles, values, alpha=0.25, color='blue')
            
            # 设置标签
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(list(normalized_metrics.keys()))
            ax.set_ylim(0, 1)
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            if save_path:
                save_chart(fig, save_path)
                self.logger.info(f"风险指标图表已保存到 {save_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"绘制风险指标失败: {e}")
            raise


def generate_analysis_charts(data: pd.DataFrame, 
                           trades: List[Dict] = None,
                           metrics: Dict[str, float] = None,
                           output_dir: str = "charts") -> Dict[str, str]:
    """
    便捷函数：生成分析图表
    
    Args:
        data: OHLCV数据
        trades: 交易记录
        metrics: 风险指标
        output_dir: 输出目录
        
    Returns:
        Dict[str, str]: 图表文件路径字典
    """
    generator = ChartGenerator()
    chart_paths = {}
    
    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        # 价格图表
        price_chart = generator.plot_price_chart(data, "价格走势图")
        price_path = f"{output_dir}/price_chart.png"
        chart_paths['price'] = price_path
        
        # 成交量图表
        volume_chart = generator.plot_volume_chart(data, "成交量图")
        volume_path = f"{output_dir}/volume_chart.png"
        chart_paths['volume'] = volume_path
        
        # 如果有交易数据，生成交易分布图
        if trades:
            trade_chart = generator.plot_trade_distribution(trades, "交易分析")
            trade_path = f"{output_dir}/trade_distribution.png"
            chart_paths['trades'] = trade_path
        
        # 如果有风险指标，生成风险指标图
        if metrics:
            risk_chart = generator.plot_risk_metrics(metrics, "风险指标")
            risk_path = f"{output_dir}/risk_metrics.png"
            chart_paths['risk'] = risk_path
        
        generator.logger.info(f"所有图表已生成到 {output_dir} 目录")
        
    except Exception as e:
        generator.logger.error(f"生成图表失败: {e}")
    
    return chart_paths