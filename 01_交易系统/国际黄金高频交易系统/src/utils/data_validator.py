from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from loguru import logger

class DataValidator:
    """数据验证和清理工具类"""
    
    @staticmethod
    def validate_market_data(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证和清理市场数据
        
        Args:
            data: 原始市场数据
            
        Returns:
            清理后的市场数据，如果验证失败则返回 None
        """
        try:
            # 验证必要字段
            required_fields = ['time', 'symbol', 'source', 'open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"市场数据缺少必要字段: {field}")
                    return None
            
            # 验证数据类型
            if not isinstance(data['time'], datetime):
                data['time'] = datetime.fromisoformat(data['time'])
            
            # 验证数值字段
            numeric_fields = ['open', 'high', 'low', 'close', 'volume', 'bid_price', 'ask_price']
            for field in numeric_fields:
                if field in data and data[field] is not None:
                    try:
                        data[field] = Decimal(str(data[field]))
                    except (ValueError, TypeError):
                        logger.warning(f"市场数据字段 {field} 的值无效: {data[field]}")
                        return None
            
            # 验证数值范围
            if data['high'] < data['low']:
                logger.warning(f"市场数据 high 值小于 low 值: {data}")
                return None
            
            if data['close'] < data['low'] or data['close'] > data['high']:
                logger.warning(f"市场数据 close 值超出 high-low 范围: {data}")
                return None
            
            if data['open'] < data['low'] or data['open'] > data['high']:
                logger.warning(f"市场数据 open 值超出 high-low 范围: {data}")
                return None
            
            # 验证成交量
            if data['volume'] < 0:
                logger.warning(f"市场数据 volume 值为负数: {data}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"市场数据验证失败: {str(e)}")
            return None
    
    @staticmethod
    def validate_trading_signal(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证和清理交易信号
        
        Args:
            data: 原始交易信号数据
            
        Returns:
            清理后的交易信号数据，如果验证失败则返回 None
        """
        try:
            # 验证必要字段
            required_fields = ['time', 'symbol', 'signal_type', 'direction', 'price', 'confidence']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"交易信号缺少必要字段: {field}")
                    return None
            
            # 验证数据类型
            if not isinstance(data['time'], datetime):
                data['time'] = datetime.fromisoformat(data['time'])
            
            # 验证数值字段
            numeric_fields = ['price', 'confidence']
            for field in numeric_fields:
                try:
                    data[field] = Decimal(str(data[field]))
                except (ValueError, TypeError):
                    logger.warning(f"交易信号字段 {field} 的值无效: {data[field]}")
                    return None
            
            # 验证方向
            if data['direction'] not in ['buy', 'sell']:
                logger.warning(f"交易信号方向无效: {data['direction']}")
                return None
            
            # 验证置信度范围
            if not 0 <= data['confidence'] <= 1:
                logger.warning(f"交易信号置信度超出范围: {data['confidence']}")
                return None
            
            # 验证价格
            if data['price'] <= 0:
                logger.warning(f"交易信号价格无效: {data['price']}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"交易信号验证失败: {str(e)}")
            return None
    
    @staticmethod
    def validate_order(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证和清理订单数据
        
        Args:
            data: 原始订单数据
            
        Returns:
            清理后的订单数据，如果验证失败则返回 None
        """
        try:
            # 验证必要字段
            required_fields = ['order_id', 'time', 'symbol', 'order_type', 'direction', 'price', 'volume', 'status']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"订单数据缺少必要字段: {field}")
                    return None
            
            # 验证数据类型
            if not isinstance(data['time'], datetime):
                data['time'] = datetime.fromisoformat(data['time'])
            
            # 验证数值字段
            numeric_fields = ['price', 'volume']
            for field in numeric_fields:
                try:
                    data[field] = Decimal(str(data[field]))
                except (ValueError, TypeError):
                    logger.warning(f"订单数据字段 {field} 的值无效: {data[field]}")
                    return None
            
            # 验证方向
            if data['direction'] not in ['buy', 'sell']:
                logger.warning(f"订单方向无效: {data['direction']}")
                return None
            
            # 验证订单类型
            if data['order_type'] not in ['market', 'limit', 'stop', 'stop_limit']:
                logger.warning(f"订单类型无效: {data['order_type']}")
                return None
            
            # 验证订单状态
            if data['status'] not in ['pending', 'open', 'filled', 'cancelled', 'rejected']:
                logger.warning(f"订单状态无效: {data['status']}")
                return None
            
            # 验证价格和数量
            if data['price'] <= 0:
                logger.warning(f"订单价格无效: {data['price']}")
                return None
            
            if data['volume'] <= 0:
                logger.warning(f"订单数量无效: {data['volume']}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"订单数据验证失败: {str(e)}")
            return None
    
    @staticmethod
    def clean_historical_data(
        data: List[Dict[str, Any]],
        data_type: str,
        max_age_days: int = 30
    ) -> List[Dict[str, Any]]:
        """清理历史数据
        
        Args:
            data: 历史数据列表
            data_type: 数据类型 ('market_data', 'trading_signal', 'order')
            max_age_days: 最大保留天数
            
        Returns:
            清理后的数据列表
        """
        try:
            now = datetime.utcnow()
            cleaned_data = []
            
            for item in data:
                # 验证数据
                if data_type == 'market_data':
                    validated_item = DataValidator.validate_market_data(item)
                elif data_type == 'trading_signal':
                    validated_item = DataValidator.validate_trading_signal(item)
                elif data_type == 'order':
                    validated_item = DataValidator.validate_order(item)
                else:
                    logger.warning(f"未知的数据类型: {data_type}")
                    continue
                
                if validated_item is None:
                    continue
                
                # 检查数据年龄
                if (now - validated_item['time']).days > max_age_days:
                    continue
                
                cleaned_data.append(validated_item)
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"历史数据清理失败: {str(e)}")
            return [] 