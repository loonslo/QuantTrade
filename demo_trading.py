#!/usr/bin/env python3
"""
实际交易演示脚本
展示如何使用交易器进行模拟交易
"""

from modules.trader import Trader, OrderSide, OrderType
from modules.strategy import Strategy
from modules.data import DataLoader
import pandas as pd

def demo_basic_trading():
    """基础交易演示"""
    print("🎯 基础交易演示")
    print("="*50)
    
    # 创建交易器（测试模式）
    trader = Trader(test_mode=True)
    
    # 显示初始账户状态
    print("📊 初始账户状态:")
    trader.print_account_summary()
    
    # 模拟买入BTC
    print("\n🟢 执行买入操作:")
    try:
        order = trader.place_market_order('BTC/USDT', OrderSide.BUY, 0.001)
        print(f"✅ 买入成功: 订单ID {order.id}")
    except Exception as e:
        print(f"❌ 买入失败: {e}")
    
    # 显示交易后状态
    print("\n📊 交易后账户状态:")
    trader.print_account_summary()
    
    # 模拟卖出BTC
    print("\n🔴 执行卖出操作:")
    try:
        order = trader.place_market_order('BTC/USDT', OrderSide.SELL, 0.001)
        print(f"✅ 卖出成功: 订单ID {order.id}")
    except Exception as e:
        print(f"❌ 卖出失败: {e}")
    
    # 显示最终状态
    print("\n📊 最终账户状态:")
    trader.print_account_summary()

def demo_strategy_trading():
    """策略交易演示"""
    print("\n🎯 策略交易演示")
    print("="*50)
    
    # 获取历史数据
    data_loader = DataLoader()
    ohlcv = data_loader.fetch_ohlcv('BTC/USDT', '1h', 100)
    df = data_loader.to_dataframe(ohlcv)
    
    # 生成交易信号
    strategy_func = Strategy.mean_reversion
    signals = strategy_func(df)
    
    print(f"📈 生成 {len(signals[signals != 0])} 个交易信号")
    
    # 创建交易器
    trader = Trader(test_mode=True)
    
    # 执行信号交易
    for timestamp, signal in signals[signals != 0].items():
        if timestamp in df.index:
            price = df.loc[timestamp, 'close']
            action = "买入" if signal == 1 else "卖出"
            
            print(f"\n📊 {timestamp}: {action}信号 @ ${price:.2f}")
            
            try:
                if signal == 1:  # 买入
                    order = trader.place_market_order('BTC/USDT', OrderSide.BUY, 0.001)
                    print(f"✅ 买入成功: 0.001 BTC")
                else:  # 卖出
                    order = trader.place_market_order('BTC/USDT', OrderSide.SELL, 0.001)
                    print(f"✅ 卖出成功: 0.001 BTC")
            except Exception as e:
                print(f"❌ 交易失败: {e}")
    
    # 显示最终状态
    print("\n📊 策略交易后账户状态:")
    trader.print_account_summary()

def demo_risk_management():
    """风险管理演示"""
    print("\n🎯 风险管理演示")
    print("="*50)
    
    # 创建交易器（设置严格的风险参数）
    trader = Trader(test_mode=True)
    
    # 尝试大额交易（应该被风险控制阻止）
    print("🛡️ 测试风险控制:")
    try:
        # 尝试买入超过账户余额的金额
        order = trader.place_market_order('BTC/USDT', OrderSide.BUY, 1.0)  # 1 BTC
        print("❌ 风险控制失败")
    except ValueError as e:
        print(f"✅ 风险控制生效: {e}")
    
    # 尝试正常交易
    print("\n🟢 正常交易:")
    try:
        order = trader.place_market_order('BTC/USDT', OrderSide.BUY, 0.001)
        print("✅ 正常交易成功")
    except Exception as e:
        print(f"❌ 正常交易失败: {e}")

def demo_order_types():
    """订单类型演示"""
    print("\n🎯 订单类型演示")
    print("="*50)
    
    trader = Trader(test_mode=True)
    
    # 市价单
    print("📋 市价单:")
    try:
        order = trader.place_market_order('BTC/USDT', OrderSide.BUY, 0.001)
        print(f"✅ 市价单成功: {order.id}")
    except Exception as e:
        print(f"❌ 市价单失败: {e}")
    
    # 限价单
    print("\n📋 限价单:")
    try:
        order = trader.place_limit_order('BTC/USDT', OrderSide.SELL, 0.001, 50000)
        print(f"✅ 限价单成功: {order.id}")
    except Exception as e:
        print(f"❌ 限价单失败: {e}")
    
    # 取消订单
    print("\n📋 取消订单:")
    pending_orders = trader.order_manager.get_pending_orders()
    if pending_orders:
        order = pending_orders[0]
        success = trader.cancel_order(order.id)
        if success:
            print(f"✅ 订单取消成功: {order.id}")
        else:
            print(f"❌ 订单取消失败: {order.id}")
    else:
        print("ℹ️ 无待取消订单")

def demo_position_tracking():
    """持仓跟踪演示"""
    print("\n🎯 持仓跟踪演示")
    print("="*50)
    
    trader = Trader(test_mode=True)
    
    # 买入多个币种
    print("🟢 买入多个币种:")
    symbols = ['BTC/USDT', 'ETH/USDT']
    
    for symbol in symbols:
        try:
            order = trader.place_market_order(symbol, OrderSide.BUY, 0.001)
            print(f"✅ {symbol} 买入成功")
        except Exception as e:
            print(f"❌ {symbol} 买入失败: {e}")
    
    # 显示所有持仓
    print("\n📊 当前持仓:")
    positions = trader.position_manager.get_all_positions()
    for symbol, position in positions.items():
        if position.quantity > 0:
            current_price = trader.get_current_price(symbol)
            unrealized_pnl = (current_price - position.avg_price) * position.quantity
            print(f"  📦 {symbol}: {position.quantity:.6f} @ ${position.avg_price:.2f}")
            print(f"     当前价格: ${current_price:.2f}, 未实现盈亏: ${unrealized_pnl:.2f}")

def main():
    """主演示函数"""
    print("🚀 实际交易功能演示")
    print("="*60)
    
    # 运行各种演示
    demo_basic_trading()
    demo_strategy_trading()
    demo_risk_management()
    demo_order_types()
    demo_position_tracking()
    
    print("\n🎉 演示完成！")
    print("💡 提示:")
    print("  - 这是测试模式，不会进行真实交易")
    print("  - 可以修改 test_mode=False 进行实盘交易")
    print("  - 请确保API密钥配置正确")
    print("  - 建议先用小资金测试")

if __name__ == "__main__":
    main() 