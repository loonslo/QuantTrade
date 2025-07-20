import pandas as pd
from modules.data import DataLoader
from modules.strategy import Strategy
from modules.backtest import Backtester
from modules.position_manager import FixedRatioPositionManager, AllInPositionManager, PyramidAllPositionManager

def test_strategy_commission():
    """测试所有策略的手续费情况"""
    
    # 数据获取
    data_loader = DataLoader()
    ohlcv = data_loader.fetch_ohlcv('ETH/USDT', '15m', 1000)
    df = data_loader.to_dataframe(ohlcv)
    
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
    
    results = []
    
    print("🔍 测试所有策略的手续费情况...")
    print("=" * 80)
    
    for strategy_name, strategy_func in strategies:
        for pm_name, position_manager in position_managers:
            try:
                # 生成信号
                signals = strategy_func(df)
                
                # 回测
                backtester = Backtester(strategy_func, position_manager=position_manager)
                backtester.run(df, initial_capital=10000, commission=0.001)  # 0.1%手续费
                stats = backtester.stats()
                
                # 记录结果
                result = {
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
                
                print(f"{strategy_name} + {pm_name}: 交易{stats['total_trades']}次, "
                      f"手续费${stats['total_commission']:.2f} ({stats['commission_rate']:.2%}), "
                      f"净收益{stats['total_return'] - stats['commission_rate']:.2%}")
                
            except Exception as e:
                print(f"{strategy_name} + {pm_name}: 错误 - {e}")
    
    # 生成汇总报告
    df_results = pd.DataFrame(results)
    
    print("\n📊 手续费汇总报告")
    print("=" * 80)
    
    # 按策略汇总
    strategy_summary = df_results.groupby('策略').agg({
        '总交易次数': 'mean',
        '总手续费': 'mean',
        '手续费率': 'mean',
        '净收益率': 'mean'
    }).round(4)
    
    print("\n按策略汇总:")
    print(strategy_summary)
    
    # 按仓位管理汇总
    pm_summary = df_results.groupby('仓位管理').agg({
        '总交易次数': 'mean',
        '总手续费': 'mean',
        '手续费率': 'mean',
        '净收益率': 'mean'
    }).round(4)
    
    print("\n按仓位管理汇总:")
    print(pm_summary)
    
    # 保存到Excel
    df_results.to_excel('commission_analysis.xlsx', index=False)
    print(f"\n✅ 详细结果已保存到 commission_analysis.xlsx")
    
    return df_results

if __name__ == '__main__':
    test_strategy_commission() 