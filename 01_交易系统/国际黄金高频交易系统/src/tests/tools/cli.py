import click
import asyncio
import os
from typing import List, Optional
from .data_generator import TestDataGenerator
from .result_analyzer import TestResultAnalyzer
from .report_generator import ReportGenerator
from .environment_manager import EnvironmentManager

@click.group()
def cli():
    """量化交易系统测试工具"""
    pass

@cli.group()
def data():
    """测试数据生成工具"""
    pass

@data.command()
@click.option('--type', type=click.Choice(['market', 'trade', 'system', 'orderbook', 'history', 'performance', 'error', 'scenario']), required=True)
@click.option('--output', '-o', required=True, help='输出文件路径')
@click.option('--symbol', help='交易对')
@click.option('--timeframe', help='时间周期')
@click.option('--start-date', help='开始日期')
@click.option('--end-date', help='结束日期')
@click.option('--count', type=int, help='数据条数')
def generate(type: str, output: str, **kwargs):
    """生成测试数据"""
    generator = TestDataGenerator({})
    
    async def run():
        if type == 'market':
            data = await generator.generate_market_data(
                symbol=kwargs.get('symbol', 'BTC/USDT'),
                timeframe=kwargs.get('timeframe', '1m'),
                start_date=kwargs.get('start_date'),
                end_date=kwargs.get('end_date')
            )
        elif type == 'trade':
            data = await generator.generate_trade_data(
                symbol=kwargs.get('symbol', 'BTC/USDT'),
                count=kwargs.get('count', 100)
            )
        elif type == 'system':
            data = await generator.generate_system_data(
                duration=kwargs.get('count', 100)
            )
        elif type == 'orderbook':
            data = await generator.generate_orderbook(
                symbol=kwargs.get('symbol', 'BTC/USDT')
            )
        elif type == 'history':
            data = await generator.generate_trade_history(
                symbol=kwargs.get('symbol', 'BTC/USDT'),
                count=kwargs.get('count', 100)
            )
        elif type == 'performance':
            data = await generator.generate_performance_data(
                duration=kwargs.get('count', 100)
            )
        elif type == 'error':
            data = await generator.generate_error_data(
                count=kwargs.get('count', 100)
            )
        else:
            data = await generator.generate_test_scenarios(
                count=kwargs.get('count', 10)
            )
            
        # 保存数据
        data.to_csv(output, index=False)
        
    asyncio.run(run())

@cli.group()
def analyze():
    """测试结果分析工具"""
    pass

@analyze.command()
@click.option('--input', '-i', required=True, help='输入文件路径')
@click.option('--output', '-o', required=True, help='输出文件路径')
@click.option('--type', type=click.Choice(['prediction', 'performance', 'error']), required=True)
def analyze_results(input: str, output: str, type: str):
    """分析测试结果"""
    analyzer = TestResultAnalyzer({})
    
    async def run():
        if type == 'prediction':
            results = await analyzer.analyze_predictions(input)
        elif type == 'performance':
            results = await analyzer.analyze_performance(input)
        else:
            results = await analyzer.analyze_errors(input)
            
        # 保存分析结果
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
            
    asyncio.run(run())

@cli.group()
def report():
    """测试报告生成工具"""
    pass

@report.command()
@click.option('--input', '-i', required=True, help='输入文件路径')
@click.option('--output', '-o', required=True, help='输出文件路径')
@click.option('--format', type=click.Choice(['html', 'pdf']), default='html', help='报告格式')
def generate_report(input: str, output: str, format: str):
    """生成测试报告"""
    generator = ReportGenerator({})
    
    async def run():
        # 读取输入数据
        with open(input, 'r') as f:
            data = json.load(f)
            
        # 生成报告
        await generator.generate_report(
            data=data,
            output_path=output,
            report_format=format
        )
        
    asyncio.run(run())

@cli.group()
def env():
    """测试环境管理工具"""
    pass

@env.command()
@click.option('--name', required=True, help='环境名称')
@click.option('--python-version', default='3.8', help='Python版本')
@click.option('--requirements', '-r', multiple=True, help='依赖包')
def create(name: str, python_version: str, requirements: List[str]):
    """创建测试环境"""
    manager = EnvironmentManager({})
    
    async def run():
        await manager.create_environment(
            name,
            python_version=python_version,
            requirements=list(requirements)
        )
        
    asyncio.run(run())

@env.command()
@click.option('--name', required=True, help='环境名称')
def remove(name: str):
    """删除测试环境"""
    manager = EnvironmentManager({})
    
    async def run():
        await manager.remove_environment(name)
        
    asyncio.run(run())

@env.command()
@click.option('--name', required=True, help='环境名称')
def info(name: str):
    """获取环境信息"""
    manager = EnvironmentManager({})
    
    async def run():
        info = await manager.get_environment_info(name)
        click.echo(json.dumps(info, indent=2))
        
    asyncio.run(run())

@env.command()
@click.option('--name', required=True, help='环境名称')
@click.option('--output', '-o', required=True, help='输出文件路径')
def export(name: str, output: str):
    """导出环境配置"""
    manager = EnvironmentManager({})
    
    async def run():
        await manager.export_environment(name, output)
        
    asyncio.run(run())

@env.command()
@click.option('--input', '-i', required=True, help='输入文件路径')
def import_env(input: str):
    """导入环境配置"""
    manager = EnvironmentManager({})
    
    async def run():
        env_path = await manager.import_environment(input)
        click.echo(f'环境已导入到: {env_path}')
        
    asyncio.run(run())

if __name__ == '__main__':
    cli() 