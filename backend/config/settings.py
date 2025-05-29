
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    trading_enabled: bool = True
    currency_mode: str = "multi"
    logging_enabled: bool = True
    twelve_data_key: str = "YOUR_TWELVE_DATA_API_KEY"
    telegram_token: str = "YOUR_TELEGRAM_BOT_TOKEN"
    telegram_chat_id: str = "YOUR_TELEGRAM_CHAT_ID"

settings = Settings()
