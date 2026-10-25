# -*- coding: utf-8 -*-
"""
币种信息服务
负责本地存储和管理币种信息，包括图标缓存
"""

import json
import os
import requests
import hashlib
from typing import Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path

from utils.core.logger_manager import get_logger


class CoinInfoService:
    """币种信息服务"""

    def __init__(self, cache_dir: str = "data/cache/coins", icons_dir: str = "assets/icons"):
        self.logger = get_logger('coin_info_service')
        self.cache_dir = Path(cache_dir)
        self.icons_dir = Path(icons_dir)
        self.cache_file = self.cache_dir / "coin_info_cache.json"

        # 创建目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.icons_dir.mkdir(parents=True, exist_ok=True)

        # 加载缓存
        self.coin_cache = self._load_cache()

        # 初始化默认币种
        self._init_default_coins()

    def _load_cache(self) -> Dict:
        """加载本地缓存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"加载币种缓存: {len(data)} 条记录")
                    return data
        except Exception as e:
            self.logger.error(f"加载缓存失败: {e}")
        return {}

    def _save_cache(self):
        """保存缓存到本地"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.coin_cache, f, ensure_ascii=False, indent=2)
            self.logger.info(f"保存币种缓存: {len(self.coin_cache)} 条记录")
        except Exception as e:
            self.logger.error(f"保存缓存失败: {e}")

    def _init_default_coins(self):
        """初始化默认币种"""
        default_coins = {
            "BTC": ("Bitcoin", "BTC", "https://cryptologos.cc/logos/bitcoin-btc-logo.png"),
            "ETH": ("Ethereum", "ETH", "https://cryptologos.cc/logos/ethereum-eth-logo.png"),
            "BNB": ("BNB", "BNB", "https://cryptologos.cc/logos/bnb-bnb-logo.png"),
            "ADA": ("Cardano", "ADA", "https://cryptologos.cc/logos/cardano-ada-logo.png"),
            "SOL": ("Solana", "SOL", "https://cryptologos.cc/logos/solana-sol-logo.png"),
            "XRP": ("XRP", "XRP", "https://cryptologos.cc/logos/xrp-xrp-logo.png"),
            "DOT": ("Polkadot", "DOT", "https://cryptologos.cc/logos/polkadot-new-dot-logo.png"),
            "DOGE": ("Dogecoin", "DOGE", "https://cryptologos.cc/logos/dogecoin-doge-logo.png"),
            "AVAX": ("Avalanche", "AVAX", "https://cryptologos.cc/logos/avalanche-avax-logo.png"),
            "MATIC": ("Polygon", "MATIC", "https://cryptologos.cc/logos/polygon-matic-logo.png"),
            "LTC": ("Litecoin", "LTC", "https://cryptologos.cc/logos/litecoin-ltc-logo.png"),
            "LINK": ("Chainlink", "LINK", "https://cryptologos.cc/logos/chainlink-link-logo.png"),
            "UNI": ("Uniswap", "UNI", "https://cryptologos.cc/logos/uniswap-uni-logo.png"),
            "ATOM": ("Cosmos", "ATOM", "https://cryptologos.cc/logos/cosmos-atom-logo.png"),
            "VET": ("VeChain", "VET", "https://cryptologos.cc/logos/vechain-vet-logo.png"),
            "FIL": ("Filecoin", "FIL", "https://cryptologos.cc/logos/filecoin-fil-logo.png"),
            "TRX": ("TRON", "TRX", "https://cryptologos.cc/logos/tron-trx-logo.png"),
            "ETC": ("Ethereum Classic", "ETC", "https://cryptologos.cc/logos/ethereum-classic-etc-logo.png"),
            "XLM": ("Stellar", "XLM", "https://cryptologos.cc/logos/stellar-xlm-logo.png"),
            "BCH": ("Bitcoin Cash", "BCH", "https://cryptologos.cc/logos/bitcoin-cash-bch-logo.png"),
            "ALGO": ("Algorand", "ALGO", "https://cryptologos.cc/logos/algorand-algo-logo.png"),
            "XMR": ("Monero", "XMR", "https://cryptologos.cc/logos/monero-xmr-logo.png"),
            "EOS": ("EOS", "EOS", "https://cryptologos.cc/logos/eos-eos-logo.png"),
            "AAVE": ("Aave", "AAVE", "https://cryptologos.cc/logos/aave-aave-logo.png"),
            "MKR": ("Maker", "MKR", "https://cryptologos.cc/logos/maker-mkr-logo.png"),
            "COMP": ("Compound", "COMP", "https://cryptologos.cc/logos/compound-comp-logo.png"),
            "YFI": ("yearn.finance", "YFI", "https://cryptologos.cc/logos/yearn-finance-yfi-logo.png"),
            "SNX": ("Synthetix", "SNX", "https://cryptologos.cc/logos/synthetix-snx-logo.png"),
            "CRV": ("Curve", "CRV", "https://cryptologos.cc/logos/curve-dao-token-crv-logo.png"),
            "SUSHI": ("SushiSwap", "SUSHI", "https://cryptologos.cc/logos/sushiswap-sushi-logo.png"),
            "1INCH": ("1inch", "1INCH", "https://cryptologos.cc/logos/1inch-1inch-logo.png"),
            "ENJ": ("Enjin Coin", "ENJ", "https://cryptologos.cc/logos/enjin-coin-enj-logo.png"),
            "MANA": ("Decentraland", "MANA", "https://cryptologos.cc/logos/decentraland-mana-logo.png"),
            "SAND": ("The Sandbox", "SAND", "https://cryptologos.cc/logos/the-sandbox-sand-logo.png"),
            "AXS": ("Axie Infinity", "AXS", "https://cryptologos.cc/logos/axie-infinity-axs-logo.png"),
            "SHIB": ("Shiba Inu", "SHIB", "https://cryptologos.cc/logos/shiba-inu-shib-logo.png"),
            "PEPE": ("Pepe", "PEPE", "https://cryptologos.cc/logos/pepe-pepe-logo.png"),
            "FLOKI": ("Floki", "FLOKI", "https://cryptologos.cc/logos/floki-floi-logo.png"),
            "USDC": ("USD Coin", "USDC", "https://cryptologos.cc/logos/usd-coin-usdc-logo.png"),
            "ZEC": ("Zcash", "ZEC", "https://cryptologos.cc/logos/zcash-zec-logo.png"),
            "STX": ("Stacks", "STX", "https://cryptologos.cc/logos/stacks-stx-logo.png"),
            "APT": ("Aptos", "APT", "https://cryptologos.cc/logos/aptos-apt-logo.png"),
            "NEAR": ("Near Protocol", "NEAR", "https://cryptologos.cc/logos/near-protocol-near-logo.png"),
            "FTM": ("Fantom", "FTM", "https://cryptologos.cc/logos/fantom-ftm-logo.png"),
            "SUI": ("Sui", "SUI", "https://cryptologos.cc/logos/sui-sui-logo.png"),
            "TIA": ("Celestia", "TIA", "https://cryptologos.cc/logos/celestia-tia-logo.png"),
            "WLD": ("Worldcoin", "WLD", "https://cryptologos.cc/logos/worldcoin-wld-logo.png"),
            "JTO": ("Jito", "JTO", "https://cryptologos.cc/logos/jito-jto-logo.png"),
            "ARB": ("Arbitrum", "ARB", "https://cryptologos.cc/logos/arbitrum-arb-logo.png"),
            "OP": ("Optimism", "OP", "https://cryptologos.cc/logos/optimism-op-logo.png"),
            "IMX": ("Immutable X", "IMX", "https://cryptologos.cc/logos/immutable-x-imx-logo.png"),
            "LDO": ("Lido DAO", "LDO", "https://cryptologos.cc/logos/lido-dao-ldo-logo.png"),
            "INJ": ("Injective", "INJ", "https://cryptologos.cc/logos/injective-inj-logo.png"),
            "SEI": ("Sei", "SEI", "https://cryptologos.cc/logos/sei-sei-logo.png"),
            "BLUR": ("Blur", "BLUR", "https://cryptologos.cc/logos/blur-blur-logo.png"),
            "RAY": ("Raydium", "RAY", "https://cryptologos.cc/logos/raydium-ray-logo.png"),
            "SRM": ("Serum", "SRM", "https://cryptologos.cc/logos/serum-srm-logo.png"),
            "MNGO": ("Mango", "MNGO", "https://cryptologos.cc/logos/mango-mango-logo.png"),
        }

        # 加载到缓存
        for symbol, (name, symbol_upper, icon_url) in default_coins.items():
            if symbol not in self.coin_cache:
                # 下载图标
                local_icon_path = self._download_icon(symbol, icon_url)

                self.coin_cache[symbol] = {
                    "name": name,
                    "symbol": symbol_upper,
                    "icon_url": local_icon_path,
                    "source": "default",
                    "updated_at": datetime.now().isoformat()
                }

        # 保存缓存
        self._save_cache()

    def _download_icon(self, symbol: str, icon_url: str) -> str:
        """下载图标到本地"""
        try:
            # 生成文件名
            file_ext = os.path.splitext(icon_url)[1] or ".png"
            safe_symbol = "".join(c for c in symbol if c.isalnum()).upper()
            local_filename = f"{safe_symbol}{file_ext}"
            local_path = self.icons_dir / local_filename

            # 如果本地文件已存在，直接返回
            if local_path.exists():
                return str(local_path)

            # 下载图标
            response = requests.get(icon_url, timeout=10)
            response.raise_for_status()

            # 保存到本地
            with open(local_path, 'wb') as f:
                f.write(response.content)

            self.logger.info(f"下载图标成功: {symbol} -> {local_path}")
            return str(local_path)

        except Exception as e:
            self.logger.error(f"下载图标失败: {symbol} - {e}")
            # 返回原URL作为备选
            return icon_url

    def get_coin_info(self, base_asset: str) -> Optional[Dict]:
        """获取币种信息"""
        symbol = base_asset.upper()

        # 优先从缓存获取
        if symbol in self.coin_cache:
            return self.coin_cache[symbol]

        # 缓存中没有，尝试从API获取
        self.logger.info(f"缓存中没有 {symbol}，尝试从API获取...")
        coin_data = self._fetch_from_api(symbol)

        if coin_data:
            # 下载图标
            local_icon_path = self._download_icon(symbol, coin_data.get('icon_url', ''))

            # 保存到缓存
            self.coin_cache[symbol] = {
                "name": coin_data.get('name', symbol),
                "symbol": symbol,
                "icon_url": local_icon_path,
                "source": "api",
                "updated_at": datetime.now().isoformat()
            }
            self._save_cache()

            return self.coin_cache[symbol]

        return None

    def _fetch_from_api(self, symbol: str) -> Optional[Dict]:
        """从API获取币种信息"""
        try:
            # 使用CoinPaprika API
            url = f"https://api.coinpaprika.com/v1/tickers/{symbol.lower()}-usd"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                return {
                    "name": data.get('name', symbol),
                    "symbol": symbol,
                    "icon_url": data.get('logo', ''),
                    "source": "coinpaprika"
                }
        except Exception as e:
            self.logger.error(f"从API获取 {symbol} 失败: {e}")

        return None

    def update_coin_info(self, symbol: str, name: str, icon_url: str) -> bool:
        """更新币种信息"""
        try:
            symbol = symbol.upper()

            # 下载新图标
            local_icon_path = self._download_icon(symbol, icon_url)

            # 更新缓存
            self.coin_cache[symbol] = {
                "name": name,
                "symbol": symbol,
                "icon_url": local_icon_path,
                "source": "updated",
                "updated_at": datetime.now().isoformat()
            }

            self._save_cache()
            self.logger.info(f"更新币种信息成功: {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"更新币种信息失败: {symbol} - {e}")
            return False

    def get_all_coins(self) -> Dict:
        """获取所有币种信息"""
        return self.coin_cache.copy()

    def get_coins_list(self) -> list:
        """获取币种列表（用于API返回）"""
        result = []
        for symbol, info in self.coin_cache.items():
            result.append({
                "symbol": f"{symbol}USDT",  # 默认加上USDT后缀
                "base_asset": symbol,
                "quote_asset": "USDT",
                "coin_name": info["name"],
                "coin_symbol": info["symbol"],
                "icon_url": info["icon_url"],
                "market_cap": 0,  # 默认值，可以后续更新
            })
        return result

    def refresh_from_api(self) -> int:
        """从API刷新所有币种信息"""
        updated_count = 0

        # 这里是示例，实际中可以从CoinGecko等获取完整列表
        popular_symbols = ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOT", "DOGE", "AVAX", "MATIC"]

        for symbol in popular_symbols:
            if self._fetch_and_update(symbol):
                updated_count += 1

        self.logger.info(f"刷新完成，更新了 {updated_count} 个币种")
        return updated_count

    def _fetch_and_update(self, symbol: str) -> bool:
        """获取并更新单个币种"""
        try:
            data = self._fetch_from_api(symbol)
            if data:
                return self.update_coin_info(symbol, data['name'], data.get('icon_url', ''))
        except Exception as e:
            self.logger.error(f"刷新 {symbol} 失败: {e}")
        return False


# 全局服务实例
_coin_info_service: Optional[CoinInfoService] = None


def get_coin_info_service() -> CoinInfoService:
    """获取币种信息服务实例（单例模式）"""
    global _coin_info_service
    if _coin_info_service is None:
        _coin_info_service = CoinInfoService()
    return _coin_info_service
