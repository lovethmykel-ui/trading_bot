from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    accounts = relationship("ExchangeAccount", back_populates="user")
    settings = relationship("Settings", back_populates="user", uselist=False)

class ExchangeAccount(Base):
    __tablename__ = 'exchange_accounts'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    exchange_name = Column(String, nullable=False) # e.g., 'bybit'
    api_key = Column(String, nullable=False)
    api_secret = Column(String, nullable=False)  # In a production environment this should use sqlalchemy-utils EncryptedType
    is_testnet = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="accounts")
    balances = relationship("Balance", back_populates="account")
    positions = relationship("Position", back_populates="account")
    orders = relationship("Order", back_populates="account")
    trades = relationship("Trade", back_populates="account")

class Balance(Base):
    __tablename__ = 'balances'
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('exchange_accounts.id'), nullable=False)
    asset = Column(String, nullable=False)
    free = Column(Float, default=0.0)
    locked = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("ExchangeAccount", back_populates="balances")

class Position(Base):
    __tablename__ = 'positions'
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('exchange_accounts.id'), nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False) # 'LONG' or 'SHORT'
    size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("ExchangeAccount", back_populates="positions")

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('exchange_accounts.id'), nullable=False)
    symbol = Column(String, nullable=False)
    order_type = Column(String, nullable=False) # 'LIMIT', 'MARKET', etc.
    side = Column(String, nullable=False) # 'BUY', 'SELL'
    price = Column(Float, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False) # 'OPEN', 'FILLED', 'CANCELED'
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("ExchangeAccount", back_populates="orders")

class MarketData(Base):
    __tablename__ = 'market_data'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    last_price = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=False)
    high_24h = Column(Float, nullable=False)
    low_24h = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Candle(Base):
    __tablename__ = 'candles'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=False) # e.g., '1m', '1h', '1d'
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('exchange_accounts.id'), nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    account = relationship("ExchangeAccount", back_populates="trades")

class SystemLog(Base):
    __tablename__ = 'system_logs'
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, nullable=False) # 'INFO', 'WARNING', 'ERROR'
    component = Column(String, nullable=False)
    message = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    theme = Column(String, default='dark')
    notifications_enabled = Column(Boolean, default=True)
    risk_level = Column(String, default='medium')

    user = relationship("User", back_populates="settings")
