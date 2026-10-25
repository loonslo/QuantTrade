# -*- coding: utf-8 -*-
"""
系统配置API路由
提供系统配置项的查询和管理接口

[RELOAD] - Updated to use local cache for coin icons
"""

from fastapi import APIRouter, HTTPException
from api.schemas.config import CoinListResponse
from api.middleware.response_formatter import ResponseFormatter

router = APIRouter(prefix="/config", tags=["系统配置"])
response_handler = ResponseFormatter()


def get_coin_info(base_asset: str) -> tuple[str, str, str]:
    """
    获取币种信息（名称和图标）

    Args:
        base_asset: 基础货币符号，如BTC

    Returns:
        (coin_name, coin_symbol, icon_url)
    """
    # 首先尝试从本地缓存文件读取
    try:
        from pathlib import Path
        import json

        cache_file = Path("data/cache/coins/coin_info_cache.json")
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                coin_cache = json.load(f)

            symbol_upper = base_asset.upper()
            if symbol_upper in coin_cache:
                coin_data = coin_cache[symbol_upper]
                # 转换本地路径为可访问的 HTTP 路径
                local_path = coin_data['icon_url']
                print(f"[DEBUG] {symbol_upper}: local_path={local_path}")
                # 如果是本地路径 (assets\icons\XXX.png 或 assets/icons/XXX.png)，转换为 /static/icons/XXX.png
                # 注意: assets目录已挂载到 /static，所以路径应该是 /static/icons/XXX.png
                if local_path.startswith('assets'):
                    # 提取文件名 (icons/XXX.png) 并确保使用正斜杠
                    file_path = local_path.replace('assets\\', '').replace('assets/', '').replace('\\', '/')
                    http_path = '/static/' + file_path
                    print(f"[DEBUG] {symbol_upper}: file_path={file_path}, http_path={http_path}")
                    return (
                        coin_data['name'],
                        coin_data['symbol'],
                        http_path
                    )
                else:
                    # 如果已经是完整路径，直接返回
                    return (
                        coin_data['name'],
                        coin_data['symbol'],
                        coin_data['icon_url']
                    )
    except Exception:
        # 读取缓存失败，继续使用硬编码映射
        pass

    # 使用硬编码映射（备选方案）- 使用绝对路径让前端可访问
    print(f"[DEBUG] Using hardcoded mapping for: {base_asset}")
    coin_map = {
        "BTC": ("Bitcoin", "BTC", "/static/icons/BTC.png"),
        "ETH": ("Ethereum", "ETH", "/static/icons/ETH.png"),
        "BNB": ("BNB", "BNB", "/static/icons/BNB.png"),
        "ADA": ("Cardano", "ADA", "/static/icons/ADA.png"),
        "SOL": ("Solana", "SOL", "/static/icons/SOL.png"),
        "XRP": ("XRP", "XRP", "/static/icons/XRP.png"),
        "DOT": ("Polkadot", "DOT", "/static/icons/DOT.png"),
        "DOGE": ("Dogecoin", "DOGE", "/static/icons/DOGE.png"),
        "AVAX": ("Avalanche", "AVAX", "/static/icons/AVAX.png"),
        "MATIC": ("Polygon", "MATIC", "/static/icons/MATIC.png"),
        "LTC": ("Litecoin", "LTC", "/static/icons/LTC.png"),
        "LINK": ("Chainlink", "LINK", "/static/icons/LINK.png"),
        "UNI": ("Uniswap", "UNI", "/static/icons/UNI.png"),
        "ATOM": ("Cosmos", "ATOM", "/static/icons/ATOM.png"),
        "VET": ("VeChain", "VET", "/static/icons/VET.png"),
        "FIL": ("Filecoin", "FIL", "/static/icons/FIL.png"),
        "TRX": ("TRON", "TRX", "/static/icons/TRX.png"),
        "ETC": ("Ethereum Classic", "ETC", "/static/icons/ETC.png"),
        "XLM": ("Stellar", "XLM", "/static/icons/XLM.png"),
        "BCH": ("Bitcoin Cash", "BCH", "/static/icons/BCH.png"),
        "ALGO": ("Algorand", "ALGO", "/static/icons/ALGO.png"),
        "XMR": ("Monero", "XMR", "/static/icons/XMR.png"),
        "EOS": ("EOS", "EOS", "/static/icons/EOS.png"),
        "AAVE": ("Aave", "AAVE", "/static/icons/AAVE.png"),
        "MKR": ("Maker", "MKR", "/static/icons/MKR.png"),
        "COMP": ("Compound", "COMP", "/static/icons/COMP.png"),
        "YFI": ("yearn.finance", "YFI", "/static/icons/YFI.png"),
        "SNX": ("Synthetix", "SNX", "/static/icons/SNX.png"),
        "CRV": ("Curve", "CRV", "/static/icons/CRV.png"),
        "SUSHI": ("SushiSwap", "SUSHI", "/static/icons/SUSHI.png"),
        "1INCH": ("1inch", "1INCH", "/static/icons/1INCH.png"),
        "ENJ": ("Enjin Coin", "ENJ", "/static/icons/ENJ.png"),
        "MANA": ("Decentraland", "MANA", "/static/icons/MANA.png"),
        "SAND": ("The Sandbox", "SAND", "/static/icons/SAND.png"),
        "AXS": ("Axie Infinity", "AXS", "/static/icons/AXS.png"),
        "SHIB": ("Shiba Inu", "SHIB", "/static/icons/SHIB.png"),
        "PEPE": ("Pepe", "PEPE", "/static/icons/PEPE.png"),
        "FLOKI": ("Floki", "FLOKI", "/static/icons/FLOKI.png"),
        "USDC": ("USD Coin", "USDC", "/static/icons/USDC.png"),
        "ZEC": ("Zcash", "ZEC", "/static/icons/ZEC.png"),
        "STX": ("Stacks", "STX", "/static/icons/STX.png"),
        "APT": ("Aptos", "APT", "/static/icons/APT.png"),
        "NEAR": ("Near Protocol", "NEAR", "/static/icons/NEAR.png"),
        "FTM": ("Fantom", "FTM", "/static/icons/FTM.png"),
        "SUI": ("Sui", "SUI", "/static/icons/SUI.png"),
        "TIA": ("Celestia", "TIA", "/static/icons/TIA.png"),
        "WLD": ("Worldcoin", "WLD", "/static/icons/WLD.png"),
        "JTO": ("Jito", "JTO", "/static/icons/JTO.png"),
        "ARB": ("Arbitrum", "ARB", "/static/icons/ARB.png"),
        "OP": ("Optimism", "OP", "/static/icons/OP.png"),
        "IMX": ("Immutable X", "IMX", "/static/icons/IMX.png"),
        "LDO": ("Lido DAO", "LDO", "/static/icons/LDO.png"),
        "INJ": ("Injective", "INJ", "/static/icons/INJ.png"),
        "SEI": ("Sei", "SEI", "/static/icons/SEI.png"),
        "BLUR": ("Blur", "BLUR", "/static/icons/BLUR.png"),
        "RAY": ("Raydium", "RAY", "/static/icons/RAY.png"),
        "SRM": ("Serum", "SRM", "/static/icons/SRM.png"),
        "MNGO": ("Mango", "MNGO", "/static/icons/MNGO.png"),
    }

    base_asset_upper = base_asset.upper()
    return coin_map.get(base_asset_upper, (base_asset, base_asset_upper, "/static/icons/default.png"))


@router.get("/coin-list")
async def get_coin_list():
    """
    获取支持的币种列表

    从crypto_market_rankings表获取is_valid=1的有效币种，返回包含基础信息和图标的完整列表。

    ## 功能特点
    - 从crypto_market_rankings表获取有效的币种数据
    - 包含基础货币、计价货币和市值信息
    - 自动补充币种图标和全称
    - 按市值排名排序（从高到低）
    - 只返回is_valid=1的有效币种

    ## 返回数据说明
    每个币种返回的数据包括：
    - 交易对符号（如 BTCUSDT）
    - 基础货币和计价货币
    - 币种全称和简称
    - 图标URL
    - 市值（美元）

    ## 使用场景
    - 币种选择器
    - 市场概览页面
    - 交易对初始化
    - 前端下拉列表
    - 完整的币种列表展示
    """
    try:
        from services.orm.crypto_market_rankings_orm import get_crypto_market_rankings_service_orm

        # 获取市场排行服务
        rankings_service = get_crypto_market_rankings_service_orm()

        # 从crypto_market_rankings表获取is_valid=1的有效币种
        market_data = rankings_service.get_latest_rankings(quote_asset="USDT", limit=200)

        if not market_data:
            # 如果没有数据，返回默认列表
            coin_list = [
                {
                    "symbol": "BTCUSDT",
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                    "coin_name": "Bitcoin",
                    "coin_symbol": "BTC",
                    "icon_url": "https://cryptologos.cc/logos/bitcoin-btc-logo.png",
                    "market_cap": 1200000000000.0
                },
                {
                    "symbol": "ETHUSDT",
                    "base_asset": "ETH",
                    "quote_asset": "USDT",
                    "coin_name": "Ethereum",
                    "coin_symbol": "ETH",
                    "icon_url": "https://cryptologos.cc/logos/ethereum-eth-logo.png",
                    "market_cap": 300000000000.0
                }
            ]
        else:
            # 转换为CoinListResponse格式
            coin_list = []
            for data in market_data:
                symbol = data.get('symbol', '')

                # 处理不同格式的symbol
                if '/' in symbol:
                    # 格式: "BTC/USDT"
                    parts = symbol.split('/')
                    if len(parts) == 2 and parts[1] == 'USDT':
                        base_asset = parts[0]
                        standard_symbol = f"{parts[0]}USDT"
                    elif len(parts) == 2:
                        # 其他格式如 "BTC-USD"
                        base_asset = parts[0]
                        standard_symbol = f"{parts[0]}USDT"
                    else:
                        # 格式不正确，跳过
                        continue
                else:
                    # 格式: "BTCUSDT" (不需要处理)
                    base_asset = symbol
                    standard_symbol = symbol

                # 补充币种名称和图标
                coin_name, coin_symbol, icon_url = get_coin_info(base_asset)

                coin_list.append({
                    "symbol": standard_symbol,
                    "base_asset": base_asset,
                    "quote_asset": "USDT",
                    "coin_name": coin_name,
                    "coin_symbol": coin_symbol,
                    "icon_url": icon_url,
                    "market_cap": data.get('market_cap', 0)
                })

        return response_handler.format_success(coin_list)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取币种列表失败: {str(e)}")



