# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from modules.data import DataLoader
from modules.strategy import Strategy
from modules.backtest import Backtester
from modules.signal import SignalSender
from modules.plot import Plotter

# 参数配置
SYMBOL = 'BTC/USDT'  # 可选 'BTC/USDT' 或 'ETH/USDT'
TIMEFRAME = '1h'
LIMIT = 300



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # 1. 数据获取
    data_loader = DataLoader()
    ohlcv = data_loader.fetch_ohlcv(SYMBOL, TIMEFRAME, LIMIT)
    df = data_loader.to_dataframe(ohlcv)


    # 2. 策略信号
    print("📈 生成交易信号...")
    signals = Strategy.ma_cross(df)
    print(f"✅ 生成 {len(signals[signals != 0])} 个交易信号")
    # 打印所有非零信号的时间、类型和价格
    print("\n所有交易信号：")
    for ts, sig in signals[signals != 0].items():
        action = "买入" if sig == 1 else "卖出"
        price = df.loc[ts, 'close'] if ts in df.index else 'N/A'
        print(f"{ts}: {action} @ {price}")

    # 3. 回测
    print("📊 执行回测...")
    backtester = Backtester(Strategy.ma_cross)
    backtester.run(df, initial_capital=1000000, commission=0.001)
    stats = backtester.stats()
    
    # 打印回测结果
    backtester.print_summary()

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

