from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from src.features.base_features import BaseFeatureGenerator

class MarketFeatureGenerator(BaseFeatureGenerator):
    def __init__(self, lookback_periods: List[int] = None):
        super().__init__()
        self.lookback_periods = lookback_periods or [5, 10, 20, 50, 200]
        
    async def generate_features(self,
                              symbol: str,
                              start_time: datetime,
                              end_time: datetime,
                              source: Optional[str] = None) -> pd.DataFrame:
        """生成市场特征"""
        # 获取额外的历史数据以计算特征
        max_lookback = max(self.lookback_periods)
        extended_start = start_time - timedelta(days=max_lookback)
        
        # 获取市场数据
        df = await self.get_market_data(
            symbol=symbol,
            start_time=extended_start,
            end_time=end_time,
            source=source
        )
        
        if df.empty:
            return pd.DataFrame()
            
        # 计算基本技术指标
        df = self.calculate_technical_indicators(df)
        
        # 计算订单簿特征
        df = self.calculate_order_book_features(df)
        
        # 计算市场微观结构特征
        df = self.calculate_market_microstructure(df)
        
        # 计算高级特征
        df = self.calculate_advanced_features(df)
        
        # 处理缺失值
        df = self.handle_missing_values(df)
        
        # 移除异常值
        columns_to_clean = [
            'returns', 'volatility', 'spread_ratio', 'volume_ratio',
            'trade_intensity', 'price_impact', 'amihud_illiquidity'
        ]
        df = self.remove_outliers(df, columns_to_clean)
        
        # 只返回请求的时间范围内的数据
        return df[start_time:end_time]
        
    def calculate_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算高级特征"""
        # 价格动量
        for period in self.lookback_periods:
            df[f'momentum_{period}'] = df['close'].pct_change(period)
            
        # 波动率特征
        for period in self.lookback_periods:
            # 历史波动率
            df[f'hist_volatility_{period}'] = df['returns'].rolling(period).std() * np.sqrt(252)
            # 价格范围波动率
            df[f'range_volatility_{period}'] = df['high_low_range'].rolling(period).mean()
            
        # 趋势强度指标
        for period in self.lookback_periods:
            df[f'trend_strength_{period}'] = (
                df['close'] - df[f'sma_{period}']
            ) / df[f'sma_{period}']
            
        # 价格突破指标
        for period in self.lookback_periods:
            df[f'price_breakout_{period}'] = (
                df['close'] > df['high'].rolling(period).max().shift(1)
            ).astype(int) - (
                df['close'] < df['low'].rolling(period).min().shift(1)
            ).astype(int)
            
        # 成交量特征
        for period in self.lookback_periods:
            # 成交量趋势
            df[f'volume_trend_{period}'] = (
                df['volume'] > df['volume'].rolling(period).mean()
            ).astype(int)
            # 成交量波动率
            df[f'volume_volatility_{period}'] = (
                df['volume'].rolling(period).std() / 
                df['volume'].rolling(period).mean()
            )
            
        # 价格和成交量的相关性
        for period in self.lookback_periods:
            df[f'price_volume_corr_{period}'] = (
                df['returns'].rolling(period)
                .corr(df['volume'].pct_change())
            )
            
        # RSI动量
        df['rsi_momentum'] = df['rsi'].diff()
        
        # MACD动量
        df['macd_momentum'] = df['macd'].diff()
        
        # 布林带相对位置
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 价格波动模式
        df['price_pattern'] = (
            (df['close'] > df['open']).astype(int) * 2 +
            (df['close'] > df['close'].shift(1)).astype(int)
        )
        
        # 交易活跃度
        df['trading_activity'] = df['volume'] * df['high_low_range']
        
        # 市场效率系数
        for period in self.lookback_periods:
            df[f'market_efficiency_{period}'] = (
                df['close'].diff(period).abs() /
                df['high_low_range'].rolling(period).sum()
            )
            
        # 价格加速度
        df['price_acceleration'] = df['returns'].diff()
        
        # 趋势一致性
        df['trend_consistency'] = (
            (df['sma_5'] > df['sma_10']).astype(int) +
            (df['sma_10'] > df['sma_20']).astype(int) +
            (df['sma_20'] > df['sma_50']).astype(int)
        )
        
        return df 