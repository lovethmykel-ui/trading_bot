import os
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Quantum Ensemble"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./quant_trading.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "YOUR_SUPER_SECRET_KEY_HERE")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Bybit Settings
    BYBIT_TESTNET: bool = os.getenv("BYBIT_TESTNET", "true").lower() == "true"

    # Live Trading Bot Settings
    RISK_PER_TRADE_PCT: float = float(os.getenv("RISK_PER_TRADE_PCT", "10.0"))   # 10% of balance per trade
    STOP_LOSS_PCT: float = float(os.getenv("STOP_LOSS_PCT", "2.0"))              # 2% stop loss
    TAKE_PROFIT_PCT: float = float(os.getenv("TAKE_PROFIT_PCT", "4.0"))          # 4% take profit
    TRADING_INTERVAL_SECONDS: int = int(os.getenv("TRADING_INTERVAL_SECONDS", "300"))  # 5 minutes
    TOP_PAIRS_TO_SCAN: int = int(os.getenv("TOP_PAIRS_TO_SCAN", "50"))          # Scan top 50 USDT pairs by volume
    MIN_24H_VOLUME_USDT: float = float(os.getenv("MIN_24H_VOLUME_USDT", "1000000"))    # Min $1M daily volume
    SIGNAL_CONVICTION_THRESHOLD: float = float(os.getenv("SIGNAL_CONVICTION_THRESHOLD", "0.60"))  # 60% consensus

    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_AUTHORIZED_CHAT_ID: str = os.getenv("TELEGRAM_AUTHORIZED_CHAT_ID", "")

    class Config:
        env_file = ".env"

settings = Settings()
