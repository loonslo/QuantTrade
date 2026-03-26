import os
import time
import pandas as pd
from datetime import datetime, timedelta
from modules.data import DataLoader
from modules.strategy import Strategy
from modules.trader import Trader, OrderSide, OrderType
from modules.position_manager import FixedRatioPositionManager
from modules.database import DatabaseManager
import logging
from modules.binance_account import BinanceAccount  # 新增

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
                 initial_capital: float = 10000, test_mode: bool = True, timeframe: str = '1m',
                 binance_config: dict = None,
                 stop_loss_pct: float = 0.02, take_profit_pct: float = 0.05):  # 止损2%，止盈5%
        if strategy_func is not None and not callable(strategy_func):
            raise ValueError("strategy_func must be callable")
        self.symbol = symbol
        self.strategy_func = strategy_func
        self.initial_capital = initial_capital
        self.test_mode = test_mode
        self.timeframe = timeframe
        self.binance_config = binance_config
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # 初始化组件
        self.data_loader = DataLoader()
        if self.test_mode:
            self.trader = Trader(test_mode=True)
            self.account = None
        else:
            self.trader = None  # 不再用Trader
            self.account = BinanceAccount(self.binance_config)
        self.position_manager = FixedRatioPositionManager()
        self.db_manager = DatabaseManager()
        
        # 交易状态
        self.last_signal = 0
        self.is_running = False
        self.trade_history = []
        # 持仓信息：用于跟踪入场价和止损价
        self.positions = {}  # {symbol: {'entry_price': float, 'shares': float, 'entry_time': datetime}}
        
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
    
    def _check_stop_loss_take_profit(self, current_price: float):
        """检查是否触发止损或止盈。返回 (stop_loss_triggered, take_profit_triggered)"""
        pos = self.positions.get(self.symbol)
        if not pos:
            return False, False
        entry_price = pos['entry_price']
        stop_loss_price = entry_price * (1 - self.stop_loss_pct)
        take_profit_price = entry_price * (1 + self.take_profit_pct)
        if current_price <= stop_loss_price:
            return True, False
        if current_price >= take_profit_price:
            return False, True
        return False, False
    
    def _check_and_execute_signals(self):
        """检查并执行交易信号"""
        try:
            # 获取最新数据
            ohlcv = self.data_loader.fetch_ohlcv(self.symbol, self.timeframe, 100)
            df = self.data_loader.to_dataframe(ohlcv)
            
            if df.empty:
                logger.warning("获取数据失败，跳过本次检查")
                return
            
            current_price = df['close'].iloc[-1]
            
            # 检查是否触发止损/止盈
            sl_triggered, tp_triggered = self._check_stop_loss_take_profit(current_price)
            if sl_triggered:
                logger.warning(f"触发止损机制！当前价格: ${current_price:.2f}")
                self._execute_sell_signal(current_price, df.index[-1], reason='stop_loss')
                self.last_signal = -1  # 避免重复卖出
                return
            if tp_triggered:
                logger.info(f"触发止盈机制！当前价格: ${current_price:.2f}")
                self._execute_sell_signal(current_price, df.index[-1], reason='take_profit')
                self.last_signal = -1
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
            signal_side = "买入" if signal == 1 else "卖出"
            logger.warning(f"⚠️ 信号确认: {signal_side}信号 @ ${current_price:.2f}，确认执行...")
            
            if signal == 1:  # 买入信号
                self._execute_buy_signal(current_price, timestamp)
            elif signal == -1:  # 卖出信号
                self._execute_sell_signal(current_price, timestamp, reason=None)
                
        except Exception as e:
            logger.error(f"执行信号时发生错误: {e}")
    
    def _execute_buy_signal(self, price: float, timestamp):
        """执行买入信号"""
        try:
            if self.test_mode:
                # 获取可用资金
                available_capital = self.trader.get_balance('USDT')
            else:
                available_capital = self.account.get_balance('USDT')
            # 计算购买数量
            shares, cost = self.position_manager.on_buy_signal(
                available_capital, 0, price, 0.001
            )
            if shares > 0 and cost <= available_capital:
                if self.test_mode:
                    order = self.trader.place_market_order(
                        self.symbol, OrderSide.BUY, shares
                    )
                else:
                    order = self.account.buy(self.symbol, shares)
                # 记录持仓信息（用于止损追踪）
                self.positions[self.symbol] = {
                    'entry_price': price,
                    'shares': shares,
                    'entry_time': timestamp
                }
                # 保存交易记录到数据库
                self.db_manager.save_trade_record(
                    getattr(order, 'id', None), self.symbol, 'buy', 'market',
                    shares, price, cost, getattr(order, 'commission', 0),
                    getattr(order, 'status', 'executed'), timestamp, self.strategy_func.__name__
                )
                # 记录交易
                trade_record = {
                    'timestamp': timestamp,
                    'action': 'BUY',
                    'quantity': shares,
                    'price': price,
                    'cost': cost,
                    'order_id': getattr(order, 'id', None),
                    'status': getattr(order, 'status', 'executed')
                }
                self.trade_history.append(trade_record)
                logger.info(f"买入信号执行成功: {shares} @ ${price:.2f}")
            else:
                logger.warning(f"买入失败: 资金不足或数量过小 (shares={shares}, cost={cost})")
        except Exception as e:
            logger.error(f"执行买入信号失败: {e}")
    
    def _execute_sell_signal(self, price: float, timestamp, reason=None):
        """执行卖出信号"""
        try:
            if self.test_mode:
                position = self.trader.position_manager.get_position(self.symbol)
                shares = position.quantity if position and position.quantity > 0 else 0
            else:
                # 实盘：查询币余额
                shares = self.account.get_balance(self.symbol.split('/')[0])
            if shares > 0:
                if self.test_mode:
                    order = self.trader.place_market_order(
                        self.symbol, OrderSide.SELL, shares
                    )
                else:
                    order = self.account.sell(self.symbol, shares)
                revenue = shares * price
                self.db_manager.save_trade_record(
                    getattr(order, 'id', None), self.symbol, 'sell', 'market',
                    shares, price, revenue, getattr(order, 'commission', 0),
                    getattr(order, 'status', 'executed'), timestamp, self.strategy_func.__name__
                )
                trade_record = {
                    'timestamp': timestamp,
                    'action': 'SELL',
                    'quantity': shares,
                    'price': price,
                    'revenue': revenue,
                    'order_id': getattr(order, 'id', None),
                    'status': getattr(order, 'status', 'executed'),
                    'reason': reason or 'signal'
                }
                self.trade_history.append(trade_record)
                # 清除持仓记录
                self.positions.pop(self.symbol, None)
                reason_text = f"（{reason}）" if reason else ""
                logger.info(f"卖出信号执行成功{reason_text}: {shares} @ ${price:.2f}")
            else:
                logger.warning("卖出失败: 无持仓可卖")
        except Exception as e:
            logger.error(f"执行卖出信号失败: {e}")
    
    def _print_status(self, df: pd.DataFrame, current_signal: int):
        """打印当前状态"""
        current_price = df['close'].iloc[-1]
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⏰ {current_time}")
        print(f"📊 {self.symbol} 当前价格: ${current_price:.2f}")
        print(f"📈 当前信号: {self._signal_to_text(current_signal)}")
        if self.test_mode:
            # 模拟账户打印
            summary = self.trader.get_account_summary()
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
        else:
            # 实盘账户打印
            usdt_balance = self.account.get_balance('USDT')
            coin = self.symbol.split('/')[0]
            coin_balance = self.account.get_balance(coin)
            print(f"💵 实盘USDT余额: ${usdt_balance}")
            print(f"📦 实盘{coin}持仓: {coin_balance}")
            # 可选：查询当前市值
            print(f"📦 持仓市值: ${coin_balance * current_price:.2f}")

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
        print("\n" + "="*60)
        print("🎯 交易结束 - 最终摘要")
        print("="*60)
        print(f"初始资金: ${self.initial_capital:.2f}")
        if self.test_mode:
            summary = self.trader.get_account_summary()
            print(f"最终资产: ${summary['total_balance']:.2f}")
            print(f"总盈亏: ${summary['total_balance'] - self.initial_capital:.2f}")
            print(f"总收益率: {((summary['total_balance'] / self.initial_capital) - 1) * 100:.2f}%")
        else:
            usdt_balance = self.account.get_balance('USDT')
            coin = self.symbol.split('/')[0]
            coin_balance = self.account.get_balance(coin)
            current_price = self.account.exchange.fetch_ticker(self.symbol)['last']
            total_balance = usdt_balance + coin_balance * current_price
            print(f"最终资产: ${total_balance:.2f}")
            print(f"总盈亏: ${total_balance - self.initial_capital:.2f}")
            print(f"总收益率: {((total_balance / self.initial_capital) - 1) * 100:.2f}%")
            print(f"USDT余额: ${usdt_balance}")
            print(f"{coin}持仓: {coin_balance}")
            print(f"当前价格: ${current_price}")
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

def _validate_binance_config(api_key: str = None, api_secret: str = None):
    """验证 Binance 配置是否完整"""
    if not api_key or not api_secret:
        print("❌ 实盘模式需要配置API密钥")
        print("请在环境变量中设置 BINANCE_API_KEY 和 BINANCE_SECRET")
        return False
    return True


def main():
    """主函数"""
    print("🚀 启动实时交易系统")
    print("="*50)
    
    # 配置参数
    symbol = 'ETH/USDT'
    strategy_func = Strategy.mean_reversion  # 可以切换策略
    initial_capital = 10000
    test_mode = True  # 设置为False进行实盘交易
    timeframe = '5m'  # 支持自定义K线周期，如'1m', '5m', '15m', '1h', '4h', '1d'
    check_interval = 60  # 检查间隔（秒），建议与K线周期匹配
    stop_loss_pct = 0.02  # 止损比例（2%）
    take_profit_pct = 0.05  # 止盈比例（5%）

    # 实盘模式配置
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET')
    binance_config = {
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'},
    }

    if not test_mode:
        if not _validate_binance_config(api_key, api_secret):
            return
        # 查询实盘USDT余额作为初始资金
        account = BinanceAccount(binance_config)
        usdt_balance = account.get_balance('USDT')
        print(f"当前USDT余额: {usdt_balance}")
        initial_capital = usdt_balance
    
    # 创建实时交易器
    live_trader = LiveTrader(
        symbol=symbol,
        strategy_func=strategy_func,
        initial_capital=initial_capital,
        test_mode=test_mode,
        timeframe=timeframe,
        binance_config=binance_config if not test_mode else None,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct
    )
    
    # 显示初始账户状态（仅测试模式）
    if test_mode:
        live_trader.trader.print_account_summary()
    
    if not test_mode:
        print("⚠️  实盘模式警告：")
        print("   - 将使用真实资金进行交易")
        print("   - 请确保API密钥配置正确")
        print("   - 建议先用小资金测试")
        print()
    
    print(f"交易对: {symbol}")
    print(f"策略: {strategy_func.__name__}")
    print(f"初始资金: ${initial_capital}")
    print(f"模式: {'测试模式' if test_mode else '实盘模式'}")
    print(f"K线周期: {timeframe}")
    print(f"检查间隔: {check_interval}秒")
    print(f"止损比例: {stop_loss_pct*100}%")
    print(f"止盈比例: {take_profit_pct*100}%")
    print("="*50)
    
    # 开始交易
    try:
        live_trader.start(check_interval)
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断交易")
        live_trader.stop()

if __name__ == "__main__":
    main() 