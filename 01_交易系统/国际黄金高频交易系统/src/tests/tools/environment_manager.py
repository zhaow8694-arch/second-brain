import os
import json
import yaml
import shutil
import subprocess
import venv
from typing import Dict, List, Optional, Union
import asyncio
from pathlib import Path

class EnvironmentManager:
    """测试环境管理器"""
    
    def __init__(self, config: Dict):
        """初始化环境管理器
        
        Args:
            config: 配置字典，包含环境管理参数
        """
        self.config = config
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.env_dir = os.path.join(self.base_dir, 'test_envs')
        self.temp_dir = os.path.join(self.base_dir, 'temp')
        
        # 创建必要的目录
        os.makedirs(self.env_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
    async def create_environment(
        self,
        env_name: str,
        python_version: str = '3.8',
        requirements: Optional[List[str]] = None
    ) -> str:
        """创建测试环境
        
        Args:
            env_name: 环境名称
            python_version: Python版本
            requirements: 依赖包列表
            
        Returns:
            环境路径
        """
        # 创建环境目录
        env_path = os.path.join(self.env_dir, env_name)
        if os.path.exists(env_path):
            raise ValueError(f'环境 {env_name} 已存在')
            
        # 创建虚拟环境
        venv.create(
            env_path,
            with_pip=True,
            system_site_packages=False
        )
        
        # 安装依赖
        if requirements:
            await self.install_requirements(env_path, requirements)
            
        return env_path
        
    async def install_requirements(
        self,
        env_path: str,
        requirements: List[str]
    ) -> None:
        """安装依赖包
        
        Args:
            env_path: 环境路径
            requirements: 依赖包列表
        """
        # 获取pip路径
        pip_path = os.path.join(env_path, 'Scripts', 'pip.exe')
        
        # 安装依赖
        for req in requirements:
            subprocess.run([pip_path, 'install', req], check=True)
            
    async def remove_environment(
        self,
        env_name: str
    ) -> None:
        """删除测试环境
        
        Args:
            env_name: 环境名称
        """
        env_path = os.path.join(self.env_dir, env_name)
        if not os.path.exists(env_path):
            raise ValueError(f'环境 {env_name} 不存在')
            
        shutil.rmtree(env_path)
        
    async def get_environment_info(
        self,
        env_name: str
    ) -> Dict:
        """获取环境信息
        
        Args:
            env_name: 环境名称
            
        Returns:
            环境信息字典
        """
        env_path = os.path.join(self.env_dir, env_name)
        if not os.path.exists(env_path):
            raise ValueError(f'环境 {env_name} 不存在')
            
        # 获取Python版本
        python_path = os.path.join(env_path, 'Scripts', 'python.exe')
        version = subprocess.check_output([python_path, '--version']).decode().strip()
        
        # 获取已安装的包
        pip_path = os.path.join(env_path, 'Scripts', 'pip.exe')
        packages = subprocess.check_output([pip_path, 'list', '--format=json']).decode()
        packages = json.loads(packages)
        
        return {
            'name': env_name,
            'path': env_path,
            'python_version': version,
            'packages': packages
        }
        
    async def update_environment(
        self,
        env_name: str,
        requirements: List[str]
    ) -> None:
        """更新环境依赖
        
        Args:
            env_name: 环境名称
            requirements: 新的依赖包列表
        """
        env_path = os.path.join(self.env_dir, env_name)
        if not os.path.exists(env_path):
            raise ValueError(f'环境 {env_name} 不存在')
            
        # 更新依赖
        await self.install_requirements(env_path, requirements)
        
    async def export_environment(
        self,
        env_name: str,
        output_path: str
    ) -> str:
        """导出环境配置
        
        Args:
            env_name: 环境名称
            output_path: 输出文件路径
            
        Returns:
            导出文件路径
        """
        # 获取环境信息
        env_info = await self.get_environment_info(env_name)
        
        # 创建导出数据
        export_data = {
            'name': env_name,
            'python_version': env_info['python_version'],
            'packages': [
                {
                    'name': pkg['name'],
                    'version': pkg['version']
                }
                for pkg in env_info['packages']
            ]
        }
        
        # 保存导出文件
        with open(output_path, 'w') as f:
            yaml.dump(export_data, f)
            
        return output_path
        
    async def import_environment(
        self,
        config_path: str
    ) -> str:
        """导入环境配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            环境路径
        """
        # 读取配置文件
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # 创建环境
        env_path = await self.create_environment(
            config['name'],
            config['python_version']
        )
        
        # 安装依赖
        requirements = [
            f"{pkg['name']}=={pkg['version']}"
            for pkg in config['packages']
        ]
        await self.install_requirements(env_path, requirements)
        
        return env_path
        
    async def run_in_environment(
        self,
        env_name: str,
        command: List[str],
        cwd: Optional[str] = None
    ) -> Dict:
        """在指定环境中运行命令
        
        Args:
            env_name: 环境名称
            command: 命令列表
            cwd: 工作目录
            
        Returns:
            执行结果字典
        """
        env_path = os.path.join(self.env_dir, env_name)
        if not os.path.exists(env_path):
            raise ValueError(f'环境 {env_name} 不存在')
            
        # 设置环境变量
        env = os.environ.copy()
        env['VIRTUAL_ENV'] = env_path
        env['PATH'] = os.path.join(env_path, 'Scripts') + os.pathsep + env['PATH']
        
        # 运行命令
        process = await asyncio.create_subprocess_exec(
            *command,
            env=env,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            'return_code': process.returncode,
            'stdout': stdout.decode() if stdout else '',
            'stderr': stderr.decode() if stderr else ''
        }
        
    async def cleanup_temp_files(self) -> None:
        """清理临时文件"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            
    async def list_environments(self) -> List[str]:
        """列出所有测试环境
        
        Returns:
            环境名称列表
        """
        return [
            d for d in os.listdir(self.env_dir)
            if os.path.isdir(os.path.join(self.env_dir, d))
        ]
        
    async def validate_environment(
        self,
        env_name: str
    ) -> Dict:
        """验证环境配置
        
        Args:
            env_name: 环境名称
            
        Returns:
            验证结果字典
        """
        env_path = os.path.join(self.env_dir, env_name)
        if not os.path.exists(env_path):
            raise ValueError(f'环境 {env_name} 不存在')
            
        # 检查Python解释器
        python_path = os.path.join(env_path, 'Scripts', 'python.exe')
        if not os.path.exists(python_path):
            return {
                'valid': False,
                'errors': ['Python解释器不存在']
            }
            
        # 检查pip
        pip_path = os.path.join(env_path, 'Scripts', 'pip.exe')
        if not os.path.exists(pip_path):
            return {
                'valid': False,
                'errors': ['pip不存在']
            }
            
        # 检查依赖包
        try:
            packages = subprocess.check_output([pip_path, 'list', '--format=json']).decode()
            packages = json.loads(packages)
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'获取依赖包列表失败: {str(e)}']
            }
            
        return {
            'valid': True,
            'python_path': python_path,
            'pip_path': pip_path,
            'packages': packages
        } 