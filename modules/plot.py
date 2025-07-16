import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional, Dict, Any
import numpy as np

class Plotter:
    def __init__(self):
        """初始化绘图器"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
    
    def plot_kline(self, df: pd.DataFrame, signals: Optional[pd.Series] = None, 
                   title: str = "K线图与交易信号"):
        """
        绘制K线和买卖信号点
        :param df: K线数据
        :param signals: 交易信号
        :param title: 图表标题
        """
        print("📈 生成K线图...")
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[3, 1])
        
        # 绘制K线图
        self._plot_candlestick(ax1, df, signals)
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # 绘制成交量
        self._plot_volume(ax2, df)
        ax2.set_title("成交量", fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        import os
        os.makedirs('charts', exist_ok=True)
        plt.savefig(f'charts/kline_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png', 
                   dpi=300, bbox_inches='tight')
        
        print("✅ K线图已保存到 charts/ 目录")
        plt.show()
    
    def _plot_candlestick(self, ax, df: pd.DataFrame, signals: Optional[pd.Series] = None):
        """绘制K线图"""
        # 绘制K线
        for i in range(len(df)):
            open_price = df['open'].iloc[i]
            close_price = df['close'].iloc[i]
            high_price = df['high'].iloc[i]
            low_price = df['low'].iloc[i]
            timestamp = df.index[i]
            
            # 判断涨跌
            if close_price >= open_price:
                color = 'red'  # 上涨
                body_height = close_price - open_price
                body_bottom = open_price
            else:
                color = 'green'  # 下跌
                body_height = open_price - close_price
                body_bottom = close_price
            
            # 绘制实体
            if body_height > 0:
                ax.bar(timestamp, body_height, bottom=body_bottom, 
                      color=color, alpha=0.7, width=0.8)
            
            # 绘制上下影线
            ax.plot([timestamp, timestamp], [low_price, high_price], 
                   color='black', linewidth=1)
        
        # 绘制交易信号
        if signals is not None:
            buy_signals = signals[signals == 1]
            sell_signals = signals[signals == -1]
            
            # 买入信号（绿色三角形向上）
            if len(buy_signals) > 0:
                buy_prices = df.loc[buy_signals.index, 'low'] * 0.99  # 稍微低于最低价
                ax.scatter(buy_signals.index, buy_prices, 
                          color='green', marker='^', s=100, 
                          label='买入信号', zorder=5)
            
            # 卖出信号（红色三角形向下）
            if len(sell_signals) > 0:
                sell_prices = df.loc[sell_signals.index, 'high'] * 1.01  # 稍微高于最高价
                ax.scatter(sell_signals.index, sell_prices, 
                          color='red', marker='v', s=100, 
                          label='卖出信号', zorder=5)
            
            ax.legend()
        
        # 设置x轴格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _plot_volume(self, ax, df: pd.DataFrame):
        """绘制成交量"""
        # 根据涨跌设置颜色
        colors = ['red' if close >= open else 'green' 
                 for close, open in zip(df['close'], df['open'])]
        
        ax.bar(df.index, df['volume'], color=colors, alpha=0.7)
        ax.set_ylabel('成交量')
        
        # 设置x轴格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def plot_equity_curve(self, equity_curve: pd.DataFrame, title: str = "权益曲线"):
        """
        绘制权益曲线
        :param equity_curve: 权益曲线数据
        :param title: 图表标题
        """
        if equity_curve.empty:
            print("❌ 没有权益曲线数据")
            return
        
        print("📊 生成权益曲线...")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[2, 1])
        
        # 绘制权益曲线
        ax1.plot(equity_curve['timestamp'], equity_curve['equity'], 
                linewidth=2, color='blue', label='账户权益')
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('权益 ($)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 绘制回撤
        equity_curve['cummax'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['equity'] - equity_curve['cummax']) / equity_curve['cummax']
        
        ax2.fill_between(equity_curve['timestamp'], equity_curve['drawdown'], 0, 
                        color='red', alpha=0.3, label='回撤')
        ax2.set_ylabel('回撤 (%)')
        ax2.set_xlabel('时间')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # 设置x轴格式
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # 保存图片
        import os
        os.makedirs('charts', exist_ok=True)
        plt.savefig(f'charts/equity_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png', 
                   dpi=300, bbox_inches='tight')
        
        print("✅ 权益曲线已保存到 charts/ 目录")
        plt.show()
    
    def plot_trade_analysis(self, trades: list, title: str = "交易分析"):
        """
        绘制交易分析图
        :param trades: 交易记录
        :param title: 图表标题
        """
        if not trades:
            print("❌ 没有交易记录")
            return
        
        print("📊 生成交易分析图...")
        
        # 转换为DataFrame
        trades_df = pd.DataFrame(trades)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 交易盈亏分布
        if 'profit' in trades_df.columns:
            profits = trades_df[trades_df['action'] == 'SELL']['profit']
            ax1.hist(profits, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax1.set_title('交易盈亏分布')
            ax1.set_xlabel('盈亏 ($)')
            ax1.set_ylabel('频次')
            ax1.axvline(0, color='red', linestyle='--', alpha=0.7)
        
        # 2. 交易时间分布
        if 'timestamp' in trades_df.columns:
            trades_df['hour'] = pd.to_datetime(trades_df['timestamp']).dt.hour
            hour_counts = trades_df['hour'].value_counts().sort_index()
            ax2.bar(hour_counts.index, hour_counts.values, alpha=0.7, color='orange')
            ax2.set_title('交易时间分布')
            ax2.set_xlabel('小时')
            ax2.set_ylabel('交易次数')
        
        # 3. 累计盈亏
        if 'profit' in trades_df.columns:
            sell_trades = trades_df[trades_df['action'] == 'SELL']
            cumulative_profit = sell_trades['profit'].cumsum()
            ax3.plot(range(len(cumulative_profit)), cumulative_profit, 
                    linewidth=2, color='green')
            ax3.set_title('累计盈亏')
            ax3.set_xlabel('交易次数')
            ax3.set_ylabel('累计盈亏 ($)')
            ax3.grid(True, alpha=0.3)
        
        # 4. 交易价格分布
        if 'price' in trades_df.columns:
            buy_prices = trades_df[trades_df['action'] == 'BUY']['price']
            sell_prices = trades_df[trades_df['action'] == 'SELL']['price']
            
            ax4.hist(buy_prices, bins=20, alpha=0.5, label='买入价格', color='green')
            ax4.hist(sell_prices, bins=20, alpha=0.5, label='卖出价格', color='red')
            ax4.set_title('交易价格分布')
            ax4.set_xlabel('价格 ($)')
            ax4.set_ylabel('频次')
            ax4.legend()
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # 保存图片
        import os
        os.makedirs('charts', exist_ok=True)
        plt.savefig(f'charts/trade_analysis_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png', 
                   dpi=300, bbox_inches='tight')
        
        print("✅ 交易分析图已保存到 charts/ 目录")
        plt.show() 