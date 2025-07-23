import ccxt

exchange = ccxt.binance({
    "proxies": {
        "http": "http://127.0.0.1:6823",
        "https": "http://127.0.0.1:6823"
    },
    "timeout": 10000,
    "enableRateLimit": True
})

print("ccxt version:", ccxt.__version__)
print("exchange.urls:", exchange.urls)
print(exchange.fetch_ticker('BTC/USDT'))