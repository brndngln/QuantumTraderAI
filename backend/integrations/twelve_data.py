
import httpx
from backend.config.settings import settings

def fetch_realtime_data(symbols):
    url = f"https://api.twelvedata.com/time_series?symbol={','.join(symbols)}&interval=1min&apikey={settings.twelve_data_key}"
    response = httpx.get(url)
    return response.json()
