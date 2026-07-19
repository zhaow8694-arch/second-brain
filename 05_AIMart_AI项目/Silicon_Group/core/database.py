import sqlite3
import os
import json
from datetime import datetime

# 使用绝对路径，确保从任何目录调用时都指向同一个数据库
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "silicon_empire.db")

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()

    # 作战日志表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS battle_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        stage TEXT NOT NULL,
        target TEXT NOT NULL,
        content TEXT NOT NULL
    )
    ''')

    # 状态快照表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS snapshots (
        session_id TEXT NOT NULL,
        stage TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        context TEXT NOT NULL,
        PRIMARY KEY (session_id, stage)
    )
    ''')

    # 影子实盘订单表 (Paper Trading)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS paper_trades (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        symbol TEXT NOT NULL,
        direction TEXT NOT NULL,
        quantity REAL NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL,
        pnl REAL,
        status TEXT NOT NULL DEFAULT 'open',
        open_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        close_time DATETIME
    )
    ''')

    # 资金表 (虚拟账户)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS paper_account (
        id INTEGER PRIMARY KEY,
        balance REAL NOT NULL DEFAULT 100000.0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 插入初始资金记录（如果不存在）
    cursor.execute('SELECT COUNT(*) FROM paper_account')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO paper_account (id, balance) VALUES (1, 100000.0)')

    # ===== 实盘交易记录表 (Live Trading) =====
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS live_trades (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        order_type TEXT NOT NULL DEFAULT 'market',
        quantity REAL NOT NULL,
        price REAL,
        cost REAL,
        status TEXT NOT NULL DEFAULT 'new',
        stop_loss_price REAL,
        take_profit_price REAL,
        stop_loss_order_id TEXT,
        take_profit_order_id TEXT,
        pnl REAL,
        close_time DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ===== 调度器运行记录表 =====
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scheduler_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cycle INTEGER NOT NULL,
        status TEXT NOT NULL,
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        finished_at DATETIME,
        symbols_count INTEGER,
        symbols_analyzed TEXT,
        trade_plans TEXT,
        summary TEXT
    )
    ''')

    # ===== 系统状态快报表 =====
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        gateway_mode TEXT,
        scheduler_active INTEGER DEFAULT 0,
        binance_connected INTEGER DEFAULT 0,
        usdt_balance REAL,
        open_positions INTEGER,
        last_cycle_status TEXT
    )
    ''')

    conn.commit()
    conn.close()

# 自动初始化
init_db()
