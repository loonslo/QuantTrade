import pandas as pd
import re
import backtrader as bt
from modules.data import DataLoader
from modules.strategy import Strategy
from modules.position_manager import AllInPositionManager, FixedRatioPositionManager, PyramidAllPositionManager, TwoThreeFivePositionManager
from modules.database import DatabaseManager
from datetime import datetime

def safe_sheet_name(name, max_length=31):
    name = re.sub(r'[:\\/?*\[\]]', '_', name)
    return name[:max_length]

# 桥接策略类
class SignalBridgeStrategy(bt.Strategy):
    def __init__(self, signals, position_manager):
        self.signals = signals
        self.position_manager = position_manager

    def next(self):
        idx = len(self) - 1
        if self.signals is None or idx >= len(self.signals):
            return
        signal = self.signals.iloc[idx]
        price = self.datas[0].close[0]
        cash = self.broker.get_cash()
        position = self.position.size
        commission = self.broker.getcommissioninfo(self.datas[0]).p.commission
        if not self.position and signal == 1:
            shares, _ = self.position_manager.on_buy_signal(cash, 0, price, commission)
            if shares > 0:
                self.buy(size=shares)
        elif self.position and signal == -1:
            shares = self.position.size
            if shares > 0:
                self.close()

# 策略与参数映射
strategy_map = {
    'ma_cross': (Strategy.ma_cross, {'short_window': 5, 'long_window': 20}),
    'rsi_signal': (Strategy.rsi_signal, {'period': 14, 'overbought': 70, 'oversold': 30}),
    'bollinger_breakout': (Strategy.bollinger_breakout, {'window': 20, 'num_std': 2}),
    'macd_cross': (Strategy.macd_cross, {'fast': 12, 'slow': 26, 'signal': 9}),
    'momentum': (Strategy.momentum, {'window': 10, 'threshold': 0.025}),
    'mean_reversion': (Strategy.mean_reversion, {'window': 100, 'threshold': 1.5}),
    'breakout': (Strategy.breakout, {'window': 20}),
    'turtle': (Strategy.turtle, {'entry_window': 18, 'exit_window': 12}),
    'kdj_signal': (Strategy.kdj_signal, {'n': 9, 'k_period': 3, 'd_period': 3}),
    'kama_cross': (Strategy.kama_cross, {'fast': 2, 'slow': 30, 'window': 50}),
}
# 仓位管理器映射
sizer_map = {
    '全仓': AllInPositionManager(),
    '固定比例': FixedRatioPositionManager(),
    '金字塔': PyramidAllPositionManager(),
    '235': TwoThreeFivePositionManager(),
}

def test_strategy_commission_bt():
    backtest_settings = [
        {"desc": "1m/1000/ERA", "symbol": "ERA/USDT", "timeframe": "1m", "limit": 1000}
    ]
    all_results = []
    db_manager = DatabaseManager()
    for setting in backtest_settings:
        data_loader = DataLoader()
        ohlcv = data_loader.fetch_ohlcv(setting['symbol'], setting['timeframe'], setting['limit'])
        df = data_loader.to_dataframe(ohlcv)
        df.index = pd.to_datetime(df.index)
        data = bt.feeds.PandasData(dataname=df)
        for strat_name, (signal_func, signal_kwargs) in strategy_map.items():
            signals = signal_func(df, **signal_kwargs)
            for pm_name, pm in sizer_map.items():
                cerebro = bt.Cerebro()
                cerebro.addstrategy(SignalBridgeStrategy, signals=signals, position_manager=pm)
                cerebro.adddata(data)
                cerebro.broker.setcash(10000)
                cerebro.broker.setcommission(commission=0.001)
                cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade')
                cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
                cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
                result = cerebro.run()
                stats = result[0].analyzers
                trade_stats = stats.trade.get_analysis()
                total_trades = trade_stats.get('total', {}).get('total', 0)
                win_rate = (trade_stats.get('won', {}).get('total', 0) / total_trades) if total_trades else 0
                initial_capital = 10000
                final_value = cerebro.broker.getvalue()
                total_return = (final_value - initial_capital) / initial_capital
                commission_rate = 0.001
                result_row = {
                    '数据集': setting['desc'],
                    '策略+仓位管理': f"{Strategy.get_strategy_name_cn(strat_name)}+{pm_name}",
                    '策略': Strategy.get_strategy_name_cn(strat_name),
                    '仓位管理': pm_name,
                    '总交易次数': total_trades,
                    '总手续费': 'N/A',
                    '手续费率': commission_rate,
                    '总收益率': total_return,
                    '净收益率': total_return - commission_rate,
                    '胜率': win_rate
                }
                df_results = pd.DataFrame([result_row])
                all_results.append(df_results)
                print(f"\n📊 手续费汇总报告（数据集：{setting['desc']} 策略: {strat_name} 仓位: {pm_name}）")
                print("=" * 80)
                print(df_results)
                excel_filename = 'commission_analysis.xlsx'
                safe_desc = safe_sheet_name(setting['desc'])
                with pd.ExcelWriter(excel_filename, mode='a' if setting != backtest_settings[0] else 'w', engine='openpyxl') as writer:
                    df_results.to_excel(writer, sheet_name=f"{safe_desc}_{strat_name}_{pm_name}", index=False)
                db_manager.save_commission_summary(
                    symbol=setting['symbol'],
                    dataset_desc=setting['desc'],
                    strategy=Strategy.get_strategy_name_cn(strat_name),
                    position_manager=pm_name,
                    total_trades=total_trades,
                    total_commission=0,
                    commission_rate=commission_rate,
                    net_return=total_return - commission_rate,
                    win_rate=win_rate,
                    summary_time=datetime.now()
                )
    final_df = pd.concat(all_results, ignore_index=True)
    return final_df

if __name__ == '__main__':
    test_strategy_commission_bt()