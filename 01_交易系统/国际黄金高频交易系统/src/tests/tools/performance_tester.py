import time
import asyncio
import psutil
import numpy as np
from typing import Dict, Any, Callable, List
from loguru import logger

class PerformanceTester:
    """性能测试器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化性能测试器
        
        Args:
            config: 配置字典
        """
        self._config = config
        self._results = {}
        
    async def measure_performance(
        self,
        test_name: str,
        func: Callable,
        *args,
        iterations: int = 1,
        **kwargs
    ) -> Dict[str, float]:
        """测量函数性能
        
        Args:
            test_name: 测试名称
            func: 要测试的函数
            *args: 函数的位置参数
            iterations: 重复测试次数
            **kwargs: 函数的关键字参数
            
        Returns:
            性能指标字典
        """
        execution_times = []
        memory_usages = []
        cpu_usages = []
        
        process = psutil.Process()
        
        for i in range(iterations):
            # 记录初始状态
            start_time = time.perf_counter()
            start_memory = process.memory_info().rss
            start_cpu = process.cpu_percent()
            
            # 执行函数
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in performance test {test_name}: {e}")
                continue
                
            # 记录结束状态
            end_time = time.perf_counter()
            end_memory = process.memory_info().rss
            end_cpu = process.cpu_percent()
            
            # 计算指标
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = (end_cpu + start_cpu) / 2
            
            execution_times.append(execution_time)
            memory_usages.append(memory_usage)
            cpu_usages.append(cpu_usage)
            
            # 等待系统状态恢复
            await asyncio.sleep(0.1)
            
        # 计算统计指标
        metrics = {
            'execution_time': np.mean(execution_times),
            'execution_time_std': np.std(execution_times),
            'memory_usage': np.mean(memory_usages),
            'memory_usage_std': np.std(memory_usages),
            'cpu_usage': np.mean(cpu_usages),
            'cpu_usage_std': np.std(cpu_usages),
            'iterations': iterations
        }
        
        # 保存结果
        self._results[test_name] = metrics
        
        return metrics
        
    def get_test_results(self, test_name: str = None) -> Dict[str, Dict[str, float]]:
        """获取测试结果
        
        Args:
            test_name: 测试名称，如果为None则返回所有结果
            
        Returns:
            测试结果字典
        """
        if test_name:
            return {test_name: self._results.get(test_name, {})}
        return self._results
        
    def compare_results(
        self,
        test_name1: str,
        test_name2: str
    ) -> Dict[str, float]:
        """比较两次测试结果
        
        Args:
            test_name1: 第一个测试名称
            test_name2: 第二个测试名称
            
        Returns:
            性能改进百分比
        """
        result1 = self._results.get(test_name1, {})
        result2 = self._results.get(test_name2, {})
        
        if not result1 or not result2:
            return {}
            
        improvements = {}
        for metric in ['execution_time', 'memory_usage', 'cpu_usage']:
            if metric in result1 and metric in result2:
                improvement = (result1[metric] - result2[metric]) / result1[metric] * 100
                improvements[f'{metric}_improvement'] = improvement
                
        return improvements
        
    def generate_report(self, test_name: str = None) -> str:
        """生成性能测试报告
        
        Args:
            test_name: 测试名称，如果为None则生成所有测试的报告
            
        Returns:
            测试报告字符串
        """
        results = self.get_test_results(test_name)
        
        report = []
        report.append("Performance Test Report")
        report.append("=" * 50)
        
        for name, metrics in results.items():
            report.append(f"\nTest: {name}")
            report.append("-" * 30)
            
            if metrics:
                report.append(f"Execution Time: {metrics['execution_time']:.4f}s ± {metrics['execution_time_std']:.4f}s")
                report.append(f"Memory Usage: {metrics['memory_usage']/1024/1024:.2f}MB ± {metrics['memory_usage_std']/1024/1024:.2f}MB")
                report.append(f"CPU Usage: {metrics['cpu_usage']:.1f}% ± {metrics['cpu_usage_std']:.1f}%")
                report.append(f"Iterations: {metrics['iterations']}")
            else:
                report.append("No metrics available")
                
        return "\n".join(report)
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        pass 