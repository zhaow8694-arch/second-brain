import os
import json
import aiohttp
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
from src.features.market_features import MarketFeatureGenerator

class DeepSeekAnalyzer:
    def __init__(self, api_key: str):
        """
        初始化DeepSeek分析器
        
        Args:
            api_key: DeepSeek API密钥
        """
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # 需要确认实际的API端点
        self.feature_generator = MarketFeatureGenerator()
        
    async def _call_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",  # 需要确认实际的模型名称
            "messages": messages,
            "temperature": 0.1  # 使用较低的temperature以获得更确定性的输出
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                if response.status != 200:
                    raise Exception(f"API调用失败: {await response.text()}")
                return await response.json()
                
    def _prepare_market_analysis_prompt(self, 
                                      market_data: pd.DataFrame,
                                      symbol: str) -> List[Dict[str, str]]:
        """准备市场分析提示"""
        # 提取最新的市场状态
        latest_data = market_data.iloc[-1]
        
        # 计算一些关键指标的变化
        price_change_24h = (
            (latest_data['close'] - market_data.iloc[-24]['close']) 
            / market_data.iloc[-24]['close'] 
            * 100 if len(market_data) >= 24 else 0
        )
        
        volume_change_24h = (
            (latest_data['volume'] - market_data.iloc[-24]['volume'])
            / market_data.iloc[-24]['volume']
            * 100 if len(market_data) >= 24 else 0
        )
        
        # 构建市场状态描述
        market_state = f"""
当前市场状态 ({symbol}):
- 最新价格: {latest_data['close']:.2f}
- 24小时价格变化: {price_change_24h:.2f}%
- 当前RSI: {latest_data['rsi']:.2f}
- MACD: {latest_data['macd']:.2f}
- 布林带位置: {latest_data['bb_position']:.2f}
- 成交量变化: {volume_change_24h:.2f}%
- 市场趋势: {'上涨' if latest_data['trend'] == 1 else '下跌' if latest_data['trend'] == -1 else '横盘'}
- 波动率: {latest_data['volatility']:.4f}
- 趋势强度: {latest_data['trend_strength_20']:.4f}
- 市场效率: {latest_data['market_efficiency_20']:.4f}
"""

        prompt = f"""
作为一个专业的金融市场分析AI，请基于以下市场数据进行分析并提供交易建议：

{market_state}

请提供：
1. 市场趋势分析
2. 支撑和阻力位预测
3. 短期（1小时）价格走势预测
4. 交易建议（包括建议的进场价格、止损位和目标价位）
5. 风险评估（1-10分，1最低风险，10最高风险）

请确保分析简洁明了，并给出具体的数值建议。
"""
        
        return [{"role": "user", "content": prompt}]
        
    async def analyze_market(self,
                           symbol: str,
                           lookback_hours: int = 24) -> Dict[str, Any]:
        """分析市场并生成交易建议"""
        # 获取市场数据
        end_time = datetime.now()
        start_time = end_time - pd.Timedelta(hours=lookback_hours)
        
        market_data = await self.feature_generator.generate_features(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time
        )
        
        if market_data.empty:
            raise ValueError(f"无法获取{symbol}的市场数据")
            
        # 准备API调用
        messages = self._prepare_market_analysis_prompt(market_data, symbol)
        
        # 调用API获取分析结果
        response = await self._call_api(messages)
        
        try:
            analysis = response['choices'][0]['message']['content']
            
            # 解析API响应
            result = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'raw_analysis': analysis,
                'market_data': {
                    'close': float(market_data.iloc[-1]['close']),
                    'volume': float(market_data.iloc[-1]['volume']),
                    'rsi': float(market_data.iloc[-1]['rsi']),
                    'trend': int(market_data.iloc[-1]['trend'])
                }
            }
            
            # 尝试从分析文本中提取具体建议
            try:
                # 这里可以添加更复杂的文本解析逻辑
                if "建议买入" in analysis.lower() or "看涨" in analysis:
                    result['signal'] = 'buy'
                elif "建议卖出" in analysis.lower() or "看跌" in analysis:
                    result['signal'] = 'sell'
                else:
                    result['signal'] = 'neutral'
                    
                # 提取风险评分
                risk_score = None
                for line in analysis.split('\n'):
                    if '风险评估' in line and '10' in line:
                        try:
                            risk_score = int(line.split(':')[-1].strip().split('/')[0])
                        except:
                            pass
                if risk_score is not None:
                    result['risk_score'] = risk_score
                    
            except Exception as e:
                print(f"解析分析结果时出错: {str(e)}")
                result['signal'] = 'neutral'
                result['risk_score'] = 5  # 默认中等风险
                
            return result
            
        except Exception as e:
            raise Exception(f"处理API响应时出错: {str(e)}")
            
    async def get_batch_analysis(self,
                               symbols: List[str],
                               lookback_hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """批量分析多个市场"""
        results = {}
        for symbol in symbols:
            try:
                result = await self.analyze_market(symbol, lookback_hours)
                results[symbol] = result
            except Exception as e:
                print(f"分析{symbol}时出错: {str(e)}")
                continue
        return results 