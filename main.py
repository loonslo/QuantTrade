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
LIMIT = 200


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # 1. 数据获取
    data_loader = DataLoader()
    ohlcv = data_loader.fetch_ohlcv(SYMBOL, TIMEFRAME, LIMIT)
    df = data_loader.to_dataframe(ohlcv)

    # 2. 策略信号
    signals = Strategy.ma_cross(df)

    # 3. 回测
    backtester = Backtester(Strategy.ma_cross)
    backtester.run(df)
    stats = backtester.stats()

    # 4. 信号输出
    sender = SignalSender()
    sender.send_terminal(signals)

    # 5. 可视化
    plotter = Plotter()
    plotter.plot_kline(df, signals)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
