import os
import sys
import signal
import subprocess
from dotenv import load_dotenv

from core.model_router import get_llm_config
from core.cost_watchdog import get_status, is_meltdown
from core.battle_log import generate_session_id
from core.security_auditor import scan_project
from core.guard_dog import is_meltdown_active
from command.menu import show_menu, get_choice, MENU_OPTIONS
from command.operations import (
    run_financial_mission,
    run_arsenal_mission,
    run_marketing_mission,
    run_total_war,
    run_academy_mission,
    run_logistics_mission,
    run_campaign_mission,
    run_campaign_execute_mission,
    run_dashboard_mission,
    run_identity_mission,
    run_guard_dog_mission,
    run_rag_mission,
    run_shadow_test_mission,
    run_resume_mission,
    run_market_data_mission,
    run_backtest_mission,
    run_portfolio_mission,
    run_chief_of_staff_mission,
    run_scheduler_mission,
)
from command.report import generate_report, open_report

load_dotenv()

# 必须在任何模块写入日志前先初始化数据库，防止冷启动时表不存在
from core.database import init_db
init_db()

SESSION_ID = generate_session_id()

print("=" * 60)
print(f"  ⚔️ 硅基远征军 - 统帅部指挥系统 (V2.7)")
print(f"  会话编号: {SESSION_ID}")
print("=" * 60)

print("\n🔍 执行安全审计...")
audit_result = scan_project(".")
if audit_result["leaks_found"] > 0:
    print(f"⚠️  发现 {audit_result['leaks_found']} 处潜在敏感信息泄露")
else:
    print("✅ 安全审计通过")

if is_meltdown():
    print(f"\n❌ 今日 API 预算已耗尽！熔断触发，任务终止。")
    exit(1)
else:
    print(f"✅ 预算充足 (${get_status()['remaining']})")

if is_meltdown_active():
    print(f"\n❌ Guard Dog 熔断已触发！系统锁定，任务终止。")
    print(f"   解除熔断请运行: python -c \"from core.guard_dog import release_meltdown; release_meltdown()\"")
    exit(1)

print(f"\n🧠 混合大脑部署:")
for name, cfg in [("高阶决策", get_llm_config("high")), ("常规任务", get_llm_config("medium")), ("低成本任务", get_llm_config("low"))]:
    print(f"    {name} → {cfg['model']}")

MISSION_ROUTER = {
    "1": run_financial_mission,
    "2": run_arsenal_mission,
    "3": run_marketing_mission,
    "4": run_total_war,
    "5": run_academy_mission,
    "6": run_logistics_mission,
    "7": run_campaign_mission,
    "8": run_campaign_execute_mission,
    "9": run_dashboard_mission,
    "10": run_identity_mission,
    "11": run_guard_dog_mission,
    "12": run_rag_mission,
    "13": run_shadow_test_mission,
    "14": run_resume_mission,
    "15": run_market_data_mission,
    "16": run_backtest_mission,
    "17": run_portfolio_mission,
    "18": run_chief_of_staff_mission,
    "19": run_scheduler_mission,
}

show_menu()

choice = None
try:
    choice = get_choice()
except (EOFError, KeyboardInterrupt) as e:
    print(f"\n⚠️  输入中断 ({type(e).__name__})，使用默认选项 15 (行情数据引擎)")
    choice = "15"

mission_func = MISSION_ROUTER.get(choice)
if not mission_func:
    print("❌ 无效选择")
    exit(1)

final_output = None
try:
    final_output = mission_func(SESSION_ID)
except KeyboardInterrupt:
    print(f"\n\n⚠️  任务被用户中断 (KeyboardInterrupt)")
    print("   部分结果可能已保存到日志")
    final_output = "任务被用户中断"
except Exception as e:
    print(f"\n\n❌ 任务执行异常: {type(e).__name__}: {e}")
    print("   系统将继续生成报告")
    final_output = f"任务异常: {e}"

if final_output is None:
    final_output = "任务未返回结果"

report_name = generate_report(SESSION_ID, [], final_output)

print(f"\n{'='*60}")
print(f"  📄 报告摘要")
print(f"{'='*60}")
try:
    with open(report_name, "r", encoding="utf-8") as f:
        print(f.read())
except:
    pass

print(f"\n📁 完整报告文件: {os.path.abspath(report_name)}")
print(f"📁 作战日志: battle_logs/{SESSION_ID}.md")
open_report(report_name)
