from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

class BaseExecutor(ABC):
    """交易执行器基类"""
    
    def __init__(self, api_key: str, api_secret: str, test_mode: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.test_mode = test_mode
        
    @abstractmethod
    async def open_position(self,
                          symbol: str,
                          direction: str,
                          volume: float,
                          price: Optional[float] = None,
                          stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None) -> Dict[str, Any]:
        """开仓"""
        pass
        
    @abstractmethod
    async def close_position(self,
                           position_id: str,
                           volume: Optional[float] = None) -> Dict[str, Any]:
        """平仓"""
        pass
        
    @abstractmethod
    async def modify_position(self,
                            position_id: str,
                            stop_loss: Optional[float] = None,
                            take_profit: Optional[float] = None) -> Dict[str, Any]:
        """修改持仓"""
        pass
        
    @abstractmethod
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取持仓"""
        pass
        
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        pass
        
    @abstractmethod
    async def execute_batch_orders(self,
                                 orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量执行订单"""
        pass 