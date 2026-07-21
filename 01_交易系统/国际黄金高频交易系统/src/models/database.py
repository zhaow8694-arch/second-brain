from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MarketData(BaseModel):
    """市场数据模型"""
    id: Optional[int] = None
    time: datetime
    symbol: str
    source: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
        
class TradingSignal(BaseModel):
    """交易信号模型"""
    id: Optional[int] = None
    time: datetime
    symbol: str
    signal_type: str
    direction: str
    price: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
        
class Order(BaseModel):
    """交易订单模型"""
    id: Optional[int] = None
    order_id: str
    time: datetime
    symbol: str
    order_type: str
    direction: str
    price: float
    volume: float
    status: str
    signal_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True

# 数据库表创建SQL
CREATE_TABLES_SQL = """
-- 创建市场数据表
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    time TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    source VARCHAR(20) NOT NULL,
    open DECIMAL(20,8) NOT NULL,
    high DECIMAL(20,8) NOT NULL,
    low DECIMAL(20,8) NOT NULL,
    close DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    bid_price DECIMAL(20,8),
    ask_price DECIMAL(20,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建交易信号表
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    time TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建交易订单表
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    time TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    status VARCHAR(20) NOT NULL,
    signal_id INTEGER REFERENCES trading_signals(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_market_data_time_symbol ON market_data(time, symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_source ON market_data(symbol, source);
CREATE INDEX IF NOT EXISTS idx_trading_signals_time_symbol ON trading_signals(time, symbol);
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_time_symbol ON orders(time, symbol);
CREATE INDEX IF NOT EXISTS idx_orders_signal_id ON orders(signal_id);
""" 