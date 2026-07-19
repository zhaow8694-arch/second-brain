import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

errors = []

try:
    from core.database import init_db
    init_db()
    print("[OK] core.database")
except Exception as e:
    errors.append(f"core.database: {e}")
    print(f"[FAIL] core.database: {e}")

try:
    from core.quality_gate import cross_audit, AUDIT_RULES_B
    print(f"[OK] core.quality_gate (AUDIT_RULES_B has {len(AUDIT_RULES_B)} types)")
except Exception as e:
    errors.append(f"core.quality_gate: {e}")
    print(f"[FAIL] core.quality_gate: {e}")

try:
    from arsenal.code_generator import generate_product
    print("[OK] arsenal.code_generator")
except Exception as e:
    errors.append(f"arsenal.code_generator: {e}")
    print(f"[FAIL] arsenal.code_generator: {e}")

try:
    from core.market_data import get_price
    print("[OK] core.market_data")
except Exception as e:
    errors.append(f"core.market_data: {e}")
    print(f"[FAIL] core.market_data: {e}")

try:
    from core.model_router import get_llm_config
    cfg = get_llm_config("medium")
    print(f"[OK] core.model_router -> model={cfg['model']}")
except Exception as e:
    errors.append(f"core.model_router: {e}")
    print(f"[FAIL] core.model_router: {e}")

print()
if errors:
    print(f"RESULT: {len(errors)} error(s) found")
else:
    print("RESULT: All modules loaded successfully")
