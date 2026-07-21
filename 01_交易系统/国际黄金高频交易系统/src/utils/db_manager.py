from typing import Any, Dict, List, Optional
import asyncio
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis
from loguru import logger
from src.config.database import db_settings

class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self):
        self._pg_pool = None
        self._redis_client = None
        self._initialized = False
        
    async def initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return
            
        try:
            # 初始化PostgreSQL连接池
            self._pg_pool = await asyncpg.create_pool(
                **db_settings.get_postgres_config()
            )
            
            # 初始化Redis客户端
            self._redis_client = redis.Redis(
                **db_settings.get_redis_config(),
                decode_responses=True
            )
            
            self._initialized = True
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
            
    async def close(self):
        """关闭数据库连接"""
        if not self._initialized:
            return
            
        try:
            if self._pg_pool:
                await self._pg_pool.close()
            if self._redis_client:
                await self._redis_client.close()
                
            self._initialized = False
            logger.info("Database connections closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
            raise
            
    @asynccontextmanager
    async def get_pg_connection(self):
        """获取PostgreSQL连接
        
        Yields:
            asyncpg.Connection: PostgreSQL连接对象
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._pg_pool.acquire() as connection:
            yield connection
            
    async def execute_query(self, query: str, *args) -> Any:
        """执行SQL查询
        
        Args:
            query (str): SQL查询语句
            *args: 查询参数
            
        Returns:
            Any: 查询结果
        """
        async with self.get_pg_connection() as conn:
            return await conn.execute(query, *args)
            
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """获取单条记录
        
        Args:
            query (str): SQL查询语句
            *args: 查询参数
            
        Returns:
            Optional[Dict[str, Any]]: 查询结果
        """
        async with self.get_pg_connection() as conn:
            return await conn.fetchrow(query, *args)
            
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """获取多条记录
        
        Args:
            query (str): SQL查询语句
            *args: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        async with self.get_pg_connection() as conn:
            return await conn.fetch(query, *args)
            
    async def execute_many(self, query: str, args_list: List[tuple]) -> Any:
        """批量执行SQL语句
        
        Args:
            query (str): SQL语句
            args_list (List[tuple]): 参数列表
            
        Returns:
            Any: 执行结果
        """
        async with self.get_pg_connection() as conn:
            return await conn.executemany(query, args_list)
            
    async def set_cache(self, key: str, value: Any, expire: int = 3600):
        """设置缓存
        
        Args:
            key (str): 缓存键
            value (Any): 缓存值
            expire (int): 过期时间(秒)
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            await self._redis_client.set(key, str(value), ex=expire)
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            
    async def get_cache(self, key: str) -> Optional[str]:
        """获取缓存
        
        Args:
            key (str): 缓存键
            
        Returns:
            Optional[str]: 缓存值
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            return await self._redis_client.get(key)
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None
            
    async def delete_cache(self, key: str):
        """删除缓存
        
        Args:
            key (str): 缓存键
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            await self._redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            
    async def clear_cache(self):
        """清空缓存"""
        if not self._initialized:
            await self.initialize()
            
        try:
            await self._redis_client.flushdb()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

# 创建全局数据库管理器实例
db_manager = DatabaseManager() 