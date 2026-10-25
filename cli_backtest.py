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
from modules.database import DatabaseManager

# 配置参数
SYMBOL = 'ERA/USDT'
TIMEFRAME = '1m'
LIMIT = 1000

if __name__ == '__main__':
    # 配置参数（建议放在文件顶部或配置文件中）
    SYMBOL = 'BTC/USDT'
    TIMEFRAME = '1h'
    LIMIT = 500

    # 1. 初始化数据加载器（会自动处理数据库连接）
    data_loader = DataLoader(env='production')  # 使用生产环境配置

    # 2. 智能获取数据（自动优先从数据库获取）
    try:
        print(f"正在获取{SYMBOL}的{TIMEFRAME}周期数据，数量{LIMIT}条...")
        ohlcv = data_loader.fetch_ohlcv(SYMBOL, TIMEFRAME, LIMIT)
        df = data_loader.to_dataframe(ohlcv)

        # 3. 打印数据概览
        print("\n获取到的数据概览:")
        print(f"时间范围: {df.index[0]} 至 {df.index[-1]}")
        print(f"数据条数: {len(df)}")
        print(df.head(3))

        # 4. 保存数据到数据库（已集成在fetch_ohlcv中，不需要单独保存）
        # 除非需要强制更新，可以这样：
        # from modules.database import DatabaseManager
        # DatabaseManager().save_market_data(df, SYMBOL, TIMEFRAME)

    except Exception as e:
        print(f"数据获取失败: {str(e)}")



    # 2. 策略信号
    strategy_func = Strategy.mean_reversion # 只需改这里即可切换策略
    print("📈 生成交易信号...")
    # 为动量策略设置更合理的参数
    if strategy_func.__name__ == 'momentum':
        signals = strategy_func(df, window=10, threshold=0.02)  # 增加阈值到2%
    else:
        signals = strategy_func(df)
    print(f"✅ 生成 {len(signals[signals != 0])} 个交易信号")
    
    # 保存交易信号到数据库
    strategy_name = strategy_func.__name__
    for timestamp, signal in signals[signals != 0].items():
        if timestamp in df.index:
            price = df.loc[timestamp, 'close']
            db_manager.save_trading_signal(SYMBOL, timestamp, signal, strategy_name, price)
    
    # 打印所有非零信号的时间、类型和价格
    print("\n所有交易信号：")
    for ts, sig in signals[signals != 0].items():
        action = "买入" if sig == 1 else "卖出"
        price = df.loc[ts, 'close'] if ts in df.index else 'N/A'
        print(f"{ts}: {action} @ {price}")

    # 预测下一个信号价格
    print("\n🔮 预测下一个信号价格...")
    predictions = Strategy.predict_next_signals(df, strategy_name)
    if predictions.get('next_buy'):
        print(f"下一个买入信号触发价格: ${predictions['next_buy']:.2f}")
    if predictions.get('next_sell'):
        print(f"下一个卖出信号触发价格: ${predictions['next_sell']:.2f}")
    if not predictions.get('next_buy') and not predictions.get('next_sell'):
        print("当前无预测信号")
    if predictions.get('message'):
        print(f"预测信息: {predictions['message']}")
    
    # 保存策略预测到数据库
    current_price = df['close'].iloc[-1]
    current_time = df.index[-1]
    db_manager.save_strategy_prediction(
        strategy_name, SYMBOL, current_time,
        predictions.get('next_buy'), predictions.get('next_sell'),
        current_price, predictions.get('message')
    )

    # 3. 回测
    print("📊 执行回测...")
    backtester = Backtester(strategy_func, position_manager=FixedRatioPositionManager())
    backtester.run(df, initial_capital=100, commission=0.001)  # 0.1%手续费
    stats = backtester.stats()
    
    # 打印回测结果
    backtester.print_summary()
    print(f"净收益率: {stats['total_return'] - stats['commission_rate']:.2%}")

    # 自动获取策略名
    strategy_name = strategy_func.__name__ if hasattr(strategy_func, '__name__') else str(strategy_func)
    start_time = df.index[0] if len(df) > 0 else ''
    end_time = df.index[-1] if len(df) > 0 else ''
    
    # 保存回测结果到数据库
    backtest_result = {
        'strategy_name': strategy_name,
        'symbol': SYMBOL,
        'start_time': start_time,
        'end_time': end_time,
        'initial_capital': stats['initial_capital'],
        'final_capital': stats['final_capital'],
        'total_return': stats['total_return'],
        'annual_return': stats['annual_return'],
        'sharpe_ratio': stats['sharpe_ratio'],
        'max_drawdown': stats['max_drawdown'],
        'total_trades': stats['total_trades'],
        'win_rate': stats['win_rate'],
        'avg_win': stats['avg_win'],
        'avg_loss': stats['avg_loss'],
        'profit_factor': stats['profit_factor'],
        'total_days': stats['total_days'],
        'total_commission': stats['total_commission'],
        'commission_rate': stats['commission_rate'],
        'net_return': stats['total_return'] - stats['commission_rate'],
        'position_manager': 'FixedRatioPositionManager',
        'parameters': {}
    }
    db_manager.save_backtest_result(backtest_result)
    
    # Excel导出（保持原有功能）
    excel_path = 'backtest_results.xlsx'
    if os.path.exists(excel_path):
        df_excel = pd.read_excel(excel_path)
        backtest_id = len(df_excel) + 1
    else:
        backtest_id = 1

    # 处理result_row中的时间，去除时区
    def remove_tz(dt):
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            return dt.tz_convert('Asia/Shanghai').tz_localize(None)
        return dt

    result_row = {
        '回溯次数': backtest_id,
        '策略': strategy_name,
        '起始时间': remove_tz(start_time),
        '结束时间': remove_tz(end_time),
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
        '回测天数': stats['total_days'],
        '总手续费': stats['total_commission'],
        '手续费率': stats['commission_rate'],
        '净收益率': stats['total_return'] - stats['commission_rate']
    }
    if os.path.exists(excel_path):
        df_excel = pd.read_excel(excel_path)
        df_excel = pd.concat([df_excel, pd.DataFrame([result_row])], ignore_index=True)
    else:
        df_excel = pd.DataFrame([result_row])
    # 写入Excel前彻底去除所有带时区的datetime
    for col in df_excel.columns:
        if pd.api.types.is_datetime64_any_dtype(df_excel[col]):
            df_excel[col] = pd.to_datetime(df_excel[col]).dt.tz_localize(None)
    if hasattr(df_excel.index, 'tz') and df_excel.index.tz is not None:
        df_excel.index = df_excel.index.tz_localize(None)
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
    
    # 6. 显示数据库统计
    print("\n📊 数据库统计信息:")
    db_stats = db_manager.get_database_stats()
    for key, value in db_stats.items():
        if key.endswith('_count'):
            table_name = key.replace('_count', '').replace('_', ' ')
            print(f"  {table_name}: {value} 条记录")
    
    if 'data_start' in db_stats and 'data_end' in db_stats:
        print(f"  数据时间范围: {db_stats['data_start']} 到 {db_stats['data_end']}")
    
    print("\n✅ 所有数据已保存到数据库 quanttrade.db")

