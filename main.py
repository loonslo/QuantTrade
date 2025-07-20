# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import os
from datetime import datetime
import inspect
from modules.data import DataLoader
from modules.position_manager import FixedRatioPositionManager
from modules.strategy import Strategy
from modules.backtest import Backtester
from modules.signal import SignalSender
from modules.plot import Plotter

# 参数配置
SYMBOL = 'ETH/USDT'  # 可选 'BTC/USDT' 或 'ETH/USDT'
TIMEFRAME = '15m'
LIMIT = 1000



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # 1. 数据获取
    data_loader = DataLoader()
    ohlcv = data_loader.fetch_ohlcv(SYMBOL, TIMEFRAME, LIMIT)
    df = data_loader.to_dataframe(ohlcv)


    # 2. 策略信号
    strategy_func = Strategy.ma_cross # 只需改这里即可切换策略
    print("📈 生成交易信号...")
    # 为动量策略设置更合理的参数
    if strategy_func.__name__ == 'momentum':
        signals = strategy_func(df, window=10, threshold=0.02)  # 增加阈值到2%
    else:
        signals = strategy_func(df)
    print(f"✅ 生成 {len(signals[signals != 0])} 个交易信号")
    # 打印所有非零信号的时间、类型和价格
    print("\n所有交易信号：")
    for ts, sig in signals[signals != 0].items():
        action = "买入" if sig == 1 else "卖出"
        price = df.loc[ts, 'close'] if ts in df.index else 'N/A'
        print(f"{ts}: {action} @ {price}")

    # 预测下一个信号价格
    print("\n🔮 预测下一个信号价格...")
    strategy_name = strategy_func.__name__
    predictions = Strategy.predict_next_signals(df, strategy_name)
    if predictions.get('next_buy'):
        print(f"下一个买入信号触发价格: ${predictions['next_buy']:.2f}")
    if predictions.get('next_sell'):
        print(f"下一个卖出信号触发价格: ${predictions['next_sell']:.2f}")
    if not predictions.get('next_buy') and not predictions.get('next_sell'):
        print("当前无预测信号")
    if predictions.get('message'):
        print(f"预测信息: {predictions['message']}")

    # 3. 回测
    print("📊 执行回测...")
    backtester = Backtester(strategy_func, position_manager=FixedRatioPositionManager())
    backtester.run(df, initial_capital=100, commission=0.001)
    stats = backtester.stats()
    
    # 打印回测结果
    backtester.print_summary()

    # 自动获取策略名
    strategy_name = strategy_func.__name__ if hasattr(strategy_func, '__name__') else str(strategy_func)
    start_time = df.index[0] if len(df) > 0 else ''
    end_time = df.index[-1] if len(df) > 0 else ''
    excel_path = 'backtest_results.xlsx'
    if os.path.exists(excel_path):
        df_excel = pd.read_excel(excel_path)
        backtest_id = len(df_excel) + 1
    else:
        backtest_id = 1
    result_row = {
        '回溯次数': backtest_id,
        '策略': strategy_name,
        '起始时间': start_time,
        '结束时间': end_time,
        '初始资金': stats['initial_capital'],
        '最终资金': stats['final_capital'],
        '总收益率': stats['total_return'],
        '年化收益率': stats['annual_return'],
        '夏普比率': stats['sharpe_ratio'],
        '最大回撤': stats['max_drawdown'],
        '总交易次数': stats['total_trades'],
        '胜率': stats['win_rate'],
        '平均盈利': stats['avg_win'],
        '平均亏损': stats['avg_loss'],
        '盈亏比': stats['profit_factor'],
        '回测天数': stats['total_days']
    }
    if os.path.exists(excel_path):
        df_excel = pd.read_excel(excel_path)
        df_excel = pd.concat([df_excel, pd.DataFrame([result_row])], ignore_index=True)
    else:
        df_excel = pd.DataFrame([result_row])
    df_excel.to_excel(excel_path, index=False)

    # 4. 信号输出
    sender = SignalSender()
    sender.send_terminal(signals)

    # 5. 可视化
    print("📈 生成可视化图表...")
    plotter = Plotter()
    plotter.plot_kline(df, signals)

    # 绘制权益曲线
    equity_curve = backtester.get_equity_curve()
    if not equity_curve.empty:
        plotter.plot_equity_curve(equity_curve)

    # 绘制交易分析
    trades = backtester.get_trades()
    if trades:
        plotter.plot_trade_analysis(trades)

