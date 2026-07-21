from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from datetime import datetime
from src.models.deepseek_analyzer import DeepSeekAnalyzer
from src.utils.db_manager import DatabaseManager

class SignalGenerator:
    def __init__(self, deepseek_api_key: str):
        """
        初始化交易信号生成器
        
        Args:
            deepseek_api_key: DeepSeek API密钥
        """
        self.analyzer = DeepSeekAnalyzer(deepseek_api_key)
        self.db_manager = DatabaseManager()
        
    def _extract_price_levels(self, analysis: str) -> Dict[str, float]:
        """从分析文本中提取价格水平"""
        levels = {
            'entry_price': None,
            'stop_loss': None,
            'target_price': None
        }
        
        try:
            # 查找包含价格信息的行
            lines = analysis.split('\n')
            for line in lines:
                line = line.lower()
                # 提取进场价格
                if '进场价格' in line or '建议价格' in line:
                    prices = [float(s) for s in line.split() if s.replace('.', '').isdigit()]
                    if prices:
                        levels['entry_price'] = prices[0]
                
                # 提取止损价格
                if '止损' in line:
                    prices = [float(s) for s in line.split() if s.replace('.', '').isdigit()]
                    if prices:
                        levels['stop_loss'] = prices[0]
                
                # 提取目标价格
                if '目标价位' in line or '目标价格' in line:
                    prices = [float(s) for s in line.split() if s.replace('.', '').isdigit()]
                    if prices:
                        levels['target_price'] = prices[0]
        except Exception as e:
            print(f"提取价格水平时出错: {str(e)}")
            
        return levels
        
    def _calculate_signal_strength(self, 
                                 market_data: Dict[str, Any],
                                 ai_signal: str,
                                 risk_score: int) -> float:
        """计算信号强度"""
        # 基础分数
        base_score = 0.5
        
        # 根据AI信号调整
        if ai_signal == 'buy':
            base_score += 0.2
        elif ai_signal == 'sell':
            base_score -= 0.2
            
        # 根据RSI调整
        rsi = market_data['rsi']
        if rsi > 70:  # 超买
            base_score -= 0.1
        elif rsi < 30:  # 超卖
            base_score += 0.1
            
        # 根据趋势调整
        if market_data['trend'] == 1:  # 上涨趋势
            base_score += 0.1
        elif market_data['trend'] == -1:  # 下跌趋势
            base_score -= 0.1
            
        # 根据风险评分调整
        risk_adjustment = (10 - risk_score) / 20  # 转换为-0.5到0.5之间
        base_score += risk_adjustment
        
        # 确保分数在0到1之间
        return max(0, min(1, base_score))
        
    async def _save_signal(self, signal_data: Dict[str, Any]) -> None:
        """保存交易信号到数据库"""
        query = """
            INSERT INTO trading_signals (
                time, symbol, signal_type, direction, price,
                stop_loss, target_price, confidence, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            signal_data['timestamp'],
            signal_data['symbol'],
            signal_data['signal_type'],
            signal_data['direction'],
            signal_data['entry_price'],
            signal_data['stop_loss'],
            signal_data['target_price'],
            signal_data['confidence'],
            signal_data['metadata']
        )
        
        await self.db_manager.execute_query(query, *values)
        
    async def generate_signal(self, 
                            symbol: str,
                            lookback_hours: int = 24) -> Dict[str, Any]:
        """生成交易信号"""
        # 获取DeepSeek分析结果
        analysis_result = await self.analyzer.analyze_market(
            symbol=symbol,
            lookback_hours=lookback_hours
        )
        
        # 提取价格水平
        price_levels = self._extract_price_levels(analysis_result['raw_analysis'])
        
        # 计算信号强度
        signal_strength = self._calculate_signal_strength(
            market_data=analysis_result['market_data'],
            ai_signal=analysis_result['signal'],
            risk_score=analysis_result.get('risk_score', 5)
        )
        
        # 生成交易信号
        signal = {
            'timestamp': analysis_result['timestamp'],
            'symbol': symbol,
            'signal_type': 'ai_combined',  # 信号类型
            'direction': analysis_result['signal'],  # 交易方向
            'entry_price': price_levels['entry_price'],
            'stop_loss': price_levels['stop_loss'],
            'target_price': price_levels['target_price'],
            'confidence': signal_strength,
            'metadata': {
                'ai_analysis': analysis_result['raw_analysis'],
                'market_data': analysis_result['market_data'],
                'risk_score': analysis_result.get('risk_score', 5)
            }
        }
        
        # 保存信号到数据库
        await self._save_signal(signal)
        
        return signal
        
    async def generate_batch_signals(self,
                                   symbols: List[str],
                                   lookback_hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """批量生成交易信号"""
        signals = {}
        for symbol in symbols:
            try:
                signal = await self.generate_signal(symbol, lookback_hours)
                signals[symbol] = signal
            except Exception as e:
                print(f"生成{symbol}的交易信号时出错: {str(e)}")
                continue
        return signals
        
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """验证交易信号的有效性"""
        required_fields = [
            'timestamp', 'symbol', 'signal_type', 'direction',
            'entry_price', 'stop_loss', 'target_price', 'confidence'
        ]
        
        # 检查必需字段
        if not all(field in signal for field in required_fields):
            return False
            
        # 验证价格水平的逻辑性
        if signal['direction'] == 'buy':
            if not (signal['stop_loss'] < signal['entry_price'] < signal['target_price']):
                return False
        elif signal['direction'] == 'sell':
            if not (signal['stop_loss'] > signal['entry_price'] > signal['target_price']):
                return False
                
        # 验证置信度
        if not 0 <= signal['confidence'] <= 1:
            return False
            
        return True 