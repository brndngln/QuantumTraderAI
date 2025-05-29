
import httpx
import time

API_ENDPOINTS = {
    "twelvedata": "https://api.twelvedata.com/time_series?symbol=AAPL&interval=1min",
    "yahoo": "https://query1.finance.yahoo.com/v7/finance/quote?symbols=AAPL"
}

def measure_latency():
    results = {}
    for name, url in API_ENDPOINTS.items():
        start = time.time()
        try:
            httpx.get(url, timeout=2)
            latency = time.time() - start
        except Exception:
            latency = float("inf")
        results[name] = latency
    return min(results, key=results.get)
