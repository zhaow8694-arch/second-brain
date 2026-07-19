import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

errors = []

# Test 1: backtester session_id bug
try:
    from core.backtester import run_backtest
    data = [{'close': float(100+i), 'high': float(102+i), 'low': float(99+i), 'open': float(100+i), 'volume': 1000} for i in range(30)]
    result = run_backtest('BTC/USDT', 'ma_cross', data)
    print("[OK] backtester win_rate=" + str(result.get("win_rate")))
except Exception as e:
    errors.append("backtester: " + str(e))
    print("[FAIL] backtester: " + str(e))

# Test 2: portfolio open/close
try:
    from core.database import init_db
    init_db()
    from core.portfolio import open_position, close_position, get_portfolio_summary
    r = open_position('test_audit', 'BTC/USDT', 'long', 0.001, 90000.0)
    print("[OK] portfolio.open_position: " + str(r.get("position_id")))
    r2 = close_position('test_audit', 'BTC/USDT', 'long', 91000.0)
    print("[OK] portfolio.close_position pnl=" + str(r2.get("pnl")))
except Exception as e:
    errors.append("portfolio: " + str(e))
    print("[FAIL] portfolio: " + str(e))

# Test 3: cost_watchdog
try:
    from core.cost_watchdog import get_status
    s = get_status()
    print("[OK] cost_watchdog budget=" + str(s["daily_budget"]))
except Exception as e:
    errors.append("cost_watchdog: " + str(e))
    print("[FAIL] cost_watchdog: " + str(e))

# Test 4: model_router env loaded at module import
try:
    from core.model_router import get_llm_config
    cfg = get_llm_config('low')
    key_ok = cfg['api_key'] is not None
    print("[OK] model_router low: model=" + cfg["model"] + " key_present=" + str(key_ok))
    cfg_h = get_llm_config('high')
    print("[OK] model_router high: model=" + cfg_h["model"])
except Exception as e:
    errors.append("model_router: " + str(e))
    print("[FAIL] model_router: " + str(e))

# Test 5: quality_gate XSS fix
try:
    from core.quality_gate import cross_audit
    # Should FAIL: contains <script> AND innerHTML
    r = cross_audit("audit_test", "<script>alert(1)</script> innerHTML=bad", "generated_code")
    if not r["passed"]:
        print("[OK] quality_gate XSS blocked correctly")
    else:
        errors.append("quality_gate XSS: should have blocked malicious code but passed")
        print("[FAIL] quality_gate XSS: failed to block malicious code")
except Exception as e:
    errors.append("quality_gate: " + str(e))
    print("[FAIL] quality_gate: " + str(e))

# Test 6: scheduler import
try:
    from core.scheduler import get_status as sched_status, TRADABLE_SYMBOLS
    s = sched_status()
    print("[OK] scheduler: " + str(len(TRADABLE_SYMBOLS)) + " symbols, active=" + str(s["active"]))
except Exception as e:
    errors.append("scheduler: " + str(e))
    print("[FAIL] scheduler: " + str(e))

# Test 7: financial_gateway no thread polling
try:
    import inspect
    from core import financial_gateway
    src = inspect.getsource(financial_gateway._FuturesClient.set_stop_loss_take_profit)
    if "threading.Thread" in src:
        errors.append("financial_gateway: thread polling still present in set_stop_loss_take_profit")
        print("[FAIL] financial_gateway: thread polling still present - P0 fix not applied")
    else:
        print("[OK] financial_gateway: thread polling removed, server-side orders only")
except Exception as e:
    errors.append("financial_gateway: " + str(e))
    print("[FAIL] financial_gateway: " + str(e))

print()
if errors:
    print("RESULT: " + str(len(errors)) + " error(s) found")
    for e in errors:
        print("  ERR: " + e)
else:
    print("RESULT: All checks passed")
