import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = 'quanttrade.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库，创建必要的表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 市场数据表 - 修改唯一约束，允许不同币种在同一时间戳
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    timeframe TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp, timeframe)
                )
            ''')
            
            # 2. 交易信号表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    signal INTEGER NOT NULL,  -- 1: 买入, -1: 卖出, 0: 无信号
                    strategy_name TEXT NOT NULL,
                    strategy_params TEXT,  -- JSON格式存储策略参数
                    price REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 3. 交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,  -- 'buy' or 'sell'
                    order_type TEXT NOT NULL,  -- 'market' or 'limit'
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    cost REAL NOT NULL,
                    commission REAL NOT NULL,
                    status TEXT NOT NULL,  -- 'pending', 'filled', 'cancelled'
                    timestamp DATETIME NOT NULL,
                    filled_at DATETIME,
                    strategy_name TEXT,
                    signal_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (signal_id) REFERENCES trading_signals (id)
                )
            ''')
            
            # 4. 持仓记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS position_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    unrealized_pnl REAL DEFAULT 0,
                    realized_pnl REAL DEFAULT 0,
                    total_commission REAL DEFAULT 0,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 5. 回测结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    initial_capital REAL NOT NULL,
                    final_capital REAL NOT NULL,
                    total_return REAL NOT NULL,
                    annual_return REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    win_rate REAL NOT NULL,
                    avg_win REAL NOT NULL,
                    avg_loss REAL NOT NULL,
                    profit_factor REAL NOT NULL,
                    total_days INTEGER NOT NULL,
                    total_commission REAL NOT NULL,
                    commission_rate REAL NOT NULL,
                    net_return REAL NOT NULL,
                    position_manager TEXT,
                    parameters TEXT,  -- JSON格式存储策略参数
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 6. 账户余额记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS balance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT NOT NULL,
                    balance REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 7. 策略预测表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    next_buy_price REAL,
                    next_sell_price REAL,
                    current_price REAL NOT NULL,
                    prediction_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time ON market_data(symbol, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON trading_signals(symbol, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trade_records(symbol, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_symbol_time ON position_records(symbol, timestamp)')
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def save_market_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """保存市场数据"""
        with sqlite3.connect(self.db_path) as conn:
            # 准备数据
            df_to_save = df.reset_index().copy()
            df_to_save['symbol'] = symbol
            df_to_save['timeframe'] = timeframe
            
            # 重命名列以匹配数据库结构
            df_to_save = df_to_save.rename(columns={
                'datetime': 'timestamp',
                'date': 'timestamp'
            })
            
            # 确保时间戳列是datetime类型
            if 'timestamp' in df_to_save.columns:
                df_to_save['timestamp'] = pd.to_datetime(df_to_save['timestamp'])
            
            # 选择需要的列并确保数据类型正确
            required_columns = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'timeframe']
            df_to_save = df_to_save[required_columns].copy()
            
            # 确保数值列是float类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df_to_save[col] = pd.to_numeric(df_to_save[col], errors='coerce')
            
            # 删除包含NaN的行
            df_to_save = df_to_save.dropna()
            
            if not df_to_save.empty:
                # 使用INSERT OR REPLACE来处理重复数据（同一币种同一时间戳）
                cursor = conn.cursor()
                for _, row in df_to_save.iterrows():
                    # 转换时间戳类型
                    timestamp = row['timestamp']
                    if hasattr(timestamp, 'to_pydatetime'):
                        timestamp = timestamp.to_pydatetime()
                    elif isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO market_data 
                        (symbol, timestamp, open, high, low, close, volume, timeframe)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['symbol'], timestamp, row['open'], row['high'],
                        row['low'], row['close'], row['volume'], row['timeframe']
                    ))
                
                conn.commit()
                logger.info(f"保存了 {len(df_to_save)} 条市场数据记录")
            else:
                logger.warning("没有有效的市场数据需要保存")
    
    def save_trading_signal(self, symbol: str, timestamp, signal: int, 
                           strategy_name: str, price: float, strategy_params: Dict = None):
        """保存交易信号"""
        # 转换时间戳类型
        if hasattr(timestamp, 'to_pydatetime'):
            timestamp = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO trading_signals 
                (symbol, timestamp, signal, strategy_name, strategy_params, price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                timestamp,
                signal,
                strategy_name,
                json.dumps(strategy_params) if strategy_params else None,
                price
            ))
            conn.commit()
            logger.info(f"保存交易信号: {symbol} {timestamp} {signal}")
    
    def save_trade_record(self, order_id: str, symbol: str, side: str, order_type: str,
                         quantity: float, price: float, cost: float, commission: float,
                         status: str, timestamp, strategy_name: str = None,
                         signal_id: int = None):
        """保存交易记录"""
        # 转换时间戳类型
        if hasattr(timestamp, 'to_pydatetime'):
            timestamp = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trade_records 
                (order_id, symbol, side, order_type, quantity, price, cost, commission, 
                 status, timestamp, strategy_name, signal_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_id, symbol, side, order_type, quantity, price, cost, commission,
                status, timestamp, strategy_name, signal_id
            ))
            conn.commit()
            logger.info(f"保存交易记录: {order_id} {symbol} {side}")
    
    def save_position_record(self, symbol: str, quantity: float, avg_price: float,
                           unrealized_pnl: float, realized_pnl: float, total_commission: float,
                           timestamp):
        """保存持仓记录"""
        # 转换时间戳类型
        if hasattr(timestamp, 'to_pydatetime'):
            timestamp = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO position_records 
                (symbol, quantity, avg_price, unrealized_pnl, realized_pnl, total_commission, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, quantity, avg_price, unrealized_pnl, realized_pnl, total_commission, timestamp))
            conn.commit()
    
    def save_backtest_result(self, result: Dict):
        """保存回测结果"""
        # 转换时间戳类型
        for time_key in ['start_time', 'end_time']:
            if time_key in result and result[time_key]:
                if hasattr(result[time_key], 'to_pydatetime'):
                    result[time_key] = result[time_key].to_pydatetime()
                elif isinstance(result[time_key], str):
                    result[time_key] = datetime.fromisoformat(result[time_key].replace('Z', '+00:00'))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO backtest_results 
                (strategy_name, symbol, start_time, end_time, initial_capital, final_capital,
                 total_return, annual_return, sharpe_ratio, max_drawdown, total_trades,
                 win_rate, avg_win, avg_loss, profit_factor, total_days, total_commission,
                 commission_rate, net_return, position_manager, parameters)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.get('strategy_name'),
                result.get('symbol'),
                result.get('start_time'),
                result.get('end_time'),
                result.get('initial_capital'),
                result.get('final_capital'),
                result.get('total_return'),
                result.get('annual_return'),
                result.get('sharpe_ratio'),
                result.get('max_drawdown'),
                result.get('total_trades'),
                result.get('win_rate'),
                result.get('avg_win'),
                result.get('avg_loss'),
                result.get('profit_factor'),
                result.get('total_days'),
                result.get('total_commission'),
                result.get('commission_rate'),
                result.get('net_return'),
                result.get('position_manager'),
                json.dumps(result.get('parameters', {}))
            ))
            conn.commit()
            logger.info(f"保存回测结果: {result.get('strategy_name')}")
    
    def save_balance_record(self, currency: str, balance: float, timestamp):
        """保存余额记录"""
        # 转换时间戳类型
        if hasattr(timestamp, 'to_pydatetime'):
            timestamp = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO balance_records (currency, balance, timestamp)
                VALUES (?, ?, ?)
            ''', (currency, balance, timestamp))
            conn.commit()
    
    def save_strategy_prediction(self, strategy_name: str, symbol: str, timestamp,
                               next_buy_price: float = None, next_sell_price: float = None,
                               current_price: float = None, prediction_message: str = None):
        """保存策略预测"""
        # 转换时间戳类型
        if hasattr(timestamp, 'to_pydatetime'):
            timestamp = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO strategy_predictions 
                (strategy_name, symbol, timestamp, next_buy_price, next_sell_price, 
                 current_price, prediction_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (strategy_name, symbol, timestamp, next_buy_price, next_sell_price,
                  current_price, prediction_message))
            conn.commit()
    
    def get_market_data(self, symbol: str, start_time: datetime = None, 
                       end_time: datetime = None, timeframe: str = None, limit: int = None) -> pd.DataFrame:
        """获取市场数据"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM market_data WHERE symbol = ?"
            params = [symbol]
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if timeframe:
                query += " AND timeframe = ?"
                params.append(timeframe)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                df = df.sort_index()
            
            return df
    
    def get_trading_signals(self, symbol: str, start_time: datetime = None, 
                           end_time: datetime = None, strategy_name: str = None) -> pd.DataFrame:
        """获取交易信号"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM trading_signals WHERE symbol = ?"
            params = [symbol]
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if strategy_name:
                query += " AND strategy_name = ?"
                params.append(strategy_name)
            
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                df = df.sort_index()
            
            return df
    
    def get_trade_records(self, symbol: str = None, start_time: datetime = None, 
                         end_time: datetime = None) -> pd.DataFrame:
        """获取交易记录"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM trade_records WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                df = df.sort_index()
            
            return df
    
    def get_backtest_results(self, strategy_name: str = None, symbol: str = None) -> pd.DataFrame:
        """获取回测结果"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM backtest_results WHERE 1=1"
            params = []
            
            if strategy_name:
                query += " AND strategy_name = ?"
                params.append(strategy_name)
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            query += " ORDER BY created_at DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['start_time'] = pd.to_datetime(df['start_time'])
                df['end_time'] = pd.to_datetime(df['end_time'])
            
            return df
    
    def get_strategy_performance_summary(self) -> pd.DataFrame:
        """获取策略性能摘要"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT 
                    strategy_name,
                    symbol,
                    COUNT(*) as backtest_count,
                    AVG(total_return) as avg_return,
                    AVG(sharpe_ratio) as avg_sharpe,
                    AVG(max_drawdown) as avg_drawdown,
                    AVG(win_rate) as avg_win_rate,
                    AVG(total_commission) as avg_commission,
                    MAX(created_at) as last_test
                FROM backtest_results 
                GROUP BY strategy_name, symbol
                ORDER BY avg_return DESC
            '''
            
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                df['last_test'] = pd.to_datetime(df['last_test'])
            
            return df
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理市场数据
            cursor.execute('DELETE FROM market_data WHERE timestamp < ?', (cutoff_date,))
            market_deleted = cursor.rowcount
            
            # 清理信号数据
            cursor.execute('DELETE FROM trading_signals WHERE timestamp < ?', (cutoff_date,))
            signals_deleted = cursor.rowcount
            
            # 清理余额记录
            cursor.execute('DELETE FROM balance_records WHERE timestamp < ?', (cutoff_date,))
            balance_deleted = cursor.rowcount
            
            conn.commit()
            
            logger.info(f"清理了 {market_deleted} 条市场数据, {signals_deleted} 条信号数据, {balance_deleted} 条余额记录")
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 各表记录数
            tables = ['market_data', 'trading_signals', 'trade_records', 
                     'position_records', 'backtest_results', 'balance_records', 'strategy_predictions']
            
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # 数据时间范围
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM market_data')
            time_range = cursor.fetchone()
            if time_range[0]:
                stats['data_start'] = time_range[0]
                stats['data_end'] = time_range[1]
            
            return stats 