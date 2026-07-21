import pytest
import os
import json
import yaml
from typing import Dict, List
import asyncio

from src.tests.tools.environment_manager import EnvironmentManager

@pytest.fixture
def env_manager():
    """创建环境管理器实例"""
    return EnvironmentManager(
        config={
            'environment': {
                'base_dir': 'test_envs',
                'temp_dir': 'temp'
            }
        }
    )

@pytest.fixture
def test_requirements():
    """创建测试依赖列表"""
    return [
        'pytest==7.4.0',
        'numpy==1.24.3',
        'pandas==2.0.3'
    ]

class TestEnvironmentManager:
    """测试环境管理器测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, env_manager):
        """测试环境管理器初始化"""
        assert isinstance(env_manager.config, dict)
        assert 'environment' in env_manager.config
        assert os.path.exists(env_manager.env_dir)
        assert os.path.exists(env_manager.temp_dir)
        
    @pytest.mark.asyncio
    async def test_create_environment(self, env_manager, test_requirements):
        """测试创建测试环境"""
        # 创建环境
        env_path = await env_manager.create_environment(
            'test_env',
            python_version='3.8',
            requirements=test_requirements
        )
        
        # 验证环境目录
        assert os.path.exists(env_path)
        assert os.path.exists(os.path.join(env_path, 'Scripts', 'python.exe'))
        assert os.path.exists(os.path.join(env_path, 'Scripts', 'pip.exe'))
        
        # 验证依赖安装
        pip_path = os.path.join(env_path, 'Scripts', 'pip.exe')
        packages = json.loads(
            subprocess.check_output([pip_path, 'list', '--format=json']).decode()
        )
        package_names = [pkg['name'] for pkg in packages]
        assert 'pytest' in package_names
        assert 'numpy' in package_names
        assert 'pandas' in package_names
        
    @pytest.mark.asyncio
    async def test_remove_environment(self, env_manager):
        """测试删除测试环境"""
        # 创建环境
        env_path = await env_manager.create_environment('test_env')
        
        # 删除环境
        await env_manager.remove_environment('test_env')
        
        # 验证环境已删除
        assert not os.path.exists(env_path)
        
    @pytest.mark.asyncio
    async def test_get_environment_info(self, env_manager, test_requirements):
        """测试获取环境信息"""
        # 创建环境
        await env_manager.create_environment(
            'test_env',
            requirements=test_requirements
        )
        
        # 获取环境信息
        env_info = await env_manager.get_environment_info('test_env')
        
        # 验证环境信息
        assert env_info['name'] == 'test_env'
        assert os.path.exists(env_info['path'])
        assert 'Python' in env_info['python_version']
        assert len(env_info['packages']) > 0
        
    @pytest.mark.asyncio
    async def test_update_environment(self, env_manager, test_requirements):
        """测试更新环境依赖"""
        # 创建环境
        await env_manager.create_environment('test_env')
        
        # 更新依赖
        await env_manager.update_environment('test_env', test_requirements)
        
        # 验证依赖安装
        env_info = await env_manager.get_environment_info('test_env')
        package_names = [pkg['name'] for pkg in env_info['packages']]
        assert 'pytest' in package_names
        assert 'numpy' in package_names
        assert 'pandas' in package_names
        
    @pytest.mark.asyncio
    async def test_export_environment(self, env_manager, test_requirements):
        """测试导出环境配置"""
        # 创建环境
        await env_manager.create_environment(
            'test_env',
            requirements=test_requirements
        )
        
        # 导出环境配置
        output_path = os.path.join('temp', 'env_config.yaml')
        export_path = await env_manager.export_environment('test_env', output_path)
        
        # 验证导出文件
        assert os.path.exists(export_path)
        with open(export_path, 'r') as f:
            config = yaml.safe_load(f)
            assert config['name'] == 'test_env'
            assert 'Python' in config['python_version']
            assert len(config['packages']) > 0
            
    @pytest.mark.asyncio
    async def test_import_environment(self, env_manager, test_requirements):
        """测试导入环境配置"""
        # 创建并导出环境
        await env_manager.create_environment(
            'test_env',
            requirements=test_requirements
        )
        output_path = os.path.join('temp', 'env_config.yaml')
        await env_manager.export_environment('test_env', output_path)
        
        # 删除原环境
        await env_manager.remove_environment('test_env')
        
        # 导入环境配置
        env_path = await env_manager.import_environment(output_path)
        
        # 验证环境
        assert os.path.exists(env_path)
        env_info = await env_manager.get_environment_info('test_env')
        package_names = [pkg['name'] for pkg in env_info['packages']]
        assert 'pytest' in package_names
        assert 'numpy' in package_names
        assert 'pandas' in package_names
        
    @pytest.mark.asyncio
    async def test_run_in_environment(self, env_manager):
        """测试在环境中运行命令"""
        # 创建环境
        await env_manager.create_environment('test_env')
        
        # 运行命令
        result = await env_manager.run_in_environment(
            'test_env',
            ['python', '--version']
        )
        
        # 验证结果
        assert result['return_code'] == 0
        assert 'Python' in result['stdout']
        
    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self, env_manager):
        """测试清理临时文件"""
        # 创建临时文件
        temp_file = os.path.join(env_manager.temp_dir, 'test.txt')
        with open(temp_file, 'w') as f:
            f.write('test')
            
        # 清理临时文件
        await env_manager.cleanup_temp_files()
        
        # 验证清理结果
        assert not os.path.exists(temp_file)
        assert os.path.exists(env_manager.temp_dir)
        
    @pytest.mark.asyncio
    async def test_list_environments(self, env_manager):
        """测试列出所有环境"""
        # 创建多个环境
        await env_manager.create_environment('env1')
        await env_manager.create_environment('env2')
        
        # 列出环境
        environments = await env_manager.list_environments()
        
        # 验证结果
        assert 'env1' in environments
        assert 'env2' in environments
        
    @pytest.mark.asyncio
    async def test_validate_environment(self, env_manager):
        """测试验证环境配置"""
        # 创建环境
        await env_manager.create_environment('test_env')
        
        # 验证环境
        result = await env_manager.validate_environment('test_env')
        
        # 验证结果
        assert result['valid']
        assert os.path.exists(result['python_path'])
        assert os.path.exists(result['pip_path'])
        assert isinstance(result['packages'], list)
        
    @pytest.mark.asyncio
    async def test_error_handling(self, env_manager):
        """测试错误处理"""
        # 测试创建已存在的环境
        await env_manager.create_environment('test_env')
        with pytest.raises(ValueError):
            await env_manager.create_environment('test_env')
            
        # 测试删除不存在的环境
        with pytest.raises(ValueError):
            await env_manager.remove_environment('nonexistent')
            
        # 测试获取不存在环境的信息
        with pytest.raises(ValueError):
            await env_manager.get_environment_info('nonexistent')
            
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, env_manager):
        """测试并发操作"""
        # 创建多个环境
        tasks = [
            env_manager.create_environment(f'env{i}')
            for i in range(3)
        ]
        await asyncio.gather(*tasks)
        
        # 获取多个环境的信息
        tasks = [
            env_manager.get_environment_info(f'env{i}')
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks)
        
        # 验证结果
        assert len(results) == 3
        for result in results:
            assert os.path.exists(result['path'])
            assert 'Python' in result['python_version'] 