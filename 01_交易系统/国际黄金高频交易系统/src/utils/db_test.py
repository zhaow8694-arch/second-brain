import asyncio
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from redis import Redis
import aiomysql
from loguru import logger

class DatabaseTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = {}
        
    async def test_postgresql(self) -> bool:
        """测试PostgreSQL连接"""
        try:
            engine = create_async_engine(
                self.config['postgresql']['url'],
                echo=False
            )
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with async_session() as session:
                await session.execute("SELECT 1")
                await session.commit()
            
            await engine.dispose()
            self.results['postgresql'] = True
            logger.info("PostgreSQL连接测试成功")
            return True
        except Exception as e:
            self.results['postgresql'] = False
            logger.error(f"PostgreSQL连接测试失败: {str(e)}")
            return False
    
    async def test_redis(self) -> bool:
        """测试Redis连接"""
        try:
            redis = Redis(
                host=self.config['redis']['host'],
                port=self.config['redis']['port'],
                db=self.config['redis']['db'],
                decode_responses=True
            )
            redis.ping()
            self.results['redis'] = True
            logger.info("Redis连接测试成功")
            return True
        except Exception as e:
            self.results['redis'] = False
            logger.error(f"Redis连接测试失败: {str(e)}")
            return False
    
    async def test_mysql(self) -> bool:
        """测试MySQL连接"""
        try:
            conn = await aiomysql.connect(
                host=self.config['mysql']['host'],
                port=self.config['mysql']['port'],
                user=self.config['mysql']['user'],
                password=self.config['mysql']['password'],
                db=self.config['mysql']['database']
            )
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
            conn.close()
            self.results['mysql'] = True
            logger.info("MySQL连接测试成功")
            return True
        except Exception as e:
            self.results['mysql'] = False
            logger.error(f"MySQL连接测试失败: {str(e)}")
            return False
    
    async def test_all(self) -> Dict[str, bool]:
        """测试所有数据库连接"""
        tasks = [
            self.test_postgresql(),
            self.test_redis(),
            self.test_mysql()
        ]
        await asyncio.gather(*tasks)
        return self.results

async def main():
    # 从环境变量或配置文件加载数据库配置
    config = {
        'postgresql': {
            'url': 'postgresql+asyncpg://user:password@localhost:5432/dbname'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        },
        'mysql': {
            'host': 'localhost',
            'port': 3306,
            'user': 'user',
            'password': 'password',
            'database': 'dbname'
        }
    }
    
    tester = DatabaseTester(config)
    results = await tester.test_all()
    
    # 打印测试结果
    logger.info("数据库连接测试结果:")
    for db, success in results.items():
        status = "成功" if success else "失败"
        logger.info(f"{db}: {status}")

if __name__ == "__main__":
    asyncio.run(main()) 