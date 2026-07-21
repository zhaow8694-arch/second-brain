from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.db_manager import DatabaseManager

class BaseFeatureGenerator(ABC):
    def __init__(self):
        self.db_manager = DatabaseManager()
        
    async def get_market_data(self, 
                            symbol: str,
                            start_time: datetime,
                            end_time: datetime,
                            source: Optional[str] = None) -> pd.DataFrame:
        """从数据库获取市场数据"""
        query = """
            SELECT time, symbol, source, open, high, low, close, 
                   volume, bid_price, ask_price
            FROM market_data
            WHERE symbol = %s AND time BETWEEN %s AND %s
        """
        params = [symbol, start_time, end_time]
        
        if source:
            query += " AND source = %s"
            params.append(source)
            
        query += " ORDER BY time ASC"
        
        data = await self.db_manager.execute_query(query, *params)
        
        # 转换为DataFrame
        df = pd.DataFrame(data, columns=[
            'time', 'symbol', 'source', 'open', 'high', 'low',
            'close', 'volume', 'bid_price', 'ask_price'
        ])
        
        if not df.empty:
            df.set_index('time', inplace=True)
            
        return df
        
    @abstractmethod
    async def generate_features(self,
                              symbol: str,
                              start_time: datetime,
                              end_time: datetime,
                              **kwargs) -> pd.DataFrame:
        """生成特征"""
        pass
        
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算常用技术指标"""
        # 确保数据按时间排序
        df = df.sort_index()
        
        # 价格变化
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close']).diff()
        
        # 波动率指标
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['high_low_range'] = (df['high'] - df['low']) / df['close']
        
        # 移动平均线
        for period in [5, 10, 20, 50, 200]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # 成交量指标
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # 价格趋势
        df['trend'] = np.where(df['close'] > df['sma_20'], 1,
                             np.where(df['close'] < df['sma_20'], -1, 0))
        
        return df
        
    def calculate_order_book_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算订单簿特征"""
        # 买卖价差
        df['spread'] = df['ask_price'] - df['bid_price']
        df['spread_ratio'] = df['spread'] / df['close']
        
        # 中间价格
        df['mid_price'] = (df['ask_price'] + df['bid_price']) / 2
        
        # 价格偏离
        df['price_deviation'] = (df['close'] - df['mid_price']) / df['mid_price']
        
        return df
        
    def calculate_market_microstructure(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算市场微观结构特征"""
        # 交易强度
        df['trade_intensity'] = df['volume'] / df['high_low_range']
        
        # 价格冲击
        df['price_impact'] = df['returns'].abs() / df['volume']
        
        # 流动性指标
        df['amihud_illiquidity'] = df['returns'].abs() / df['volume']
        
        # 价格效率
        df['price_efficiency'] = df['returns'].rolling(window=20).mean() / \
                                df['returns'].rolling(window=20).std()
        
        return df
        
    def remove_outliers(self, df: pd.DataFrame, columns: List[str],
                       n_std: float = 3.0) -> pd.DataFrame:
        """移除异常值"""
        for col in columns:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                df[col] = df[col].clip(mean - n_std * std, mean + n_std * std)
        return df
        
    def handle_missing_values(self, df: pd.DataFrame,
                            method: str = 'ffill') -> pd.DataFrame:
        """处理缺失值"""
        if method == 'ffill':
            df = df.fillna(method='ffill')
        elif method == 'bfill':
            df = df.fillna(method='bfill')
        elif method == 'interpolate':
            df = df.interpolate(method='linear')
            
        return df 