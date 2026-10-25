"""
币安数据提供者
提供币安交易所的数据访问、交易操作和文件处理功能
"""
import pandas as pd
import time
import asyncio
import json
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from functools import lru_cache
import requests
from utils.core.logger_manager import get_logger
from utils import ConfigConstants
from utils.validation.exceptions import DataException
from core.data_provider import BaseDataProvider, DataProviderMixin
from data.storage.sqlite_storage import SQLiteStorage
# 移除数据缓存依赖，直接使用数据库


class BinanceDataProvider(BaseDataProvider, DataProviderMixin):
    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None,
                 proxies: Optional[Dict[str, str]] = None, data_dir: str = "data",
                 use_private_api: bool = False, testnet: bool = False,
                 enable_cache: bool = True, max_retries: int = ConfigConstants.MAX_RETRIES, 
                 retry_delay: float = ConfigConstants.RETRY_DELAY, timeout: int = ConfigConstants.API_TIMEOUT * 1000,
                 enable_futures: bool = False):
        """
        初始化 - 只使用ccxt
        
        Args:
            api_key: API密钥
            secret: API密钥
            proxies: 代理配置
            data_dir: 数据目录
            use_private_api: 是否使用私有API
            testnet: 是否使用测试网
            enable_cache: 是否启用缓存
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 请求超时时间（毫秒）
            enable_futures: 是否启用期货/合约数据支持
        """
        super().__init__()
        self.logger = get_logger('binance_provider')
        self.api_key = api_key or None
        self.secret = secret or None
        
        # 如果没有传入代理配置，尝试从配置文件加载
        if proxies is None:
            self.proxies = self._load_proxy_config()
        else:
            self.proxies = proxies
        self.data_dir = data_dir
        self.use_private_api = use_private_api
        self.testnet = testnet
        self.enable_cache = enable_cache
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.enable_futures = enable_futures
        
        # 缓存配置
        self._market_cap_cache = None
        self._last_cache_update = 0
        self.CACHE_TIMEOUT = 3600  # 1小时缓存
        
        # 连接池和重试配置
        self._connection_pool = {}
        self._last_request_time = 0
        self._rate_limit_delay = 0.1  # 100ms间隔
        
        # 期货交易所实例
        self.futures_exchange = None
        
        self._init_exchange()

    # 统一的核心接口实现（仅保留新架构版本）
    def get_ohlcv(self, symbol: str, timeframe: str = '1m',
                  start_time: Optional[Union[int, float, datetime]] = None,
                  end_time: Optional[Union[int, float, datetime]] = None,
                  limit: Optional[int] = None,
                  save_to_db: bool = False, overwrite: bool = False) -> pd.DataFrame:
        """
        获取OHLCV数据（统一实现）
        - timeframe: 与ccxt一致，如 '1m','1h','1d'...
        - start_time/end_time: 支持毫秒级Unix时间戳(int/float)或datetime；内部会统一转换
        - 返回: index为datetime（Asia/Shanghai，无tz），列包含 ['symbol','open','high','low','close','volume']
        """
        return self._retry_operation(
            lambda: self._get_ohlcv_internal(symbol, timeframe, start_time, end_time, limit, save_to_db, overwrite),
            f"获取 {symbol} {timeframe} 数据"
        )

    def _get_ohlcv_internal(self, symbol: str, timeframe: str = '1m',
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           limit: Optional[int] = None,
                           save_to_db: bool = False, overwrite: bool = False) -> pd.DataFrame:
        """
        内部OHLCV数据获取方法
        """
        try:
            self.logger.info(f"获取 {symbol} {timeframe} 数据")
            ccxt_timeframe = self._convert_timeframe(timeframe)

            # 估算limit（如未给定）
            if limit is None:
                if start_time and end_time and isinstance(start_time, datetime) and isinstance(end_time, datetime):
                    time_diff = end_time - start_time
                    seconds = max(1, time_diff.total_seconds())
                    unit_seconds = {
                        '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
                        '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '8h': 28800,
                        '12h': 43200, '1d': 86400, '3d': 259200, '1w': 604800, '1M': 2592000
                    }.get(timeframe, 60)
                    limit = min(int(seconds / unit_seconds) + 10, 1000)
                else:
                    limit = 500

            # 规范化时间以用于缓存
            dt_start = self._to_datetime(start_time) if start_time else None
            dt_end = self._to_datetime(end_time) if end_time else None

            # 移除缓存逻辑，直接使用数据库存储

            # 调用ccxt
            since = self._ensure_timestamp(start_time) if start_time else None
            ohlcv = self.exchange.fetch_ohlcv(symbol=symbol, timeframe=ccxt_timeframe, since=since, limit=limit)
            if not ohlcv:
                self.logger.warning(f"未获取到 {symbol} 数据")
                return pd.DataFrame()

            df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
            df['symbol'] = symbol
            
            # 获取永续合约数据（如果支持）
            try:
                # 获取最新的持仓量数据
                df = df[["symbol", "datetime", "open", "high", "low", "close", "volume"]]
                # 过滤数据（如果提供了结束时间）
                if dt_end is not None:
                    df = df[df['datetime'] <= dt_end]

            except Exception as e:
                # 期货数据获取失败不影响现货数据
                self.logger.warning(f"期货数据获取失败（不影响现货数据）: {e}")

            # 可选保存
            if save_to_db and not df.empty:
                try:
                    # 直接使用DataFrame，不需要重置索引
                    storage = SQLiteStorage()
                    success = storage.save_market_data(df, symbol, overwrite=overwrite)
                    if success:
                        self.logger.info(f"✅ 数据已保存到数据库: {symbol}")
                    else:
                        self.logger.warning(f"⚠️ 保存数据到数据库失败: {symbol}")
                except Exception as e:
                    self.logger.warning(f"⚠️ 保存数据到数据库失败: {e}")

            self.logger.info(f"获取到 {symbol} 数据: {len(df)} 条")
            return df
        except Exception as e:
            self.logger.error(f"获取 {symbol} 数据失败: {e}")
            raise DataException(f"获取 {symbol} 数据失败: {e}")

    def get_symbols(self) -> List[str]:
        """
        获取可用的交易对列表
        Returns:
            List[str]: 交易对列表
        Raises:
            DataException: 获取失败时抛出
        """
        return self._retry_operation(
            lambda: self._get_symbols_internal(),
            "获取交易对列表"
        )

    def _get_symbols_internal(self) -> List[str]:
        """内部获取交易对列表方法"""
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            self.logger.error(f"获取交易对列表失败: {e}")
            raise DataException(f"获取交易对列表失败: {e}")

    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取市场信息
        Args:
            symbol: 交易对
        Returns:
            Dict[str, Any]: 市场信息
        Raises:
            DataException: 获取失败时抛出
        """
        return self._retry_operation(
            lambda: self._get_market_info_internal(symbol),
            f"获取 {symbol} 市场信息"
        )

    def _get_market_info_internal(self, symbol: str) -> Dict[str, Any]:
        """内部获取市场信息方法"""
        try:
            market = self.exchange.load_markets()[symbol]
            return {
                'symbol': symbol,
                'base_asset': market.get('base'),
                'quote_asset': market.get('quote'),
                'min_qty': market.get('limits', {}).get('amount', {}).get('min', 0),
                'max_qty': market.get('limits', {}).get('amount', {}).get('max', float('inf')),
                'step_size': market.get('precision', {}).get('amount', 0.001),
                'min_notional': market.get('limits', {}).get('cost', {}).get('min', 0),
                'precision': market.get('precision', {}).get('price', 6)
            }
        except Exception as e:
            self.logger.error(f"获取市场信息失败: {e}")
            raise DataException(f"获取市场信息失败: {e}", symbol)

    # ====== 币安专属扩展功能 ======
    def create_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None, order_type: str = 'market') -> Optional[Dict]:
        """
        创建订单
        Args:
            symbol: 交易对
            side: 'buy' or 'sell'
            amount: 下单数量
            price: 限价单需填
            order_type: 'market' or 'limit'
        Returns:
            Dict: 订单信息
        Raises:
            DataException: 下单失败时抛出
        """
        return self._retry_operation(
            lambda: self._create_order_internal(symbol, side, amount, price, order_type),
            f"创建 {symbol} {side} 订单"
        )

    def _create_order_internal(self, symbol: str, side: str, amount: float, price: Optional[float] = None, order_type: str = 'market') -> Optional[Dict]:
        """内部创建订单方法"""
        try:
            if order_type == 'market':
                order = self.exchange.create_market_order(symbol, side, amount)
            else:
                if price is None:
                    raise DataException("限价单必须指定价格", symbol)
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            return order
        except Exception as e:
            self.logger.error(f'下单失败: {e}')
            raise DataException(f'下单失败: {e}', symbol)

    def cancel_all_orders(self, symbol: str) -> bool:
        """
        撤销所有订单
        Args:
            symbol: 交易对
        Returns:
            bool: 是否成功
        """
        return self._retry_operation(
            lambda: self._cancel_all_orders_internal(symbol),
            f"撤销 {symbol} 所有订单"
        )

    def _cancel_all_orders_internal(self, symbol: str) -> bool:
        """内部撤销所有订单方法"""
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            for order in orders:
                self.exchange.cancel_order(order['id'], symbol)
            return True
        except Exception as e:
            self.logger.error(f'撤单失败: {e}')
            return False

    def get_balance(self, asset: Optional[str] = None) -> Dict[str, float]:
        """
        获取余额
        Args:
            asset: 资产名称，None表示获取所有资产
        Returns:
            Dict[str, float]: 余额信息
        """
        return self._retry_operation(
            lambda: self._get_balance_internal(asset),
            f"获取{'所有' if asset is None else asset}余额"
        )

    def _get_balance_internal(self, asset: Optional[str] = None) -> Dict[str, float]:
        """内部获取余额方法"""
        try:
            balance = self.exchange.fetch_balance()
            if asset:
                return {asset: balance['free'].get(asset, 0)}
            return balance['free']
        except Exception as e:
            self.logger.error(f'获取余额失败: {e}')
            return {}

    @lru_cache(maxsize=128)
    def get_top_50_symbols(self, quote_asset: str = 'USDT', use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        获取交易量前50的加密货币
        Args:
            quote_asset: 计价货币
            use_cache: 是否使用缓存
        Returns:
            Dict[str, Dict[str, Any]]: 币种信息
        """
        try:
            import time
            current_time = time.time()
            if use_cache and self._market_cap_cache and (current_time - self._last_cache_update) < self.CACHE_TIMEOUT:
                return self._market_cap_cache
                
            return self._retry_operation(
                lambda: self._get_top_50_symbols_internal(quote_asset, current_time),
                "获取交易量前50币种"
            )
        except Exception as e:
            self.logger.error(f"获取前50币种价格失败: {str(e)}")
            return {}

    def _get_top_50_symbols_internal(self, quote_asset: str, current_time: float) -> Dict[str, Dict[str, Any]]:
        """内部获取前50币种方法"""
        tickers = self.exchange.fetch_tickers()
        markets = self.exchange.load_markets()
        quote_filter = f"/{quote_asset}"
        filtered_tickers = {
            k: v for k, v in tickers.items()
            if k.endswith(quote_filter) and v.get('quoteVolume')
        }
        sorted_tickers = sorted(
            filtered_tickers.values(),
            key=lambda x: float(x['quoteVolume']),
            reverse=True
        )[:50]
        result = {}
        for i, t in enumerate(sorted_tickers):
            symbol = t['symbol'].replace(quote_filter, '')
            market = markets.get(t['symbol'], {})
            price = float(t['last'])
            
            # 计算24小时涨跌幅
            change_24h = t.get('percentage', 0.0)
            if change_24h is None:
                # 如果没有百分比，尝试用 open/close 计算
                if t.get('open') and t.get('close'):
                    change_24h = ((price - float(t['open'])) / float(t['open'])) * 100
                else:
                    change_24h = 0.0
            
            # 计算涨跌金额
            change_amount = (price * change_24h) / 100 if change_24h else 0.0
            
            # 计算市值（使用24小时成交量作为近似）
            volume_24h = float(t.get('quoteVolume', 0))
            # 市值估算：成交量 * 价格（这是一个简化的估算）
            market_cap = volume_24h * price if volume_24h and price else 0.0
            
            # 获取市场精度信息
            precision_info = market.get('precision', {})
            price_precision = precision_info.get('price', 8)
            amount_precision = precision_info.get('amount', 8)
            
            # 确保精度是整数类型
            if isinstance(price_precision, float):
                price_precision = int(price_precision) if price_precision == int(price_precision) else 8
            if isinstance(amount_precision, float):
                amount_precision = int(amount_precision) if amount_precision == int(amount_precision) else 8
                
            # 根据价格大小自动调整显示精度
            if price >= 1000:
                display_precision = max(0, min(2, price_precision))
            elif price >= 100:
                display_precision = max(1, min(3, price_precision))
            elif price >= 10:
                display_precision = max(2, min(4, price_precision))
            elif price >= 1:
                display_precision = max(3, min(5, price_precision))
            elif price >= 0.1:
                display_precision = max(4, min(6, price_precision))
            elif price >= 0.01:
                display_precision = max(5, min(7, price_precision))
            else:
                display_precision = max(6, min(8, price_precision))
            
            result[symbol] = {
                'price': price,
                'change_24h': round(change_24h, 2),
                'change_amount': round(change_amount, 2),
                'volume_24h': volume_24h,
                'market_cap': market_cap,
                'rank': i + 1,  # 添加排名
                'price_precision': int(price_precision),
                'amount_precision': int(amount_precision),
                'display_precision': display_precision,
                'formatted_price': f"{price:.{display_precision}f}"
            }
        self._market_cap_cache = result
        self._last_cache_update = current_time
        return result

    def get_top_20_symbols(self, quote_asset: str = 'USDT', use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        获取交易量前20的加密货币（以24H成交额近似市值排序）
        Args:
            quote_asset: 计价货币
            use_cache: 是否使用缓存
        Returns:
            Dict[str, Dict[str, Any]]: 币种信息
        """
        try:
            all_top = self.get_top_50_symbols(quote_asset=quote_asset, use_cache=use_cache)
            # 只取前20
            return dict(list(all_top.items())[:20])
        except Exception as e:
            self.logger.error(f"获取前20币种价格失败: {str(e)}")
            return {}

    # ====== 工具方法/缓存/代理配置等 ======
    def _init_exchange(self):
        """
        初始化交易所接口
        """
        try:
            exchange_kwargs = {
                'timeout': self.timeout,
                'enableRateLimit': True,
                'proxies': self.proxies,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                }
            }
            if self.proxies:
                self.logger.info(f"🔧 使用代理配置: {self.proxies}")
            else:
                self.logger.info("🔧 未配置代理")
            if self.use_private_api and self.api_key and self.secret:
                exchange_kwargs['apiKey'] = self.api_key
                exchange_kwargs['secret'] = self.secret
            import ccxt
            self.exchange = ccxt.binance(exchange_kwargs)
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
            
            # 打印现货接口地址信息
            self.logger.info("成功创建币安现货交易所连接")
            self.logger.info(f"现货API基础地址: {self.exchange.urls['api']['public']}")
            self.logger.info(f"现货私有API地址: {self.exchange.urls['api']['private']}")
            if self.testnet:
                self.logger.info("当前使用现货测试网模式")
            else:
                self.logger.info("当前使用现货生产网模式")
            
            # 如果启用期货支持，创建期货交易所实例
            if self.enable_futures:
                futures_kwargs = exchange_kwargs.copy()
                futures_kwargs['options']['defaultType'] = 'future'
                self.futures_exchange = ccxt.binance(futures_kwargs)
                if self.testnet:
                    self.futures_exchange.set_sandbox_mode(True)
                
                # 打印期货接口地址信息
                self.logger.info("成功创建币安期货交易所连接")
                self.logger.info(f"期货API基础地址: {self.futures_exchange.urls['api']['fapiPublic']}")
                self.logger.info(f"期货私有API地址: {self.futures_exchange.urls['api']['fapiPrivate']}")
                self.logger.info(f"期货数据API地址: {self.futures_exchange.urls['api']['fapiData']}")
                if self.testnet:
                    self.logger.info("当前使用期货测试网模式")
                else:
                    self.logger.info("当前使用期货生产网模式")
                
        except Exception as e:
            self.logger.error(f"创建币安交易所连接失败: {e}")
            raise DataException(f"无法连接到币安交易所: {e}")

    # ==================== 合约数据获取功能 ====================
    
    def get_open_interest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取永续合约持仓量数据
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
            
        Returns:
            持仓量数据字典
        """
        if not self.enable_futures or not self.futures_exchange:
            self.logger.warning("期货功能未启用，无法获取持仓量数据")
            return None
            
        return self._retry_operation(
            lambda: self._get_open_interest_internal(symbol),
            f"获取 {symbol} 持仓量数据"
        )
    
    def _get_open_interest_internal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """内部获取持仓量方法 - 多个备用策略"""
        try:
            # 防御性校验：期货交易所未初始化
            if not self.enable_futures or not self.futures_exchange:
                self.logger.warning("期货功能未启用或期货交易所未初始化，无法获取持仓量数据")
                return None

            # 规范化交易对格式（支持传入 BTCUSDT / BTC/USDT）
            symbol_norm = symbol
            if '/' not in symbol_norm and isinstance(symbol_norm, str):
                for qa in ['USDT', 'BUSD', 'USDC', 'TUSD']:
                    if symbol_norm.endswith(qa):
                        base = symbol_norm[:-len(qa)]
                        symbol_norm = f"{base}/{qa}"
                        break

            # 策略1: fetch_open_interest（直接获取）
            if self.futures_exchange.has.get('fetchOpenInterest', False):
                try:
                    open_interest = self.futures_exchange.fetch_open_interest(symbol_norm)
                    if open_interest and 'openInterest' in open_interest:
                        self.logger.info(f"策略1成功获取持仓量: {symbol_norm}")
                        return open_interest
                    else:
                        self.logger.warning(f"策略1返回数据无效: {open_interest}")
                except Exception as e1:
                    self.logger.warning(f"策略1 fetch_open_interest失败: {e1}")

            # 策略2: fetch_open_interest_history（获取历史数据，取最新一条）
            if self.futures_exchange.has.get('fetchOpenInterestHistory', False):
                try:
                    history = self.futures_exchange.fetch_open_interest_history(symbol_norm, limit=1)
                    if history and len(history) > 0 and 'openInterest' in history[0]:
                        self.logger.info(f"策略2成功获取持仓量: {symbol_norm}")
                        return history[0]
                    else:
                        self.logger.warning(f"策略2返回数据无效: {history}")
                except Exception as e2:
                    self.logger.warning(f"策略2 fetch_open_interest_history失败: {e2}")

            # 策略3: 尝试从期货 OHLCV 数据中获取（部分交易所可能有持仓量数据）
            try:
                if hasattr(self.futures_exchange, 'fetch_ohlcv'):
                    ohlcv = self.futures_exchange.fetch_ohlcv(symbol_norm, '1m', limit=1)
                    if ohlcv and len(ohlcv) > 0:
                        # 检查是否有持仓量字段（某些交易所的 OHLCV 包含额外信息）
                        last_candle = ohlcv[-1]
                        if len(last_candle) >= 6 and last_candle[5] is not None:
                            self.logger.info(f"策略3从 OHLCV 提取持仓量: {symbol_norm}")
                            return {
                                'symbol': symbol_norm,
                                'openInterest': float(last_candle[5]),
                                'timestamp': int(time.time() * 1000)
                            }
            except Exception as e3:
                self.logger.warning(f"策略3从 OHLCV 获取持仓量失败: {e3}")

            # 策略4: 使用 REST API 直接请求（币安特有）
            if 'binance' in self.futures_exchange.id.lower():
                try:
                    url = f"{self.futures_exchange.urls['api']['future']}/fapi/v1/openInterest"
                    params = {'symbol': symbol.replace('/', '')}  # 币安使用 BTCUSDT 格式
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'openInterest' in data:
                            self.logger.info(f"策略4直接请求 REST API 获取持仓量: {symbol_norm}")
                            return {
                                'symbol': symbol_norm,
                                'openInterest': float(data['openInterest']),
                                'timestamp': data.get('timestamp', int(time.time() * 1000))
                            }
                except Exception as e4:
                    self.logger.warning(f"策略4直接请求 REST API 失败: {e4}")

            self.logger.error(f"所有策略都无法获取持仓量数据: {symbol_norm}")
            return None

        except Exception as e:
            self.logger.error(f"获取持仓量失败: {symbol}, 错误: {e}")
            return None
    
    def get_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取永续合约资金费率数据
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
            
        Returns:
            资金费率数据字典
        """
        if not self.enable_futures or not self.futures_exchange:
            self.logger.warning("期货功能未启用，无法获取资金费率数据")
            return None
            
        return self._retry_operation(
            lambda: self._get_funding_rate_internal(symbol),
            f"获取 {symbol} 资金费率数据"
        )
    
    def _get_funding_rate_internal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """内部获取资金费率方法"""
        try:
            # 防御性校验：期货交易所未初始化
            if not self.enable_futures or not self.futures_exchange:
                self.logger.warning("期货功能未启用或期货交易所未初始化，无法获取资金费率数据")
                return None

            # 规范化交易对格式（支持传入 BTCUSDT / BTC/USDT）
            symbol_norm = symbol
            if '/' not in symbol_norm and isinstance(symbol_norm, str):
                for qa in ['USDT', 'BUSD', 'USDC', 'TUSD']:
                    if symbol_norm.endswith(qa):
                        base = symbol_norm[:-len(qa)]
                        symbol_norm = f"{base}/{qa}"
                        break

            # 只使用fetch_funding_rate获取最新资金费率，不使用历史数据
            if self.futures_exchange.has.get('fetchFundingRate', False):
                try:
                    funding_rate = self.futures_exchange.fetch_funding_rate(symbol_norm)
                    # 确保返回数据包含timestamp字段
                    if funding_rate and 'timestamp' not in funding_rate:
                        if 'fundingTime' in funding_rate:
                            funding_rate['timestamp'] = funding_rate['fundingTime']
                        elif 'time' in funding_rate:
                            funding_rate['timestamp'] = funding_rate['time']
                    self.logger.info(f"成功获取最新资金费率: {symbol_norm}")
                    return funding_rate
                except Exception as e1:
                    self.logger.warning(f"fetch_funding_rate失败: {e1}")
            else:
                self.logger.warning(f"交易所不支持fetchFundingRate方法: {symbol_norm}")

            return None

        except Exception as e:
            self.logger.error(f"获取资金费率失败: {symbol}, 错误: {e}")
            return None
    
    def get_futures_ohlcv(self, symbol: str, timeframe: str = '1m',
                         start_time: Optional[Union[int, float, datetime]] = None,
                         end_time: Optional[Union[int, float, datetime]] = None,
                         limit: Optional[int] = None) -> pd.DataFrame:
        """
        获取期货K线数据（包含合约指标）
        
        Args:
            symbol: 交易对
            timeframe: 时间框架
            start_time: 开始时间
            end_time: 结束时间
            limit: 数据限制
            
        Returns:
            包含合约指标的K线数据DataFrame
        """
        if not self.enable_futures or not self.futures_exchange:
            self.logger.warning("期货功能未启用，无法获取期货K线数据")
            return pd.DataFrame()
            
        return self._retry_operation(
            lambda: self._get_futures_ohlcv_internal(symbol, timeframe, start_time, end_time, limit),
            f"获取 {symbol} 期货K线数据"
        )
    
    def _get_futures_ohlcv_internal(self, symbol: str, timeframe: str = '1m',
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None,
                                   limit: Optional[int] = None) -> pd.DataFrame:
        """内部获取期货K线数据方法"""
        try:
            # 转换时间框架
            ccxt_timeframe = timeframe
            
            # 估算limit
            if limit is None:
                if start_time and end_time and isinstance(start_time, datetime) and isinstance(end_time, datetime):
                    time_diff = end_time - start_time
                    seconds = max(1, time_diff.total_seconds())
                    unit_seconds = {
                        '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
                        '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '8h': 28800,
                        '12h': 43200, '1d': 86400, '3d': 259200, '1w': 604800, '1M': 2592000
                    }.get(timeframe, 60)
                    limit = min(int(seconds / unit_seconds) + 10, 1000)
                else:
                    limit = 500
            
            # 调用期货API
            since = self._ensure_timestamp(start_time) if start_time else None
            ohlcv = self.futures_exchange.fetch_ohlcv(symbol=symbol, timeframe=ccxt_timeframe, since=since, limit=limit)
            
            if not ohlcv:
                self.logger.warning(f"未获取到期货数据: {symbol}")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
            df['symbol'] = symbol
            df = df[['symbol', 'datetime', 'open', 'high', 'low', 'close', 'volume']]
            df.set_index('datetime', inplace=True)
            
            # 过滤时间范围
            if start_time or end_time:
                if start_time:
                    df = df[df.index >= start_time]
                if end_time:
                    df = df[df.index <= end_time]
            
            self.logger.info(f"成功获取期货K线数据: {symbol}, 数据量: {len(df)}")
            return df
            
        except Exception as e:
            self.logger.error(f"获取期货K线数据失败: {symbol}, 错误: {e}")
            return pd.DataFrame()

    def _load_proxy_config(self) -> Optional[Dict[str, str]]:
        """从配置文件加载代理设置"""
        try:
            # 尝试多个可能的配置文件位置
            possible_paths = [
                "config/config.json",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json"),
            ]
            
            config = None
            config_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    config_path = path
                    break
            
            if config is None:
                self.logger.debug(f"配置文件不存在于任何位置")
                return None
            
            # 优先使用 external_apis.binance.proxies，如果没有则使用全局 proxies
            # 注意: binance 配置在 external_apis 下面
            proxies = config.get('external_apis', {}).get('binance', {}).get('proxies')
            if not proxies:
                proxies = config.get('proxies')
            
            # 检查代理配置是否为空
            if not proxies or proxies == {}:
                self.logger.debug("配置文件中未设置代理")
                return None
            
            self.logger.info(f"从配置文件自动加载代理设置: {proxies}")
            return proxies
            
        except Exception as e:
            self.logger.warning(f"自动加载代理配置失败: {e}")
            return None

    def _retry_operation(self, operation, operation_name: str):
        """
        重试操作装饰器
        
        Args:
            operation: 要执行的操作函数
            operation_name: 操作名称（用于日志）
            
        Returns:
            操作结果
            
        Raises:
            DataException: 重试失败后抛出
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # 速率限制控制
                current_time = time.time()
                time_since_last = current_time - self._last_request_time
                if time_since_last < self._rate_limit_delay:
                    time.sleep(self._rate_limit_delay - time_since_last)
                
                result = operation()
                self._last_request_time = time.time()
                return result
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"第 {attempt + 1} 次尝试 {operation_name} 失败: {e}")
                
                if attempt < self.max_retries - 1:
                    # 指数退避重试
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"{operation_name} 重试 {self.max_retries} 次后失败")
                    raise DataException(f"{operation_name} 失败: {e}")
        
        raise DataException(f"{operation_name} 失败: {last_exception}")

    def clear_cache(self):
        """
        清除市值数据缓存
        """
        self._market_cap_cache = None
        self._last_cache_update = 0
        # 清除LRU缓存
        self.get_top_50_symbols.cache_clear()

    def _ensure_timestamp(self, t):
        if isinstance(t, int):
            return t
        elif isinstance(t, float):
            return int(t)
        elif isinstance(t, datetime):
            return self._datetime_to_timestamp(t)
        elif t is None:
            return None
        else:
            raise ValueError(f"Unsupported time type: {type(t)}")

    def _to_datetime(self, t):
        from datetime import datetime
        if isinstance(t, int):
            return datetime.fromtimestamp(t / 1000)
        elif isinstance(t, float):
            return datetime.fromtimestamp(t / 1000)
        elif isinstance(t, datetime):
            return t
        else:
            return None

    # （已上方统一实现）

    # 删除无效的MarketData对象返回，统一直接返回DataFrame

    # ==================== 市场信息功能 ====================

    def get_detailed_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取详细市场信息
        
        Args:
            symbol: 交易对
            
        Returns:
            Dict[str, Any]: 市场信息
        """
        return self._retry_operation(
            lambda: self._get_detailed_market_info_internal(symbol),
            f"获取 {symbol} 详细市场信息"
        )

    def _get_detailed_market_info_internal(self, symbol: str) -> Dict[str, Any]:
        """内部获取详细市场信息方法"""
        try:
            markets = self.exchange.load_markets()
            if symbol in markets:
                market = markets[symbol]
                return {
                    'symbol': symbol,
                    'base_asset': market.get('base'),
                    'quote_asset': market.get('quote'),
                    'min_qty': market.get('limits', {}).get('amount', {}).get('min', 0),
                    'max_qty': market.get('limits', {}).get('amount', {}).get('max', float('inf')),
                    'step_size': market.get('precision', {}).get('amount', 0.001),
                    'min_notional': market.get('limits', {}).get('cost', {}).get('min', 0),
                    'precision': market.get('precision', {}).get('price', 6)
                }
            else:
                return {
                    'symbol': symbol,
                    'base_asset': 'UNKNOWN',
                    'quote_asset': 'UNKNOWN',
                    'min_qty': 0.001,
                    'max_qty': 1000,
                    'step_size': 0.001,
                    'min_notional': 10,
                    'precision': 6
                }

        except Exception as e:
            self.logger.error(f"获取市场信息失败: {e}")
            return {
                'symbol': symbol,
                'base_asset': 'UNKNOWN',
                'quote_asset': 'UNKNOWN',
                'min_qty': 0.001,
                'max_qty': 1000,
                'step_size': 0.001,
                'min_notional': 10,
                'precision': 6
            }

    def get_latest_price(self, symbol: str) -> Optional[dict]:
        """
        获取最新价格和24H涨跌幅
        Returns:
            dict: {"price": float, "change_24h": float}
        """
        return self._retry_operation(
            lambda: self._get_latest_price_internal(symbol),
            f"获取 {symbol} 最新价格"
        )

    def _get_latest_price_internal(self, symbol: str) -> Optional[dict]:
        """内部获取最新价格方法"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            # 涨跌幅百分比，ccxt标准字段为 'percentage' 或 'change'，优先用 'percentage'
            change_24h = ticker.get('percentage')
            if change_24h is None:
                # 若无百分比，尝试用 'change' 字段（绝对值），用 close/open 算百分比
                if ticker.get('open'):
                    change_24h = (price - ticker['open']) / ticker['open'] * 100
                else:
                    change_24h = 0.0
            return {"price": price, "change_24h": change_24h}
        except Exception as e:
            self.logger.error(f"获取 {symbol} 最新价格失败: {e}")
            return None

    def get_24hr_ticker_statistics(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取24小时ticker统计
        
        Returns:
            List[Dict[str, Any]]: 24小时ticker统计列表
        """
        return self._retry_operation(
            lambda: self._get_24hr_ticker_statistics_internal(),
            "获取24小时ticker统计"
        )
    
    def _get_24hr_ticker_statistics_internal(self) -> Optional[List[Dict[str, Any]]]:
        """内部获取24小时ticker统计方法"""
        try:
            tickers = self.exchange.fetch_tickers()
            # 转换为列表格式
            ticker_list = []
            for symbol, ticker_data in tickers.items():
                if ticker_data.get('quoteVolume'):  # 只包含有交易量的交易对
                    ticker_list.append(ticker_data)
            return ticker_list
        except Exception as e:
            self.logger.error(f"获取24小时ticker统计失败: {e}")
            # 降级回退：直接调用Binance公开REST接口 /api/v3/ticker/24hr
            try:
                import requests
                base_url = 'https://api.binance.com'
                url = f"{base_url}/api/v3/ticker/24hr"
                sess = requests.Session()
                adapter = requests.adapters.HTTPAdapter(max_retries=3)
                sess.mount('https://', adapter)
                resp = sess.get(url, timeout=self.timeout / 1000, proxies=self.proxies)
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, list):
                    self.logger.warning("/api/v3/ticker/24hr 返回格式非列表，放弃回退结果")
                    return None
                # 标准化为 ccxt 类似字段名，尽量兼容上游过滤逻辑
                result: List[Dict[str, Any]] = []
                for item in data:
                    try:
                        # Binance 原生返回字段包含：symbol, lastPrice, priceChangePercent, priceChange, volume, quoteVolume 等
                        norm = {
                            'symbol': item.get('symbol'),
                            'last': float(item.get('lastPrice', 0) or 0.0),
                            'percentage': float(item.get('priceChangePercent', 0) or 0.0),
                            'change': float(item.get('priceChange', 0) or 0.0),
                            'baseVolume': float(item.get('volume', 0) or 0.0),
                            'quoteVolume': float(item.get('quoteVolume', 0) or 0.0)
                        }
                        result.append(norm)
                    except Exception:
                        continue
                self.logger.info("已使用 REST 回退获取24小时ticker统计数据")
                return result
            except Exception as e2:
                self.logger.error(f"REST 回退获取24小时ticker统计失败: {e2}")
                return None

    def get_timeframes(self) -> List[str]:
        """
        获取支持的时间周期
        
        Returns:
            List[str]: 时间周期列表
        """
        return self._retry_operation(
            lambda: self._get_timeframes_internal(),
            "获取时间周期列表"
        )

    def _get_timeframes_internal(self) -> List[str]:
        """内部获取时间周期方法"""
        try:
            timeframes = self.exchange.timeframes
            return list(timeframes.keys())
        except Exception as e:
            self.logger.error(f"获取时间周期列表失败: {e}")
            return []

    def get_exchange_info(self) -> Dict[str, Any]:
        """
        获取交易所信息
        
        Returns:
            Dict[str, Any]: 交易所信息
        """
        return self._retry_operation(
            lambda: self._get_exchange_info_internal(),
            "获取交易所信息"
        )

    def _get_exchange_info_internal(self) -> Dict[str, Any]:
        """内部获取交易所信息方法"""
        try:
            info = {
                'name': self.exchange.id,
                'url': self.exchange.urls['www'],
                'timeframes': self.get_timeframes(),
                'symbols': self.get_symbols(),
                'rate_limit': self.exchange.rateLimit,
                'has': self.exchange.has
            }
            return info
        except Exception as e:
            self.logger.error(f"获取交易所信息失败: {e}")
            return {}

    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        获取速率限制信息
        
        Returns:
            Dict[str, Any]: 速率限制信息
        """
        try:
            return {
                'rate_limit': self.exchange.rateLimit,
                'last_request_time': getattr(self.exchange, 'last_request_time', None),
                'last_response_time': getattr(self.exchange, 'last_response_time', None)
            }
        except Exception as e:
            self.logger.error(f"获取速率限制信息失败: {e}")
            return {}

    # ==================== 历史数据功能 ====================

    def get_historical_data(self, symbol: str, timeframe: str = '1d',
                            days: int = 30) -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            symbol: 交易对
            timeframe: 时间周期
            days: 天数
            
        Returns:
            pd.DataFrame: 历史数据
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        return self.get_ohlcv(symbol, timeframe, start_time, end_time)

    def get_recent_data(self, symbol: str, timeframe: str = '1m',
                        hours: int = 24) -> pd.DataFrame:
        """
        获取最近数据
        
        Args:
            symbol: 交易对
            timeframe: 时间周期
            hours: 小时数
            
        Returns:
            pd.DataFrame: 最近数据
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # 根据时间周期和小时数计算合适的limit
        if timeframe == '1m':
            estimated_limit = hours * 60 + 10
        elif timeframe == '5m':
            estimated_limit = hours * 12 + 10
        elif timeframe == '15m':
            estimated_limit = hours * 4 + 10
        elif timeframe == '30m':
            estimated_limit = hours * 2 + 10
        elif timeframe == '1h':
            estimated_limit = hours + 10
        elif timeframe == '4h':
            estimated_limit = max(hours // 4 + 10, 50)
        elif timeframe == '1d':
            estimated_limit = max(hours // 24 + 10, 30)
        else:
            estimated_limit = 500

        # 限制最大值为1000
        limit = min(estimated_limit, 1000)

        self.logger.info(f"获取最近 {hours} 小时的 {timeframe} 数据，估算需要 {limit} 条记录")

        return self.get_ohlcv(symbol, timeframe, start_time, end_time, limit)

    # ==================== 工具方法 ====================

    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            bool: 连接是否正常
        """
        return self._retry_operation(
            lambda: self._test_connection_internal(),
            "测试连接"
        )
    
    def test_futures_api(self) -> Dict[str, Any]:
        """
        测试期货API支持情况
        
        Returns:
            Dict[str, Any]: 期货API支持情况
        """
        result = {
            'futures_enabled': self.enable_futures,
            'futures_exchange_available': self.futures_exchange is not None,
            'supported_methods': {}
        }
        
        if not self.enable_futures or not self.futures_exchange:
            result['error'] = '期货功能未启用或期货交易所实例不可用'
            return result
        
        try:
            # 检查支持的方法
            result['supported_methods'] = {
                'fetchFundingRate': self.futures_exchange.has.get('fetchFundingRate', False),
                'fetchOpenInterest': self.futures_exchange.has.get('fetchOpenInterest', False),
                'fetchFundingRateHistory': self.futures_exchange.has.get('fetchFundingRateHistory', False),
                'fetchOpenInterestHistory': self.futures_exchange.has.get('fetchOpenInterestHistory', False),
            }
                
        except Exception as e:
            result['error'] = f'测试期货API失败: {e}'
        
        return result

    def _test_connection_internal(self) -> bool:
        """内部测试连接方法"""
        try:
            # 获取服务器时间
            server_time = self.exchange.fetch_time()
            self.logger.info(f"服务器时间: {datetime.fromtimestamp(server_time / 1000)}")
            return True
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False

    def _convert_timeframe(self, timeframe: str) -> str:
        """
        转换时间周期格式
        
        Args:
            timeframe: 时间周期
            
        Returns:
            str: CCXT格式的时间周期
        """
        # 时间周期映射
        timeframe_map = {
            '1m': '1m',
            '3m': '3m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '2h': '2h',
            '4h': '4h',
            '6h': '6h',
            '8h': '8h',
            '12h': '12h',
            '1d': '1d',
            '3d': '3d',
            '1w': '1w',
            '1M': '1M'
        }

        return timeframe_map.get(timeframe, '1m')

    def _datetime_to_timestamp(self, dt: datetime) -> int:
        """
        转换datetime为时间戳
        
        Args:
            dt: datetime对象
            
        Returns:
            int: 时间戳（毫秒）
        """
        return int(dt.timestamp() * 1000)

    def _timestamp_to_datetime(self, timestamp: int) -> datetime:
        """
        转换时间戳为datetime
        
        Args:
            timestamp: 时间戳（毫秒）
            
        Returns:
            datetime: datetime对象
        """
        return datetime.fromtimestamp(timestamp / 1000)

    # ==================== 期货历史序列（OI/资金费率） ====================

    def get_open_interest_history(self,
                                  symbol: str,
                                  start_time: Optional[datetime] = None,
                                  end_time: Optional[datetime] = None,
                                  timeframe: Optional[str] = '15m',
                                  limit: int = 1000) -> Optional[pd.DataFrame]:
        """获取持仓量历史序列（优先用期货数据API）。

        返回 DataFrame: columns=['timestamp','value']，timestamp 为本地时间（Asia/Shanghai）无时区。
        """
        try:
            if not self.enable_futures or not self.futures_exchange:
                self.logger.warning("期货功能未启用，无法获取持仓量历史")
                return None

            # 规范化交易对到无斜杠的格式，供Binance期货数据API使用
            symbol_norm = symbol
            if '/' in symbol_norm:
                symbol_norm = symbol_norm.replace('/', '')

            # Binance期货数据API：/futures/data/openInterestHist
            base_url = self.futures_exchange.urls['api'].get('fapiData')
            if not base_url:
                self.logger.warning("期货数据API地址不可用")
                return None

            # 映射时间框架到period（Binance OI历史仅支持 5m/15m/30m/1h/4h）
            # 提高日线查询的时间粒度到 1h，便于日线重采样取“最后值”体现日间变化
            tf_map = {'1m': '5m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h', '4h': '1h', '1d': '1h'}
            period = tf_map.get((timeframe or '15m'), '15m')

            # 若提供时间窗，按Binance限制（近30天）进行裁剪，避免-1130错误
            st = start_time
            et = end_time
            if st and et:
                try:
                    if isinstance(st, (int, float)):
                        st_dt = datetime.fromtimestamp(int(st) / 1000) if isinstance(st, int) else datetime.fromtimestamp(int(st))
                    else:
                        st_dt = st
                    if isinstance(et, (int, float)):
                        et_dt = datetime.fromtimestamp(int(et) / 1000) if isinstance(et, int) else datetime.fromtimestamp(int(et))
                    else:
                        et_dt = et
                    max_span = timedelta(days=29)
                    if (et_dt - st_dt) > max_span:
                        st_dt = et_dt - max_span
                        st = st_dt
                except Exception:
                    pass

            params: Dict[str, Any] = {
                'symbol': symbol_norm,
                'period': period,
                'limit': min(max(limit, 1), 1000),
                'contractType': 'PERPETUAL'
            }
            if st:
                params['startTime'] = self._ensure_timestamp(st)
            if et:
                params['endTime'] = self._ensure_timestamp(et)

            # base_url 通常已为 https://fapi.binance.com/futures/data
            # 只需追加资源名，避免路径重复
            url = f"{base_url}/openInterestHist"
            # 使用重试Session，避免偶发网络错误
            sess = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=3)
            sess.mount('https://', adapter)
            resp = sess.get(url, params=params, timeout=self.timeout / 1000)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None

            # 解析
            rows = []
            for item in data:
                ts_ms = item.get('timestamp')
                # 优先使用单品种 openInterest，避免总和 sumOpenInterest 导致数值“看起来更平”
                val = item.get('openInterest') or item.get('openInterestAmount') or item.get('sumOpenInterest')
                if ts_ms is None or val is None:
                    continue
                ts = datetime.fromtimestamp(int(ts_ms) / 1000).astimezone().astimezone(tz=None).replace(tzinfo=None)
                rows.append({'timestamp': ts, 'value': float(val)})

            df = pd.DataFrame(rows)
            if df.empty:
                return None
            df = df.sort_values('timestamp')
            # 统一格式为字符串供上游使用
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            return df
        except Exception as e:
            self.logger.warning(f"获取持仓量历史失败: {symbol}, 错误: {e}")
            return None

    def get_funding_rate_history(self,
                                 symbol: str,
                                 start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None,
                                 timeframe: Optional[str] = None,
                                 limit: int = 1000) -> Optional[pd.DataFrame]:
        """获取资金费率历史序列。

        返回 DataFrame: columns=['timestamp','value']，timestamp 为本地时间（Asia/Shanghai）无时区。
        """
        try:
            if not self.enable_futures or not self.futures_exchange:
                self.logger.warning("期货功能未启用，无法获取资金费率历史")
                return None

            symbol_norm = symbol
            if '/' in symbol_norm:
                symbol_norm = symbol_norm.replace('/', '')

            base_url = self.futures_exchange.urls['api'].get('fapiPublic')
            if not base_url:
                self.logger.warning("期货公共API地址不可用")
                return None

            # 规范化，避免出现 .../fapi/v1/v1/fundingRate
            base_norm = base_url.rstrip('/')
            if base_norm.endswith('/v1'):
                base_norm = base_norm[:-3]
            url = f"{base_norm}/v1/fundingRate"

            def _fetch_window(st: Optional[datetime], et: Optional[datetime]) -> List[Dict[str, Any]]:
                # Binance 限制单次窗口 ≤ 30天，必要时裁剪
                st_dt = st
                et_dt = et
                try:
                    if st_dt and et_dt and (et_dt - st_dt) > timedelta(days=29):
                        st_dt = et_dt - timedelta(days=29)
                except Exception:
                    pass
                params: Dict[str, Any] = {
                    'symbol': symbol_norm,
                    'limit': min(max(limit, 1), 1000)
                }
                if st_dt:
                    params['startTime'] = self._ensure_timestamp(st_dt)
                if et_dt:
                    params['endTime'] = self._ensure_timestamp(et_dt)

                # 简单重试避免偶发 SSL/EOF 错误
                sess = requests.Session()
                adapter = requests.adapters.HTTPAdapter(max_retries=3)
                sess.mount('https://', adapter)
                resp = sess.get(url, params=params, timeout=self.timeout / 1000)
                resp.raise_for_status()
                return resp.json() or []

            rows: List[Dict[str, Any]] = []
            if start_time and end_time:
                # 分段抓取，步长 29 天
                cur = start_time
                while cur < end_time:
                    seg_end = min(end_time, cur + timedelta(days=29))
                    try:
                        data = _fetch_window(cur, seg_end)
                    except Exception as e:
                        self.logger.warning(f"资金费率分段获取失败: {symbol_norm} {cur}->{seg_end}: {e}")
                        data = []
                    for item in data:
                        ts_ms = item.get('fundingTime') or item.get('time')
                        val = item.get('fundingRate') or item.get('rate')
                        if ts_ms is None or val is None:
                            continue
                        ts = datetime.fromtimestamp(int(ts_ms) / 1000).astimezone().astimezone(tz=None).replace(tzinfo=None)
                        rows.append({'timestamp': ts, 'value': float(val)})
                    # 推进到下一段，避免重叠
                    cur = seg_end + timedelta(milliseconds=1)
            else:
                # 未给时间窗，单次获取
                data = _fetch_window(start_time, end_time)
                for item in data:
                    ts_ms = item.get('fundingTime') or item.get('time')
                    val = item.get('fundingRate') or item.get('rate')
                    if ts_ms is None or val is None:
                        continue
                    ts = datetime.fromtimestamp(int(ts_ms) / 1000).astimezone().astimezone(tz=None).replace(tzinfo=None)
                    rows.append({'timestamp': ts, 'value': float(val)})

            df = pd.DataFrame(rows).drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            if df.empty:
                return None
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            return df
        except Exception as e:
            self.logger.warning(f"获取资金费率历史失败: {symbol}, 错误: {e}")
            return None

    # ==================== 异步支持 ====================
    
    async def get_ohlcv_async(self, symbol: str, timeframe: str = '1m',
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None,
                              limit: Optional[int] = None) -> pd.DataFrame:
        """
        异步获取OHLCV数据
        
        Args:
            symbol: 交易对
            timeframe: 时间周期
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            
        Returns:
            pd.DataFrame: OHLCV数据
        """
        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.get_ohlcv, 
            symbol, timeframe, start_time, end_time, limit
        )

    async def get_latest_price_async(self, symbol: str) -> Optional[dict]:
        """
        异步获取最新价格
        
        Args:
            symbol: 交易对
            
        Returns:
            Optional[dict]: 价格信息
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_latest_price, symbol)

    async def get_multiple_prices_async(self, symbols: List[str]) -> Dict[str, Optional[dict]]:
        """
        异步批量获取多个交易对的最新价格
        
        Args:
            symbols: 交易对列表
            
        Returns:
            Dict[str, Optional[dict]]: 价格信息字典
        """
        tasks = [self.get_latest_price_async(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        price_dict = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                self.logger.error(f"获取 {symbol} 价格失败: {result}")
                price_dict[symbol] = None
            else:
                price_dict[symbol] = result
                
        return price_dict

    def get_hourly_ohlcv(self, symbol: str, interval: str = '1h', limit: int = 500) -> Optional[List[Dict]]:
        """
        获取指定周期K线，interval 支持 '1h', '4h', '1d'
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
            interval: 时间周期，支持 '1h', '4h', '1d'
            limit: 数据条数，默认 500
            
        Returns:
            Optional[List[Dict]]: K线数据列表，每条包含 timestamp, open, high, low, close, volume
        """
        return self._retry_operation(
            lambda: self._get_hourly_ohlcv_internal(symbol, interval, limit),
            f"获取 {symbol} {interval} K线数据"
        )

    def _get_hourly_ohlcv_internal(self, symbol: str, interval: str, limit: int) -> Optional[List[Dict]]:
        """
        内部获取指定周期K线方法
        
        Args:
            symbol: 交易对
            interval: 时间周期
            limit: 数据条数
            
        Returns:
            Optional[List[Dict]]: K线数据列表
        """
        try:
            # 转换时间周期格式
            ccxt_timeframe = self._convert_timeframe(interval)
            
            # 调用ccxt获取数据
            ohlcv = self.exchange.fetch_ohlcv(symbol=symbol, timeframe=ccxt_timeframe, limit=limit)
            
            if not ohlcv:
                self.logger.warning(f"未获取到 {symbol} {interval} 数据")
                return None
            
            # 转换为标准格式
            result = []
            for candle in ohlcv:
                ts_ms = candle[0]
                dt = datetime.fromtimestamp(ts_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
                result.append({
                    'timestamp': dt,
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            self.logger.info(f"获取 {symbol} {interval} 数据: {len(result)} 条")
            return result
            
        except Exception as e:
            self.logger.error(f"获取 {symbol} {interval} K线数据失败: {e}")
            return None


