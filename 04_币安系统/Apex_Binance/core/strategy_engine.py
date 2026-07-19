"""
策略引擎模块
负责交易信号生成和策略逻辑
"""
import time
import logging
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
from config import Config as config
from core.exchange_client import exchange_client
from core.risk_manager import risk_manager

logger = logging.getLogger(__name__)


class StrategyEngine:
    """策略引擎"""
    
    def __init__(self):
        self.data_cache = {}  # K线数据缓存
        self.funding_rates = {}  # 资金费率缓存
        self.last_funding_fetch = 0
        self.last_scan_index = 0
        self._max_cache_size = 100
        
    def get_cached_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """获取缓存的K线数据"""
        # 兼容短格式: ETH -> ETH/USDT
        full_symbol = symbol if '/' in symbol else f"{symbol}/USDT"
        cache_key = f"{full_symbol}_{timeframe}"
        cache_time = self._get_cache_time(timeframe)
        
        if cache_key in self.data_cache:
            cache_entry = self.data_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < cache_time:
                return cache_entry['data']
        
        # 缓存失效，重新获取数据
        df = exchange_client.fetch_ohlcv(full_symbol, timeframe)
        if df is not None:
            if len(self.data_cache) >= self._max_cache_size:
                oldest_key = min(self.data_cache, key=lambda k: self.data_cache[k]['timestamp'])
                del self.data_cache[oldest_key]
            self.data_cache[cache_key] = {
                'timestamp': time.time(),
                'data': df
            }
        
        return df
    
    def _get_cache_time(self, timeframe: str) -> int:
        """获取缓存时间（秒）"""
        cache_times = {
            '15m': 120,      # 2分钟
            '1h': 300,       # 5分钟
            '4h': 600,       # 10分钟
            '1d': 3600,      # 1小时
        }
        return cache_times.get(timeframe, 300)
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Z-Wei: 计算 ADX 判断市场趋势强度
        ADX > 30: 强趋势, ADX > 20: 弱趋势, ADX <= 20: 震荡
        """
        if len(df) < period * 2:
            return 0.0
        
        high, low, close = df['high'], df['low'], df['close']
        prev_close = close.shift(1)

        tr = pd.DataFrame({
            'tr1': high - low,
            'tr2': (high - prev_close).abs(),
            'tr3': (low - prev_close).abs()
        }).max(axis=1)
        atr = tr.ewm(alpha=1 / period, adjust=False).mean()

        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0))
        minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0))

        plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr.replace(0, 1e-10)
        minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr.replace(0, 1e-10)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.ewm(alpha=1 / period, adjust=False).mean()

        result = float(adx.iloc[-1])
        return result if not pd.isna(result) else 0.0

    def _is_trending(self, df: pd.DataFrame) -> bool:
        """Z-Wei: 震荡市不交易 — ADX < threshold 则跳过"""
        adx = self._calculate_adx(df, period=14)
        return adx >= config.ADX_TRENDING_THRESHOLD

    def _get_market_regime(self, df: pd.DataFrame) -> str:
        """
        Z-Wei: 市场状态分类
        'strong_trend' | 'weak_trend' | 'ranging'
        """
        adx = self._calculate_adx(df, period=14)
        if adx >= config.ADX_STRONG_TREND:
            return 'strong_trend'
        elif adx >= config.ADX_TRENDING_THRESHOLD:
            return 'weak_trend'
        return 'ranging'

    def _is_dangerous_candle(self, df: pd.DataFrame, window: int = 20) -> bool:
        """
        Z-Wei: 实体突然放大 → FVG/订单失衡 → 危险，跳过信号
        """
        if len(df) < window + 1:
            return False

        bodies = abs(df['close'] - df['open'])
        latest_body = bodies.iloc[-1]
        avg_body = bodies.iloc[-(window + 1):-1].mean()

        if avg_body <= 0:
            return False

        return latest_body / avg_body > config.DANGEROUS_BODY_MULTIPLIER

    def _score_breakout_quality(self, df: pd.DataFrame, direction: str, window: int = 20) -> float:
        """
        Z-Wei突破质量评分 (0-1):
        - 实体占比 (body / range): 0.5 权重
        - 突兀度惩罚: 0.3 权重
        - 收线位置: 0.2 权重
        """
        if len(df) < window + 1:
            return 0.5

        latest = df.iloc[-1]
        total_range = latest['high'] - latest['low']

        # 1. 实体占比
        body = abs(latest['close'] - latest['open'])
        body_ratio = body / total_range if total_range > 0 else 0

        # 2. 突兀度惩罚
        recent_ranges = (df['high'] - df['low']).iloc[-(window + 1):-1]
        avg_range = float(recent_ranges.mean())
        expansion_ratio = total_range / avg_range if avg_range > 0 else 1.0

        if expansion_ratio > config.SIGNAL_EXPANSION_MAX:
            expansion_score = 0.2
        elif expansion_ratio > config.SIGNAL_EXPANSION_MAX * 0.75:
            expansion_score = 0.5
        else:
            expansion_score = 1.0

        # 3. 收线位置
        if total_range > 0:
            close_pos = (latest['close'] - latest['low']) / total_range
        else:
            close_pos = 0.5

        if direction == 'long':
            pos_score = close_pos
        else:
            pos_score = 1 - close_pos

        quality = body_ratio * 0.50 + expansion_score * 0.30 + pos_score * 0.20
        return round(min(max(quality, 0.0), 1.0), 2)
    
    def update_funding_rates(self) -> None:
        """更新资金费率"""
        if time.time() - self.last_funding_fetch < 3600:
            return
        
        try:
            for symbol in exchange_client.symbols:
                try:
                    rate = exchange_client.fetch_funding_rate(symbol)
                    if rate is not None:
                        short_sym = symbol.split('/')[0]
                        self.funding_rates[short_sym] = rate
                except Exception:
                    continue
            self.last_funding_fetch = time.time()
            logger.debug(f"资金费率更新完成: {len(self.funding_rates)}个币种")
        except Exception as e:
            logger.warning(f"更新资金费率失败: {e}")
    
    def calculate_indicators(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """计算技术指标"""
        if df is None or len(df) < 50:
            return df
        
        df = df.copy()
        
        if timeframe == '4h':
            # 4小时图：长期趋势指标
            df['ema60'] = df['close'].ewm(span=60).mean()
            df['ema576'] = df['close'].ewm(span=576).mean()
            
        elif timeframe == '1h':
            # 1小时图：中期趋势指标
            df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['ema60'] = df['close'].ewm(span=60).mean()
            df['macd'] = df['ema12'] - df['ema26']
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['signal']
            
        elif timeframe == '15m':
            # 15分钟图：短期交易指标
            df['ema14'] = df['close'].ewm(span=14).mean()
            df['ema21'] = df['close'].ewm(span=21).mean()
            df['ema60'] = df['close'].ewm(span=60).mean()
            
            # MACD
            df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema12'] - df['ema26']
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['signal']
            
            # 成交量指标
            df['vol_sma20'] = df['volume'].rolling(20).mean()
            
            # ATR计算
            df['prev_close'] = df['close'].shift(1)
            df['tr'] = df.apply(
                lambda row: max(
                    row['high'] - row['low'],
                    abs(row['high'] - row['prev_close']),
                    abs(row['low'] - row['prev_close'])
                ) if not pd.isna(row['prev_close']) else row['high'] - row['low'],
                axis=1
            )
            df['atr'] = df['tr'].ewm(alpha=1/14).mean()
            
            # RSI计算
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            loss = loss.replace(0, 1e-10)
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            df['rsi'] = df['rsi'].fillna(50)
        
        return df
    
    def generate_signal(self, symbol: str) -> Optional[Dict]:
        """生成交易信号"""
        try:
            # 获取多时间框架数据
            df_15m = self.get_cached_data(symbol, '15m')
            df_1h = self.get_cached_data(symbol, '1h')
            df_4h = self.get_cached_data(symbol, '4h')
            
            if df_15m is None or df_1h is None or df_4h is None:
                return None
            
            # ===== Z-Wei 市场状态过滤 =====
            # 1. 震荡市跳过
            if not self._is_trending(df_15m):
                logger.debug(f"{symbol} ADX震荡市({self._calculate_adx(df_15m):.1f})，跳过")
                return None
            
            # 2. 危险K线跳过
            if self._is_dangerous_candle(df_15m):
                logger.debug(f"{symbol} 检测到危险K线，跳过")
                return None
            # ===============================
            
            # 计算指标
            df_15m = self.calculate_indicators(df_15m, '15m')
            df_1h = self.calculate_indicators(df_1h, '1h')
            df_4h = self.calculate_indicators(df_4h, '4h')
            
            if len(df_15m) < 50 or len(df_1h) < 50:
                return None
            
            # 获取最新数据
            latest_15m = df_15m.iloc[-1]
            latest_1h = df_1h.iloc[-1]
            latest_4h = df_4h.iloc[-1]
            
            # 趋势判断
            trend_4h = self._check_trend(df_4h)
            trend_1h = self._check_trend(df_1h)
            
            # 动量判断
            momentum = self._check_momentum(df_15m)
            
            # 成交量确认
            volume_confirmation = self._check_volume(df_15m)
            
            # 生成信号
            signal = self._generate_trading_signal(
                trend_4h, trend_1h, momentum, volume_confirmation
            )
            
            if signal:
                # 计算ATR用于仓位管理
                atr = latest_15m.get('atr', latest_15m['close'] * 0.02)
                
                # Z-Wei: 突破质量评分 + 市场状态
                quality = self._score_breakout_quality(df_15m, signal['direction'])
                if quality < 0.4:
                    logger.debug(f"{symbol} 突破质量过低({quality:.2f})，丢弃信号")
                    return None
                
                signal.update({
                    'symbol': symbol,
                    'current_price': latest_15m['close'],
                    'atr': atr,
                    'timestamp': time.time(),
                    'trend_4h': trend_4h,
                    'trend_1h': trend_1h,
                    'momentum': momentum,
                    'volume_confirmation': volume_confirmation,
                    'breakout_quality': quality,
                    'market_regime': self._get_market_regime(df_15m),
                })
                
                logger.debug(f"生成信号: {symbol} - {signal['direction']}")
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"生成信号失败 {symbol}: {e}")
            return None
    
    def _check_trend(self, df: pd.DataFrame) -> str:
        """检查趋势方向"""
        if len(df) < 20:
            return 'neutral'
        
        # 简单趋势判断：价格与EMA的关系
        if 'ema60' in df.columns:
            latest_close = df['close'].iloc[-1]
            ema60 = df['ema60'].iloc[-1]
            
            if latest_close > ema60 * 1.005:
                return 'bullish'
            elif latest_close < ema60 * 0.995:
                return 'bearish'
        
        return 'neutral'
    
    def _check_momentum(self, df: pd.DataFrame) -> str:
        """检查动量"""
        if len(df) < 20:
            return 'neutral'
        
        rsi = None
        if 'rsi' in df.columns:
            rsi = df['rsi'].iloc[-1]
        
        macd_bullish = False
        macd_bearish = False
        if 'macd_hist' in df.columns:
            macd_hist = df['macd_hist'].iloc[-1]
            prev_macd_hist = df['macd_hist'].iloc[-2] if len(df) > 1 else 0
            macd_bullish = macd_hist > 0 and macd_hist > prev_macd_hist
            macd_bearish = macd_hist < 0 and macd_hist < prev_macd_hist
        
        # 综合RSI和MACD判断
        if rsi is not None:
            if rsi > 70:
                if macd_bearish:
                    return 'bearish_momentum'
                return 'overbought'
            elif rsi < 30:
                if macd_bullish:
                    return 'bullish_momentum'
                return 'oversold'
        
        if macd_bullish:
            return 'bullish_momentum'
        if macd_bearish:
            return 'bearish_momentum'
        
        return 'neutral'
    
    def _check_volume(self, df: pd.DataFrame) -> bool:
        """检查成交量确认"""
        if len(df) < 20:
            return False
        
        if 'vol_sma20' in df.columns and 'volume' in df.columns:
            latest_volume = df['volume'].iloc[-1]
            volume_sma = df['vol_sma20'].iloc[-1]
            
            # 成交量大于均线即可（不强制放量）
            return latest_volume >= volume_sma * 1.0
        
        return False
    
    def _generate_trading_signal(self, trend_4h: str, trend_1h: str, 
                                momentum: str, volume_confirmation: bool) -> Optional[Dict]:
        """生成交易信号"""
        
        # 强趋势信号（无需成交量确认）
        if trend_4h == 'bullish' and trend_1h == 'bullish' and momentum == 'bullish_momentum':
            return {
                'direction': 'long',
                'strength': 'strong',
                'reason': '强趋势共振'
            }
        
        if trend_4h == 'bearish' and trend_1h == 'bearish' and momentum == 'bearish_momentum':
            return {
                'direction': 'short',
                'strength': 'strong',
                'reason': '强趋势共振'
            }
        
        # 普通信号（需要成交量确认）
        if volume_confirmation:
            # 多头信号条件
            if (trend_4h in ['bullish', 'neutral'] and 
                trend_1h == 'bullish' and
                momentum in ['bullish_momentum', 'oversold']):
                
                return {
                    'direction': 'long',
                    'strength': 'medium',
                    'reason': '趋势共振 + 放量确认'
                }
            
            # 空头信号条件
            if (trend_4h in ['bearish', 'neutral'] and 
                trend_1h == 'bearish' and
                momentum in ['bearish_momentum', 'overbought']):
                
                return {
                    'direction': 'short',
                    'strength': 'medium',
                    'reason': '趋势共振 + 放量确认'
                }
        
        return None
    
    def scan_markets(self) -> List[Dict]:
        """扫描市场寻找交易机会"""
        signals = []
        
        if not exchange_client.symbols:
            logger.warning("没有可用的交易对")
            return signals
        
        # 更新资金费率
        self.update_funding_rates()
        
        # 从上次扫描的位置开始
        start_idx = self.last_scan_index
        symbols_to_scan = exchange_client.symbols[start_idx:] + exchange_client.symbols[:start_idx]
        
        for i, symbol in enumerate(symbols_to_scan[:10]):  # 每次扫描10个币种
            signal = self.generate_signal(symbol)
            if signal:
                signals.append(signal)
            
            # 更新扫描索引
            self.last_scan_index = (start_idx + i + 1) % len(exchange_client.symbols)
            
            # 短暂暂停，避免API限制
            time.sleep(0.1)
        
        return signals
    
    def get_market_analysis(self, symbol: str) -> Dict:
        """获取市场分析报告"""
        try:
            df_15m = self.get_cached_data(symbol, '15m')
            df_1h = self.get_cached_data(symbol, '1h')
            
            if df_15m is None or df_1h is None:
                return {}
            
            df_15m = self.calculate_indicators(df_15m, '15m')
            df_1h = self.calculate_indicators(df_1h, '1h')
            
            latest_15m = df_15m.iloc[-1]
            latest_1h = df_1h.iloc[-1]
            
            analysis = {
                'symbol': symbol,
                'current_price': latest_15m['close'],
                'trend_15m': self._check_trend(df_15m),
                'trend_1h': self._check_trend(df_1h),
                'momentum': self._check_momentum(df_15m),
                'volume_status': 'high' if self._check_volume(df_15m) else 'normal',
                'atr': latest_15m.get('atr', 0),
                'rsi': latest_15m.get('rsi', 50),
                'timestamp': time.time()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"获取市场分析失败 {symbol}: {e}")
            return {}

    def get_position_momentum(self, symbol: str, timeframe: str = '15m') -> Dict:
        """
        Z-Wei: 供平仓模块调用的持仓动量快照
        返回: {'rsi': float, 'rsi_prev': float}
        """
        df = self.get_cached_data(symbol, timeframe)
        if df is None or len(df) < 3:
            return {}
        
        df = self.calculate_indicators(df, timeframe)
        result = {}
        if 'rsi' in df.columns and len(df) >= 2:
            result['rsi'] = float(df['rsi'].iloc[-1])
            result['rsi_prev'] = float(df['rsi'].iloc[-2])
        return result


# 创建全局策略引擎实例
strategy_engine = StrategyEngine()