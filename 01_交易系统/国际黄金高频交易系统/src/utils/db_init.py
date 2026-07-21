import asyncio
import aiomysql
from loguru import logger
from config.config import DATABASE_CONFIG

async def create_database():
    """创建数据库"""
    try:
        # 连接到MySQL服务器
        conn = await aiomysql.connect(
            host=DATABASE_CONFIG['host'],
            port=DATABASE_CONFIG['port'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password']
        )
        
        async with conn.cursor() as cursor:
            # 创建数据库
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {DATABASE_CONFIG['database']}"
            )
            logger.info(f"Database {DATABASE_CONFIG['database']} created successfully")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

async def init_mysql_tables():
    """初始化MySQL表"""
    try:
        # 连接到trading_db数据库
        conn = await aiomysql.connect(
            host=DATABASE_CONFIG['host'],
            port=DATABASE_CONFIG['port'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            db=DATABASE_CONFIG['database']
        )
        
        async with conn.cursor() as cursor:
            # 创建market_data表
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id          BIGINT          AUTO_INCREMENT PRIMARY KEY,
                    time        DATETIME(3)     NOT NULL,
                    symbol      VARCHAR(20)     NOT NULL,
                    source      VARCHAR(10)     NOT NULL,
                    open        DECIMAL(20,8)   NOT NULL,
                    high        DECIMAL(20,8)   NOT NULL,
                    low         DECIMAL(20,8)   NOT NULL,
                    close       DECIMAL(20,8)   NOT NULL,
                    volume      DECIMAL(20,8)   NOT NULL,
                    bid_price   DECIMAL(20,8),
                    ask_price   DECIMAL(20,8),
                    INDEX idx_time_symbol (time, symbol)
                ) ENGINE=InnoDB;
            """)
            
            # 创建trades表
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id              BIGINT          AUTO_INCREMENT PRIMARY KEY,
                    time            DATETIME(3)     NOT NULL,
                    trade_id        VARCHAR(32)     NOT NULL,
                    symbol          VARCHAR(20)     NOT NULL,
                    direction       VARCHAR(4)      NOT NULL,
                    price           DECIMAL(20,8)   NOT NULL,
                    quantity        DECIMAL(20,8)   NOT NULL,
                    strategy_id     VARCHAR(32)     NOT NULL,
                    platform        VARCHAR(10)     NOT NULL,
                    status          VARCHAR(10)     NOT NULL,
                    pnl             DECIMAL(20,8),
                    execution_time  INTEGER,
                    INDEX idx_time (time),
                    INDEX idx_trade_id (trade_id),
                    INDEX idx_symbol_time (symbol, time)
                ) ENGINE=InnoDB;
            """)
            
            # 创建策略性能表
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_metrics (
                    id              BIGINT          AUTO_INCREMENT PRIMARY KEY,
                    time            DATETIME(3)     NOT NULL,
                    strategy_id     VARCHAR(32)     NOT NULL,
                    symbol          VARCHAR(20)     NOT NULL,
                    win_rate        DECIMAL(5,2),
                    sharpe_ratio    DECIMAL(10,4),
                    max_drawdown    DECIMAL(10,4),
                    total_pnl       DECIMAL(20,8),
                    trade_count     INTEGER,
                    INDEX idx_strategy_time (strategy_id, time)
                ) ENGINE=InnoDB;
            """)
            
            # 创建分区（可选，根据需要添加）
            # 这里使用RANGE分区作为示例
            await cursor.execute("""
                ALTER TABLE market_data
                PARTITION BY RANGE (TO_DAYS(time)) (
                    PARTITION p_2024_01 VALUES LESS THAN (TO_DAYS('2024-02-01')),
                    PARTITION p_2024_02 VALUES LESS THAN (TO_DAYS('2024-03-01')),
                    PARTITION p_2024_03 VALUES LESS THAN (TO_DAYS('2024-04-01')),
                    PARTITION p_max VALUES LESS THAN MAXVALUE
                );
            """)
            
        await conn.commit()
        logger.info("MySQL tables initialized successfully")
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error initializing MySQL tables: {e}")
        raise

async def init_database():
    """初始化数据库和表"""
    await create_database()
    await init_mysql_tables()

if __name__ == "__main__":
    asyncio.run(init_database()) 