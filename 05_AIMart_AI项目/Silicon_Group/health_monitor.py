"""
Silicon Group 健康监控器
每 5 分钟检查一次系统状态，发现问题自动修复
"""
import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

CHECK_INTERVAL = 300  # 5分钟
WARN_FILE = "health_warnings.json"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def check_process():
    """检查 start_auto.py 或 run_24h.py 是否在运行"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=10
        )
        lines = [l.strip() for l in result.stdout.split('\n') if l.strip()]
        python_count = len(lines)
        
        # 检查是否有我们的脚本在运行
        our_scripts = 0
        for l in lines:
            if 'start_auto.py' in l or 'run_24h.py' in l:
                our_scripts += 1
        
        return {
            'python_processes': python_count,
            'our_scripts': our_scripts,
            'alive': our_scripts > 0
        }
    except Exception as e:
        return {'error': str(e), 'alive': False}

def check_db():
    """检查数据库是否有最近的调度器记录"""
    try:
        import sqlite3
        db_path = os.path.abspath(os.path.join('core', '..', 'silicon_empire.db'))
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 最新调度器运行
        cur.execute("SELECT started_at, status FROM scheduler_runs ORDER BY rowid DESC LIMIT 1")
        row = cur.fetchone()
        last_run = row[0] if row else 'never'
        last_status = row[1] if row else 'unknown'
        
        # 订单数
        cur.execute("SELECT COUNT(*) FROM live_trades")
        trade_count = cur.fetchone()[0]
        
        conn.close()
        return {
            'last_run': last_run,
            'last_status': last_status,
            'trade_count': trade_count
        }
    except Exception as e:
        return {'error': str(e)}

def check_api():
    """检查 DeepSeek API 是否可用"""
    try:
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            return {'available': False, 'reason': 'no key'}
        r = requests.get(
            "https://api.deepseek.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10
        )
        return {'available': r.ok, 'status': r.status_code}
    except Exception as e:
        return {'available': False, 'error': str(e)}

def check_exchange():
    """检查交易所连接是否正常"""
    try:
        from core.financial_gateway import _FuturesClient
        client = _FuturesClient()
        data = client._request("GET", "/fapi/v2/account")
        total = sum(float(a.get('walletBalance', 0)) for a in data.get('assets', []))
        positions = sum(1 for p in data.get('positions', []) if float(p.get('positionAmt', 0)) != 0)
        return {'connected': True, 'balance': round(total, 2), 'positions': positions}
    except Exception as e:
        return {'connected': False, 'error': str(e)}

def auto_repair(issues):
    """自动修复发现的问题"""
    if 'process_dead' in issues:
        log("🚨 进程已死，自动重启...")
        subprocess.Popen(
            [sys.executable, 'run_24h.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        log("✅ 已启动 run_24h.py 守护进程")
    
    if 'api_down' in issues:
        log("⚠️ API 不可用，记录警告")
        warnings = []
        if os.path.exists(WARN_FILE):
            with open(WARN_FILE) as f:
                warnings = json.load(f)
        warnings.append({
            'time': datetime.now().isoformat(),
            'type': 'api_down',
            'detail': issues.get('api_detail', '')
        })
        with open(WARN_FILE, 'w') as f:
            json.dump(warnings[-10:], f)

def main():
    log("🩺 健康监控器启动")
    log(f"    检查间隔: {CHECK_INTERVAL}秒")
    log(f"    监控项目: 进程/数据库/API/交易所\n")
    
    while True:
        issues = []
        
        # 1. 检查进程
        proc = check_process()
        if not proc.get('alive'):
            issues.append('process_dead')
            log("❌ 进程检查: 未发现运行中的脚本")
        else:
            log(f"✅ 进程检查: {proc['our_scripts']}个脚本运行中")
        
        # 2. 检查数据库
        db = check_db()
        if 'error' in db:
            log(f"⚠️ 数据库检查: {db['error']}")
        else:
            log(f"✅ 数据库检查: 最后运行={db['last_run']}, 状态={db['last_status']}, 订单={db['trade_count']}笔")
        
        # 3. 检查 API
        api = check_api()
        if not api.get('available'):
            issues.append('api_down')
            issues['api_detail'] = api.get('error', api.get('reason', 'unknown'))
            log(f"⚠️ API检查: 不可用 - {api.get('error', '')}")
        else:
            log(f"✅ API检查: 可用")
        
        # 4. 检查交易所
        ex = check_exchange()
        if ex.get('connected'):
            log(f"✅ 交易所检查: 余额={ex['balance']} USDT, 持仓={ex['positions']}个")
        else:
            log(f"⚠️ 交易所检查: 连接失败 - {ex.get('error', '')}")
        
        # 5. 自动修复
        if issues:
            auto_repair(issues)
        else:
            log("✅ 所有检查通过，系统健康\n")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
