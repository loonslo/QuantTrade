#!/usr/bin/env python3
"""
数据分析脚本
用于查询和分析数据库中的交易数据、策略性能等
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from modules.database import DatabaseManager
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self, db_path: str = 'quanttrade.db'):
        self.db_manager = DatabaseManager(db_path)
    
    def analyze_strategy_performance(self):
        """分析策略性能"""
        print("📊 策略性能分析")
        print("="*60)
        
        # 获取策略性能摘要
        performance_df = self.db_manager.get_strategy_performance_summary()
        
        if performance_df.empty:
            print("暂无回测数据")
            return
        
        print("策略性能排名:")
        for i, row in performance_df.iterrows():
            print(f"{i+1}. {row['strategy_name']} ({row['symbol']})")
            print(f"   回测次数: {row['backtest_count']}")
            print(f"   平均收益率: {row['avg_return']:.2%}")
            print(f"   平均夏普比率: {row['avg_sharpe']:.2f}")
            print(f"   平均最大回撤: {row['avg_drawdown']:.2%}")
            print(f"   平均胜率: {row['avg_win_rate']:.2%}")
            print(f"   平均手续费: ${row['avg_commission']:.2f}")
            print(f"   最后测试: {row['last_test']}")
            print()
        
        # 绘制策略性能对比图
        self._plot_strategy_comparison(performance_df)
    
    def analyze_trading_signals(self, symbol: str = 'BTC/USDT', days: int = 30):
        """分析交易信号"""
        print(f"📈 交易信号分析 - {symbol}")
        print("="*60)
        
        start_time = datetime.now() - timedelta(days=days)
        signals_df = self.db_manager.get_trading_signals(symbol, start_time=start_time)
        
        if signals_df.empty:
            print("暂无交易信号数据")
            return
        
        # 信号统计
        total_signals = len(signals_df)
        buy_signals = len(signals_df[signals_df['signal'] == 1])
        sell_signals = len(signals_df[signals_df['signal'] == -1])
        
        print(f"总信号数: {total_signals}")
        print(f"买入信号: {buy_signals} ({buy_signals/total_signals:.1%})")
        print(f"卖出信号: {sell_signals} ({sell_signals/total_signals:.1%})")
        
        # 按策略分组统计
        strategy_stats = signals_df.groupby('strategy_name').agg({
            'signal': ['count', lambda x: (x == 1).sum(), lambda x: (x == -1).sum()]
        }).round(2)
        strategy_stats.columns = ['总信号', '买入信号', '卖出信号']
        print(f"\n按策略统计:")
        print(strategy_stats)
        
        # 绘制信号分布图
        self._plot_signal_distribution(signals_df)
    
    def analyze_trade_records(self, symbol: str = None, days: int = 30):
        """分析交易记录"""
        print("💰 交易记录分析")
        print("="*60)
        
        start_time = datetime.now() - timedelta(days=days)
        trades_df = self.db_manager.get_trade_records(symbol, start_time=start_time)
        
        if trades_df.empty:
            print("暂无交易记录")
            return
        
        # 交易统计
        total_trades = len(trades_df)
        buy_trades = len(trades_df[trades_df['side'] == 'buy'])
        sell_trades = len(trades_df[trades_df['side'] == 'sell'])
        total_volume = trades_df['quantity'].sum()
        total_commission = trades_df['commission'].sum()
        
        print(f"总交易次数: {total_trades}")
        print(f"买入交易: {buy_trades}")
        print(f"卖出交易: {sell_trades}")
        print(f"总交易量: {total_volume:.6f}")
        print(f"总手续费: ${total_commission:.2f}")
        
        # 按策略分组统计
        if 'strategy_name' in trades_df.columns:
            strategy_trades = trades_df.groupby('strategy_name').agg({
                'order_id': 'count',
                'quantity': 'sum',
                'commission': 'sum',
                'cost': 'sum'
            }).round(4)
            strategy_trades.columns = ['交易次数', '交易量', '手续费', '交易金额']
            print(f"\n按策略统计:")
            print(strategy_trades)
        
        # 绘制交易分析图
        self._plot_trade_analysis(trades_df)
    
    def analyze_market_data(self, symbol: str = 'BTC/USDT', days: int = 7):
        """分析市场数据"""
        print(f"📊 市场数据分析 - {symbol}")
        print("="*60)
        
        start_time = datetime.now() - timedelta(days=days)
        market_df = self.db_manager.get_market_data(symbol, start_time=start_time, timeframe='1h')
        
        if market_df.empty:
            print("暂无市场数据")
            return
        
        # 市场数据统计
        print(f"数据点数量: {len(market_df)}")
        print(f"时间范围: {market_df.index[0]} 到 {market_df.index[-1]}")
        print(f"最高价: ${market_df['high'].max():.2f}")
        print(f"最低价: ${market_df['low'].min():.2f}")
        print(f"平均价: ${market_df['close'].mean():.2f}")
        print(f"总成交量: {market_df['volume'].sum():.2f}")
        
        # 价格变化统计
        price_change = market_df['close'].pct_change().dropna()
        print(f"平均日收益率: {price_change.mean():.2%}")
        print(f"收益率标准差: {price_change.std():.2%}")
        print(f"最大单日涨幅: {price_change.max():.2%}")
        print(f"最大单日跌幅: {price_change.min():.2%}")
        
        # 绘制市场数据图
        self._plot_market_data(market_df)
    
    def get_recent_activity(self, hours: int = 24):
        """获取最近活动"""
        print(f"🕒 最近 {hours} 小时活动")
        print("="*60)
        
        start_time = datetime.now() - timedelta(hours=hours)
        
        # 最近交易信号
        signals_df = self.db_manager.get_trading_signals(start_time=start_time)
        if not signals_df.empty:
            print("最近交易信号:")
            for _, signal in signals_df.head(5).iterrows():
                action = "买入" if signal['signal'] == 1 else "卖出"
                print(f"  {signal['timestamp']} {signal['symbol']} {action} @ ${signal['price']:.2f}")
        
        # 最近交易记录
        trades_df = self.db_manager.get_trade_records(start_time=start_time)
        if not trades_df.empty:
            print("\n最近交易记录:")
            for _, trade in trades_df.head(5).iterrows():
                print(f"  {trade['timestamp']} {trade['symbol']} {trade['side']} "
                      f"{trade['quantity']:.6f} @ ${trade['price']:.2f}")
        
        # 最近策略预测
        # 这里可以添加策略预测的查询和显示
    
    def _plot_strategy_comparison(self, performance_df):
        """绘制策略性能对比图"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('策略性能对比', fontsize=16)
        
        # 平均收益率对比
        axes[0, 0].bar(performance_df['strategy_name'], performance_df['avg_return'])
        axes[0, 0].set_title('平均收益率')
        axes[0, 0].set_ylabel('收益率')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 夏普比率对比
        axes[0, 1].bar(performance_df['strategy_name'], performance_df['avg_sharpe'])
        axes[0, 1].set_title('平均夏普比率')
        axes[0, 1].set_ylabel('夏普比率')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 最大回撤对比
        axes[1, 0].bar(performance_df['strategy_name'], performance_df['avg_drawdown'])
        axes[1, 0].set_title('平均最大回撤')
        axes[1, 0].set_ylabel('回撤')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 胜率对比
        axes[1, 1].bar(performance_df['strategy_name'], performance_df['avg_win_rate'])
        axes[1, 1].set_title('平均胜率')
        axes[1, 1].set_ylabel('胜率')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('charts/strategy_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_signal_distribution(self, signals_df):
        """绘制信号分布图"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('交易信号分析', fontsize=16)
        
        # 信号分布饼图
        signal_counts = signals_df['signal'].value_counts()
        axes[0, 0].pie(signal_counts.values, labels=['卖出', '买入', '无信号'], autopct='%1.1f%%')
        axes[0, 0].set_title('信号分布')
        
        # 按策略的信号数量
        strategy_signals = signals_df.groupby('strategy_name')['signal'].count()
        axes[0, 1].bar(strategy_signals.index, strategy_signals.values)
        axes[0, 1].set_title('各策略信号数量')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 信号时间分布
        signals_df['hour'] = signals_df.index.hour
        hour_counts = signals_df['hour'].value_counts().sort_index()
        axes[1, 0].plot(hour_counts.index, hour_counts.values)
        axes[1, 0].set_title('信号时间分布')
        axes[1, 0].set_xlabel('小时')
        axes[1, 0].set_ylabel('信号数量')
        
        # 价格分布
        axes[1, 1].hist(signals_df['price'], bins=20, alpha=0.7)
        axes[1, 1].set_title('信号价格分布')
        axes[1, 1].set_xlabel('价格')
        axes[1, 1].set_ylabel('频次')
        
        plt.tight_layout()
        plt.savefig('charts/signal_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_trade_analysis(self, trades_df):
        """绘制交易分析图"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('交易记录分析', fontsize=16)
        
        # 交易量分布
        axes[0, 0].hist(trades_df['quantity'], bins=20, alpha=0.7)
        axes[0, 0].set_title('交易量分布')
        axes[0, 0].set_xlabel('交易量')
        axes[0, 0].set_ylabel('频次')
        
        # 手续费分布
        axes[0, 1].hist(trades_df['commission'], bins=20, alpha=0.7)
        axes[0, 1].set_title('手续费分布')
        axes[0, 1].set_xlabel('手续费')
        axes[0, 1].set_ylabel('频次')
        
        # 买卖交易对比
        side_counts = trades_df['side'].value_counts()
        axes[1, 0].pie(side_counts.values, labels=side_counts.index, autopct='%1.1f%%')
        axes[1, 0].set_title('买卖交易比例')
        
        # 交易金额时间序列
        trades_df['date'] = trades_df.index.date
        daily_volume = trades_df.groupby('date')['cost'].sum()
        axes[1, 1].plot(daily_volume.index, daily_volume.values)
        axes[1, 1].set_title('日交易金额')
        axes[1, 1].set_xlabel('日期')
        axes[1, 1].set_ylabel('交易金额')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('charts/trade_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_market_data(self, market_df):
        """绘制市场数据图"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('市场数据分析', fontsize=16)
        
        # 价格走势
        axes[0, 0].plot(market_df.index, market_df['close'])
        axes[0, 0].set_title('价格走势')
        axes[0, 0].set_ylabel('价格')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 成交量
        axes[0, 1].bar(market_df.index, market_df['volume'], alpha=0.7)
        axes[0, 1].set_title('成交量')
        axes[0, 1].set_ylabel('成交量')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 价格分布
        axes[1, 0].hist(market_df['close'], bins=30, alpha=0.7)
        axes[1, 0].set_title('价格分布')
        axes[1, 0].set_xlabel('价格')
        axes[1, 0].set_ylabel('频次')
        
        # 收益率分布
        returns = market_df['close'].pct_change().dropna()
        axes[1, 1].hist(returns, bins=30, alpha=0.7)
        axes[1, 1].set_title('收益率分布')
        axes[1, 1].set_xlabel('收益率')
        axes[1, 1].set_ylabel('频次')
        
        plt.tight_layout()
        plt.savefig('charts/market_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    """主函数"""
    print("📊 量化交易数据分析工具")
    print("="*60)
    
    analyzer = DataAnalyzer()
    
    while True:
        print("\n请选择分析功能:")
        print("1. 策略性能分析")
        print("2. 交易信号分析")
        print("3. 交易记录分析")
        print("4. 市场数据分析")
        print("5. 最近活动查看")
        print("6. 数据库统计信息")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-6): ").strip()
        
        if choice == '0':
            print("👋 再见！")
            break
        elif choice == '1':
            analyzer.analyze_strategy_performance()
        elif choice == '2':
            symbol = input("请输入交易对 (默认 BTC/USDT): ").strip() or 'BTC/USDT'
            days = int(input("请输入分析天数 (默认 30): ").strip() or '30')
            analyzer.analyze_trading_signals(symbol, days)
        elif choice == '3':
            symbol = input("请输入交易对 (留空为全部): ").strip() or None
            days = int(input("请输入分析天数 (默认 30): ").strip() or '30')
            analyzer.analyze_trade_records(symbol, days)
        elif choice == '4':
            symbol = input("请输入交易对 (默认 BTC/USDT): ").strip() or 'BTC/USDT'
            days = int(input("请输入分析天数 (默认 7): ").strip() or '7')
            analyzer.analyze_market_data(symbol, days)
        elif choice == '5':
            hours = int(input("请输入小时数 (默认 24): ").strip() or '24')
            analyzer.get_recent_activity(hours)
        elif choice == '6':
            stats = analyzer.db_manager.get_database_stats()
            print("\n📊 数据库统计信息:")
            for key, value in stats.items():
                if key.endswith('_count'):
                    table_name = key.replace('_count', '').replace('_', ' ')
                    print(f"  {table_name}: {value} 条记录")
            if 'data_start' in stats and 'data_end' in stats:
                print(f"  数据时间范围: {stats['data_start']} 到 {stats['data_end']}")
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 