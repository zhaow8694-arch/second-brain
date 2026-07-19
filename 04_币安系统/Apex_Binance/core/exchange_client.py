"""
交易所客户端模块
封装CCXT接口，提供统一的交易接口
"""
import time
import logging
from typing import Dict, List, Optional, Tuple, Any

import ccxt
import pandas as pd
from config import Config as config

logger = logging.getLogger(__name__)


class ExchangeClient:
    """交易所客户端"""
    
    def __init__(self):
        self.exchange = None
        self.markets = {}
        self.symbols = []
        self.initialized = False
        
    def initialize(self, demo_mode: bool = True) -> bool:
        """初始化交易所连接"""
        try:
            logger.info("正在初始化交易所连接...")
            
            self.exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET,
                'timeout': 15000,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True
                },
                'enableRateLimit': True
            })
            
            if demo_mode:
                try:
                    self.exchange.enable_demo_trading(True)
                    logger.info("已启用模拟交易模式")
                except AttributeError:
                    logger.warning("模拟交易模式不支持，将使用实盘模式")
            
            # 加载市场信息
            self.markets = self.exchange.load_markets(True)
            
            # 过滤有效的交易对
            self.symbols = [
                symbol for symbol in config.SYMBOL_LIST 
                if symbol in self.markets
            ]
            
            # 设置双向持仓模式
            self._set_hedge_mode()
            
            self.initialized = True
            logger.info(f"交易所初始化完成，有效交易对: {len(self.symbols)}个")
            return True
            
        except Exception as e:
            logger.error(f"交易所初始化失败: {e}")
            return False
    
    def _set_hedge_mode(self) -> None:
        """设置双向持仓模式"""
        try:
            position_mode = self.exchange.fapiPrivateGetPositionSideDual()
            
            if str(position_mode.get('dualSidePosition')).lower() != 'true':
                logger.info("正在切换到双向持仓模式...")
                self.exchange.fapiPrivatePostPositionSideDual({'dualSidePosition': 'true'})
                logger.info("双向持仓模式设置成功")
            else:
                logger.debug("账户已是双向持仓模式")
                
        except Exception as e:
            logger.warning(f"设置双向持仓模式失败: {e}")
    
    def get_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        try:
            balance = self.exchange.fetch_balance(params={'type': 'future'})
            
            result = {
                'total': float(balance.get('total', {}).get('USDT', 0)),
                'free': float(balance.get('free', {}).get('USDT', 0)),
                'used': float(balance.get('used', {}).get('USDT', 0))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            return {'total': 0.0, 'free': 0.0, 'used': 0.0}
    
    def get_positions(self) -> Dict[str, Dict]:
        """获取所有持仓"""
        try:
            raw_positions = self.exchange.fetch_positions()
            
            positions = {}
            for pos in raw_positions:
                try:
                    contracts_str = pos.get('contracts', '0')
                    contracts = abs(float(contracts_str)) if contracts_str is not None else 0
                    
                    if contracts > 0:
                        symbol = pos['symbol'].split('/')[0].replace(':', '')
                        
                        # 安全地获取数值字段
                        entry_price = pos.get('entryPrice', 0)
                        mark_price = pos.get('markPrice', 0)
                        unrealized_pnl = pos.get('unrealizedPnl', 0)
                        leverage = pos.get('leverage', 1)
                        
                        positions[symbol] = {
                            'symbol': symbol,  # 短格式: DOT
                            'side': pos.get('side', 'unknown').lower(),
                            'contracts': contracts,
                            'entry_price': float(entry_price) if entry_price is not None else 0,
                            'mark_price': float(mark_price) if mark_price is not None else 0,
                            'unrealized_pnl': float(unrealized_pnl) if unrealized_pnl is not None else 0,
                            'leverage': float(leverage) if leverage is not None else 1
                        }
                except (ValueError, TypeError) as e:
                    logger.warning(f"解析持仓数据失败 {pos.get('symbol', 'unknown')}: {e}")
                    continue
            
            return positions
            
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return {}
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            logger.warning(f"获取K线数据失败 {symbol} {timeframe}: {e}")
            return None
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """设置杠杆"""
        try:
            self.exchange.set_leverage(leverage, symbol)
            logger.debug(f"设置杠杆成功: {symbol} {leverage}x")
            return True
        except Exception as e:
            logger.warning(f"设置杠杆失败 {symbol} {leverage}x: {e}")
            return False
    
    def create_market_order(self, symbol: str, side: str, amount: float, params: Dict = None) -> Optional[Dict]:
        """创建市价单"""
        try:
            if params is None:
                params = {}
            
            order = self.exchange.create_market_order(symbol, side, amount, params)
            logger.info(f"市价单创建成功: {symbol} {side} {amount}")
            return order
            
        except Exception as e:
            logger.error(f"创建市价单失败 {symbol} {side} {amount}: {e}")
            return None
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params: Dict = None) -> Optional[Dict]:
        """创建限价单"""
        try:
            if params is None:
                params = {}
            
            order = self.exchange.create_limit_order(symbol, side, amount, price, params)
            logger.info(f"限价单创建成功: {symbol} {side} {amount} @ {price}")
            return order
            
        except Exception as e:
            logger.error(f"创建限价单失败 {symbol} {side} {amount} @ {price}: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """取消订单"""
        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"订单取消成功: {symbol} {order_id}")
            return True
        except Exception as e:
            logger.error(f"取消订单失败 {symbol} {order_id}: {e}")
            return False
    
    def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """获取行情数据"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            if not ticker:
                return None
            
            # 安全地获取价格数据
            last_price = ticker.get('last')
            if last_price is None:
                last_price = ticker.get('close', 0)
            
            return {
                'symbol': symbol,
                'last': float(last_price) if last_price is not None else 0,
                'bid': float(ticker.get('bid', 0)) if ticker.get('bid') is not None else 0,
                'ask': float(ticker.get('ask', 0)) if ticker.get('ask') is not None else 0,
                'high': float(ticker.get('high', 0)) if ticker.get('high') is not None else 0,
                'low': float(ticker.get('low', 0)) if ticker.get('low') is not None else 0,
                'volume': float(ticker.get('volume', 0)) if ticker.get('volume') is not None else 0,
                'open': float(ticker.get('open', 0)) if ticker.get('open') is not None else 0
            }
        except Exception as e:
            logger.warning(f"获取行情数据失败 {symbol}: {e}")
            return None
    
    def fetch_funding_rate(self, symbol: str) -> Optional[float]:
        """获取资金费率"""
        try:
            funding_data = self.exchange.fetch_funding_rate(symbol)
            return abs(float(funding_data.get('fundingRate', 0)))
        except Exception as e:
            logger.warning(f"获取资金费率失败 {symbol}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """测试连接"""
        if self.exchange is None:
            logger.error("交易所对象未初始化")
            return False
        try:
            balance = self.get_balance()
            if balance['total'] > 0:
                logger.info("交易所连接测试成功")
                return True
            logger.error("交易所连接测试失败: 余额为0或API密钥无效")
            return False
        except Exception as e:
            logger.error(f"交易所连接测试失败: {e}")
            return False


# 创建全局交易所客户端实例
exchange_client = ExchangeClient()