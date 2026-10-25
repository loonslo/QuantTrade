import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# Test Stooq for S&P 500
print("=== Testing Stooq S&P 500 ===")
try:
    url = "https://stooq.com/q/d/l/?s=^spx&i=d"
    response = session.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Content (first 500 chars): {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test Stooq for USDCNY
print("=== Testing Stooq USDCNY ===")
try:
    url = "https://stooq.com/q/d/l/?s=cnyusd&i=d"
    response = session.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Content (first 500 chars): {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test alternative Yahoo Finance endpoint
print("=== Testing Yahoo Finance Alternative ===")
try:
    # Try the older v7 API
    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EGSPC"
    response = session.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Content (first 1000 chars): {response.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
