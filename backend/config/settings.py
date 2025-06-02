
from pydantic import BaseSettings
from typing import Optional, List, Dict
from pathlib import Path
import os

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
ENV_VARS = {
    'API_KEY': 'YOUR_API_KEY',
    'REDIS_URL': 'redis://localhost:6379',
    'DATABASE_URL': 'sqlite:///./trading.db',
    'TELEGRAM_TOKEN': 'YOUR_TELEGRAM_BOT_TOKEN',
    'TELEGRAM_CHAT_ID': 'YOUR_TELEGRAM_CHAT_ID',
    'TWELVE_DATA_API_KEY': 'YOUR_TWELVE_DATA_API_KEY',
    'ALPHA_VANTAGE_API_KEY': 'YOUR_ALPHA_VANTAGE_API_KEY',
    'BINANCE_API_KEY': 'YOUR_BINANCE_API_KEY',
    'BINANCE_SECRET_KEY': 'YOUR_BINANCE_SECRET_KEY',
    'BACKEND_URL': 'http://localhost:8000',
    'FRONTEND_URL': 'http://localhost:3000',
    'RATE_LIMIT_WINDOW': '60',
    'RATE_LIMIT_MAX': '1000',
    'MAX_TRADE_SIZE': '100000',
    'MAX_POSITIONS': '10',
    'MAX_LEVERAGE': '5'
}

class Settings(BaseSettings):
    # Core Settings
    trading_enabled: bool = True
    currency_mode: str = "multi"
    logging_enabled: bool = True
    debug_mode: bool = False
    
    # API Keys
    api_key: str = ENV_VARS['API_KEY']
    telegram_token: str = ENV_VARS['TELEGRAM_TOKEN']
    telegram_chat_id: str = ENV_VARS['TELEGRAM_CHAT_ID']
    twelve_data_key: str = ENV_VARS['TWELVE_DATA_API_KEY']
    alpha_vantage_key: str = ENV_VARS['ALPHA_VANTAGE_API_KEY']
    binance_api_key: str = ENV_VARS['BINANCE_API_KEY']
    binance_secret_key: str = ENV_VARS['BINANCE_SECRET_KEY']
    
    # URLs
    backend_url: str = ENV_VARS['BACKEND_URL']
    frontend_url: str = ENV_VARS['FRONTEND_URL']
    
    # Rate Limiting
    rate_limit_window: int = int(ENV_VARS['RATE_LIMIT_WINDOW'])
    rate_limit_max: int = int(ENV_VARS['RATE_LIMIT_MAX'])
    
    # Trading Parameters
    max_trade_size: float = float(ENV_VARS['MAX_TRADE_SIZE'])
    max_positions: int = int(ENV_VARS['MAX_POSITIONS'])
    max_leverage: float = float(ENV_VARS['MAX_LEVERAGE'])
    
    # Database
    redis_url: str = ENV_VARS['REDIS_URL']
    database_url: str = ENV_VARS['DATABASE_URL']
    
    # Security
    jwt_secret: str = "your_jwt_secret"
    rate_limit_window: int = 60
    rate_limit_max: int = 1000
    
    # Cache
    cache_ttl: int = 3600
    redis_cache_prefix: str = "quantum_trader:"
    
    # Broker
    broker_timeout: int = 30
    broker_retry_delay: int = 5
    
    # Strategy Parameters
    min_confidence: float = 0.7
    max_risk_per_trade: float = 0.02
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
