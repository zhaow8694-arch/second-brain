"""
Silicon Group 24/7 守护启动器
如果主进程崩溃或退出，自动重启
"""
import subprocess
import time
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  [GUARDIAN] Silicon Group 24/7 Auto-Restart Daemon")
print("  Will restart start_auto.py if it crashes.")
print("=" * 60)

restart_count = 0
while True:
    restart_count += 1
    print(f"\n[{time.strftime('%H:%M:%S')}] 🚀 Launching start_auto.py (attempt #{restart_count})...")
    try:
        proc = subprocess.Popen(
            [sys.executable, 'start_auto.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        for line in proc.stdout:
            print(line, end='', flush=True)
        proc.wait()
        exit_code = proc.returncode
        print(f"\n[{time.strftime('%H:%M:%S')}] ⚠️ start_auto.py exited with code {exit_code}", flush=True)
    except Exception as e:
        print(f"\n[{time.strftime('%H:%M:%S')}] ❌ Launch error: {e}", flush=True)

    print(f"[{time.strftime('%H:%M:%S')}] 🔄 Restarting in 10 seconds...", flush=True)
    time.sleep(10)
