import asyncio
import concurrent.futures
from functools import lru_cache
from typing import List, Dict, Any, Callable, TypeVar, Optional
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import os
import time
from loguru import logger

T = TypeVar('T')

class PerformanceOptimizer:
    """性能优化器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化性能优化器
        
        Args:
            config: 配置字典
        """
        self._config = config
        self._max_workers = config.get('max_workers', multiprocessing.cpu_count())
        self._chunk_size = config.get('chunk_size', 1000)
        self._thread_pool = ThreadPoolExecutor(max_workers=self._max_workers)
        self._process_pool = ProcessPoolExecutor(max_workers=self._max_workers)
        self._cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(self._cache_dir, exist_ok=True)
        
    @property
    def executor(self) -> ThreadPoolExecutor:
        """获取线程池执行器"""
        return self._thread_pool
        
    @property
    def process_executor(self) -> ProcessPoolExecutor:
        """获取进程池执行器"""
        return self._process_pool
        
    async def parallel_process(
        self,
        items: List[T],
        process_func: Callable[[T], Any],
        chunk_size: int = 100,
        use_processes: bool = False
    ) -> List[Any]:
        """并行处理数据
        
        Args:
            items: 要处理的数据项列表
            process_func: 处理函数
            chunk_size: 每个块的大小
            use_processes: 是否使用进程池
            
        Returns:
            处理结果列表
        """
        results = []
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        async def process_chunk(chunk: List[T]) -> List[Any]:
            if use_processes:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.process_executor,
                    lambda: [process_func(item) for item in chunk]
                )
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.executor,
                    lambda: [process_func(item) for item in chunk]
                )
                
        tasks = [process_chunk(chunk) for chunk in chunks]
        chunk_results = await asyncio.gather(*tasks)
        
        for chunk_result in chunk_results:
            results.extend(chunk_result)
            
        return results
        
    @lru_cache(maxsize=1000)
    def cached_computation(self, func: Callable, *args, **kwargs) -> Any:
        """缓存计算结果
        
        Args:
            func: 计算函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            计算结果
        """
        return func(*args, **kwargs)
        
    async def parallel_data_generation(
        self,
        generator_func: Callable,
        params_list: List[Dict[str, Any]],
        chunk_size: int = 10
    ) -> List[pd.DataFrame]:
        """并行生成数据
        
        Args:
            generator_func: 数据生成函数
            params_list: 参数列表
            chunk_size: 每个块的大小
            
        Returns:
            生成的数据列表
        """
        async def generate_chunk(params: List[Dict[str, Any]]) -> List[pd.DataFrame]:
            results = []
            for params in params:
                try:
                    result = await generator_func(**params)
                    results.append(result)
                except Exception as e:
                    logger.error(f"数据生成错误: {str(e)}")
                    results.append(None)
            return results
            
        chunks = [params_list[i:i + chunk_size] for i in range(0, len(params_list), chunk_size)]
        tasks = [generate_chunk(chunk) for chunk in chunks]
        chunk_results = await asyncio.gather(*tasks)
        
        results = []
        for chunk_result in chunk_results:
            results.extend([r for r in chunk_result if r is not None])
            
        return results
        
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """优化DataFrame的内存使用
        
        Args:
            df: 原始DataFrame
            
        Returns:
            优化后的DataFrame
        """
        # 优化数值类型列
        for col in df.select_dtypes(include=['int']).columns:
            c_min = df[col].min()
            c_max = df[col].max()
            
            if c_min >= 0:
                if c_max < 255:
                    df[col] = df[col].astype(np.uint8)
                elif c_max < 65535:
                    df[col] = df[col].astype(np.uint16)
                elif c_max < 4294967295:
                    df[col] = df[col].astype(np.uint32)
            else:
                if c_min > -128 and c_max < 127:
                    df[col] = df[col].astype(np.int8)
                elif c_min > -32768 and c_max < 32767:
                    df[col] = df[col].astype(np.int16)
                elif c_min > -2147483648 and c_max < 2147483647:
                    df[col] = df[col].astype(np.int32)
                    
        # 优化浮点类型列
        for col in df.select_dtypes(include=['float']).columns:
            df[col] = df[col].astype(np.float32)
            
        # 优化字符串类型列
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # 如果唯一值比例小于50%
                df[col] = df[col].astype('category')
                
        return df
        
    def parallel_apply(self, df: pd.DataFrame, func, *args, **kwargs) -> pd.DataFrame:
        """并行应用函数到DataFrame
        
        Args:
            df: 输入DataFrame
            func: 要应用的函数
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数
            
        Returns:
            处理后的DataFrame
        """
        chunks = np.array_split(df, self._chunk_size)
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            results = list(executor.map(lambda x: func(x, *args, **kwargs), chunks))
        return pd.concat(results)
        
    def parallel_process(self, data: list, func, *args, **kwargs) -> list:
        """并行处理列表数据
        
        Args:
            data: 输入数据列表
            func: 要应用的函数
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数
            
        Returns:
            处理后的列表
        """
        chunks = [data[i:i + self._chunk_size] for i in range(0, len(data), self._chunk_size)]
        with ProcessPoolExecutor(max_workers=self._max_workers) as executor:
            results = list(executor.map(lambda x: func(x, *args, **kwargs), chunks))
        return [item for sublist in results for item in sublist]
        
    def cleanup(self):
        """清理资源"""
        self._thread_pool.shutdown()
        self._process_pool.shutdown()
        logger.info("Performance optimizer resources cleaned up")
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        self.cleanup() 