import time
import pandas as pd
from datetime import datetime, timedelta
from modules.data import DataLoader
from modules.strategy import Strategy
from modules.trader import Trader, OrderSide, OrderType
from modules.position_manager import FixedRatioPositionManager
from modules.database import DatabaseManager
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LiveTrader:
    """实时交易执行器"""
    
    def __init__(self, symbol: str = 'BTC/USDT', strategy_func=None, 
                 initial_capital: float = 10000, test_mode: bool = True, timeframe: str = '1m'):
        self.symbol = symbol
        self.strategy_func = strategy_func
        self.initial_capital = initial_capital
        self.test_mode = test_mode
        self.timeframe = timeframe
        
        # 初始化组件
        self.data_loader = DataLoader()
        self.trader = Trader(test_mode=test_mode)
        self.position_manager = FixedRatioPositionManager()
        self.db_manager = DatabaseManager()
        
        # 交易状态
        self.last_signal = 0
        self.is_running = False
        self.trade_history = []
        
        logger.info(f"实时交易器初始化完成 - 交易对: {symbol}, 测试模式: {test_mode}, K线周期: {timeframe}")
    
    def start(self, interval_seconds: int = 60):
        """开始实时交易"""
        self.is_running = True
        logger.info(f"开始实时交易 - 检查间隔: {interval_seconds}秒")
        
        try:
            while self.is_running:
                self._check_and_execute_signals()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在停止交易...")
            self.stop()
        except Exception as e:
            logger.error(f"交易过程中发生错误: {e}")
            self.stop()
    
    def stop(self):
        """停止交易"""
        self.is_running = False
        logger.info("交易已停止")
        self._print_final_summary()
    
    def _check_and_execute_signals(self):
        """检查并执行交易信号"""
        try:
            # 获取最新数据
            ohlcv = self.data_loader.fetch_ohlcv(self.symbol, self.timeframe, 100)
            df = self.data_loader.to_dataframe(ohlcv)
            
            if df.empty:
                logger.warning("获取数据失败，跳过本次检查")
                return
            
            # 保存市场数据到数据库
            self.db_manager.save_market_data(df, self.symbol, self.timeframe)
            
            # 生成交易信号
            signals = self.strategy_func(df)
            current_signal = signals.iloc[-1] if len(signals) > 0 else 0
            current_price = df['close'].iloc[-1]
            current_time = df.index[-1]
            
            # 保存交易信号到数据库
            strategy_name = self.strategy_func.__name__
            self.db_manager.save_trading_signal(
                self.symbol, current_time, current_signal, strategy_name, current_price
            )
            
            # 保存策略预测
            predictions = Strategy.predict_next_signals(df, strategy_name)
            self.db_manager.save_strategy_prediction(
                strategy_name, self.symbol, current_time,
                predictions.get('next_buy'), predictions.get('next_sell'),
                current_price, predictions.get('message')
            )
            
            # 检查是否有新信号
            if current_signal != self.last_signal and current_signal != 0:
                self._execute_signal(current_signal, df)
                self.last_signal = current_signal
            
            # 保存账户余额记录
            summary = self.trader.get_account_summary()
            self.db_manager.save_balance_record('USDT', summary['usdt_balance'], current_time)
            
            # 保存持仓记录
            for symbol, position in summary['positions'].items():
                if position.quantity > 0:
                    current_price = self.trader.get_current_price(symbol)
                    unrealized_pnl = (current_price - position.avg_price) * position.quantity
                    self.db_manager.save_position_record(
                        symbol, position.quantity, position.avg_price,
                        unrealized_pnl, position.realized_pnl, position.total_commission,
                        current_time
                    )
            
            # 打印当前状态
            self._print_status(df, current_signal)
            
        except Exception as e:
            logger.error(f"检查信号时发生错误: {e}")
    
    def _execute_signal(self, signal: int, df: pd.DataFrame):
        """执行交易信号"""
        current_price = df['close'].iloc[-1]
        timestamp = df.index[-1]
        
        try:
            if signal == 1:  # 买入信号
                self._execute_buy_signal(current_price, timestamp)
            elif signal == -1:  # 卖出信号
                self._execute_sell_signal(current_price, timestamp)
                
        except Exception as e:
            logger.error(f"执行信号时发生错误: {e}")
    
    def _execute_buy_signal(self, price: float, timestamp):
        """执行买入信号"""
        try:
            # 获取可用资金
            available_capital = self.trader.get_balance('USDT')
            
            # 计算购买数量
            shares, cost = self.position_manager.on_buy_signal(
                available_capital, 0, price, 0.001
            )
            
            if shares > 0 and cost <= available_capital:
                # 下市价单
                order = self.trader.place_market_order(
                    self.symbol, OrderSide.BUY, shares
                )
                
                # 保存交易记录到数据库
                self.db_manager.save_trade_record(
                    order.id, self.symbol, 'buy', 'market',
                    shares, price, cost, order.commission,
                    order.status, timestamp, self.strategy_func.__name__
                )
                
                # 记录交易
                trade_record = {
                    'timestamp': timestamp,
                    'action': 'BUY',
                    'quantity': shares,
                    'price': price,
                    'cost': cost,
                    'order_id': order.id,
                    'status': 'executed'
                }
                self.trade_history.append(trade_record)
                
                logger.info(f"买入信号执行成功: {shares} @ ${price:.2f}")
                
            else:
                logger.warning(f"买入失败: 资金不足或数量过小 (shares={shares}, cost={cost})")
                
        except Exception as e:
            logger.error(f"执行买入信号失败: {e}")
    
    def _execute_sell_signal(self, price: float, timestamp):
        """执行卖出信号"""
        try:
            # 获取当前持仓
            position = self.trader.position_manager.get_position(self.symbol)
            
            if position and position.quantity > 0:
                # 计算卖出数量（全部卖出）
                shares = position.quantity
                
                # 下市价单
                order = self.trader.place_market_order(
                    self.symbol, OrderSide.SELL, shares
                )
                
                # 保存交易记录到数据库
                revenue = shares * price
                self.db_manager.save_trade_record(
                    order.id, self.symbol, 'sell', 'market',
                    shares, price, revenue, order.commission,
                    order.status, timestamp, self.strategy_func.__name__
                )
                
                # 记录交易
                trade_record = {
                    'timestamp': timestamp,
                    'action': 'SELL',
                    'quantity': shares,
                    'price': price,
                    'revenue': revenue,
                    'order_id': order.id,
                    'status': 'executed'
                }
                self.trade_history.append(trade_record)
                
                logger.info(f"卖出信号执行成功: {shares} @ ${price:.2f}")
                
            else:
                logger.warning("卖出失败: 无持仓可卖")
                
        except Exception as e:
            logger.error(f"执行卖出信号失败: {e}")
    
    def _print_status(self, df: pd.DataFrame, current_signal: int):
        """打印当前状态"""
        current_price = df['close'].iloc[-1]
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 获取账户摘要
        summary = self.trader.get_account_summary()
        
        print(f"\n⏰ {current_time}")
        print(f"📊 {self.symbol} 当前价格: ${current_price:.2f}")
        print(f"📈 当前信号: {self._signal_to_text(current_signal)}")
        print(f"💰 总资产: ${summary['total_balance']:.2f}")
        print(f"💵 USDT余额: ${summary['usdt_balance']:.2f}")
        print(f"📦 持仓价值: ${summary['position_value']:.2f}")
        print(f"📊 日盈亏: ${summary['daily_pnl']:.2f}")
        
        # 显示持仓详情
        if summary['positions']:
            for symbol, position in summary['positions'].items():
                if position.quantity > 0:
                    current_price = self.trader.get_current_price(symbol)
                    unrealized_pnl = (current_price - position.avg_price) * position.quantity
                    print(f"  📦 {symbol}: {position.quantity:.6f} @ ${position.avg_price:.2f} "
                          f"(盈亏: ${unrealized_pnl:.2f})")
    
    def _signal_to_text(self, signal: int) -> str:
        """将信号转换为文本"""
        if signal == 1:
            return "🟢 买入信号"
        elif signal == -1:
            return "🔴 卖出信号"
        else:
            return "⚪ 无信号"
    
    def _print_final_summary(self):
        """打印最终摘要"""
        summary = self.trader.get_account_summary()
        
        print("\n" + "="*60)
        print("🎯 交易结束 - 最终摘要")
        print("="*60)
        print(f"初始资金: ${self.initial_capital:.2f}")
        print(f"最终资产: ${summary['total_balance']:.2f}")
        print(f"总盈亏: ${summary['total_balance'] - self.initial_capital:.2f}")
        print(f"总收益率: {((summary['total_balance'] / self.initial_capital) - 1) * 100:.2f}%")
        print(f"总交易次数: {len(self.trade_history)}")
        
        # 显示数据库统计
        db_stats = self.db_manager.get_database_stats()
        print(f"\n📊 数据库统计:")
        print(f"  市场数据记录: {db_stats.get('market_data_count', 0)}")
        print(f"  交易信号记录: {db_stats.get('trading_signals_count', 0)}")
        print(f"  交易记录: {db_stats.get('trade_records_count', 0)}")
        print(f"  持仓记录: {db_stats.get('position_records_count', 0)}")
        
        if self.trade_history:
            print("\n📋 交易记录:")
            for i, trade in enumerate(self.trade_history[-10:], 1):  # 显示最近10笔
                print(f"  {i}. {trade['timestamp']} {trade['action']} "
                      f"{trade['quantity']:.6f} @ ${trade['price']:.2f}")
        
        print("="*60)

def main():
    """主函数"""
    print("🚀 启动实时交易系统")
    print("="*50)
    
    # 配置参数
    symbol = 'ETH/USDT'
    strategy_func = Strategy.mean_reversion  # 可以切换策略
    initial_capital = 10000
    test_mode = True  # 设置为False进行实盘交易
    timeframe = '1m'  # 支持自定义K线周期，如'1m', '5m', '15m', '1h', '4h', '1d'
    check_interval = 60  # 检查间隔（秒），建议与K线周期匹配
    
    # 实盘模式配置
    api_key = None
    api_secret = None
    
    if not test_mode:
        print("⚠️  实盘模式警告：")
        print("   - 将使用真实资金进行交易")
        print("   - 请确保API密钥配置正确")
        print("   - 建议先用小资金测试")
        print()
        
        # 从环境变量或配置文件获取API密钥
        import os
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET')
        
        if not api_key or not api_secret:
            print("❌ 实盘模式需要配置API密钥")
            print("请在环境变量中设置 BINANCE_API_KEY 和 BINANCE_SECRET")
            return
    
    print(f"交易对: {symbol}")
    print(f"策略: {strategy_func.__name__}")
    print(f"初始资金: ${initial_capital}")
    print(f"模式: {'测试模式' if test_mode else '实盘模式'}")
    print(f"K线周期: {timeframe}")
    print(f"检查间隔: {check_interval}秒")
    if not test_mode:
        print(f"API密钥: {'已配置' if api_key else '未配置'}")
    print("="*50)
    
    # 创建实时交易器
    live_trader = LiveTrader(
        symbol=symbol,
        strategy_func=strategy_func,
        initial_capital=initial_capital,
        test_mode=test_mode,
        timeframe=timeframe
    )
    
    # 显示初始账户状态
    live_trader.trader.print_account_summary()
    
    # 开始交易
    try:
        live_trader.start(check_interval)
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断交易")
        live_trader.stop()

if __name__ == "__main__":
    main() 