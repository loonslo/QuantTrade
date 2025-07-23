import pandas as pd
from modules.data import DataLoader
from modules.strategy import Strategy
from modules.backtest import Backtester
from modules.position_manager import FixedRatioPositionManager, AllInPositionManager, PyramidAllPositionManager
import re

def safe_sheet_name(name, max_length=31):
    """
    替换Excel sheet名中的非法字符，并截断长度不超过31
    """
    # Excel sheet名不能包含: : \ / ? * [ ]
    name = re.sub(r'[:\\/?*\[\]]', '_', name)
    # 截断长度
    return name[:max_length]

def test_strategy_commission():
    """测试所有策略+仓位管理组合的手续费情况，并增加3m/500数据的回溯结果"""

    # 策略列表
    strategies = [
        ('ma_cross', Strategy.ma_cross),
        ('rsi_signal', Strategy.rsi_signal),
        ('bollinger_breakout', Strategy.bollinger_breakout),
        ('macd_cross', Strategy.macd_cross),
        ('momentum', Strategy.momentum),
        ('mean_reversion', Strategy.mean_reversion),
        ('breakout', Strategy.breakout),
        ('turtle', Strategy.turtle),
        ('kdj_signal', Strategy.kdj_signal),
        ('kama_cross', Strategy.kama_cross)
    ]

    # 仓位管理器
    position_managers = [
        ('固定比例', FixedRatioPositionManager()),
        ('全仓', AllInPositionManager()),
        ('金字塔', PyramidAllPositionManager())
    ]

    # 回测参数设置
    backtest_settings = [
        {
            "desc": "3m/500/ETH",
            "symbol": "ETH/USDT",
            "timeframe": "15m",
            "limit": 1000
        },
        {
            "desc": "3m/500/BTC",
            "symbol": "BTC/USDT",
            "timeframe": "15m",
            "limit": 1000
        }
    ]

    all_results = []

    for setting in backtest_settings:
        # 不打印每次买入卖出，仅打印最终结果
        # 数据获取
        data_loader = DataLoader()
        ohlcv = data_loader.fetch_ohlcv(setting['symbol'], setting['timeframe'], setting['limit'])
        df = data_loader.to_dataframe(ohlcv)

        results = []

        for strategy_name, strategy_func in strategies:
            for pm_name, position_manager in position_managers:
                try:
                    # 生成信号
                    signals = strategy_func(df)

                    # 回测
                    backtester = Backtester(strategy_func, position_manager=position_manager)
                    backtester.run(df, initial_capital=10000, commission=0.001)  # 0.1%手续费
                    stats = backtester.stats()

                    # 记录结果（以“策略+仓位管理”作为唯一组合）
                    result = {
                        '数据集': setting['desc'],
                        '策略+仓位管理': f"{strategy_name}+{pm_name}",
                        '策略': strategy_name,
                        '仓位管理': pm_name,
                        '总交易次数': stats['total_trades'],
                        '总手续费': stats['total_commission'],
                        '手续费率': stats['commission_rate'],
                        '总收益率': stats['total_return'],
                        '净收益率': stats['total_return'] - stats['commission_rate'],
                        '胜率': stats['win_rate']
                    }
                    results.append(result)

                    print(f"{strategy_name}+{pm_name}: 交易{stats['total_trades']}次, "
                          f"手续费${stats['total_commission']:.2f} ({stats['commission_rate']:.2%}), "
                          f"净收益{stats['total_return'] - stats['commission_rate']:.2%}")

                except Exception as e:
                    # 只打印错误信息
                    print(f"{strategy_name}+{pm_name}: 错误 - {e}")

        # 生成汇总报告
        df_results = pd.DataFrame(results)
        all_results.append(df_results)

        # 只打印最终汇总结果
        print(f"\n📊 手续费汇总报告（数据集：{setting['desc']}）")
        print("=" * 80)

        # 按“策略+仓位管理”组合汇总
        combo_summary = df_results.groupby('策略+仓位管理').agg({
            '总交易次数': 'mean',
            '总手续费': 'mean',
            '手续费率': 'mean',
            '净收益率': 'mean'
        }).round(4)

        print("\n按策略+仓位管理组合汇总:")
        print(combo_summary)

        # 保存到Excel（每个数据集单独sheet）
        excel_filename = 'commission_analysis.xlsx'
        # 替换sheet名中的非法字符
        safe_desc = safe_sheet_name(setting['desc'])
        with pd.ExcelWriter(excel_filename, mode='a' if setting != backtest_settings[0] else 'w', engine='openpyxl') as writer:
            df_results.to_excel(writer, sheet_name=safe_desc, index=False)
        print(f"\n✅ 详细结果已保存到 {excel_filename}（Sheet: {safe_desc}）")

    # 合并所有结果返回
    final_df = pd.concat(all_results, ignore_index=True)
    return final_df

if __name__ == '__main__':
    test_strategy_commission()